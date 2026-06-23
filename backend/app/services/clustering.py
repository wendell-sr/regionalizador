from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from shapely.geometry import MultiPoint, Point, Polygon, mapping
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score

from app.domain.exceptions import CapacityError, EmptyDataError


@dataclass
class Region:
    index: int
    polygon: Polygon | None
    candidates: int
    participants: int
    schools: int
    capacity: int
    max_distance_m: float
    status: str
    centroid_x: float
    centroid_y: float
    school_ids: list[int] = field(default_factory=list)
    participant_ids: list[int] = field(default_factory=list)


@dataclass
class RegionalizationResult:
    regions: list[Region]
    participants: pd.DataFrame
    schools: pd.DataFrame
    metrics: dict
    target_crs: str = "EPSG:31983"
    city_name: str | None = None


@dataclass
class KScore:
    k: int
    silhouette: float | None
    inertia: float | None


@dataclass
class SuggestionResult:
    recommended: int
    scores: list[KScore]
    n_participants: int


@dataclass
class AlgorithmMetrics:
    algorithm: str  # "kmeans" | "kmedoids" | "dbscan"
    n_clusters: int
    n_noise: int
    silhouette: float | None
    inertia: float | None
    runtime_ms: int


@dataclass
class AlgorithmComparison:
    algorithms: list[AlgorithmMetrics]
    winner: str
    n_participants: int


def run_kmeans(
    participants_xy: np.ndarray,
    n_clusters: int,
    seed: int = 42,
) -> tuple[np.ndarray, KMeans]:
    if len(participants_xy) < n_clusters:
        raise EmptyDataError(
            f"Participantes ({len(participants_xy)}) < clusters ({n_clusters})"
        )
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=seed)
    labels = km.fit_predict(participants_xy)
    return labels, km


def run_kmedoids(
    participants_xy: np.ndarray,
    n_clusters: int,
    seed: int = 42,
    sample_size: int = 2000,
    max_iter: int = 50,
) -> tuple[np.ndarray, float]:
    """K-Medoids (PAM simplificado) implementado sem sklearn-extra.

    PAM: inicialização k-medoids++ (kmeans++ aproximado) + iteração swap até convergir.
    Subamostra se N > sample_size (O(n²) por iteração).
    """
    n = len(participants_xy)
    if n < n_clusters:
        raise EmptyDataError(
            f"Participantes ({n}) < clusters ({n_clusters})"
        )
    rng = np.random.default_rng(seed)
    if n > sample_size:
        idx = rng.choice(n, size=sample_size, replace=False)
        sub = participants_xy[idx]
        original_idx = idx
    else:
        sub = participants_xy
        original_idx = None

    n_sub = len(sub)
    dists = cdist(sub, sub, metric="euclidean")

    # Inicialização: k-medoids++ (baseado em distâncias, não squared)
    medoid_idx = np.empty(n_clusters, dtype=int)
    medoid_idx[0] = int(rng.integers(n_sub))
    for i in range(1, n_clusters):
        d_to_closest = dists[:, medoid_idx[:i]].min(axis=1)
        probs = d_to_closest / d_to_closest.sum() if d_to_closest.sum() > 0 else np.ones(n_sub) / n_sub
        medoid_idx[i] = int(rng.choice(n_sub, p=probs))

    labels_sub = np.argmin(dists[:, medoid_idx], axis=1)

    for _ in range(max_iter):
        cost = float(dists[np.arange(n_sub), labels_sub].sum())
        improved = False
        for i in range(n_clusters):
            for j in range(n_sub):
                if j in medoid_idx:
                    continue
                new_medoids = medoid_idx.copy()
                new_medoids[i] = j
                new_labels = np.argmin(dists[:, new_medoids], axis=1)
                new_cost = float(dists[np.arange(n_sub), new_labels].sum())
                if new_cost < cost - 1e-6:
                    medoid_idx = new_medoids
                    labels_sub = new_labels
                    cost = new_cost
                    improved = True
        if not improved:
            break

    inertia = float(dists[np.arange(n_sub), labels_sub].sum())
    if original_idx is not None:
        return labels_sub, inertia
    return labels_sub, inertia


def _dbscan_eps_heuristic(xy: np.ndarray, k: int = 4) -> float:
    """Heurística: distância média ao k-ésimo vizinho mais próximo."""
    from sklearn.neighbors import NearestNeighbors

    nbrs = NearestNeighbors(n_neighbors=k + 1).fit(xy)
    distances, _ = nbrs.kneighbors(xy)
    return float(np.mean(distances[:, k]))


