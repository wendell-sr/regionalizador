"""Testes para app/main.py — cobre AC1, AC10 (criação de job e polling de status)."""

from __future__ import annotations

import io
import zipfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.config import settings
from app.db.database import Base, engine


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Cada teste usa DB e storage temporários."""
    test_db = tmp_path / "test.db"
    test_storage = tmp_path / "storage"
    test_storage.mkdir()
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{test_db}")
    monkeypatch.setattr(settings, "storage_dir", str(test_storage))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(main_module.app)


@pytest.fixture
def synthetic_schools_xlsx() -> bytes:
    df = pd.DataFrame(
        {
            "name": ["E1", "E2", "E3"],
            "lat": [-22.95, -22.96, -22.97],
            "lon": [-43.20, -43.21, -43.22],
            "capacity": [30, 30, 30],
        }
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


@pytest.fixture
def synthetic_participants_xlsx() -> bytes:
    df = pd.DataFrame(
        {
            "name": [f"P{i}" for i in range(60)],
            "lat": [-22.95 + (i % 10) * 0.001 for i in range(60)],
            "lon": [-43.20 + (i // 10) * 0.003 for i in range(60)],
        }
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


@pytest.fixture
def synthetic_shapefile_zip(tmp_path) -> bytes:
    """Cria um shapefile válido em disco, retorna o ZIP em bytes."""
    import geopandas as gpd
    from shapely.geometry import Polygon

    poly = Polygon(
        [
            (-43.30, -22.85),
            (-43.10, -22.85),
            (-43.10, -23.05),
            (-43.30, -23.05),
            (-43.30, -22.85),
        ]
    )
    gdf = gpd.GeoDataFrame({"NM_MUN": ["Rio de Janeiro"]}, geometry=[poly], crs="EPSG:4326")
    shp_dir = tmp_path / "shp"
    shp_dir.mkdir()
    gdf.to_file(shp_dir / "muni.shp")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in shp_dir.iterdir():
            zf.write(f, arcname=f.name)
    return buf.getvalue()


class TestHealth:
    def test_returns_ok(self, client: TestClient):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestCreateJob:
    """AC1: POST /jobs cria job em background."""

    def test_create_job_returns_id_and_pending(
        self,
        client: TestClient,
        synthetic_schools_xlsx,
        synthetic_participants_xlsx,
        synthetic_shapefile_zip,
    ):
        r = client.post(
            "/jobs",
            files={
                "schools": ("s.xlsx", synthetic_schools_xlsx, "application/vnd.openxmlformats"),
                "participants": ("p.xlsx", synthetic_participants_xlsx, "application/vnd.openxmlformats"),
                "shapefile": ("muni.zip", synthetic_shapefile_zip, "application/zip"),
            },
            data={"city_name": "Rio", "n_regions": 3},
        )
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert body["status"] in {"pending", "loading", "clustering", "exporting", "done", "failed"}

    def test_missing_shapefile_returns_422(
        self, client: TestClient, synthetic_schools_xlsx, synthetic_participants_xlsx
    ):
        r = client.post(
            "/jobs",
            files={
                "schools": ("s.xlsx", synthetic_schools_xlsx),
                "participants": ("p.xlsx", synthetic_participants_xlsx),
            },
            data={"city_name": "Rio", "n_regions": 3},
        )
        assert r.status_code == 422

    def test_invalid_artifact_name_rejected(self, client: TestClient):
        r = client.get("/jobs/any-id/files/secret.xlsx")
        # 404 (job não existe) ou 400 (nome inválido) — ambos corretos
        assert r.status_code in (400, 404)


class TestGetJob:
    """AC10: GET /jobs/{id} retorna status."""

    def test_404_for_unknown_id(self, client: TestClient):
        r = client.get("/jobs/nonexistent-id")
        assert r.status_code == 404

    def test_get_returns_404(self, client: TestClient):
        r = client.get("/jobs/abc")
        assert r.status_code == 404


class TestDownloadFile:
    """AC9 + defesa contra path traversal."""

    def test_404_for_unknown_job(self, client: TestClient):
        r = client.get("/jobs/abc/files/regionalizacao_participantes.xlsx")
        assert r.status_code == 404

    def test_400_for_invalid_artifact_name(self, client: TestClient):
        r = client.get("/jobs/any/files/../../etc/passwd")
        assert r.status_code in (400, 404)


class TestGeojsonEndpoint:
    """AC8: GET /jobs/{id}/geojson retorna FeatureCollection."""

    def test_404_for_unknown_job(self, client: TestClient):
        r = client.get("/jobs/any-id/geojson")
        assert r.status_code == 404

    def test_400_for_non_done_job(self, client: TestClient, monkeypatch):
        """Job existe mas não está `done`."""
        from app.db.models import Job
        from app.db.database import SessionLocal

        with SessionLocal() as db:
            db.add(Job(id="pending-id", status="loading", params={}))
            db.commit()
        r = client.get("/jobs/pending-id/geojson")
        assert r.status_code == 400

    def test_done_job_returns_geojson(self, client: TestClient):
        from app.db.models import Job
        from app.db.database import SessionLocal

        with SessionLocal() as db:
            db.add(
                Job(
                    id="done-id",
                    status="done",
                    params={},
                    result_geojson={
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": None,
                                "properties": {"layer": "region", "region_id": 0},
                            }
                        ],
                    },
                )
            )
            db.commit()
        r = client.get("/jobs/done-id/geojson")
        assert r.status_code == 200
        body = r.json()
        assert body["type"] == "FeatureCollection"
        assert len(body["features"]) == 1


class TestSuggestRegionsEndpoint:
    """Spec 004 — AC1, AC5: POST /jobs/suggest-regions."""

    def test_basic_suggestion(self, client: TestClient):
        import random

        random.seed(0)
        participants = []
        for cx, cy in [(0, 0), (1000, 0), (500, 1000)]:
            for _ in range(33):
                lat = -22.9 + cx / 1000 * 0.01 + random.uniform(-0.001, 0.001)
                lon = -43.2 + cy / 1000 * 0.01 + random.uniform(-0.001, 0.001)
                participants.append({"lat": lat, "lon": lon, "qty": 1})
        r = client.post("/jobs/suggest-regions", json={"participants": participants})
        assert r.status_code == 200
        body = r.json()
        assert body["recommended"] >= 2
        assert body["n_participants"] == 99
        assert len(body["scores"]) >= 2
        for s in body["scores"]:
            assert "k" in s
            assert "silhouette" in s
            assert "inertia" in s

    def test_400_for_empty_list(self, client: TestClient):
        r = client.post("/jobs/suggest-regions", json={"participants": []})
        assert r.status_code == 400

    def test_400_for_fewer_than_10(self, client: TestClient):
        participants = [{"lat": -22.9, "lon": -43.2, "qty": 1} for _ in range(5)]
        r = client.post("/jobs/suggest-regions", json={"participants": participants})
        assert r.status_code == 400

    def test_drops_nan_coords(self, client: TestClient):
        """Coords ausentes/vazias são removidas antes da sugestão."""
        participants = [{"lat": -22.9, "lon": -43.2, "qty": 1} for _ in range(20)]
        participants.append({"lat": None, "lon": None, "qty": 1})
        r = client.post("/jobs/suggest-regions", json={"participants": participants})
        assert r.status_code == 200
        assert r.json()["n_participants"] == 20


class TestGeocodingEndpoints:
    """Spec 005 — AC1, AC6, AC7, AC8: POST /jobs/geocode, GET, downloads."""

    def test_create_geocoding_job_cep_only(self, client: TestClient):
        from io import BytesIO
        import pandas as pd

        df = pd.DataFrame({"CEP": ["01000000", "20000000", "30100000"]})
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        r = client.post(
            "/jobs/geocode",
            files={"file": ("p.xlsx", buf.getvalue(), "application/vnd.openxmlformats")},
        )
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert body["status"] in {"pending", "processing", "done", "failed"}
        assert body["total"] == 3

    def test_create_geocoding_job_address(self, client: TestClient):
        from io import BytesIO
        import pandas as pd

        df = pd.DataFrame(
            {
                "Bairro": ["Centro"] * 5,
                "Cidade": ["Rio de Janeiro"] * 5,
                "UF": ["RJ"] * 5,
            }
        )
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        r = client.post(
            "/jobs/geocode",
            files={"file": ("p.xlsx", buf.getvalue(), "application/vnd.openxmlformats")},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 5

    def test_create_geocoding_job_400_no_columns(self, client: TestClient):
        from io import BytesIO
        import pandas as pd

        df = pd.DataFrame({"foo": [1, 2, 3]})
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        r = client.post(
            "/jobs/geocode",
            files={"file": ("p.xlsx", buf.getvalue(), "application/vnd.openxmlformats")},
        )
        assert r.status_code == 400

    def test_get_geocoding_job_404(self, client: TestClient):
        r = client.get("/jobs/geocoding/any-id")
        assert r.status_code == 404

    def test_get_geocoded_items_404(self, client: TestClient):
        r = client.get("/jobs/geocoding/any-id/geocoded")
        assert r.status_code == 404

    def test_get_geocoded_items_returns_list(self, client: TestClient):
        from app.db.database import SessionLocal
        from app.db.models import GeocodingItem, GeocodingJob

        with SessionLocal() as db:
            job = GeocodingJob(id="g1", status="done", total=2)
            db.add(job)
            db.add(GeocodingItem(job_id="g1", row_index=0, input_cep="01000000", lat=-22.9, lon=-43.2, source="awesomeapi", success=True))
            db.add(GeocodingItem(job_id="g1", row_index=1, input_address="Centro, Rio", lat=None, lon=None, source=None, success=False))
            db.commit()
        r = client.get("/jobs/geocoding/g1/geocoded")
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) == 2
        assert body["items"][0]["success"] is True
        assert body["items"][1]["success"] is False

    def test_download_file_400_unknown(self, client: TestClient):
        r = client.get("/jobs/geocoding/any/files/unknown.xlsx")
        assert r.status_code in (400, 404)


class TestCompareEndpoints:
    """Spec 006 — AC1, AC11: POST /jobs/compare, GET /jobs/compare/{id}/compare."""

    def test_create_compare_job_400_missing_shapefile(self, client: TestClient):
        r = client.post(
            "/jobs/compare",
            files={
                "schools": ("s.xlsx", b"x"),
                "participants": ("p.xlsx", b"x"),
            },
            data={"city_name": "Rio", "n_clusters_hint": 3},
        )
        assert r.status_code == 422

    def test_get_compare_status_404(self, client: TestClient):
        r = client.get("/jobs/compare/any-id")
        assert r.status_code == 404

    def test_get_compare_result_404(self, client: TestClient):
        r = client.get("/jobs/compare/any-id/compare")
        assert r.status_code == 404

    def test_get_compare_result_400_when_not_done(self, client: TestClient):
        from app.db.database import SessionLocal
        from app.db.models import CompareJob

        with SessionLocal() as db:
            db.add(CompareJob(id="c1", status="processing", params={}))
            db.commit()
        r = client.get("/jobs/compare/c1/compare")
        assert r.status_code == 400

    def test_get_compare_result_returns_algorithms(self, client: TestClient):
        from app.db.database import SessionLocal
        from app.db.models import CompareJob

        with SessionLocal() as db:
            db.add(
                CompareJob(
                    id="c2",
                    status="done",
                    params={},
                    result={
                        "winner": "kmeans",
                        "n_participants": 100,
                        "algorithms": [
                            {
                                "algorithm": "kmeans",
                                "n_clusters": 5,
                                "n_noise": 0,
                                "silhouette": 0.6,
                                "inertia": 100.0,
                                "runtime_ms": 50,
                            },
                            {
                                "algorithm": "kmedoids",
                                "n_clusters": 5,
                                "n_noise": 0,
                                "silhouette": 0.55,
                                "inertia": 120.0,
                                "runtime_ms": 80,
                            },
                            {
                                "algorithm": "dbscan",
                                "n_clusters": 4,
                                "n_noise": 10,
                                "silhouette": 0.4,
                                "inertia": None,
                                "runtime_ms": 30,
                            },
                        ],
                    },
                )
            )
            db.commit()
        r = client.get("/jobs/compare/c2/compare")
        assert r.status_code == 200
        body = r.json()
        assert body["winner"] == "kmeans"
        assert body["n_participants"] == 100
        assert len(body["algorithms"]) == 3
        assert body["algorithms"][0]["algorithm"] == "kmeans"
