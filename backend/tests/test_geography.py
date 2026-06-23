"""Testes para services/geography.py — cobre AC3 (filtragem por município)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import Polygon

from app.services.geography import (
    CityGeometry,
    filter_points_within_city,
    load_shapefile_zip,
    reproject,
)


@pytest.fixture
def city_rio() -> CityGeometry:
    """Retângulo de teste (apenas para unit tests, não é a geografia real do RJ)."""
    poly = Polygon(
        [
            (-43.30, -22.90),
            (-43.10, -22.90),
            (-43.10, -23.00),
            (-43.30, -23.00),
            (-43.30, -22.90),
        ]
    )
    return CityGeometry(name="Rio de Janeiro", geom=poly, crs="EPSG:4326")


class TestFilterPointsWithinCity:
    """AC3: apenas pontos dentro do município passam."""

    def test_keeps_inside(self, city_rio):
        df = pd.DataFrame({"name": ["A", "B"], "lat": [-22.95, -22.92], "lon": [-43.20, -43.25]})
        out = filter_points_within_city(df, city_rio)
        assert len(out) == 2

    def test_drops_outside(self, city_rio):
        df = pd.DataFrame(
            {
                "name": ["A", "B"],
                "lat": [-22.95, -23.50],
                "lon": [-43.20, -46.60],  # B = São Paulo
            }
        )
        out = filter_points_within_city(df, city_rio)
        assert len(out) == 1
        assert out.iloc[0]["name"] == "A"

    def test_keeps_all_when_empty(self, city_rio):
        df = pd.DataFrame(columns=["name", "lat", "lon"])
        out = filter_points_within_city(df, city_rio)
        assert out.empty


class TestReproject:
    def test_reproject_to_metric_crs(self):
        df = pd.DataFrame({"name": ["A"], "lat": [-22.9], "lon": [-43.2]})
        out = reproject(df, "EPSG:31983")
        assert "x" in out.columns
        assert "y" in out.columns
        # UTM-23S: (-43.2, -22.9) → (684624, 7466421)
        assert 684000 < out.iloc[0]["x"] < 685000
        assert 7466000 < out.iloc[0]["y"] < 7467000

    def test_reproject_empty(self):
        df = pd.DataFrame(columns=["name", "lat", "lon"])
        out = reproject(df, "EPSG:31983")
        assert out.empty


class TestFindCity:
    """Requer shapefile real — coberto indiretamente pelo teste de API."""

    def test_load_shapefile_zip_raises_when_not_zip(self, tmp_path: Path):
        fake = tmp_path / "notazip.zip"
        fake.write_bytes(b"not a real zip")
        with pytest.raises(Exception):
            load_shapefile_zip(fake, tmp_path / "out")