def run_dbscan(
    participants_xy: np.ndarray,
    eps: float | None = None,
    min_samples: int = 5,
) -> tuple[np.ndarray, float | None]:
    """DBSCAN com eps heurístico. Retorna (labels, silhouette)."""
    if len(participants_xy) < min_samples:
        raise EmptyDataError(
            f"Participantes ({len(participants_xy)}) < min_samples ({min_samples})"
        )
    if eps is None:
        eps = _dbscan_eps_heuristic(participants_xy)
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(participants_xy)
    sil = compute_silhouette(participants_xy, labels) if len(set(labels)) > 1 else None
    return labels, sil


def compute_silhouette(participants_xy: np.ndarray, labels: np.ndarray) -> float | None:
    if len(set(labels)) < 2 or len(participants_xy) < 4:
        return None
    return float(silhouette_score(participants_xy, labels))


def _silhouette_for_k(
    xy: np.ndarray, k: int, seed: int = 42, sample_size: int | None = 1000
) -> tuple[float | None, float | None]:
    """Roda KMeans para um k e devolve (silhouette, inertia)."""
    if len(xy) < k:
        return None, None
    labels, km = run_kmeans(xy, n_clusters=k, seed=seed)
    sil = compute_silhouette(xy, labels)
    return sil, float(km.inertia_)


def suggest_n_regions(
    participants_xy: np.ndarray,
    k_min: int = 2,
    k_max: int | None = None,
    seed: int = 42,
) -> SuggestionResult:
    """Calcula silhouette para k ∈ [k_min, min(15, √N)] e retorna o melhor.

    Critério de escolha: maior silhouette score. Em empate, o menor k.
    """
    n = len(participants_xy)
    if n < 10:
        raise EmptyDataError(f"Participantes ({n}) insuficiente para sugestão (mínimo 10)")

    upper = min(15, int(np.sqrt(n)))
    if k_max is not None:
        upper = min(upper, k_max)
    if upper < k_min:
        upper = k_min

    scores: list[KScore] = []
    for k in range(k_min, upper + 1):
        sil, inertia = _silhouette_for_k(participants_xy, k, seed=seed)
        scores.append(KScore(k=k, silhouette=sil, inertia=inertia))

    eligible = [s for s in scores if s.silhouette is not None]
    if not eligible:
        recommended = k_min
    else:
        best = max(eligible, key=lambda s: (s.silhouette, -s.k))
        recommended = best.k

    return SuggestionResult(recommended=recommended, scores=scores, n_participants=n)


def compare_algorithms(
    participants_xy: np.ndarray,
    n_clusters_hint: int = 5,
    seed: int = 42,
) -> AlgorithmComparison:
    """Roda KMeans, K-Medoids e DBSCAN e retorna métricas comparativas."""
    n = len(participants_xy)
    if n < 50:
        raise EmptyDataError(
            f"Participantes ({n}) insuficiente para comparar (mínimo 50)"
        )

    metrics: list[AlgorithmMetrics] = []

    # KMeans
    t0 = time.monotonic()
    try:
        labels_km, km = run_kmeans(participants_xy, n_clusters=n_clusters_hint, seed=seed)
        sil_km = compute_silhouette(participants_xy, labels_km)
        metrics.append(
            AlgorithmMetrics(
                algorithm="kmeans",
                n_clusters=int(len(set(labels_km))),
                n_noise=0,
                silhouette=sil_km,
                inertia=float(km.inertia_),
                runtime_ms=int((time.monotonic() - t0) * 1000),
            )
        )
    except Exception:
        metrics.append(AlgorithmMetrics("kmeans", 0, 0, None, None, 0))

    # K-Medoids
    t0 = time.monotonic()
    try:
        labels_kmed, inertia_kmed = run_kmedoids(
            participants_xy, n_clusters=n_clusters_hint, seed=seed
        )
        sil_kmed = compute_silhouette(participants_xy, labels_kmed)
        metrics.append(
            AlgorithmMetrics(
                algorithm="kmedoids",
                n_clusters=int(len(set(labels_kmed))),
                n_noise=0,
                silhouette=sil_kmed,
                inertia=inertia_kmed,
                runtime_ms=int((time.monotonic() - t0) * 1000),
            )
        )
    except Exception:
        metrics.append(AlgorithmMetrics("kmedoids", 0, 0, None, None, 0))

    # DBSCAN
    t0 = time.monotonic()
    try:
        labels_db, sil_db = run_dbscan(participants_xy)
        n_noise = int((labels_db == -1).sum())
        n_clusters_db = int(len(set(labels_db) - {-1}))
        metrics.append(
            AlgorithmMetrics(
                algorithm="dbscan",
                n_clusters=n_clusters_db,
                n_noise=n_noise,
                silhouette=sil_db,
                inertia=None,
                runtime_ms=int((time.monotonic() - t0) * 1000),
            )
        )
    except Exception:
        metrics.append(AlgorithmMetrics("dbscan", 0, 0, None, None, 0))

    eligible = [m for m in metrics if m.silhouette is not None]
    if not eligible:
        winner = "kmeans"
    else:
        best = max(eligible, key=lambda m: (m.silhouette, -m.runtime_ms))
        winner = best.algorithm

    return AlgorithmComparison(algorithms=metrics, winner=winner, n_participants=n)


