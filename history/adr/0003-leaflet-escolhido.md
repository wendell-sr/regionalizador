# ADR 0003 — Leaflet para Mapa

**Status:** Aceita
**Data:** 2026-06-21
**Spec:** 002-mapa-interativo

## Contexto
Spec 002 precisa de mapa interativo no frontend. Alternativas consideradas:
- Leaflet + react-leaflet
- MapLibre GL JS
- shadcn-chart-wrapper (limitado)
- Google Maps (pago)
- Mapbox (pago)

## Decisão
Adotar **Leaflet + react-leaflet + react-leaflet-cluster**.

## Consequências

### Positivas
- MIT, sem API key, sem custo por tile.
- react-leaflet é o wrapper canônico (componentes React idiomáticos).
- Tiles do OpenStreetMap atendem o caso de uso.
- Bundle ~150kB gzipped, aceitável.
- Plugin `react-leaflet-cluster` resolve AC5 sem código custom.

### Negativas
- Leaflet usa `window` — exige `dynamic({ ssr: false })` no Next.js.
- Tiles do OSM têm rate limit para uso intenso; produção exigirá tile server próprio.
- Ícones padrão quebram com bundler do Next — fix conhecido via `lib/leaflet-icon-fix.ts`.

### Neutras
- Alternativa MapLibre seria mais performática (WebGL), mas adiciona complexidade e requisito de tiles próprios para esta fase.
- Google/Mapbox foram rejeitados por custo e lock-in.

## Mitigações documentadas
- `next/dynamic` com `ssr: false` para o componente `<JobMap>`.
- `import "leaflet/dist/leaflet.css"` no `layout.tsx`.
- Patch dos ícones padrão em `lib/leaflet-icon-fix.ts`.
