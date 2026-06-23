"""Testes para services/clustering.py — cobre AC4, AC5, AC6, AC7, AC8."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.domain.exceptions import CapacityError, EmptyDataError
from app.services.clustering import (
    _safe_polygon,
    build_regions,
    compare_algorithms,
    compute_silhouette,
    run_dbscan,
    run_kmeans,
    run_kmedoids,
    suggest_n_regions,
)


class TestRunKmeans:
    """AC4 — Clustering em (x, y) projetados."""

    def test_basic_clustering(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        labels, km = run_kmeans(xy, n_clusters=3)
        assert len(labels) == 60
        assert len(set(labels)) == 3
        assert km.n_clusters == 3

    def test_reproducible_with_seed(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        labels_a, _ = run_kmeans(xy, n_clusters=3, seed=42)
        labels_b, _ = run_kmeans(xy, n_clusters=3, seed=42)
        np.testing.assert_array_equal(labels_a, labels_b)

    def test_too_few_participants_raises(self):
        xy = np.array([[0, 0], [1, 1]])
        with pytest.raises(EmptyDataError):
            run_kmeans(xy, n_clusters=3)


class TestComputeSilhouette:
    """AC8 — silhouette score nas métricas."""

    def test_silhouette_with_valid_labels(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        labels = np.array([0] * 20 + [1] * 20 + [2] * 20)
        score = compute_silhouette(xy, labels)
        assert score is not None
        assert -1 <= score <= 1

    def test_silhouette_none_for_single_cluster(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        labels = np.zeros(60, dtype=int)
        assert compute_silhouette(xy, labels) is None

    def test_silhouette_none_for_too_few(self):
        xy = np.array([[0, 0], [1, 1], [2, 2]])
        labels = np.array([0, 1, 0])
        assert compute_silhouette(xy, labels) is None


class TestSafePolygon:
    """AC6 — convex hull por região."""

    def test_polygon_with_three_points(self):
        pts = np.array([[0, 0], [10, 0], [5, 10]])
        poly = _safe_polygon(pts)
        assert poly is not None
        assert poly.area > 0

    def test_none_with_two_points(self):
        pts = np.array([[0, 0], [1, 1]])
        assert _safe_polygon(pts) is None

    def test_none_with_empty(self):
        assert _safe_polygon(np.empty((0, 2))) is None

    def test_collinear_points_returns_none(self):
        pts = np.array([[0, 0], [1, 0], [2, 0]])
        assert _safe_polygon(pts) is None


class TestBuildRegions:
    """AC5, AC7, AC8 — regiões, validação de capacidade, status, métricas."""

    def test_builds_n_regions(self, synthetic_participants, synthetic_schools, synthetic_labels):
        labels = np.array(synthetic_labels)
        result = build_regions(synthetic_participants, synthetic_schools, labels, "EPSG:31983")
        assert len(result.regions) == 3

    def test_regions_have_status(self, synthetic_participants, synthetic_schools, synthetic_labels):
        labels = np.array(synthetic_labels)
        result = build_regions(synthetic_participants, synthetic_schools, labels, "EPSG:31983")
        for r in result.regions:
            assert r.status in {"ok", "over_capacity", "under_capacity", "empty", "too_large"}

    def test_metrics_include_silhouette_and_capacity(
        self, synthetic_participants, synthetic_schools, synthetic_labels
    ):
        labels = np.array(synthetic_labels)
        result = build_regions(synthetic_participants, synthetic_schools, labels, "EPSG:31983")
        m = result.metrics
        assert "silhouette" in m
        assert "total_capacity" in m
        assert "total_candidates" in m
        assert "capacity_ratio" in m
        assert "total_participants" in m
        assert "total_schools" in m
        assert m["silhouette"] is not None

    def test_over_capacity_raises(self, synthetic_participants):
        """AC5: capacidade total insuficiente falha com CapacityError."""

        small_schools = pd.DataFrame(
            {"id": [0], "x": [0.0], "y": [0.0], "capacity": [1]}  # só 1 vaga
        )
        labels = np.zeros(60, dtype=int)
        with pytest.raises(CapacityError):
            build_regions(synthetic_participants, small_schools, labels, "EPSG:31983")

    def test_too_large_flag(self, synthetic_participants, synthetic_schools, synthetic_labels):
        labels = np.array(synthetic_labels)
        result = build_regions(
            synthetic_participants,
            synthetic_schools,
            labels,
            "EPSG:31983",
            max_radius_m=10.0,  # 10m — qualquer ponto viola
        )
        assert all(r.status == "too_large" for r in result.regions)

    def test_school_ids_assigned(self, synthetic_participants, synthetic_schools, synthetic_labels):
        labels = np.array(synthetic_labels)
        result = build_regions(synthetic_participants, synthetic_schools, labels, "EPSG:31983")
        total_schools_assigned = sum(len(r.school_ids) for r in result.regions)
        assert total_schools_assigned == len(synthetic_schools)

    def test_participant_ids_assigned(
        self, synthetic_participants, synthetic_schools, synthetic_labels
    ):
        labels = np.array(synthetic_labels)
        result = build_regions(synthetic_participants, synthetic_schools, labels, "EPSG:31983")
        total_p = sum(len(r.participant_ids) for r in result.regions)
        assert total_p == len(synthetic_participants)

    def test_empty_schools_raises_capacity_error(
        self, synthetic_participants, synthetic_labels
    ):
        """Sem escolas (cap=0), o capacity check final dispara CapacityError."""

        empty = pd.DataFrame({"id": [], "x": [], "y": [], "capacity": []})
        labels = np.array(synthetic_labels)
        with pytest.raises(CapacityError):
            build_regions(synthetic_participants, empty, labels, "EPSG:31983")


class TestSuggestNRegions:
    """Spec 004 — AC2, AC3, AC5: range de k, critério, N<10."""

    def test_basic_suggestion_3_clusters(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        result = suggest_n_regions(xy)
        assert result.recommended >= 2
        assert result.n_participants == 60
        assert all(2 <= s.k <= 7 for s in result.scores)

    def test_k_max_capped_at_15(self):
        rng = np.random.default_rng(42)
        xy = rng.normal(size=(10000, 2))
        result = suggest_n_regions(xy)
        assert max(s.k for s in result.scores) == 15

    def test_raises_when_too_few_participants(self):
        xy = np.array([[0, 0], [1, 1], [2, 2]])
        with pytest.raises(EmptyDataError, match="insuficiente"):
            suggest_n_regions(xy)

    def test_explicit_k_max_respected(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        result = suggest_n_regions(xy, k_max=3)
        assert all(s.k <= 3 for s in result.scores)

    def test_winner_has_highest_silhouette(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        result = suggest_n_regions(xy)
        sil_scores = [s.silhouette for s in result.scores if s.silhouette is not None]
        assert sil_scores
        max_sil = max(sil_scores)
        winner = next(s for s in result.scores if s.k == result.recommended)
        assert winner.silhouette == max_sil

    def test_tie_prefers_smaller_k(self):
        rng = np.random.default_rng(0)
        xy = rng.uniform(0, 1, size=(50, 2))
        result = suggest_n_regions(xy)
        eligible = [s for s in result.scores if s.silhouette is not None]
        if eligible:
            max_sil = max(s.silhouette for s in eligible)
            candidates = [s.k for s in eligible if s.silhouette == max_sil]
            assert result.recommended == min(candidates)

    def test_scores_have_inertia(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        result = suggest_n_regions(xy)
        for s in result.scores:
            if s.silhouette is not None:
                assert s.inertia is not None
                assert s.inertia >= 0


class TestRunKmedoids:
    """Spec 006 — run_kmedoids."""

    def test_runs_and_returns_labels(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        labels, inertia = run_kmedoids(xy, n_clusters=3)
        assert len(labels) == 60
        assert len(set(labels)) == 3
        assert inertia >= 0

    def test_raises_when_too_few(self):
        xy = np.array([[0, 0], [1, 1], [2, 2]])
        with pytest.raises(EmptyDataError):
            run_kmedoids(xy, n_clusters=5)

    def test_subsample_for_large_n(self):
        """Com N=3000 e sample_size=2000, kmedoids deve funcionar sem OOM."""
        rng = np.random.default_rng(0)
        xy = rng.normal(size=(3000, 2))
        labels, _ = run_kmedoids(xy, n_clusters=3, sample_size=2000)
        assert len(labels) == 2000  # subamostrado


class TestRunDbscan:
    """Spec 006 — run_dbscan."""

    def test_runs_with_eps_heuristic(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        labels, sil = run_dbscan(xy, min_samples=5)
        assert len(labels) == 60
        # DBSCAN pode atribuir -1 (ruído) ou cluster id
        assert all(x >= -1 for x in labels)
        # sil pode ser None se DBSCAN não encontrou clusters válidos
        assert sil is None or -1 <= sil <= 1

    def test_returns_noise_count(self, synthetic_participants):
        xy = synthetic_participants[["x", "y"]].values
        labels, _ = run_dbscan(xy, min_samples=5)
        # Todos devem ser clusterizados (3 grupos bem definidos)
        n_noise = int((labels == -1).sum())
        assert n_noise < 60  # não classifica tudo como ruído

    def test_raises_when_too_few(self):
        xy = np.array([[0, 0], [1, 1], [2, 2]])
        with pytest.raises(EmptyDataError):
            run_dbscan(xy, min_samples=10)


class TestCompareAlgorithms:
    """Spec 006 — AC2, AC3, AC4, AC9."""

    @pytest.fixture
    def enough_participants(self):
        """100 participantes em 3 clusters bem separados."""
        rng = np.random.default_rng(42)
        groups = []
        for cx, cy in [(0, 0), (5000, 0), (2500, 5000)]:
            pts = rng.normal(loc=(cx, cy), scale=300, size=(33, 2))
            groups.append(pts)
        return np.vstack(groups)

    def test_returns_3_algorithms(self, enough_participants):
        result = compare_algorithms(enough_participants, n_clusters_hint=3)
        assert len(result.algorithms) == 3
        names = {a.algorithm for a in result.algorithms}
        assert names == {"kmeans", "kmedoids", "dbscan"}

    def test_each_algorithm_has_metrics(self, enough_participants):
        result = compare_algorithms(enough_participants, n_clusters_hint=3)
        for a in result.algorithms:
            assert a.algorithm in {"kmeans", "kmedoids", "dbscan"}
            assert a.n_clusters >= 0
            assert a.runtime_ms >= 0
            if a.algorithm != "dbscan":
                # KMeans/KMedoids têm inertia
                assert a.inertia is not None

    def test_dbscan_has_noise_count(self, enough_participants):
        result = compare_algorithms(enough_participants, n_clusters_hint=3)
        db = next(a for a in result.algorithms if a.algorithm == "dbscan")
        assert db.n_noise >= 0

    def test_winner_is_highest_silhouette(self, enough_participants):
        result = compare_algorithms(enough_participants, n_clusters_hint=3)
        sil_scores = {
            a.algorithm: a.silhouette
            for a in result.algorithms
            if a.silhouette is not None
        }
        if sil_scores:
            best = max(sil_scores, key=lambda k: sil_scores[k])
            assert result.winner == best

    def test_raises_for_fewer_than_50(self):
        rng = np.random.default_rng(0)
        xy = rng.normal(size=(30, 2))
        with pytest.raises(EmptyDataError, match="50"):
            compare_algorithms(xy, n_clusters_hint=3)

    def test_n_participants_reported(self, enough_participants):
        result = compare_algorithms(enough_participants, n_clusters_hint=3)
        assert result.n_participants == 99