def _safe_polygon(points_xy: np.ndarray) -> Polygon | None:
    if len(points_xy) < 3:
        return None
    mp = MultiPoint([Point(x, y) for x, y in points_xy])
    try:
        geom = mp.convex_hull
    except Exception:
        return None
    if isinstance(geom, Polygon) and geom.is_valid and not geom.is_empty:
        return geom
    return None


def _assign_school_region(
    schools: pd.DataFrame, participants_with_region: pd.DataFrame
) -> pd.Series:
    """Atribui cada escola à região do participante mais próximo (em coords métricas)."""
    if schools.empty or participants_with_region.empty:
        return pd.Series(dtype=int, index=schools.index)
    sx = schools["x"].to_numpy()
    sy = schools["y"].to_numpy()
    px = participants_with_region["x"].to_numpy()
    py = participants_with_region["y"].to_numpy()
    pr = participants_with_region["region"].to_numpy()
    out = np.empty(len(sx), dtype=int)
    for i in range(len(sx)):
        d2 = (px - sx[i]) ** 2 + (py - sy[i]) ** 2
        out[i] = int(pr[int(np.argmin(d2))])
    return pd.Series(out, index=schools.index)


def build_regions(
    participants: pd.DataFrame,
    schools: pd.DataFrame,
    labels: np.ndarray,
    target_crs: str,
    max_radius_m: float | None = None,
    capacity_factor: float = 1.2,
) -> RegionalizationResult:
    p = participants.copy()
    p["region"] = labels

    s = schools.copy() if not schools.empty else schools
    if not s.empty:
        s["region"] = _assign_school_region(s, p[["x", "y", "region"]])
    else:
        s["region"] = pd.Series(dtype=int)

    regions: list[Region] = []
    metrics = {"total_participants": int(len(p)), "total_schools": int(len(s))}

    for idx in sorted(p["region"].unique()):
        p_in = p[p["region"] == idx]
        s_in = s[s["region"] == idx] if not s.empty else s.iloc[0:0]

        capacity = int(s_in["capacity"].sum()) if not s_in.empty else 0
        candidates = int(p_in["qty"].sum()) if "qty" in p_in.columns else int(len(p_in))

        centroid_x = float(p_in["x"].mean())
        centroid_y = float(p_in["y"].mean())
        dists = np.sqrt((p_in["x"] - centroid_x) ** 2 + (p_in["y"] - centroid_y) ** 2)
        max_dist = float(dists.max()) if len(dists) else 0.0

        status = "ok"
        if max_radius_m and max_dist > max_radius_m:
            status = "too_large"
        elif capacity == 0 and candidates > 0:
            status = "over_capacity"
        elif capacity > 0 and candidates > capacity * capacity_factor:
            status = "over_capacity"
        elif capacity > 0 and candidates < capacity * 0.5:
            status = "under_capacity"
        elif candidates == 0:
            status = "empty"

        poly = _safe_polygon(p_in[["x", "y"]].values)

        regions.append(
            Region(
                index=int(idx),
                polygon=poly,
                candidates=candidates,
                participants=int(len(p_in)),
                schools=int(len(s_in)),
                capacity=capacity,
                max_distance_m=max_dist,
                status=status,
                centroid_x=centroid_x,
                centroid_y=centroid_y,
                school_ids=s_in["id"].astype(int).tolist() if "id" in s_in.columns else [],
                participant_ids=p_in["id"].astype(int).tolist() if "id" in p_in.columns else [],
            )
        )

    total_capacity = sum(r.capacity for r in regions)
    total_candidates = sum(r.candidates for r in regions)
    if total_candidates > total_capacity * capacity_factor:
        raise CapacityError(
            f"Capacidade total ({total_capacity}) insuficiente para {total_candidates} candidatos "
            f"(fator {capacity_factor})"
        )

    metrics["total_capacity"] = total_capacity
    metrics["total_candidates"] = total_candidates
    metrics["capacity_ratio"] = (
        round(total_candidates / total_capacity, 3) if total_capacity else None
    )

    sil = compute_silhouette(p[["x", "y"]].values, labels)
    metrics["silhouette"] = round(sil, 3) if sil is not None else None

    return RegionalizationResult(
        regions=regions,
        participants=p,
        schools=s,
        metrics=metrics,
        target_crs=target_crs,
    )


def regions_to_geojson(result: RegionalizationResult) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "region_id": r.index,
                    "candidates": r.candidates,
                    "participants": r.participants,
                    "schools": r.schools,
                    "capacity": r.capacity,
                    "max_distance_m": round(r.max_distance_m, 1),
                    "status": r.status,
                },
                "geometry": mapping(r.polygon) if r.polygon else None,
            }
            for r in result.regions
        ],
    }
