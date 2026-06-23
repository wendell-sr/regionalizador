from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import simplekml
from pyproj import Transformer
from shapely.geometry import Polygon, mapping
from shapely.ops import transform as shapely_transform

from app.services.clustering import RegionalizationResult

ALLOWED_ARTIFACTS: frozenset[str] = frozenset(
    {
        "regionalizacao_participantes.xlsx",
        "regionalizacao_escolas.xlsx",
        "regionalizacao_regioes.xlsx",
        "regioes.kml",
    }
)


def export_to_xlsx(
    result: RegionalizationResult, output_dir: Path, base_name: str = "regionalizacao"
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    p_path = output_dir / f"{base_name}_participantes.xlsx"
    s_path = output_dir / f"{base_name}_escolas.xlsx"
    r_path = output_dir / f"{base_name}_regioes.xlsx"

    result.participants.to_excel(p_path, index=False)
    paths["participantes"] = p_path

    if not result.schools.empty:
        result.schools.to_excel(s_path, index=False)
        paths["escolas"] = s_path

    rows = []
    for r in result.regions:
        rows.append(
            {
                "regiao": r.index,
                "candidatos": r.candidates,
                "participantes": r.participants,
                "escolas": r.schools,
                "capacidade": r.capacity,
                "raio_max_m": round(r.max_distance_m, 1),
                "status": r.status,
            }
        )
    pd.DataFrame(rows).to_excel(r_path, index=False)
    paths["regioes"] = r_path
    return paths


def export_to_kml(
    result: RegionalizationResult, output_dir: Path, base_name: str = "regioes"
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    kml = simplekml.Kml()
    for r in result.regions:
        if r.polygon is None:
            continue
        pol = kml.newpolygon(
            name=f"Região {r.index}",
            outerboundaryis=list(r.polygon.exterior.coords),
        )
        pol.description = (
            f"Candidatos: {r.candidates}<br>"
            f"Capacidade: {r.capacity}<br>"
            f"Escolas: {r.schools}<br>"
            f"Status: {r.status}"
        )
    out = output_dir / f"{base_name}.kml"
    kml.save(str(out))
    return out


def artifact_path(output_dir: Path, name: str) -> Path:
    """Resolve um nome de artefato validado contra a whitelist.

    Levanta ValueError se o nome não estiver na whitelist (defesa contra path traversal).
    """
    if name not in ALLOWED_ARTIFACTS:
        raise ValueError(f"Artefato inválido: {name}")
    return output_dir / name


def _make_transformer(source_crs: str) -> Transformer:
    return Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)


def _reproject_point(transformer: Transformer, x: float, y: float) -> tuple[float, float]:
    lon, lat = transformer.transform(x, y)
    return lon, lat


def _reproject_polygon(transformer: Transformer, poly: Polygon) -> Polygon:
    return shapely_transform(lambda x, y, z=None: transformer.transform(x, y), poly)


def build_geojson(
    result: RegionalizationResult,
    city_geom_wkt: str | None = None,
    simplify: int = 1,
) -> dict[str, Any]:
    """Constrói FeatureCollection com 4 camadas: regions, schools, participants, city.

    Aceita o `RegionalizationResult` (em coords métricas) e a geometria do município
    (em WGS84, opcional) e devolve um FeatureCollection pronto para Leaflet.

    `simplify` reduz pontos de participantes (1 = todos, N = 1 a cada N).
    """
    transformer = _make_transformer(result.target_crs)
    features: list[dict] = []

    for r in result.regions:
        geom = None
        if r.polygon is not None:
            geom_4326 = _reproject_polygon(transformer, r.polygon)
            geom = mapping(geom_4326)
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "layer": "region",
                    "region_id": r.index,
                    "status": r.status,
                    "candidates": r.candidates,
                    "participants": r.participants,
                    "schools": r.schools,
                    "capacity": r.capacity,
                    "max_distance_m": round(r.max_distance_m, 1),
                },
            }
        )

    if not result.schools.empty:
        for _, row in result.schools.iterrows():
            if "x" not in row or "y" not in row:
                continue
            lon, lat = _reproject_point(transformer, float(row["x"]), float(row["y"]))
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "layer": "school",
                        "name": str(row.get("name", "")),
                        "capacity": int(row.get("capacity", 0)),
                        "region_id": int(row.get("region", -1)) if pd.notna(row.get("region")) else None,
                    },
                }
            )

    if not result.participants.empty and "x" in result.participants.columns:
        step = max(1, int(simplify))
        for i, (_, row) in enumerate(result.participants.iterrows()):
            if i % step != 0:
                continue
            lon, lat = _reproject_point(transformer, float(row["x"]), float(row["y"]))
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "layer": "participant",
                        "qty": int(row.get("qty", 1)) if pd.notna(row.get("qty")) else 1,
                        "region_id": int(row.get("region", -1)) if pd.notna(row.get("region")) else None,
                    },
                }
            )

    if city_geom_wkt:
        from shapely import wkt as shapely_wkt

        city_poly = shapely_wkt.loads(city_geom_wkt)
        features.append(
            {
                "type": "Feature",
                "geometry": mapping(city_poly),
                "properties": {"layer": "city", "name": result.city_name or ""},
            }
        )

    return {"type": "FeatureCollection", "features": features}
