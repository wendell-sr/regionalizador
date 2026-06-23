from __future__ import annotations

from enum import Enum


class RegionStatus(str, Enum):
    OK = "ok"
    OVER_CAPACITY = "over_capacity"
    UNDER_CAPACITY = "under_capacity"
    EMPTY = "empty"
    TOO_LARGE = "too_large"


class JobStatus(str, Enum):
    PENDING = "pending"
    LOADING = "loading"
    GEOCODING = "geocoding"
    CLUSTERING = "clustering"
    EXPORTING = "exporting"
    DONE = "done"
    FAILED = "failed"
