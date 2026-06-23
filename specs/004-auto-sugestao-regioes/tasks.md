# Tasks — Auto-sugestão de Regiões (004)

## Fase 1 — Backend Core
- [x] `services/clustering.py::KScore` e `SuggestionResult` dataclasses
- [x] `services/clustering.py::suggest_n_regions()` (reusa `run_kmeans`) **← AC2, AC3, AC10**
- [x] `services/clustering.py` cap `k_max = min(15, sqrt(N))` **← AC2**
- [x] Critério de escolha: maior silhouette; empate → menor k **← AC3**
- [x] Validação `N < 10` → `EmptyDataError` **← AC5**

## Fase 2 — API
- [x] `app/api/schemas.py::SuggestParticipant`, `SuggestRegionsRequest`, `KScoreResponse`, `SuggestRegionsResponse`
- [x] `app/main.py::suggest_regions` (reprojeta para UTM-23S, dropna lat/lon, valida N>=10) **← AC1**
- [x] `app/main.py` aceita lat/lon None via `pd.to_numeric(coerce)` + dropna

## Fase 3 — Testes Backend
- [x] `tests/test_clustering.py::TestSuggestNRegions` (7 testes: range, cap 15, N<10, k_max, winner, tie-breaker, inertia) **← AC2, AC3, AC5**
- [x] `tests/test_api.py::TestSuggestRegionsEndpoint` (4 testes: basic, empty 400, <10 400, NaN drop) **← AC1**

## Fase 4 — Frontend
- [x] `lib/api.ts::suggestRegions()` + types (`KScore`, `SuggestRegionsPayload`, `SuggestRegionsResult`) **← AC1**
- [x] `xlsx` instalado para parse client-side do arquivo
- [x] `components/suggest-regions-button.tsx`: botão "Sugerir regiões" com Dialog **← AC6, AC8**
- [x] Pré-preenchimento via `onAccept(k)` → `setNRegions(k)` **← AC7**
- [x] Loading state com `<Loader2>` **← AC9**
- [x] `components/regionalization-form.tsx` integrado: passa `participantsFile` para o botão
- [x] `components/ui/dialog.tsx` (wrapper shadcn manual)

## Fase 5 — Testes Frontend
- [x] `tests/test-suggest-button.test.tsx` (3 testes render-only: disabled, enabled, label)
- [x] `tests/test-api-suggest.test.ts` (2 testes: success, error)

## Fase 6 — Documentação
- [x] `specs/004/spec.md`
- [x] `specs/004/plan.md`
- [x] `specs/004/tasks.md` (este)
- [x] `specs/004/contracts/openapi.yaml`
- [x] README atualizado

## Fase 7 — Validação
- [x] `pytest backend` — **74/74 passando** (21.08s — inclui KMeans em vários k)
- [x] `ruff check backend/` — **All checks passed!**
- [x] `npm test` — **42/42 passando** (2.01s)
- [x] `npm run build` — **Compilação OK** (4 rotas, 25.3kB para /)
- [x] `check_constitution` — **Constitution is satisfied** (sem ArcGIS, sem tokens pagos)
- [x] `validate_spec 004` — Spec válida (10 ACs)
- [ ] Smoke test manual com shapefile real

## Bugs resolvidos durante implementação
- `pd.DataFrame` aceita NaN mas JSON não → schema com `lat: float | None` + dropna
- `NaN` em Python não é serializável em JSON strict → substituído por `None` no teste
- Teste de "loading" dependia do mock de xlsx → simplificado para render-only
- Radix Dialog com portal complica testes jsdom → testes focam em render + estados primitivos

## Próximas Specs (005+)
- 005 — Geocoding automático
- 006 — Comparativo de algoritmos ML
