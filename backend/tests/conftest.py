"""Conftest compartilhado: fixtures sintéticas para testes do backend."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_participants() -> pd.DataFrame:
    """3 grupos bem separados (em metros, UTM-23S) — KMeans converge claramente."""
    rng = np.random.default_rng(42)
    groups = []
    for cx, cy in [(0, 0), (5000, 0), (2500, 5000)]:
        pts = rng.normal(loc=(cx, cy), scale=300, size=(20, 2))
        groups.append(pd.DataFrame({"x": pts[:, 0], "y": pts[:, 1], "qty": 1}))
    df = pd.concat(groups, ignore_index=True)
    df["id"] = range(len(df))
    return df


@pytest.fixture
def synthetic_schools() -> pd.DataFrame:
    """3 escolas com capacidade suficiente para 60 participantes (25 vagas cada = 75)."""
    return pd.DataFrame(
        {
            "id": [0, 1, 2],
            "x": [0.0, 5000.0, 2500.0],
            "y": [0.0, 0.0, 5000.0],
            "capacity": [25, 25, 25],
        }
    )


@pytest.fixture
def synthetic_labels() -> list[int]:
    """Labels alinhados com os 3 grupos do fixture synthetic_participants."""
    return [0] * 20 + [1] * 20 + [2] * 20
