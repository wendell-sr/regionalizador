# Tasks — Mapa Interativo (002)

## Fase 1 — Backend (GeoJSON endpoint)
- [x] `services/exporter.py::build_geojson` (regions + schools + participants + city, reprojetado para WGS84) **← AC8**
- [x] `app/main.py::get_job_geojson` (com guarda para status≠done) **← AC8**
- [x] `app/db/models.py::Job.result_geojson` (nova coluna)
- [x] `services/clustering.py::RegionalizationResult` com `target_crs` e `city_name`
- [x] `tests/test_exporter.py::TestBuildGeojson` (7 testes) **← AC8**
- [x] `tests/test_api.py::TestGeojsonEndpoint` (3 testes)

## Fase 2 — Frontend Deps
- [x] `leaflet`, `react-leaflet@4.2.1` (compat com react 18), `react-leaflet-cluster` em `package.json`
- [x] `@types/leaflet` em devDependencies
- [x] `vitest`, `@testing-library/react`, `@testing-library/dom`, `jsdom` em devDependencies
- [x] CSS do Leaflet importado em `components/map/job-map.tsx` (via `import "leaflet/dist/leaflet.css"`)
- [x] Fix do ícone padrão do Leaflet — `lib/leaflet-icon-fix.ts` (resolve path via `import.meta.url`)

## Fase 3 — Lib
- [x] `lib/geojson.ts` (tipos `Feature`, `FeatureCollection`, helpers `isRegionFeature`, `getBounds`, etc)
- [x] `lib/api.ts::getJobGeojson(id)` com `cache: "no-store"` **← AC8**
- [x] `lib/map-colors.ts` (`STATUS_COLORS`, `getStatusColor`, `getStatusLabel`) **← AC3**

## Fase 4 — Componentes do Mapa
- [x] `components/map/map-placeholder.tsx` (loading, error, status não-done) **← AC9, AC10**
- [x] `components/map/region-polygon.tsx` (Popup com métricas + cor por status) **← AC2, AC3**
- [x] `components/map/school-marker.tsx` (divIcon custom + popup) **← AC4**
- [x] `components/map/participant-cluster.tsx` (react-leaflet-cluster) **← AC5**
- [x] `components/map/job-map.tsx` (composição + FitBounds + TileLayer OSM) **← AC1, AC6, AC12**

## Fase 5 — Integração
- [x] `components/job-status.tsx` importa `<JobMap>` via `dynamic({ ssr: false })` **← AC1, AC12 (no SSR)**
- [x] `app/jobs/[id]/page.tsx` continua server component (mapa só no cliente)

## Fase 6 — Testes Frontend
- [x] `vitest.config.mjs` + `tests/setup.ts` (jsdom + jest-dom)
- [x] `tests/test-map-colors.test.ts` (7 testes) **← AC3**
- [x] `tests/test-geojson.test.ts` (4 testes de tipos + bounds) **← AC8**
- [x] `tests/test-job-map.test.tsx` (6 testes: placeholder, fetch OK, fetch erro) **← AC9, AC11**

## Fase 7 — Documentação
- [x] `specs/002/spec.md`
- [x] `specs/002/plan.md`
- [x] `specs/002/tasks.md` (este)
- [x] `specs/002/contracts/openapi.yaml` (com endpoint `/geojson`)
- [x] `history/adr/0003-leaflet-escolhido.md`
- [x] README atualizado

## Fase 8 — Validação
- [x] `pytest backend/tests` — **63/63 passando** (10 testes novos para geojson)
- [x] `ruff check backend/` — **All checks passed!**
- [x] `npm test` — **17/17 passando** (3 arquivos de teste novos)
- [x] `npm run build` — **Compilação OK** (4 rotas)
- [x] `check_constitution` — **Constitution is satisfied** (sem ArcGIS, sem tokens pagos, sem mapbox/google)
- [x] `validate_spec 002` — Spec válida (12 ACs)
- [ ] Smoke test manual: criar job completo com shapefile real (requer upload manual)

## Bugs resolvidos durante implementação
- `Job` model precisava de coluna `result_geojson` (JSON) para cachear o GeoJSON
- `RegionalizationResult` precisava de `target_crs` e `city_name` para o `build_geojson`
- `react-leaflet@5` requer React 19; downgrade para `4.2.1` (compat React 18) para evitar conflito
- `@vitejs/plugin-react` ESM quebra em vitest config TS; usar `esbuild.jsx: "automatic"` direto
- Faltava `@testing-library/dom` (peer de `@testing-library/react`)

## Próximas Specs (003+)
- 003 — Filtros no mapa (por status, por capacidade, por raio) + URL state
- 004 — Auto-sugestão de n_regions (silhouette score)
- 005 — Geocoding automático (Nominatim + AwesomeAPI)
- 006 — Comparativo de algoritmos ML (KMeans vs KMedoids vs DBSCAN)
