# Regionalizador API

Backend Python (FastAPI) para regionalização de participantes.

## Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Endpoints
- `POST /jobs` — upload de escolas, participantes e shapefile (zip). Retorna `job_id`.
- `GET /jobs/{id}` — status e métricas.
- `GET /jobs/{id}/files/{name}` — download de XLSX/KML.

## Estrutura
```
app/
  api/        # schemas, routers
  db/         # SQLAlchemy
  domain/     # enums, exceções
  services/   # geocoding, clustering, geography, io, exporter
  config.py
  main.py
```
