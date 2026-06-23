# Tasks — Geocoding Automático (005)

## Fase 1 — Backend Refator
- [x] `services/geocoding.py::geocode_batch(on_progress=...)` (já existia, melhorado) **← AC1, AC3, AC8**
- [x] `services/geocoding.py::stats()` com hits/misses/errors/cache_size **← AC2**
- [x] Persistência em SQLite via SQLAlchemy (GeocodingJob + GeocodingItem) **← AC6**

## Fase 2 — API
- [x] `db/models.py::GeocodingJob` e `GeocodingItem`
- [x] `app/main.py::create_geocoding_job` (multipart, valida colunas, suporta CEP-only e address-only) **← AC1**
- [x] `app/main.py::_run_geocoding_job` (background, atualiza progresso a cada 5 itens) **← AC8**
- [x] `app/main.py::get_geocoding_job` (polling) **← AC10**
- [x] `app/main.py::get_geocoded` (lista por linha) **← AC6**
- [x] `app/main.py::download_geocoded_xlsx` **← AC7**
- [x] `app/main.py::download_failed_xlsx` **← AC8**
- [x] `app/api/schemas.py::GeocodingJobStatus`, `GeocodedItem`, `GeocodedResult`

## Fase 3 — Testes
- [x] `tests/test_geocoding.py::TestCache` (2 testes: hit, separate por CEP) **← AC2**
- [x] `tests/test_geocoding.py::TestRateLimit` (1 teste: sleep em gap pequeno) **← AC3**
- [x] `tests/test_geocoding.py::TestRetry` (1 teste: 503 do AwesomeAPI) **← AC4**
- [x] `tests/test_geocoding.py::TestFallbackChain` (2 testes: awesomeapi→nominatim, cep-only) **← AC5**
- [x] `tests/test_geocoding.py::TestBatch` (1 teste: progresso chamado) **← AC8**
- [x] `tests/test_geocoding.py::TestErrorHandling` (1 teste: erro não propaga) **← AC11**
- [x] `tests/test_geocoding.py::TestStats` (1 teste)
- [x] `tests/test_api.py::TestGeocodingEndpoints` (7 testes: create CEP, create address, 400, 404, list, items, download)

## Fase 4 — Frontend
- [x] `lib/api.ts::createGeocodingJob`, `getGeocodingJob`, `getGeocodedResult`, `geocodedFileUrl` **← AC1, AC6, AC7**
- [x] Types `GeocodingJobStatus`, `GeocodedItem`, `GeocodedResult`
- [x] `components/geocoding-form.tsx` (novo card com upload + polling + tabela de resultados + downloads) **← AC9, AC10**
- [x] `app/page.tsx` com 2 colunas (RegionalizationForm + GeocodingForm)
- [x] `tests/frontend/test-geocoding-form.test.tsx` (3 testes render-only)

## Fase 5 — Documentação
- [x] `specs/005/spec.md`
- [x] `specs/005/plan.md`
- [x] `specs/005/tasks.md` (este)
- [x] `specs/005/contracts/openapi.yaml`
- [x] README atualizado

## Fase 6 — Validação
- [x] `pytest backend` — **90/90 passando** (38.06s — geocoding real é lento por causa do rate limit; mockado nos testes)
- [x] `ruff check backend/` — **All checks passed!**
- [x] `npm test` — **45/45 passando** (2.14s)
- [x] `npm run build` — **Compilação OK** (4 rotas, 26.9kB para /)
- [x] `check_constitution` — **Constitution is satisfied** (sem ArcGIS, sem tokens pagos, sem mapbox/google)
- [x] `validate_spec 005` — Spec válida (12 ACs)
- [ ] Smoke test manual com XLSX real (requer conexão com internet)

## Bugs resolvidos durante implementação
- Python 3.14 removeu `asyncio.get_event_loop().run_until_complete` → substituído por `asyncio.run` nos testes
- `~` em Series bool emite DeprecationWarning → `~series.astype(bool)`
- `succeeded`/`failed` fora do escopo do `asyncio.run` → refatorado para contar via SQL após cada iteração
- TypeScript: `setItems` recebe `GeocodedResult`, não `GeocodedItem[]` → ajustada chamada
- Mocks de asyncio com `time.monotonic` complexos → testado o método `_rate_limit` diretamente

## Próxima Spec (006)
- 006 — Comparativo de algoritmos ML (KMeans vs K-Medoids vs DBSCAN)
