# Plan — Comparativo de Algoritmos ML (006)

## Arquitetura

```
┌────────────────────────────────────────────────────────────┐
│  Frontend                                                    │
│  ┌──────────────────────┐                                   │
│  │ Tabs: [Regionalizar] [Comparar]                         │
│  └──────────────────────┘                                   │
│  ┌────────────────────────────────────────────┐             │
│  │ <CompareView>                                │             │
│  │ - tabela de métricas (KMeans/KMedoids/DBSCAN)│             │
│  │ - "Recomendado" badge                       │             │
│  │ - botão "Usar este algoritmo"              │             │
│  └────────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────┘
         │ POST /jobs/compare
         ▼
┌────────────────────────────────────────────────────────────┐
│  Backend                                                     │
│  app/main.py::create_compare_job                            │
│  services/clustering.py                                     │
│    + AlgorithmComparator                                     │
│      - run_kmeans() (já existe)                             │
│      - run_kmedoids()                                       │
│      - run_dbscan()                                         │
│      - compare_all() → AlgorithmComparison                  │
└────────────────────────────────────────────────────────────┘
```

## Backend Novo

### Model de domínio
```python
# services/clustering.py
@dataclass
class AlgorithmMetrics:
    algorithm: str  # "kmeans" | "kmedoids" | "dbscan"
    n_clusters: int
    n_noise: int
    silhouette: float | None
    inertia: float | None
    runtime_ms: int
    labels: np.ndarray  # para uso futuro

@dataclass
class AlgorithmComparison:
    algorithms: list[AlgorithmMetrics]
    winner: str  # algorithm name
    n_participants: int
```

### Função
```python
def compare_algorithms(
    participants_xy: np.ndarray,
    n_clusters_hint: int = 5,
) -> AlgorithmComparison:
    """Roda KMeans, K-Medoids, DBSCAN; retorna métricas."""
```

### Endpoint
```python
@app.post("/jobs/compare", response_model=ComparisonStatus)
async def create_compare_job(
    background: BackgroundTasks,
    schools: UploadFile = File(...),
    participants: UploadFile = File(...),
    shapefile: UploadFile = File(...),
    city_name: str = Form(...),
    n_clusters_hint: int = Form(default=5),
) -> ComparisonStatus: ...
```

### Dependência
```toml
# backend/pyproject.toml
"scikit-learn-extra>=0.3",  # MIT, requer numpy
```

## Frontend

### Lib
```ts
// lib/api.ts
export type AlgorithmMetrics = {
  algorithm: "kmeans" | "kmedoids" | "dbscan"
  n_clusters: number
  n_noise: number
  silhouette: number | null
  inertia: number | null
  runtime_ms: number
}

export async function createCompareJob(form: FormData): Promise<CompareJob>
export async function getCompareResult(id: string): Promise<AlgorithmComparison>
```

### Componentes
```tsx
// components/compare-tab.tsx (formulário)
// components/compare-results.tsx (tabela + vencedor)
// components/algorithm-row.tsx (linha da tabela, clicável)
```

## Critérios de Aceite ↔ Implementação

| AC | Localização | Verificação |
|---|---|---|
| AC1 | `main.create_compare_job` | `test_api.py` |
| AC2 | `clustering.compare_algorithms` | `test_clustering.py` |
| AC3 | Schema `AlgorithmMetrics` | `test_clustering.py` |
| AC4 | `compare_algorithms` retorna `winner` | Teste |
| AC5 | `main._run_compare` reusa `reproject` | `grep` |
| AC6 | `<Tabs>` em `regionalization-form.tsx` | Manual + teste |
| AC7 | `<CompareResults>` | Teste |
| AC8 | Botão "Usar" com `router.push("/?algorithm=...")` | Teste |
| AC9 | HTTP 400 se N < 50 | `test_api.py` |
| AC10 | Bench em `test_clustering.py` | pytest-benchmark |
| AC11 | ≥ 4 testes | pytest |
| AC12 | `check_constitution` | CI |

## Não-Objetivos
- Mais de 3 algoritmos.
- Auto-seleção.
- Tuning de hiperparâmetros.
- Visualização lado-a-lado dos polígonos.
