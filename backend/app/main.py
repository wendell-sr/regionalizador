from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.schemas import (
    AlgorithmMetricsResponse,
    CompareResult,
    CompareStatus,
    GeocodedItem,
    GeocodedResult,
    GeocodingJobStatus,
    JobStatusResponse,
    KScoreResponse,
    SuggestRegionsRequest,
    SuggestRegionsResponse,
)
from app.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.models import CompareJob, GeocodingItem, GeocodingJob, Job
from app.domain.exceptions import EmptyDataError
from app.services.geocoding import geocoding_service
from app.services.io_loaders import load_participants, load_schools
from app.services.geography import (
    filter_points_within_city,
    find_city,
    load_shapefile_zip,
    reproject,
)
from app.services.clustering import (
    build_regions,
    compare_algorithms,
    run_kmeans,
    suggest_n_regions,
)
from app.services.exporter import (
    ALLOWED_ARTIFACTS,
    artifact_path,
    build_geojson,
    export_to_kml,
    export_to_xlsx,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.post("/jobs", response_model=JobStatusResponse)
async def create_job(
    background: BackgroundTasks,
    schools: UploadFile = File(...),
    participants: UploadFile = File(...),
    shapefile: UploadFile = File(...),
    city_name: str = Form(...),
    n_regions: int = Form(...),
    max_radius_km: float | None = Form(default=None),
    capacity_factor: float = Form(default=1.2),
    target_crs: str = Form(default="EPSG:31983"),
) -> JobStatusResponse:
    job_id = str(uuid.uuid4())
    storage = Path(settings.storage_dir) / job_id
    storage.mkdir(parents=True, exist_ok=True)

    (storage / "schools.xlsx").write_bytes(await schools.read())
    (storage / "participants.xlsx").write_bytes(await participants.read())
    (storage / "shapefile.zip").write_bytes(await shapefile.read())

    with SessionLocal() as db:
        db.add(
            Job(
                id=job_id,
                status="pending",
                params={
                    "city_name": city_name,
                    "n_regions": n_regions,
                    "max_radius_km": max_radius_km,
                    "capacity_factor": capacity_factor,
                    "target_crs": target_crs,
                },
            )
        )
        db.commit()

    background.add_task(_run_job, job_id)
    return _job_to_response(job_id)


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        return JobStatusResponse(
            id=job.id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            metrics=job.metrics or {},
        )


@app.get("/jobs/{job_id}/files/{name}")
def download_file(job_id: str, name: str):
    """Download de artefato (XLSX/KML) — apenas para jobs com status `done`.

    O nome é validado contra `ALLOWED_ARTIFACTS` (whitelist) para impedir
    path traversal. O arquivo é servido com o nome original.
    """
    if name not in ALLOWED_ARTIFACTS:
        raise HTTPException(400, f"Artefato inválido. Permitidos: {sorted(ALLOWED_ARTIFACTS)}")

    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        if job.status != "done":
            raise HTTPException(400, f"Job não está concluído (status={job.status})")

    storage = Path(settings.storage_dir) / job_id
    try:
        path = artifact_path(storage, name)
    except ValueError:
        raise HTTPException(400, "Artefato inválido")

    if not path.exists():
        raise HTTPException(404, f"Arquivo não encontrado: {name}")

    media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if name.endswith(".xlsx")
        else "application/vnd.google-earth.kml+xml"
    )
    return FileResponse(path, media_type=media_type, filename=name)


@app.get("/jobs/{job_id}/geojson")
def get_job_geojson(job_id: str):
    """GeoJSON do resultado (4 camadas: regions, schools, participants, city).

    Disponível apenas para jobs em status `done`. O `build_geojson` salva
    o resultado já reprojetado para WGS84 com sub-amostragem de participantes
    aplicada no `_run_job`.
    """
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        if job.status != "done":
            raise HTTPException(400, f"Job não está concluído (status={job.status})")
        return job.result_geojson or {"type": "FeatureCollection", "features": []}


