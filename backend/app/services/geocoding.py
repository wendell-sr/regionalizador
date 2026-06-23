from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


@dataclass
class GeocodeResult:
    lat: float
    lon: float
    source: str


class GeocodingService:
    def __init__(self) -> None:
        self._cache: dict[str, GeocodeResult | None] = {}
        self._sem = asyncio.Semaphore(2)
        self._last_call_ts = 0.0
        self._min_interval = 1.0 / settings.geocoding_rate_limit_per_sec
        self._hits = 0
        self._misses = 0
        self._errors = 0

    def _key(self, query: str) -> str:
        return hashlib.sha1(query.encode("utf-8")).hexdigest()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _awesomeapi(self, cep: str, client: httpx.AsyncClient) -> GeocodeResult | None:
        cep_digits = "".join(c for c in cep if c.isdigit())
        if len(cep_digits) != 8:
            return None
        r = await client.get(f"{settings.awesomeapi_url}/{cep_digits}", timeout=10.0)
        if r.status_code != 200:
            return None
        data = r.json()
        lat = data.get("lat")
        lng = data.get("lng")
        if lat and lng:
            return GeocodeResult(lat=float(lat), lon=float(lng), source="awesomeapi")
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _nominatim(self, address: str, client: httpx.AsyncClient) -> GeocodeResult | None:
        params = {"q": address, "format": "json", "limit": 1, "countrycodes": "br"}
        headers = {"User-Agent": settings.nominatim_user_agent}
        r = await client.get(
            settings.nominatim_url, params=params, headers=headers, timeout=10.0
        )
        if r.status_code != 200 or not r.json():
            return None
        item = r.json()[0]
        return GeocodeResult(lat=float(item["lat"]), lon=float(item["lon"]), source="nominatim")

    async def _rate_limit(self) -> None:
        now = time.monotonic()
        wait = self._min_interval - (now - self._last_call_ts)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_call_ts = time.monotonic()

    async def geocode(self, address: str, cep: str | None = None) -> GeocodeResult | None:
        if cep:
            key = self._key(f"cep:{cep}")
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
        address_key = self._key(f"addr:{address}")
        if address_key in self._cache:
            self._hits += 1
            return self._cache[address_key]

        self._misses += 1
        async with self._sem:
            async with httpx.AsyncClient() as client:
                if cep:
                    try:
                        result = await self._awesomeapi(cep, client)
                        if result:
                            self._cache[self._key(f"cep:{cep}")] = result
                            return result
                    except Exception:
                        self._errors += 1
                await self._rate_limit()
                try:
                    result = await self._nominatim(address, client)
                    if result:
                        self._cache[address_key] = result
                    return result
                except Exception:
                    self._errors += 1
                    return None

    def stats(self) -> dict:
        return {
            "cache_size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
        }

    async def geocode_batch(
        self, items: list[dict], on_progress=None
    ) -> list[GeocodeResult | None]:
        results: list[GeocodeResult | None] = [None] * len(items)
        for i, item in enumerate(items):
            results[i] = await self.geocode(
                address=item.get("address", ""), cep=item.get("cep")
            )
            if on_progress:
                on_progress(i + 1, len(items))
        return results


geocoding_service = GeocodingService()
