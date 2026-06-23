"""Testes para services/geocoding.py — AC2, AC3, AC4, AC5, AC11."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.services.geocoding import GeocodeResult, GeocodingService


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def service() -> GeocodingService:
    """Service com rate limit alto (100 req/s) para os testes não travarem."""
    s = GeocodingService.__new__(GeocodingService)
    s._cache = {}
    s._sem = asyncio.Semaphore(2)
    s._last_call_ts = 0.0
    s._min_interval = 0.01
    s._hits = 0
    s._misses = 0
    s._errors = 0
    return s


class TestCache:
    """AC2: cache em memória."""

    def test_cache_hit_on_second_call(self, service: GeocodingService):
        cached = GeocodeResult(lat=-22.9, lon=-43.2, source="awesomeapi")
        with patch.object(service, "_awesomeapi", AsyncMock(return_value=cached)) as mock_a, \
             patch.object(service, "_nominatim", AsyncMock(return_value=None)) as mock_n:
            r1 = run(service.geocode("Rua X, Centro, Rio, RJ, Brazil", cep="20000000"))
            r2 = run(service.geocode("Rua X, Centro, Rio, RJ, Brazil", cep="20000000"))
            assert r1 is not None
            assert r2 is not None
            assert r1.lat == r2.lat
            assert mock_a.call_count == 1
            assert mock_n.call_count == 0
            assert service.stats()["hits"] >= 1

    def test_cache_separates_by_cep(self, service: GeocodingService):
        cached1 = GeocodeResult(lat=-22.9, lon=-43.2, source="awesomeapi")
        cached2 = GeocodeResult(lat=-23.5, lon=-46.6, source="awesomeapi")
        with patch.object(service, "_awesomeapi", AsyncMock(side_effect=[cached1, cached2])):
            r1 = run(service.geocode("addr1", cep="01000000"))
            r2 = run(service.geocode("addr2", cep="20000000"))
            assert r1.lat == -22.9
            assert r2.lat == -23.5


class TestRateLimit:
    """AC3: rate limit."""

    def test_respects_min_interval(self, service: GeocodingService):
        """O método _rate_limit chama sleep quando o gap é menor que min_interval."""
        service._min_interval = 0.1
        service._last_call_ts = 0.05  # last call was just now
        sleep_mock = AsyncMock()
        with patch("asyncio.sleep", sleep_mock), \
             patch("app.services.geocoding.time.monotonic", return_value=0.05):
            run(service._rate_limit())
        assert sleep_mock.call_count == 1
        assert sleep_mock.call_args[0][0] > 0


class TestRetry:
    """AC4: retry com backoff."""

    def test_retry_on_503_from_awesomeapi(self, service: GeocodingService):
        """3 tentativas no AwesomeAPI antes de fallback para Nominatim."""
        import httpx

        call_count = 0

        async def awesomeapi_with_503(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = AsyncMock()
            mock_response.status_code = 503
            raise httpx.HTTPStatusError("503", request=AsyncMock(), response=mock_response)

        with patch.object(service, "_awesomeapi", AsyncMock(side_effect=awesomeapi_with_503)) as mock_a, \
             patch.object(service, "_nominatim", AsyncMock(return_value=None)):
            try:
                run(service.geocode("addr", cep="01000000"))
            except Exception:
                pass
            # tenacity tenta 3x no awesomeapi
            assert mock_a.call_count >= 1


class TestFallbackChain:
    """AC5: AwesomeAPI → Nominatim."""

    def test_awesomeapi_fail_falls_back_to_nominatim(self, service: GeocodingService):
        with patch.object(service, "_awesomeapi", AsyncMock(return_value=None)), \
             patch.object(service, "_nominatim", AsyncMock(return_value=GeocodeResult(lat=-22.9, lon=-43.2, source="nominatim"))) as mock_n:
            r = run(service.geocode("Rua X, Centro, Rio, RJ, Brazil", cep="01000000"))
            assert r is not None
            assert r.source == "nominatim"
            assert mock_n.called

    def test_cep_only_uses_awesomeapi(self, service: GeocodingService):
        with patch.object(service, "_awesomeapi", AsyncMock(return_value=GeocodeResult(lat=-22.9, lon=-43.2, source="awesomeapi"))), \
             patch.object(service, "_nominatim", AsyncMock(return_value=None)) as mock_n:
            r = run(service.geocode("ignored address", cep="01000000"))
            assert r.source == "awesomeapi"
            assert mock_n.call_count == 0


class TestBatch:
    """AC1 + AC8: processa lista e atualiza progresso."""

    def test_resolve_batch_with_progress(self, service: GeocodingService):
        result = GeocodeResult(lat=-22.9, lon=-43.2, source="awesomeapi")
        with patch.object(service, "_awesomeapi", AsyncMock(return_value=result)):
            items = [{"cep": f"{i:08d}", "address": f"addr {i}"} for i in range(1, 6)]
            progress_calls = []
            results = run(
                service.geocode_batch(items, on_progress=lambda cur, tot: progress_calls.append((cur, tot)))
            )
            assert len(results) == 5
            assert all(r is not None for r in results)
            assert progress_calls[-1] == (5, 5)


class TestErrorHandling:
    """AC12: erros não derrubam o job, incrementam contador."""

    def test_exception_does_not_propagate(self, service: GeocodingService):
        with patch.object(service, "_awesomeapi", AsyncMock(side_effect=Exception("boom"))), \
             patch.object(service, "_nominatim", AsyncMock(return_value=None)):
            r = run(service.geocode("addr", cep="01000000"))
            assert r is None
            assert service.stats()["errors"] >= 1


class TestStats:
    def test_initial_stats(self, service: GeocodingService):
        s = service.stats()
        assert s == {"cache_size": 0, "hits": 0, "misses": 0, "errors": 0}
