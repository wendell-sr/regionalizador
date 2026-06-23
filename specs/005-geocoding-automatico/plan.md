# Plan — Geocoding Automático (005)

## Arquitetura

```
┌────────────────────────────────────────────────────────────┐
│  Frontend                                                    │
│  ┌─────────────────────────────┐  ┌──────────────────────┐ │
│  │ Card "Geocoding de escolas" │  │ /jobs/{id} (novo)    │ │
│  │ - upload XLSX               │  │ - progress bar       │ │
│  │ - "Iniciar geocoding"       │  │ - contador           │ │
│  └─────────────────────────────┘  └──────────────────────┘ │
└────────────────────────────────────────────────────────────┘
         │                                      ▲
         │ POST /jobs/geocode                   │ poll status
         ▼                                      │
┌────────────────────────────────────────────────────────────┐
│  Backend                                                     │
│  app/main.py                                                 │
│    POST /jobs/geocode → cria job                            │
│    Background task → processa em chunks                     │
│    GET /jobs/{id}/geocoded → resultado                      │
│                                                              │
│  services/geocoding.py (reescrito)                          │
│    GeocodingService (já existe — refatorar)                  │
│    + batch() com rate limit                                 │
│    + persistência em SQLite                                 │
└────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│  Cache em memória (TTL opcional) + awesomeapi + nominatim   │
└────────────────────────────────────────────────────────────┘
```

## Backend Novo

### Refator de `services/geocoding.py`
```python
class GeocodingService:
    def __init__(self, rate_per_sec: float = 1.0): ...

    async def resolve(self, address: str, cep: str | None = None) -> GeocodeResult | None: ...
    async def resolve_batch(self, items: list[dict], on_progress=None) -> list[GeocodeResult | None]: ...
    def stats(self) -> dict: ...  # {hits, misses, errors}
```

### Models
```python
# db/models.py
class GeocodingJob(Base):
    __tablename__ = "geocoding_jobs"
    id: str
    status: str
    total: int
    processed: int
    succeeded: int
    failed: int
    progress: float
    source_file: str
    output_file: str
    failed_file: str | None
    items: list[GeocodingItem]  # relationship
```

### Endpoints
```python
# app/main.py
@app.post("/jobs/geocode", response_model=JobStatus)
async def create_geocoding_job(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    has_cep: bool = Form(default=True),
    has_address: bool = Form(default=False),
) -> JobStatus: ...

@app.get("/jobs/{id}/geocoded", response_model=GeocodedResult)
def get_geocoded(id: str) -> GeocodedResult: ...
```

## Critérios de Aceite ↔ Implementação

| AC | Localização | Verificação |
|---|---|---|
| AC1 | `main.create_geocoding_job` | `test_api.py` |
| AC2 | `GeocodingService._cache` | `test_geocoding.py::test_cache_hit` |
| AC3 | `GeocodingService._rate_limit` | `test_geocoding.py::test_rate_limit` |
| AC4 | `tenacity` decorator existente | `test_geocoding.py::test_retry_on_503` |
| AC5 | `GeocodingService.resolve` | `test_geocoding.py::test_awesomeapi_fallback_to_nominatim` |
| AC6 | `main.get_geocoded` | `test_api.py` |
| AC7 | `exporter.export_geocoded_xlsx` | `test_exporter.py` |
| AC8 | `main._run_geocoding_job` calcula % | `test_api.py` |
| AC9 | Novo card em `regionalization-form.tsx` | Manual + teste |
| AC10 | `job-status.tsx` para `GeocodingJob` | Teste |
| AC11 | ≥ 3 testes em `test_geocoding.py` | pytest |
| AC12 | `check_constitution` (já valida) | CI |

## Não-Objetivos
- Geocoding reverso.
- Edição de resultados.
- API paga.