@app.post("/jobs/suggest-regions", response_model=SuggestRegionsResponse)
def suggest_regions(req: SuggestRegionsRequest) -> SuggestRegionsResponse:
    """Sugere `n_regions` ótimo via silhouette score.

    Reusa `suggest_n_regions` (services/clustering.py) com k ∈ [2, min(15, √N)].
    """
    if not req.participants:
        raise HTTPException(400, "Lista de participantes vazia")

    df = pd.DataFrame([p.model_dump() for p in req.participants])
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    if df.empty:
        raise HTTPException(400, "Nenhum participante com coordenadas válidas")

    proj = reproject(df, req.target_crs)
    xy = proj[["x", "y"]].values

    try:
        result = suggest_n_regions(xy)
    except EmptyDataError as e:
        raise HTTPException(400, str(e))

    return SuggestRegionsResponse(
        recommended=result.recommended,
        n_participants=result.n_participants,
        scores=[
            KScoreResponse(k=s.k, silhouette=s.silhouette, inertia=s.inertia)
            for s in result.scores
        ],
    )


def _job_to_response(job_id: str) -> JobStatusResponse:
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        return JobStatusResponse(
            id=job.id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            metrics=job.metrics or {},
        )


def _update_job(job_id: str, **fields) -> None:
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            return
        for k, v in fields.items():
            setattr(job, k, v)
        db.commit()


def _run_job(job_id: str) -> None:
    try:
        storage = Path(settings.storage_dir) / job_id
        _update_job(job_id, status="loading", progress=0.05, message="Carregando arquivos")

        schools_df, _ = load_schools(storage / "schools.xlsx")
        participants_df, _ = load_participants(storage / "participants.xlsx")

        gdf = load_shapefile_zip(storage / "shapefile.zip", storage / "shp")
        with SessionLocal() as db:
            job = db.get(Job, job_id)
            params = job.params
        city = find_city(gdf, params["city_name"])

        schools_df = filter_points_within_city(
            schools_df.rename(columns={"lat": "lat", "lon": "lon"}).assign(
                lat=schools_df["lat"], lon=schools_df["lon"]
            ),
            city,
        )
        participants_df = filter_points_within_city(
            participants_df.rename(columns={"lat": "lat", "lon": "lon"}).assign(
                lat=participants_df["lat"], lon=participants_df["lon"]
            ),
            city,
        )

        if participants_df.empty:
            raise ValueError("Nenhum participante dentro do município")

        target_crs = params.get("target_crs", "EPSG:31983")
        schools_proj = reproject(schools_df, target_crs)
        participants_proj = reproject(participants_df, target_crs)
        participants_proj["id"] = range(len(participants_proj))
        schools_proj["id"] = range(len(schools_proj))

        _update_job(job_id, status="clustering", progress=0.4, message="Calculando regiões")

        xy = participants_proj[["x", "y"]].values
        labels, _ = run_kmeans(xy, n_clusters=params["n_regions"])

        max_radius_m = params.get("max_radius_km", 0) * 1000 if params.get("max_radius_km") else None

        result = build_regions(
            participants=participants_proj,
            schools=schools_proj,
            labels=labels,
            target_crs=target_crs,
            max_radius_m=max_radius_m,
            capacity_factor=params.get("capacity_factor", 1.2),
        )

        _update_job(job_id, status="exporting", progress=0.8, message="Exportando resultados")
        export_to_xlsx(result, storage)
        export_to_kml(result, storage)

        result.city_name = params["city_name"]
        result.target_crs = target_crs
        geojson = build_geojson(result, city_geom_wkt=city.geom.wkt)

        _update_job(
            job_id,
            status="done",
            progress=1.0,
            message="Concluído",
            metrics=result.metrics,
            result_geojson=geojson,
        )
    except Exception as e:
        _update_job(job_id, status="failed", message=str(e))


# -----------------------------------------------------------------------------
# Geocoding (Spec 005)
# -----------------------------------------------------------------------------


def _update_geocoding_job(job_id: str, **fields) -> None:
    with SessionLocal() as db:
        job = db.get(GeocodingJob, job_id)
        if not job:
            return
        for k, v in fields.items():
            setattr(job, k, v)
        db.commit()


def _geocoding_job_to_response(job: GeocodingJob) -> GeocodingJobStatus:
    return GeocodingJobStatus(
        id=job.id,
        status=job.status,
        total=job.total,
        processed=job.processed,
        succeeded=job.succeeded,
        failed=job.failed,
        progress=job.progress,
        message=job.message,
    )


