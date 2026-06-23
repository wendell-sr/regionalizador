from __future__ import annotations

from dataclasses import dataclass


class RegionalizadorError(Exception):
    pass


class SchemaError(RegionalizadorError):
    pass


class CapacityError(RegionalizadorError):
    pass


class GeocodingError(RegionalizadorError):
    pass


class EmptyDataError(RegionalizadorError):
    pass


@dataclass
class RegionMetrics:
    region_id: int
    participants: int
    candidates: int
    capacity: int
    schools: int
    max_distance_km: float
    capacity_ratio: float
    status: str
