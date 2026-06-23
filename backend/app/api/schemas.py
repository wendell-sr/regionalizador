from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RegionalizationRequest(BaseModel):
    n_regions: int = Field(ge=1, le=50)
    max_radius_km: float | None = Field(default=None, gt=0)
    capacity_factor: float = Field(default=1.2, ge=1.0, le=2.0)
    target_crs: str = "EPSG:31983"


class GeocodeRequest(BaseModel):
    address: str
    cep: str | None = None


class JobStatusResponse(BaseModel):
    id: str
    status: str
    progress: float
    message: str
    metrics: dict[str, Any]


class SuggestParticipant(BaseModel):
    lat: float | None = None
    lon: float | None = None
    qty: int = 1


class SuggestRegionsRequest(BaseModel):
    participants: list[SuggestParticipant]
    city_name: str | None = None
    target_crs: str = "EPSG:31983"


class KScoreResponse(BaseModel):
    k: int
    silhouette: float | None
    inertia: float | None


class SuggestRegionsResponse(BaseModel):
    recommended: int
    n_participants: int
    scores: list[KScoreResponse]


class GeocodingJobStatus(BaseModel):
    id: str
    status: str
    total: int
    processed: int
    succeeded: int
    failed: int
    progress: float
    message: str


class GeocodedItem(BaseModel):
    index: int
    input: str
    lat: float | None
    lon: float | None
    source: str | None
    success: bool


class GeocodedResult(BaseModel):
    items: list[GeocodedItem]


class CompareStatus(BaseModel):
    id: str
    status: str
    progress: float
    message: str


class AlgorithmMetricsResponse(BaseModel):
    algorithm: str
    n_clusters: int
    n_noise: int
    silhouette: float | None
    inertia: float | None
    runtime_ms: int


class CompareResult(BaseModel):
    winner: str
    n_participants: int
    algorithms: list[AlgorithmMetricsResponse]
