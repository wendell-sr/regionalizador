"""Testes para services/io_loaders.py — cobre AC2 (aliases de coluna)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.services.io_loaders import load_participants, load_schools


class TestLoadSchools:
    """AC2: aceita variações de nomes de coluna."""

    def test_canonical_columns(self, tmp_path: Path):
        df = pd.DataFrame(
            {
                "name": ["E1", "E2"],
                "lat": [-22.9, -22.95],
                "lon": [-43.2, -43.25],
                "capacity": [50, 30],
            }
        )
        p = tmp_path / "schools.xlsx"
        df.to_excel(p, index=False)
        out, cols = load_schools(p)
        assert len(out) == 2
        assert out["capacity"].sum() == 80
        assert set(cols) == {"name", "lat", "lon", "capacity"}

    def test_alternative_column_names(self, tmp_path: Path):
        """Operador usou 'Escola', 'Latitude', 'Longitude', 'CapacidadeIndicacao'."""
        df = pd.DataFrame(
            {
                "Escola": ["E1"],
                "Latitude": [-22.9],
                "Longitude": [-43.2],
                "CapacidadeIndicacao": [100],
            }
        )
        p = tmp_path / "schools.xlsx"
        df.to_excel(p, index=False)
        out, _ = load_schools(p)
        assert len(out) == 1
        assert out.iloc[0]["capacity"] == 100

    def test_y_x_aliases(self, tmp_path: Path):
        df = pd.DataFrame({"nome": ["E1"], "Y": [-22.9], "X": [-43.2], "vagas": [10]})
        p = tmp_path / "schools.xlsx"
        df.to_excel(p, index=False)
        out, _ = load_schools(p)
        assert len(out) == 1
        assert out.iloc[0]["lat"] == -22.9
        assert out.iloc[0]["lon"] == -43.2
        assert out.iloc[0]["capacity"] == 10

    def test_csv_input(self, tmp_path: Path):
        p = tmp_path / "schools.csv"
        p.write_text("name,lat,lon,capacity\nE1,-22.9,-43.2,50\n", encoding="utf-8")
        out, _ = load_schools(p)
        assert len(out) == 1

    def test_drops_rows_without_coords(self, tmp_path: Path):
        df = pd.DataFrame(
            {
                "name": ["E1", "E2", "E3"],
                "lat": [-22.9, None, -22.95],
                "lon": [-43.2, -43.25, None],
                "capacity": [10, 20, 30],
            }
        )
        p = tmp_path / "schools.xlsx"
        df.to_excel(p, index=False)
        out, _ = load_schools(p)
        assert len(out) == 1
        assert out.iloc[0]["name"] == "E1"

    def test_missing_required_columns_raises(self, tmp_path: Path):
        df = pd.DataFrame({"foo": [1], "bar": [2]})
        p = tmp_path / "schools.xlsx"
        df.to_excel(p, index=False)
        with pytest.raises(ValueError, match="obrigatórias ausentes"):
            load_schools(p)

    def test_unsupported_format_raises(self, tmp_path: Path):
        p = tmp_path / "schools.txt"
        p.write_text("invalid")
        with pytest.raises(ValueError, match="Formato não suportado"):
            load_schools(p)

    def test_default_capacity_zero(self, tmp_path: Path):
        df = pd.DataFrame({"name": ["E1"], "lat": [-22.9], "lon": [-43.2]})
        p = tmp_path / "schools.xlsx"
        df.to_excel(p, index=False)
        out, _ = load_schools(p)
        assert out.iloc[0]["capacity"] == 0


class TestLoadParticipants:
    def test_canonical(self, tmp_path: Path):
        df = pd.DataFrame({"name": ["P1", "P2"], "lat": [-22.9, -22.95], "lon": [-43.2, -43.25]})
        p = tmp_path / "p.xlsx"
        df.to_excel(p, index=False)
        out, _ = load_participants(p)
        assert len(out) == 2
        assert (out["qty"] == 1).all()

    def test_alternative_names(self, tmp_path: Path):
        """Cenário real: 'Candidato', 'Lat', 'Lng', 'QtdCandidato'."""
        df = pd.DataFrame(
            {
                "Candidato": ["A"],
                "Lat": [-22.9],
                "Lng": [-43.2],
                "QtdCandidato": [3],
            }
        )
        p = tmp_path / "p.xlsx"
        df.to_excel(p, index=False)
        out, _ = load_participants(p)
        assert len(out) == 1
        assert out.iloc[0]["qty"] == 3

    def test_keeps_rows_without_coords(self, tmp_path: Path):
        """Participantes sem lat/lon ficam NaN (filtragem posterior por geografia)."""
        df = pd.DataFrame({"name": ["P1", "P2"], "lat": [-22.9, None], "lon": [-43.2, None]})
        p = tmp_path / "p.xlsx"
        df.to_excel(p, index=False)
        out, _ = load_participants(p)
        assert len(out) == 2
        assert pd.isna(out.iloc[1]["lat"])

    def test_missing_lat_lon_raises(self, tmp_path: Path):
        df = pd.DataFrame({"name": ["P1"]})
        p = tmp_path / "p.xlsx"
        df.to_excel(p, index=False)
        with pytest.raises(ValueError, match="obrigatórias ausentes"):
            load_participants(p)
