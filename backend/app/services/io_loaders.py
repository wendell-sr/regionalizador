from __future__ import annotations

from pathlib import Path

import pandas as pd
from pydantic import BaseModel


class LoadedTable(BaseModel):
    name: str
    rows: int
    columns: list[str]


SCHEMA_SCHOOLS = {
    "name": ["nome", "escola", "name", "descricaolocalprova", "local"],
    "lat": ["latitude", "lat", "y"],
    "lon": ["longitude", "lon", "long", "lng", "x"],
    "capacity": ["capacidadeindicacao", "capacidade", "capacity", "vagas"],
    "address": ["endereco", "logradouro", "address", "bairro"],
}


SCHEMA_PARTICIPANTS = {
    "name": ["nome", "participante", "name", "candidato"],
    "lat": ["latitude", "lat", "y"],
    "lon": ["longitude", "lon", "long", "lng", "x"],
    "qty": ["qtdcandidato", "quantidade", "qty", "candidatos"],
    "document": ["cpf", "documento", "document", "rg"],
    "address": ["endereco", "bairro", "address", "cep"],
}


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    raise ValueError(f"Formato não suportado: {suffix}")


def _normalize_columns(df: pd.DataFrame, schema: dict[str, list[str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for canonical, aliases in schema.items():
        for alias in aliases:
            if alias in cols_lower:
                mapping[canonical] = cols_lower[alias]
                break
    return mapping


def load_schools(path: Path) -> tuple[pd.DataFrame, list[str]]:
    df = _read_table(path)
    mapping = _normalize_columns(df, SCHEMA_SCHOOLS)
    if "name" not in mapping or "lat" not in mapping or "lon" not in mapping:
        raise ValueError(
            f"Colunas obrigatórias ausentes. Esperado: nome, lat, lon. Recebido: {list(df.columns)}"
        )
    out = pd.DataFrame(
        {
            "name": df[mapping["name"]].astype(str),
            "lat": pd.to_numeric(df[mapping["lat"]], errors="coerce"),
            "lon": pd.to_numeric(df[mapping["lon"]], errors="coerce"),
            "capacity": (
                pd.to_numeric(df[mapping["capacity"]], errors="coerce").fillna(0).astype(int)
                if "capacity" in mapping
                else 0
            ),
            "address": df[mapping["address"]].astype(str) if "address" in mapping else "",
        }
    )
    out = out.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    return out, list(df.columns)


def load_participants(path: Path) -> tuple[pd.DataFrame, list[str]]:
    df = _read_table(path)
    mapping = _normalize_columns(df, SCHEMA_PARTICIPANTS)
    if "lat" not in mapping or "lon" not in mapping:
        raise ValueError(
            f"Colunas obrigatórias ausentes. Esperado: lat, lon. Recebido: {list(df.columns)}"
        )
    out = pd.DataFrame(
        {
            "name": df[mapping["name"]].astype(str) if "name" in mapping else "",
            "lat": pd.to_numeric(df[mapping["lat"]], errors="coerce"),
            "lon": pd.to_numeric(df[mapping["lon"]], errors="coerce"),
            "qty": (
                pd.to_numeric(df[mapping["qty"]], errors="coerce").fillna(1).astype(int)
                if "qty" in mapping
                else 1
            ),
            "document": df[mapping["document"]].astype(str) if "document" in mapping else "",
            "address": df[mapping["address"]].astype(str) if "address" in mapping else "",
        }
    )
    return out, list(df.columns)