@app.post("/jobs/geocode", response_model=GeocodingJobStatus)
async def create_geocoding_job(
    background: BackgroundTasks,
    file: UploadFile = File(...),
) -> GeocodingJobStatus:
    """Cria job de geocoding assíncrono.

    Recebe XLSX/CSV com colunas CEP/Bairro/Cidade/UF. Resolve lat/lon via
    AwesomeAPI → Nominatim com rate limit + cache + retry.
    """
    from app.services.io_loaders import _read_table

    job_id = str(uuid.uuid4())
    storage = Path(settings.storage_dir) / "geocoding" / job_id
    storage.mkdir(parents=True, exist_ok=True)

    raw = await file.read()
    input_path = storage / f"input{Path(file.filename or '').suffix or '.xlsx'}"
    input_path.write_bytes(raw)

    try:
        df = _read_table(input_path)
    except Exception as e:
        raise HTTPException(400, f"Erro ao ler arquivo: {e}")

    cols = {c.lower().strip(): c for c in df.columns}

    def col(*aliases: str) -> str | None:
        for a in aliases:
            if a in cols:
                return cols[a]
        return None

    cep_col = col("cep", "zip", "zipcode")
    bairro_col = col("bairro", "neighborhood", "district")
    cidade_col = col("cidade", "city", "municipio", "municipality")
    uf_col = col("uf", "state")
    endereco_col = col("endereco", "address", "logradouro")

    if not (cep_col or (bairro_col and cidade_col) or endereco_col):
        raise HTTPException(400, "Nenhuma coluna de CEP, bairro+cidade ou endereço encontrada")

    items: list[dict] = []
    for i, row in df.iterrows():
        cep = str(row[cep_col]) if cep_col and pd.notna(row[cep_col]) else ""
        bairro = str(row[bairro_col]) if bairro_col and pd.notna(row[bairro_col]) else ""
        cidade = str(row[cidade_col]) if cidade_col and pd.notna(row[cidade_col]) else ""
        uf = str(row[uf_col]) if uf_col and pd.notna(row[uf_col]) else ""
        endereco = str(row[endereco_col]) if endereco_col and pd.notna(row[endereco_col]) else ""
        address = ", ".join(p for p in [endereco, bairro, cidade, uf, "Brazil"] if p)
        items.append({"index": int(i), "cep": cep, "address": address})

    output_path = storage / "geocoded.xlsx"
    failed_path = storage / "failed_only.xlsx"

    with SessionLocal() as db:
        db.add(
            GeocodingJob(
                id=job_id,
                status="pending",
                total=len(items),
                source_filename=file.filename or "",
                output_path=str(output_path),
                failed_path=str(failed_path),
            )
        )
        for item in items:
            db.add(
                GeocodingItem(
                    job_id=job_id,
                    row_index=item["index"],
                    input_address=item["address"],
                    input_cep=item["cep"],
                )
            )
        db.commit()

    background.add_task(_run_geocoding_job, job_id, items, input_path, output_path, failed_path)
    with SessionLocal() as db:
        job = db.get(GeocodingJob, job_id)
        return _geocoding_job_to_response(job)


