# Regionalizador

App para regionalização de participantes com KMeans + validação de capacidade.

**Status:** MVP em desenvolvimento (Spec 001)
**Stack:** Next.js 15 + shadcn/ui · FastAPI + GeoPandas + scikit-learn

[![CI](https://github.com/wendell-sr/regionalizador/actions/workflows/ci.yml/badge.svg)](https://github.com/wendell-sr/regionalizador/actions/workflows/ci.yml)
[![Constitution](https://github.com/wendell-sr/regionalizador/actions/workflows/constitution.yml/badge.svg)](https://github.com/wendell-sr/regionalizador/actions/workflows/constitution.yml)

## Estrutura

```
regionalizador/
├── .specify/                # Spec-Driven Development (Spec-Kit)
│   ├── memory/constitution.md
│   └── scripts/             # validate_spec, check_constitution
├── specs/
│   └── 001-regionalizador-mvp/
│       ├── spec.md          # O que construir (ACs)
│       ├── plan.md          # Como construir
│       ├── tasks.md         # Quando construir
│       └── contracts/openapi.yaml
├── history/
│   ├── adr/                 # Architecture Decision Records
│   └── migration-map.md     # Legado → novo
├── backend/                 # FastAPI
└── frontend/                # Next.js
```

## Specs

| # | Título | ACs | Status |
|---|---|---|---|
| [001](specs/001-regionalizador-mvp/spec.md) | Regionalizador MVP | 10 | **Concluída** ✓ (107 testes) |
| [002](specs/002-mapa-interativo/spec.md) | Mapa interativo (Leaflet) | 12 | **Concluída** ✓ (134 testes) |
| [003](specs/003-filtros-mapa/spec.md) | Filtros no mapa | 11 | **Concluída** ✓ (154 testes) |
| [004](specs/004-auto-sugestao-regioes/spec.md) | Auto-sugestão de regiões | 10 | **Concluída** ✓ (159 testes) |
| [005](specs/005-geocoding-automatico/spec.md) | Geocoding automático | 12 | **Concluída** ✓ (152 testes) |
| [006](specs/006-comparativo-algoritmos-ml/spec.md) | Comparativo de algoritmos ML | 12 | **Concluída** ✓ (154 testes) |

## ADRs

- [0001 — Stack escolhida](history/adr/0001-stack-escolhida.md)
- [0002 — CRS fixo EPSG:31983](history/adr/0002-crs-fixo.md)
- [0003 — Leaflet para mapa](history/adr/0003-leaflet-escolhido.md)
- [0004 — K-Medoids implementado nativamente](history/adr/0004-scikit-learn-extra.md)

## Knowledge Graph (Graphify)

Este projeto usa [graphify](https://pypi.org/project/graphifyy/) para gerar um grafo de conhecimento consultável. Veja [docs/graphify.md](docs/graphify.md) para detalhes.

```bash
npm run graph:build    # construir grafo (usa OpenAI API)
npm run graph:update   # reextrair AST (sem custo de API)
npm run graph:query "como funciona o KMeans?"
```

## Quickstart

### Opção 1: Script de dev (recomendado)

Inicia backend + frontend em paralelo, com healthcheck, cores e cleanup automático:

```bash
# Unix
./scripts/dev.sh

# Windows PowerShell
.\scripts\dev.ps1

# Windows CMD / qualquer OS com Python
python scripts/dev.py

# Instalar deps + iniciar (primeira vez)
python scripts/dev.py --install

# Rodar só um lado
python scripts/dev.py --backend
python scripts/dev.py --frontend

# Custom port
python scripts/dev.py --port 9000 --frontend-port 4000
```

O script:
- Detecta o venv do backend automaticamente
- Aguarda healthcheck antes de mostrar os logs
- Encerramento limpo com Ctrl+C (mata ambos os processos)
- Mostra cores em terminais que suportam

### Opção 2: Manual (2 terminais)

```bash
# Terminal 1: backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Terminal 2: frontend
cd frontend
npm install
npm run dev
```

Acesse:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## CI

Pipeline em `.github/workflows/`:
- **`ci.yml`** — backend (ruff + pytest), frontend (build + vitest), SDD (validate_spec + constitution)
- **`constitution.yml`** — roda em todo push que toca código, garante constitution (sem ArcGIS, sem mapbox/google, sem tokens pagos, CRS tratado)

## Setup Local Recomendado

1. **Instalar pre-commit hooks** (opcional mas recomendado):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. **Rodar todos os validadores antes de commit**:
   ```bash
   # Backend
   cd backend && pytest --basetemp=/tmp/pytest-basetemp

   # Frontend
   cd frontend && npm test

   # SDD
   python .specify/scripts/validate_spec.py specs/001-regionalizador-mvp
   python .specify/scripts/check_constitution.py
   ```

## Validação SDD

```bash
python .specify/scripts/validate_spec.py specs/001-regionalizador-mvp
python .specify/scripts/check_constitution.py
```

## Migração do Legado

Veja [history/migration-map.md](history/migration-map.md) para o mapeamento de cada script antigo.
