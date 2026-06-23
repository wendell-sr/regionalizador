# Tasks — Regionalizador MVP (001)

> Cada task é uma unidade de trabalho. Marcar `[x]` quando concluída e validada.

## Fase 0 — Setup
- [x] Estrutura de pastas `backend/`, `frontend/`, `specs/`
- [x] `backend/pyproject.toml` com dependências fixadas
- [x] `frontend/package.json` + `components.json` (shadcn)
- [x] `.gitignore` raiz

## Fase 1 — Backend Core
- [x] `app/config.py` (Pydantic Settings)
- [x] `app/domain/enums.py` (JobStatus, RegionStatus)
- [x] `app/domain/exceptions.py`
- [x] `app/db/database.py` (engine + session)
- [x] `app/db/models.py` (Job, School, Participant, Region)

## Fase 2 — Services (lógica pura)
- [x] `services/io_loaders.py` (XLSX/CSV com aliases de coluna)
- [x] `services/geography.py` (shapefile, filtro, projeção)
- [x] `services/clustering.py` (KMeans + convex hull + métricas) **← AC4, AC6, AC7, AC8**
- [x] `services/geocoding.py` (Nominatim + AwesomeAPI, sem ArcGIS)
- [x] `services/exporter.py` (XLSX + KML) **← AC9**

## Fase 3 — API
- [x] `app/main.py` — POST /jobs, GET /jobs/{id} **← AC1, AC10**
- [x] `app/api/schemas.py`
- [x] `GET /jobs/{id}/files/{name}` (download com whitelist + path traversal defense) **← AC9**

## Fase 4 — Testes
- [x] `tests/conftest.py` (fixtures: synthetic_participants, synthetic_schools, synthetic_labels)
- [x] `tests/test_clustering.py` (15 testes: KMeans, silhouette, convex hull, build_regions, status, métricas, capacity, too_large) **← AC4, AC5, AC6, AC7, AC8**
- [x] `tests/test_io_loaders.py` (15 testes: aliases de coluna, CSV, dropna, schema inválido) **← AC2**
- [x] `tests/test_geography.py` (4 testes: filter, reproject, empty edge cases) **← AC3**
- [x] `tests/test_exporter.py` (10 testes: XLSX, KML, path traversal defense) **← AC9**
- [x] `tests/test_api.py` (6 testes: /health, /jobs, /jobs/{id}, /files/{name}, 422 validação) **← AC1, AC10**

## Fase 5 — Frontend
- [x] `lib/utils.ts` (cn helper)
- [x] `lib/api.ts` (cliente fetch)
- [x] `components/ui/button.tsx`
- [x] `components/ui/card.tsx`
- [x] `components/ui/input.tsx`
- [x] `components/ui/label.tsx`
- [x] `components/ui/progress.tsx`
- [x] `components/ui/sonner.tsx`
- [x] `components/status-badge.tsx`
- [x] `components/regionalization-form.tsx`
- [x] `components/job-status.tsx`
- [x] `app/layout.tsx`
- [x] `app/page.tsx`
- [x] `app/jobs/[id]/page.tsx`

## Fase 6 — Documentação
- [x] `specs/001/spec.md`
- [x] `specs/001/plan.md`
- [x] `specs/001/tasks.md` (este arquivo)
- [x] `specs/001/contracts/openapi.yaml`
- [x] `.specify/memory/constitution.md`
- [x] `history/adr/0001-stack-escolhida.md`
- [x] `history/adr/0002-crs-fixo.md`
- [x] `history/migration-map.md` (legado → novo)
- [x] `README.md` raiz
- [x] `backend/README.md`
- [x] `frontend/README.md`

## Fase 7 — Validação Final
- [x] `pytest backend/tests` — **53/53 passando** (3.71s)
- [x] `ruff check backend/` — **All checks passed!**
- [x] Smoke test: `uvicorn app.main:app` sobe; `/health` retorna 200; GET em job inexistente retorna 404; path traversal retorna 400
- [x] `check_constitution` — **Constitution is satisfied** (sem ArcGIS, sem tokens pagos, CRS tratado)
- [x] `validate_spec` — Spec válida (10 ACs)
- [ ] `npm run build` no frontend (não instalado neste ambiente)
- [ ] PR de fechamento da spec 001 (a fazer pelo usuário)

## Bugs corrigidos durante implementação
- `SCHEMA_SCHOOLS`/`SCHEMA_PARTICIPANTS` faltavam aliases `"lon"` e `"capacity"`
- `build_regions` usava boolean reindex com warning; reescrito para atribuir escola→região por nearest participant
- `find_city` aceita `NM_MUN`/`NOME`/`name`/`municipio`
- Whitelist `ALLOWED_ARTIFACTS` impede path traversal em `/files/{name}`

## Próximas Specs (002+)
- [002](specs/002-mapa-interativo/spec.md) — Mapa interativo (Leaflet)
- 003 — Filtros no mapa
- 004 — Auto-sugestão de n_regions
- 005 — Geocoding automático
- 006 — Comparativo de algoritmos ML

