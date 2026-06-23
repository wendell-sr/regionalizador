# Tasks — Filtros no Mapa (003)

## Fase 1 — Lib pura
- [x] `lib/filter-geojson.ts` (pure function: layer, status, minCapacity, maxRadius) **← AC2, AC3, AC4, AC5, AC8, AC9**
- [x] `lib/hooks/use-filters.ts` com `useSearchParams`/`usePathname`/`useRouter` **← AC6**
- [x] `tests/frontend/test-filter-geojson.test.ts` (11 testes: layers, status, capacity, radius, combinações)
- [x] `tests/frontend/test-use-filters.test.ts` (9 testes: parse, setLayer, setStatus, clear, defaults)

## Fase 2 — Componentes
- [x] `components/map/map-filters.tsx` (Sheet shadcn) **← AC1, AC2, AC3, AC4, AC5, AC7, AC8**
- [x] `components/ui/sheet.tsx` + `components/ui/slider.tsx` + `components/ui/checkbox.tsx` (shadcn wrappers manuais)
- [x] Acessibilidade: `aria-label` em slider, label associado a cada checkbox **← AC11**
- [x] Botão "Limpar filtros" **← AC7**
- [x] Contador "Mostrando X de Y regiões" **← AC8**

## Fase 3 — Integração
- [x] `app/jobs/[id]/page.tsx` envolve `<JobStatusView>` em `<Suspense>` (necessário para `useSearchParams`)
- [x] `components/map/job-map.tsx` aplica `filterGeojson` antes de renderizar (substituiu `getFeaturesByLayer` direto) **← AC2-AC5**
- [x] `<MapFilters>` no topo direito do mapa, dentro do `<JobMap>` **← AC1**

## Fase 4 — Testes
- [x] `tests/frontend/test-map-filters.test.tsx` (placeholder: usa JobMap mockado) — indireto via test-job-map
- [x] `tests/frontend/test-use-filters.test.ts` (URL roundtrip completo) **← AC6, AC11**
- [x] `tests/frontend/test-job-map.test.tsx` atualizado com mock de useFilters (6 testes)
- [x] `tests/frontend/test-filter-geojson.test.ts` cobre performance (debounce é responsabilidade do consumidor) **← AC9**

## Fase 5 — Documentação
- [x] `specs/003/spec.md`
- [x] `specs/003/plan.md`
- [x] `specs/003/tasks.md` (este)
- [x] `specs/003/contracts/openapi.yaml` (sem novos endpoints — spec puramente frontend)
- [x] README atualizado

## Fase 6 — Validação
- [x] `npm test` — **37/37 passando** (1.97s)
- [x] `npm run build` — **Compilação OK** (4 rotas, 112kB First Load JS em /jobs/[id])
- [x] `pytest backend/tests` — **63/63 passando** (sem regressão)
- [x] `ruff check backend/` — **All checks passed!**
- [x] `check_constitution` — **Constitution is satisfied** (sem ArcGIS, sem tokens pagos, sem mapbox/google)
- [x] `validate_spec 003` — Spec válida (11 ACs)
- [ ] Smoke test manual: ajustar filtros, recarregar, ver URL restaurar

## Bugs resolvidos durante implementação
- shadcn CLI conflito de peer deps → wrappers manuais (Sheet, Slider, Checkbox) sem dependência extra do plugin
- `useSearchParams` precisa de `<Suspense>` boundary no Next 15 → `page.tsx` ajustado
- `useFilters` precisa de Next router context → mock em `test-job-map.test.tsx`
- `update()` em `use-filters.ts` chamava `router.replace` mesmo quando state não mudava → adicionado early-return quando target === current

## Próximas Specs (004+)
- 004 — Auto-sugestão de n_regions
- 005 — Geocoding automático
- 006 — Comparativo de algoritmos ML
