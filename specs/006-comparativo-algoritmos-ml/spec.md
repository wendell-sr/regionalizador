# Spec — Comparativo de Algoritmos ML (006)

## Resumo
Adicionar opção de comparar KMeans, K-Medoids e DBSCAN em uma única execução. O backend retorna métricas de cada algoritmo e o frontend permite ao operador escolher o melhor para o job.

## Por quê
KMeans é rápido e estável, mas sensível a outliers. K-Medoids é mais robusto e aceita métricas arbitrárias. DBSCAN descobre clusters de formato arbitrário e identifica ruído. Em dados reais do ENEM, a escolha entre eles muda significativamente o resultado.

## Usuários
- **Analista** — quer comparar e justificar escolha com base em métricas.
- **Operador avançado** — quer controle fino além do KMeans default.

## Fora de Escopo (006)
- Algoritmos além dos 3 (sem HDBSCAN, OPTICS, etc).
- Auto-seleção do "vencedor" (operador decide com base nas métricas).
- Tuning de hiperparâmetros (silhouette por algoritmo já é suficiente).
- Visualização lado-a-lado dos polígonos (será spec 007).
- Persistência da escolha no job (operador precisa rerodar com algoritmo escolhido).

## Critérios de Aceite (Given/When/Then)

### AC1 — Endpoint comparativo
**Given** o operador quer comparar algoritmos
**When** faz `POST /jobs/compare`
**Then** recebe `comparison_id` e o backend processa em background.

### AC2 — Algoritmos implementados
**Given** o request
**When** o backend processa
**Then** executa: KMeans, K-Medoids (scikit-learn-extra), DBSCAN.

### AC3 — Métricas retornadas
**Given** o resultado
**When** o operador consulta
**Then** cada algoritmo tem: `silhouette`, `n_clusters`, `n_noise` (DBSCAN), `inertia` (KMeans/K-Medoids), `runtime_ms`.

### AC4 — Escolha do vencedor
**Given** as métricas
**When** exibidas na UI
**Then** o algoritmo com maior silhouette score recebe badge "Recomendado" (empate → menor runtime).

### AC5 — Reuso do pipeline
**Given** o endpoint
**When** o backend processa
**Then** reusa `geography.filter_points_within_city` e `reproject` (sem duplicação).

### AC6 — UI: nova aba "Comparar"
**Given** o formulário de criação de job
**When** o operador olha
**Then** vê um `<Tabs>` com abas: "Regionalizar" (existente) e "Comparar algoritmos" (nova).

### AC7 — UI: tabela de comparação
**Given** o resultado do compare
**When** o operador acessa `/jobs/{comparison_id}/compare`
**Then** vê tabela com colunas: Algoritmo, n_clusters, silhouette, runtime. Cada linha clicável para ver detalhes.

### AC8 — UI: reusar com algoritmo escolhido
**Given** o operador escolheu um algoritmo
**When** clica "Usar este algoritmo"
**Then** redireciona para o formulário de criar job com `algorithm` pré-preenchido.

### AC9 — Limites
**Given** o request
**When** o backend processa
**Then** rejeita se `n_participantes < 50` (DBSCAN precisa de volume mínimo).

### AC10 — Performance
**Given** 1k participantes
**When** o backend processa os 3 algoritmos
**Then** responde em < 60s.

### AC11 — Testes
**Given** o `AlgorithmComparator`
**When** test suite roda
**Then** ≥ 4 testes: cada algoritmo roda sem erro, métricas estão no schema, vencedor é o maior silhouette, N < 50 falha.

### AC12 — Sem dependências pagas
**Given** o backend
**When** inspecionado
**Then** apenas scikit-learn, scikit-learn-extra (MIT) e numpy. Sem serviços externos.

## Riscos
- **K-Medoids é O(n²)** — pode ser inviável para 10k+ participantes. Mitigação: cap em N para esse algoritmo (subamostrar para 2k).
- **DBSCAN parametrização** — `eps` e `min_samples` precisam de heurística. Mitigação: usar `eps=auto` baseado em k-NN distance.
- **Métrica em DBSCAN** — silhouette não funciona bem com ruído. Mostrar `n_noise` separadamente.
- **scikit-learn-extra** — dependência extra. Aceitável (MIT).

## Métricas de Sucesso
- Operador escolhe o algoritmo recomendado em ≥ 60% dos casos comparados.
- Acelera decisão de parâmetros em datasets grandes.
