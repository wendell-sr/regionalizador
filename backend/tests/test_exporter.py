"""Testes para services/exporter.py — cobre AC9 (artefatos gerados)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.services.clustering import RegionalizationResult, Region
from app.services.exporter import (
    ALLOWED_ARTIFACTS,
    artifact_path,
    build_geojson,
    export_to_kml,
    export_to_xlsx,
)


@pytest.fixture
def sample_result() -> RegionalizationResult:
    from shapely.geometry import Polygon

    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    regions = [
        Region(
            index=0,
            polygon=poly,
            candidates=20,
            participants=20,
            schools=1,
            capacity=25,
            max_distance_m=70.7,
            status="ok",
            centroid_x=50.0,
            centroid_y=50.0,
            school_ids=[0],
            participant_ids=list(range(20)),
        )
    ]
    participants = pd.DataFrame(
        {"id": range(20), "x": np.linspace(0, 100, 20), "y": np.linspace(0, 100, 20), "region": 0}
    )
    schools = pd.DataFrame({"id": [0], "x": [50.0], "y": [50.0], "capacity": [25], "region": 0})
    return RegionalizationResult(
        regions=regions, participants=participants, schools=schools, metrics={"silhouette": 0.5}
    )


class TestExportToXlsx:
    """AC9: XLSX com participantes, escolas e regiões."""

    def test_creates_three_xlsx(self, tmp_path: Path, sample_result):
        paths = export_to_xlsx(sample_result, tmp_path)
        assert "participantes" in paths
        assert "escolas" in paths
        assert "regioes" in paths
        assert paths["participantes"].exists()
        assert paths["escolas"].exists()
        assert paths["regioes"].exists()

    def test_xlsx_can_be_read_back(self, tmp_path: Path, sample_result):
        paths = export_to_xlsx(sample_result, tmp_path)
        df = pd.read_excel(paths["regioes"])
        assert "regiao" in df.columns
        assert "status" in df.columns
        assert df.iloc[0]["regiao"] == 0
        assert df.iloc[0]["status"] == "ok"

    def test_empty_schools_skips_file(self, tmp_path, sample_result):
        sample_result.schools = pd.DataFrame(columns=["id", "x", "y", "capacity", "region"])
        paths = export_to_xlsx(sample_result, tmp_path)
        assert "escolas" not in paths


class TestExportToKml:
    def test_creates_kml(self, tmp_path: Path, sample_result):
        out = export_to_kml(sample_result, tmp_path)
        assert out.exists()
        assert out.suffix == ".kml"
        content = out.read_text(encoding="utf-8")
        assert "Região" in content
        assert "Capacidade" in content

    def test_skips_regions_without_polygon(self, tmp_path, sample_result):
        sample_result.regions[0].polygon = None
        out = export_to_kml(sample_result, tmp_path)
        assert out.exists()


class TestArtifactPath:
    """Defesa contra path traversal."""

    def test_valid_name(self, tmp_path: Path):
        path = artifact_path(tmp_path, "regionalizacao_participantes.xlsx")
        assert path == tmp_path / "regionalizacao_participantes.xlsx"

    def test_rejects_path_traversal(self, tmp_path: Path):
        with pytest.raises(ValueError, match="Artefato inválido"):
            artifact_path(tmp_path, "../../etc/passwd")

    def test_rejects_arbitrary_name(self, tmp_path: Path):
        with pytest.raises(ValueError, match="Artefato inválido"):
            artifact_path(tmp_path, "secret.xlsx")

    def test_whitelist_is_complete(self):
        assert "regionalizacao_participantes.xlsx" in ALLOWED_ARTIFACTS
        assert "regionalizacao_escolas.xlsx" in ALLOWED_ARTIFACTS
        assert "regionalizacao_regioes.xlsx" in ALLOWED_ARTIFACTS
        assert "regioes.kml" in ALLOWED_ARTIFACTS


class TestBuildGeojson:
    """AC8: GeoJSON com 4 camadas (regions, schools, participants, city) reprojetado para WGS84."""

    def test_returns_featurecollection(self, sample_result):
        result = sample_result
        result.target_crs = "EPSG:31983"
        gj = build_geojson(result)
        assert gj["type"] == "FeatureCollection"
        assert isinstance(gj["features"], list)

    def test_contains_all_4_layers(self, sample_result):
        result = sample_result
        result.target_crs = "EPSG:31983"
        gj = build_geojson(result)
        layers = {f["properties"].get("layer") for f in gj["features"]}
        assert "region" in layers
        assert "school" in layers
        assert "participant" in layers

    def test_geometry_in_wgs84_lonlat_order(self, sample_result):
        """Leaflet espera [lon, lat] em EPSG:4326. Coordenadas UTM (0,0) viram lon/lat consistentes."""
        result = sample_result
        result.target_crs = "EPSG:31983"
        gj = build_geojson(result)
        for f in gj["features"]:
            geom = f.get("geometry")
            if geom and geom["type"] == "Point":
                lon, lat = geom["coordinates"]
                # Coordenadas válidas em WGS84
                assert -180 <= lon <= 180
                assert -90 <= lat <= 90
                # (0, 0) em UTM-23S (zona equatorial) está em lon≈-75, lat≈0
                assert -180 < lon < 180
                assert -90 < lat < 90

    def test_region_has_status_and_metrics(self, sample_result):
        result = sample_result
        result.target_crs = "EPSG:31983"
        gj = build_geojson(result)
        regions = [f for f in gj["features"] if f["properties"].get("layer") == "region"]
        assert len(regions) == 1
        props = regions[0]["properties"]
        assert props["status"] == "ok"
        assert "capacity" in props
        assert "candidates" in props

    def test_city_layer_when_provided(self, sample_result):
        from shapely.geometry import Polygon

        city = Polygon([(-43.3, -22.9), (-43.1, -22.9), (-43.1, -23.0), (-43.3, -23.0), (-43.3, -22.9)])
        result = sample_result
        result.target_crs = "EPSG:31983"
        gj = build_geojson(result, city_geom_wkt=city.wkt)
        layers = {f["properties"].get("layer") for f in gj["features"]}
        assert "city" in layers

    def test_simplify_reduces_participants(self, sample_result):
        """Com simplify=2, deve ter metade dos participantes."""
        import pandas as pd

        result = sample_result
        result.target_crs = "EPSG:31983"
        # Aumenta para 10 participantes
        result.participants = pd.DataFrame(
            {
                "x": [i * 5.0 for i in range(10)],
                "y": [i * 5.0 for i in range(10)],
                "qty": 1,
                "id": range(10),
                "region": 0,
            }
        )
        gj_full = build_geojson(result, simplify=1)
        gj_half = build_geojson(result, simplify=2)
        full_count = sum(1 for f in gj_full["features"] if f["properties"].get("layer") == "participant")
        half_count = sum(1 for f in gj_half["features"] if f["properties"].get("layer") == "participant")
        assert full_count == 10
        assert half_count == 5

    def test_empty_schools_and_participants(self, tmp_path):
        import pandas as pd

        result = RegionalizationResult(
            regions=[],
            participants=pd.DataFrame(columns=["x", "y", "qty", "id", "region"]),
            schools=pd.DataFrame(columns=["x", "y", "capacity", "id", "name", "region"]),
            metrics={},
            target_crs="EPSG:31983",
        )
        gj = build_geojson(result)
        assert gj["type"] == "FeatureCollection"
        assert gj["features"] == []