def _run_geocoding_job(
    job_id: str,
    items: list[dict],
    input_path: Path,
    output_path: Path,
    failed_path: Path,
) -> None:
    """Processa geocoding em chunks com progresso."""
    try:
        _update_geocoding_job(job_id, status="processing", message="Geocodificando...")

        # Processa cada item sequencialmente (rate limit no Nominatim)
        for idx, item in enumerate(items):
            result = asyncio.run(
                geocoding_service.geocode(
                    address=item["address"], cep=item.get("cep") or None
                )
            )
            if result:
                with SessionLocal() as db:
                    gi = (
                        db.query(GeocodingItem)
                        .filter_by(job_id=job_id, row_index=item["index"])
                        .first()
                    )
                    if gi:
                        gi.lat = result.lat
                        gi.lon = result.lon
                        gi.source = result.source
                        gi.success = True
                        db.commit()
            if (idx + 1) % 5 == 0 or (idx + 1) == len(items):
                with SessionLocal() as db:
                    job = db.get(GeocodingJob, job_id)
                    succeeded = db.query(GeocodingItem).filter_by(job_id=job_id, success=True).count()
                    failed = db.query(GeocodingItem).filter_by(job_id=job_id, success=False).count()
                    _update_geocoding_job(
                        job_id,
                        processed=idx + 1,
                        succeeded=succeeded,
                        failed=failed,
                        progress=(idx + 1) / len(items) if items else 0,
                    )

        # Exporta XLSX final
        original = (
            pd.read_excel(input_path)
            if input_path.suffix.lower() in {".xlsx", ".xls"}
            else pd.read_csv(input_path)
        )
        with SessionLocal() as db:
            rows = (
                db.query(GeocodingItem)
                .filter_by(job_id=job_id)
                .order_by(GeocodingItem.row_index)
                .all()
            )
            for r in rows:
                if r.lat is not None and r.lon is not None:
                    original.loc[r.row_index, "Latitude"] = r.lat
                    original.loc[r.row_index, "Longitude"] = r.lon
                original.loc[r.row_index, "GeocodingSource"] = r.source or ""
                original.loc[r.row_index, "GeocodingSuccess"] = bool(r.success)
        original.to_excel(output_path, index=False)

        if "GeocodingSuccess" in original.columns:
            mask = ~original["GeocodingSuccess"].astype(bool)
            failed_only = original[mask].copy()
        else:
            failed_only = original.iloc[0:0]
        failed_only.to_excel(failed_path, index=False)

        with SessionLocal() as db:
            job = db.get(GeocodingJob, job_id)
            succeeded = job.succeeded
            total = job.total
        stats = geocoding_service.stats()
        _update_geocoding_job(
            job_id,
            status="done",
            progress=1.0,
            message=(
                f"{succeeded}/{total} resolvidos "
                f"({round(100 * succeeded / max(total, 1))}%); "
                f"cache={stats['cache_size']} hits={stats['hits']} "
                f"misses={stats['misses']} errors={stats['errors']}"
            ),
        )
    except Exception as e:
        _update_geocoding_job(job_id, status="failed", message=str(e))


