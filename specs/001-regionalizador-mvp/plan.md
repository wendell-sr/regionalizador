# Plan — Regionalizador MVP (001)

## Arquitetura

```
┌──────────────┐    POST /jobs (multipart)    ┌──────────────┐
│   Next.js    │ ───────────────────────────▶ │   FastAPI    │
│  (shadcn)    │ ◀─── GET /jobs/{id} (poll) ──│  (services)  │
└──────────────┘                              └──────┬───────┘
                                                     │
                                          ┌──────────┴──────────┐
                                          ▼                     ▼
                                   ┌─────────────┐       ┌─────────────┐
                                   │  SQLite/    │       │  /storage/  │
                                   │  PostGIS    │       │  {job_id}/  │
                                   └─────────────┘       └─────────────┘
```

## Decisões Arquiteturais (resumo)
- **REST + polling** (não WebSocket) — mais simples e estável, suficiente para jobs de segundos.
- **SQLite agora** — zero infra; migração para PostGIS via GeoAlchemy2 já mapeada.
- **Storage em filesystem** — URLs assinadas ficam para o futuro.
- **CRS fixo EPSG:31983** — RJ/Sudeste. Suporte multi-CRS é ADR-002.

## Componentes

### Backend
| Módulo | Responsabilidade | Linhas-guia |
|---|---|---|
| `app/main.py` | FastAPI app, endpoints | < 200 |
| `app/api/schemas.py` | Pydantic request/response | < 100 |
| `app/services/clustering.py` | KMeans + validação | < 250 |
| `app/services/geography.py` | Shapefile, projeção, filtro | < 150 |
| `app/services/io_loaders.py` | XLSX/CSV → DataFrame | < 150 |
| `app/services/geocoding.py` | Nominatim + AwesomeAPI | < 150 |
| `app/services/exporter.py` | XLSX + KML | < 100 |
| `app/db/models.py` | SQLAlchemy ORM | < 100 |
| `app/db/database.py` | Engine, session | < 30 |
| `app/domain/exceptions.py` | Exceções + dataclasses | < 50 |

### Frontend
| Componente | Responsabilidade |
|---|---|
| `app/page.tsx` | Home com formulário |
| `app/jobs/[id]/page.tsx` | Página de acompanhamento |
| `components/regionalization-form.tsx` | Upload + parâmetros |
| `components/job-status.tsx` | Polling + download |
| `components/status-badge.tsx` | Badge de status |
| `lib/api.ts` | Cliente de API |
| `lib/utils.ts` | Helpers (cn, formatNumber) |

## Fluxo de Dados (Pipeline)

1. **Upload** — POST /jobs com 3 arquivos + form fields.
2. **Storage** — arquivos gravados em `storage/{job_id}/`.
3. **Loading** — `io_loaders.py` lê XLSX/CSV, normaliza colunas, valida.
4. **Geography** — `geography.py` extrai shapefile do zip, encontra município, filtra pontos.
5. **Projection** — reprojeta para EPSG:31983 (x, y em metros).
6. **Clustering** — KMeans em (x, y), retorna labels.
7. **Region build** — `clustering.build_regions` calcula métricas, convex hull, status.
8. **Export** — XLSX + KML em `storage/{job_id}/`.
9. **Persist** — métricas no SQLite, status `done`.

## Critérios de Aceite ↔ Implementação
| AC | Onde mora | Como verificar |
|---|---|---|
| AC1 | `main.create_job` | `tests/test_api.py::test_create_job` |
| AC2 | `io_loaders._normalize_columns` | `tests/test_io_loaders.py` |
| AC3 | `geography.filter_points_within_city` | `tests/test_geography.py` |
| AC4 | `clustering.run_kmeans` (recebe xy projetado) | `tests/test_clustering.py` |
| AC5 | `clustering.build_regions` (raise CapacityError) | `tests/test_clustering.py` |
| AC6 | `clustering._safe_polygon` (MultiPoint.convex_hull) | `tests/test_clustering.py` |
| AC7 | `clustering.build_regions` (status logic) | `tests/test_clustering.py` |
| AC8 | `clustering` retorna `metrics` | `tests/test_clustering.py` |
| AC9 | `exporter.export_to_xlsx/_kml` | `tests/test_exporter.py` |
| AC10 | `main.get_job` + frontend polling | Manual via `npm run dev` |

## Não-Objetivos (reforço)
- Sem WebSocket.
- Sem autenticação.
- Sem multi-tenant.
- Sem comparação de algoritmos.
