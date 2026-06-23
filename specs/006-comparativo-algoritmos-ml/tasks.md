# Tasks — Comparativo de Algoritmos ML (006)

## Fase 1 — Deps
- [x] `backend/pyproject.toml`: adicionado `scikit-learn-extra` mas removido (incompatível com Python 3.14) **→ K-Medoids implementado nativamente** **← AC12**

## Fase 2 — Backend Core
- [x] `services/clustering.py::AlgorithmMetrics` e `AlgorithmComparison` (dataclasses) **← AC1, AC3**
- [x] `services/clustering.py::run_kmedoids()` (PAM manual: k-medoids++ + swap) **← AC2**
- [x] `services/clustering.py::run_dbscan()` com `eps` via k-NN heuristic **← AC2**
- [x] `services/clustering.py::compare_algorithms()` retorna métricas de 3 algoritmos + winner **← AC2, AC4**
- [x] Subamostragem para K-Medoids se N > 2000 (sample_size) **← Risco**
- [x] Validação `N < 50` → `EmptyDataError` **← AC9**
- [x] `scipy.spatial.distance.cdist` para matriz de distâncias

## Fase 3 — API
- [x] `app/db/models.py::CompareJob` (status, progress, message, params, result)
- [x] `app/main.py::create_compare_job` (multipart) **← AC1**
- [x] `app/main.py::_run_compare_job` (reusa `reproject` + `filter_points_within_city`) **← AC5**
- [x] `app/main.py::get_compare_status` (polling) **← AC11**
- [x] `app/main.py::get_compare_result` **← AC6**
- [x] `app/api/schemas.py::CompareStatus`, `AlgorithmMetricsResponse`, `CompareResult`

## Fase 4 — Testes Backend
- [x] `tests/test_clustering.py::TestRunKmedoids` (3 testes: run, fewer raises, subsample) **← AC2**
- [x] `tests/test_clustering.py::TestRunDbscan` (3 testes: run, noise count, fewer raises) **← AC2**
- [x] `tests/test_clustering.py::TestCompareAlgorithms` (7 testes: 3 algorithms, metrics, noise, winner, N<50, n_participants) **← AC2, AC3, AC4, AC9, AC11**
- [x] `tests/test_api.py::TestCompareEndpoints` (5 testes: 422 missing, 404 status, 404 result, 400 not done, 200 result) **← AC1, AC11**

## Fase 5 — Frontend
- [x] `lib/api.ts`: `createCompareJob`, `getCompareStatus`, `getCompareResult` + types **← AC3, AC11**
- [x] `components/compare-results.tsx` (Card com botão, polling, tabela, badge "recomendado", "Usar" button) **← AC7, AC8**
- [x] `components/form-with-tabs.tsx` (Tabs "Regionalizar"/"Comparar" com file pickers compartilhados) **← AC6**
- [x] `components/ui/tabs.tsx` (Radix wrapper)
- [x] `app/page.tsx` substituiu RegionalizationForm por FormWithTabs (compat RegionalizationForm interno)
- [x] `tests/frontend/test-compare-results.test.tsx` (2 testes render-only)

## Fase 6 — Documentação
- [x] `specs/006/spec.md`
- [x] `specs/006/plan.md`
- [x] `specs/006/tasks.md` (este)
- [x] `specs/006/contracts/openapi.yaml`
- [x] `history/adr/0004-scikit-learn-extra.md` (atualizado: implementation note)
- [x] README atualizado

## Fase 7 — Validação
- [x] `pytest backend` — **107/107 passando** (39.87s)
- [x] `ruff check backend/` — **All checks passed!**
- [x] `npm test` — **47/47 passando** (2.30s) — 2 testes novos
- [x] `npm run build` — **Compilação OK** (4 rotas, 31kB para /)
- [x] `check_constitution` — **Constitution is satisfied** (sem ArcGIS, sem mapbox, sem tokens)
- [x] `validate_spec 006` — Spec válida (12 ACs)

## Bugs resolvidos durante implementação
- **scikit-learn-extra 0.3.0 incompatível com Python 3.14** (usa `distutils.version.LooseVersion` que foi removido) → implementado K-Medoids (PAM) manualmente usando scipy
- **cdist não importado** → adicionado import
- **Variável ambígua `l`** em test_clustering → renomeada para `x`
- **Ruff E712** sobre `== False` → `~series.astype(bool)` no main.py e `not expression` no test

## Próximas Specs (Roadmap completo!)
Todas as 6 specs estão concluídas. Roadmap futuro possível:
- Spec 007 — Visualização lado-a-lado dos algoritmos do compare (mapa duplo)
- Spec 008 — Persistência de preferências do usuário
- Spec 009 — Workers assíncronos (Celery/RQ) para escalar
- Spec 010 — Auth + multiusuário