@app.get("/jobs/geocoding/{job_id}", response_model=GeocodingJobStatus)
def get_geocoding_job(job_id: str) -> GeocodingJobStatus:
    with SessionLocal() as db:
        job = db.get(GeocodingJob, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        return _geocoding_job_to_response(job)


@app.get("/jobs/geocoding/{job_id}/geocoded", response_model=GeocodedResult)
def get_geocoded(job_id: str) -> GeocodedResult:
    with SessionLocal() as db:
        if not db.get(GeocodingJob, job_id):
            raise HTTPException(404, "Job não encontrado")
        rows = (
            db.query(GeocodingItem)
            .filter_by(job_id=job_id)
            .order_by(GeocodingItem.row_index)
            .all()
        )
        return GeocodedResult(
            items=[
                GeocodedItem(
                    index=r.row_index,
                    input=r.input_address or r.input_cep or f"row {r.row_index}",
                    lat=r.lat,
                    lon=r.lon,
                    source=r.source,
                    success=r.success,
                )
                for r in rows
            ]
        )


GEOCODING_FILES: dict[str, str] = {
    "geocoded.xlsx": "output_path",
    "failed_only.xlsx": "failed_path",
}


@app.get("/jobs/geocoding/{job_id}/files/{name}")
def download_geocoded_file(job_id: str, name: str):
    if name not in GEOCODING_FILES:
        raise HTTPException(400, f"Arquivo inválido. Permitidos: {list(GEOCODING_FILES)}")
    with SessionLocal() as db:
        job = db.get(GeocodingJob, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        if job.status != "done":
            raise HTTPException(400, f"Job não está concluído (status={job.status})")
        path = Path(getattr(job, GEOCODING_FILES[name]))
    if not path.exists():
        raise HTTPException(404, f"Arquivo não encontrado: {name}")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=name,
    )


# -----------------------------------------------------------------------------
# Compare Algorithms (Spec 006)
# -----------------------------------------------------------------------------


def _update_compare_job(job_id: str, **fields) -> None:
    with SessionLocal() as db:
        job = db.get(CompareJob, job_id)
        if not job:
            return
        for k, v in fields.items():
            setattr(job, k, v)
        db.commit()


def _compare_to_response(job: CompareJob) -> CompareStatus:
    return CompareStatus(
        id=job.id,
        status=job.status,
        progress=job.progress,
        message=job.message,
    )


@app.post("/jobs/compare", response_model=CompareStatus)
async def create_compare_job(
    background: BackgroundTasks,
    schools: UploadFile = File(...),
    participants: UploadFile = File(...),
    shapefile: UploadFile = File(...),
    city_name: str = Form(...),
    n_clusters_hint: int = Form(default=5),
) -> CompareStatus:
    """Cria job de comparativo de algoritmos ML (spec 006)."""

    job_id = str(uuid.uuid4())
    storage = Path(settings.storage_dir) / "compare" / job_id
    storage.mkdir(parents=True, exist_ok=True)

    (storage / "schools.xlsx").write_bytes(await schools.read())
    (storage / "participants.xlsx").write_bytes(await participants.read())
    (storage / "shapefile.zip").write_bytes(await shapefile.read())

    with SessionLocal() as db:
        db.add(
            CompareJob(
                id=job_id,
                status="pending",
                params={
                    "city_name": city_name,
                    "n_clusters_hint": n_clusters_hint,
                },
            )
        )
        db.commit()

    background.add_task(_run_compare_job, job_id)
    return _compare_to_response(db.get(CompareJob, job_id))


def _run_compare_job(job_id: str) -> None:
    try:
        storage = Path(settings.storage_dir) / "compare" / job_id
        _update_compare_job(job_id, status="processing", progress=0.1, message="Carregando dados")

        schools_df, _ = load_schools(storage / "schools.xlsx")
        participants_df, _ = load_participants(storage / "participants.xlsx")

        gdf = load_shapefile_zip(storage / "shapefile.zip", storage / "shp")
        with SessionLocal() as db:
            job = db.get(CompareJob, job_id)
            params = job.params
        city = find_city(gdf, params["city_name"])

        schools_df = filter_points_within_city(schools_df, city)
        participants_df = filter_points_within_city(participants_df, city)

        if len(participants_df) < 50:
            raise ValueError(
                f"Apenas {len(participants_df)} participantes dentro do município (mínimo 50 para compare)"
            )

        _update_compare_job(job_id, progress=0.4, message="Reprojetando")
        target_crs = "EPSG:31983"
        participants_proj = reproject(participants_df, target_crs)

        xy = participants_proj[["x", "y"]].values
        comparison = compare_algorithms(xy, n_clusters_hint=params.get("n_clusters_hint", 5))

        result_dict = {
            "winner": comparison.winner,
            "n_participants": comparison.n_participants,
            "algorithms": [
                {
                    "algorithm": a.algorithm,
                    "n_clusters": a.n_clusters,
                    "n_noise": a.n_noise,
                    "silhouette": a.silhouette,
                    "inertia": a.inertia,
                    "runtime_ms": a.runtime_ms,
                }
                for a in comparison.algorithms
            ],
        }

        _update_compare_job(
            job_id,
            status="done",
            progress=1.0,
            message=f"Vencedor: {comparison.winner}",
            result=result_dict,
        )
    except Exception as e:
        _update_compare_job(job_id, status="failed", message=str(e))


@app.get("/jobs/compare/{job_id}", response_model=CompareStatus)
def get_compare_status(job_id: str) -> CompareStatus:
    with SessionLocal() as db:
        job = db.get(CompareJob, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        return _compare_to_response(job)


@app.get("/jobs/compare/{job_id}/compare", response_model=CompareResult)
def get_compare_result(job_id: str) -> CompareResult:
    with SessionLocal() as db:
        job = db.get(CompareJob, job_id)
        if not job:
            raise HTTPException(404, "Job não encontrado")
        if job.status != "done":
            raise HTTPException(400, f"Job não está concluído (status={job.status})")
        result = job.result or {}
    return CompareResult(
        winner=result.get("winner", "kmeans"),
        n_participants=result.get("n_participants", 0),
        algorithms=[
            AlgorithmMetricsResponse(
                algorithm=a["algorithm"],
                n_clusters=a["n_clusters"],
                n_noise=a["n_noise"],
                silhouette=a["silhouette"],
                inertia=a["inertia"],
                runtime_ms=a["runtime_ms"],
            )
            for a in result.get("algorithms", [])
        ],
    )
