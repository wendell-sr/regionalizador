# Plan — Mapa Interativo (002)

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│  /jobs/{id}                                              │
│  ┌───────────────┐                                       │
│  │ <JobStatus>   │ (existente — spec 001)                │
│  └───────────────┘                                       │
│  ┌───────────────┐                                       │
│  │ <JobMap>      │ (NOVO)                                │
│  │  ├ <Layers>   │                                       │
│  │  ├ <Regions>  │ ← GeoJSON regions (polygons)          │
│  │  ├ <Schools>  │ ← GeoJSON schools (points)            │
│  │  └ <Participants> ← GeoJSON participants (clustered)  │
│  └───────────────┘                                       │
└─────────────────────────────────────────────────────────┘
         │
         │ GET /jobs/{id}/geojson
         ▼
┌─────────────────────────────────────────────────────────┐
│  Backend                                                 │
│  new endpoint: app/main.py::get_job_geojson             │
│  reusa: services/exporter.py::regions_to_geojson         │
│         services/clustering.py::Region                   │
└─────────────────────────────────────────────────────────┘
```

## Decisões Arquiteturais
- **Leaflet + react-leaflet** (MIT, sem API key) conforme ADR-0003.
- **GeoJSON único** (4 camadas) em vez de 3 endpoints — 1 request, cache simples.
- **SSR disabled** via `next/dynamic` com `ssr: false` (Leaflet usa `window`).
- **Cluster nativo** via `react-leaflet-cluster` (wrapper de `leaflet.markercluster`).
- **Cores fixas por status** em constante TS — fácil de evoluir para tema shadcn.

## Componentes Novos

| Componente | Localização | Props |
|---|---|---|
| `<JobMap>` | `components/map/job-map.tsx` | `jobId: string`, `status: string` |
| `<MapLayers>` | `components/map/map-layers.tsx` | `regions`, `schools`, `participants` |
| `<RegionPolygon>` | `components/map/region-polygon.tsx` | `feature`, `status` |
| `<SchoolMarker>` | `components/map/school-marker.tsx` | `feature` |
| `<ParticipantCluster>` | `components/map/participant-cluster.tsx` | `features` |
| `<MapPlaceholder>` | `components/map/map-placeholder.tsx` | `status`, `message` |
| `lib/geojson.ts` | `lib/geojson.ts` | fetch + types |
| `lib/map-colors.ts` | `lib/map-colors.ts` | `STATUS_COLORS`, helpers |

## Componentes Modificados
- `components/job-status.tsx` — adiciona `<JobMap>` abaixo das métricas
- `lib/api.ts` — adiciona `getJobGeojson(id)`

## Backend Novo

### Endpoint
```python
@app.get("/jobs/{job_id}/geojson", response_model=GeoJSONFeatureCollection)
def get_job_geojson(job_id: str) -> GeoJSONFeatureCollection:
    ...
```

### Função
```python
# services/exporter.py
def build_geojson(result: RegionalizationResult) -> dict:
    """Retorna FeatureCollection com 4 camadas."""
```

### Saída (exemplo)
```json
{
  "type": "FeatureCollection",
  "features": [
    { "type": "Feature", "geometry": { "type": "Polygon", ... },
      "properties": { "layer": "region", "region_id": 0, "status": "ok", ... } },
    { "type": "Feature", "geometry": { "type": "Point", ... },
      "properties": { "layer": "school", "name": "...", "capacity": 100, "region_id": 0 } },
    { "type": "Feature", "geometry": { "type": "Point", ... },
      "properties": { "layer": "participant", "qty": 1 } }
  ]
}
```

## Critérios de Aceite ↔ Implementação

| AC | Localização | Verificação |
|---|---|---|
| AC1 | `app/jobs/[id]/page.tsx` | Manual: `npm run dev` + criar job |
| AC2 | `<RegionPolygon>` + `services/clustering` | Teste unitário `test-job-map.tsx` |
| AC3 | `lib/map-colors.ts::STATUS_COLORS` | Teste unitário `test-map-colors.ts` |
| AC4 | `<SchoolMarker>` | `test-job-map.tsx` |
| AC5 | `<ParticipantCluster>` (react-leaflet-cluster) | Manual + teste |
| AC6 | `<JobMap>` `useEffect fitBounds` | Manual |
| AC7 | `<Layers>` (controle nativo Leaflet) | Manual |
| AC8 | `app/main.py::get_job_geojson` | `test_api.py::test_geojson` |
| AC9 | `<MapPlaceholder>` condicional | Teste |
| AC10 | Loading state em `<JobMap>` | Teste |
| AC11 | `vitest` ou `jest` configurado | `npm run test` |
| AC12 | Nenhuma key em env vars | `check_constitution` |

## Não-Objetivos
- Edição de polígonos.
- Múltiplos jobs comparados.
- Filtros por status (003).
- Heatmap.
