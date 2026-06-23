# Plan — Auto-sugestão de Regiões (004)

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│  Frontend (RegionalizationForm)                      │
│  ┌──────────────────┐  ┌────────────────────┐      │
│  │ <Input n_regions>│  │ <Button "Sugerir"> │      │
│  └──────────────────┘  └────────────────────┘      │
│         ▲                  │                         │
│         │ preenche         │ POST /jobs/suggest-... │
└─────────┼──────────────────┼─────────────────────────┘
          │                  ▼
          │         ┌─────────────────────────────┐
          │         │ Backend: app/main.py        │
          │         │   new endpoint              │
          │         └─────────┬───────────────────┘
          │                   │
          │                   ▼
          │         ┌─────────────────────────────┐
          │         │ services/clustering.py      │
          │         │  + suggest_n_regions()      │
          │         └─────────────────────────────┘
          │
          └── Resposta: { recommended, scores[] }
```

## Backend Novo

### Função
```python
# services/clustering.py
def suggest_n_regions(
    participants_xy: np.ndarray,
    k_min: int = 2,
    k_max: int | None = None,  # default: min(15, sqrt(N))
    seed: int = 42,
) -> SuggestionResult:
    """Testa KMeans para cada k, retorna scores + melhor k."""
```

```python
# services/clustering.py
@dataclass
class SuggestionResult:
    recommended: int
    scores: list[KScore]

@dataclass
class KScore:
    k: int
    silhouette: float | None
    inertia: float
```

### Endpoint
```python
# app/main.py
class SuggestRegionsRequest(BaseModel):
    participants: list[dict]  # [{lat, lon, qty}, ...]
    city_name: str
    target_crs: str = "EPSG:31983"

class SuggestRegionsResponse(BaseModel):
    recommended: int
    scores: list[KScore]

@app.post("/jobs/suggest-regions", response_model=SuggestRegionsResponse)
def suggest_regions(req: SuggestRegionsRequest) -> SuggestRegionsResponse: ...
```

## Frontend

### Lib
```ts
// lib/api.ts
export async function suggestRegions(payload: {
  participants: { lat: number; lon: number; qty: number }[]
  city_name: string
}): Promise<{ recommended: number; scores: KScore[] }>
```

### Componente
```tsx
// components/regionalization-form.tsx (modificado)
<Button onClick={handleSuggest} disabled={!canSuggest || loading}>
  {loading ? "Calculando..." : "Sugerir regiões"}
</Button>
<Dialog open={showScores} onOpenChange={setShowScores}>
  {/* tabela de scores */}
</Dialog>
```

## Critérios de Aceite ↔ Implementação

| AC | Localização | Verificação |
|---|---|---|
| AC1 | `app/main.py::suggest_regions` | `test_api.py::test_suggest_endpoint` |
| AC2 | `clustering.suggest_n_regions` | `test_clustering.py::test_suggest_k_range` |
| AC3 | `clustering.suggest_n_regions` (max silhouette, tie → menor) | `test_clustering.py` |
| AC4 | Bench em `test_clustering.py` | pytest-benchmark |
| AC5 | HTTP 400 se N < 10 | `test_api.py` |
| AC6 | `regionalization-form.tsx` botão | Manual + teste |
| AC7 | `setNRegions(suggested)` | Teste |
| AC8 | Dialog com tabela | Manual + teste |
| AC9 | Loading state no botão | Teste |
| AC10 | Reuso de `run_kmeans` | `grep` confirma |

## Não-Objetivos
- Auto-rodar job.
- Gap statistic.
- Visualização do elbow.
