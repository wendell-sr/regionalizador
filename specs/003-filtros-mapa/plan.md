# Plan — Filtros no Mapa (003)

## Arquitetura

```
┌──────────────────────────────────────────────────┐
│  /jobs/{id}                                       │
│  ┌──────────────────┐                             │
│  │ <JobStatus>      │                             │
│  └──────────────────┘                             │
│  ┌─────────────────────────────┐ ┌─────────────┐ │
│  │ <JobMap>                    │ │ <MapFilters>│ │
│  │  (recebe filteredFeatures)  │ │ (Sheet)     │ │
│  │                             │ │ - layers[]  │ │
│  │                             │ │ - status[]  │ │
│  │                             │ │ - capRange  │ │
│  │                             │ │ - radiusMax │ │
│  │                             │ │ - contador  │ │
│  │                             │ │ - limpar    │ │
│  └─────────────────────────────┘ └─────────────┘ │
│         ▲                                          │
│         │ URL: ?layers=...&status=...&cap=...     │
└────────────────────────────────────────────────┘
```

## Componentes Novos

| Componente | Localização | Props |
|---|---|---|
| `<MapFilters>` | `components/map/map-filters.tsx` | `geojson`, `onChange` |
| `useFilters` | `lib/hooks/use-filters.ts` | URL state + helpers |
| `lib/filter-geojson.ts` | `lib/filter-geojson.ts` | pure function |

## Componentes Modificados
- `components/map/job-map.tsx` — recebe `features` filtradas em vez do GeoJSON completo
- `app/jobs/[id]/page.tsx` — adiciona `<Sheet>` com `<MapFilters>`

## Helpers

```ts
// lib/filter-geojson.ts
export function filterGeojson(
  features: Feature[],
  filters: { layers: string[]; statuses: string[]; minCapacity: number; maxRadiusKm: number | null }
): Feature[] { ... }
```

```ts
// lib/hooks/use-filters.ts
export function useFilters() {
  return {
    filters,         // objeto tipado
    setLayer,        // (layer: string, visible: boolean) => void
    setStatus,       // (status: string, visible: boolean) => void
    setMinCapacity,  // (n: number) => void
    setMaxRadius,    // (km: number | null) => void
    clear,           // () => void
  }
}
```

## Critérios de Aceite ↔ Implementação

| AC | Localização | Verificação |
|---|---|---|
| AC1 | `app/jobs/[id]/page.tsx` | Manual + teste |
| AC2 | `<MapFilters>` checkbox → `useFilters.setLayer` | Teste |
| AC3 | `<MapFilters>` checkbox → `useFilters.setStatus` + `filterGeojson` | Teste |
| AC4 | Slider no `<MapFilters>` → `setMinCapacity` | Teste |
| AC5 | Input numérico → `setMaxRadius` | Teste |
| AC6 | `useFilters` com `useSearchParams` | Manual + teste |
| AC7 | Botão "Limpar" → `clear()` | Teste |
| AC8 | `useMemo` em `filterGeojson(features, filters)` | Teste |
| AC9 | Bench em `tests/frontend/perf.test.ts` | Vitest |
| AC10 | `tests/frontend/test-map-filters.test.tsx` (≥4 testes) | Vitest |
| AC11 | Atributos ARIA padrão shadcn | Manual via leitor de tela |

## Não-Objetivos
- Filtros salvos por usuário.
- Filtros server-side.
- Pesquisa textual.
- Heatmap.
