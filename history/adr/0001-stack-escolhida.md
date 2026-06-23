# ADR 0001 — Stack Escolhida

**Status:** Aceita
**Data:** 2026-06-21
**Spec:** 001-regionalizador-mvp

## Contexto
Substituir 4 versões legadas (Tkinter, Streamlit, ArcGIS) por uma stack web moderna, com separação clara de camadas e testabilidade.

## Decisão
- **Backend:** Python 3.11 + FastAPI + SQLAlchemy 2 + GeoPandas + scikit-learn
- **Frontend:** Next.js 15 (App Router) + React 19 + shadcn/ui + Tailwind v3
- **Geocoding:** Nominatim + AwesomeAPI (sem ArcGIS)
- **Persistência:** SQLite (MVP) → PostGIS (futuro)
- **Storage:** Filesystem local (MVP) → S3 (futuro)

## Consequências

### Positivas
- FastAPI gera OpenAPI automaticamente, alinhado com a spec.
- GeoPandas integra diretamente com shapefile, CRS e operações espaciais.
- shadcn/ui fornece componentes acessíveis sem vendor lock-in (código no repo).
- SQLAlchemy 2 permite migração para PostGIS sem mudar modelos.

### Negativas
- Polling a cada 2s no frontend é menos elegante que WebSocket/SSE.
- SQLite não é ideal para acessos concorrentes em produção (escala).
- Tailwind v3 (não v4) para compatibilidade com shadcn-ui new-york padrão.

### Neutras
- Stack comum no mercado — fácil contratação/onboarding.
- Requer dois processos rodando (uvicorn + next dev) no desenvolvimento.
