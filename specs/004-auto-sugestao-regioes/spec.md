# Spec — Auto-sugestão de Regiões (004)

## Resumo
Adicionar endpoint que calcula o número ótimo de regiões (`n_regions`) para um município usando elbow method + silhouette score. Reduz tentativa e erro do operador.

## Por quê
Hoje o operador escolhe `n_regions` no formulário (spec 001) sem base objetiva. Para um município de 5k participantes, valores como 5, 7, 10, 15 são igualmente plausíveis. A escolha impacta diretamente a qualidade do clustering.

## Usuários
- **Operador** — antes de rodar a regionalização, clica em "Sugerir regiões" e recebe um valor recomendado.
- **Analista** — compara diferentes `k` para justificar a escolha final.

## Fora de Escopo (004)
- Auto-rodar a regionalização com o `k` sugerido (operador ainda confirma).
- Algoritmos avançados de seleção de k (gap statistic, Calinski-Harabasz).
- Visualização gráfica do elbow (apenas valor numérico).
- Auto-sugestão por sub-região (sempre global).
- Recálculo online durante edição de parâmetros.

## Critérios de Aceite (Given/When/Then)

### AC1 — Endpoint de sugestão
**Given** um município selecionado + dados de participantes carregados
**When** o frontend faz `POST /jobs/suggest-regions`
**Then** recebe `{ recommended: number, scores: { k: number, silhouette: number, inertia: number }[] }`.

### AC2 — Range de k
**Given** o request
**When** o backend processa
**Then** testa `k` de `2` até `min(15, sqrt(n_participantes))`.

### AC3 — Critério de escolha
**Given** os scores calculados
**When** o backend escolhe o `k` recomendado
**Then** é o `k` com maior silhouette score; em empate, o menor `k`.

### AC4 — Performance
**Given** 5k participantes
**When** o backend processa
**Then** responde em < 30s.

### AC5 — Limites
**Given** o request
**When** o backend processa
**Then** rejeita se `n_participantes < 10` (HTTP 400).

### AC6 — UI: botão "Sugerir regiões"
**Given** o formulário de criação de job
**When** o operador preencheu município, escolas e participantes
**Then** vê um botão "Sugerir regiões" ao lado do input de `n_regions`.

### AC7 — UI: pré-preenchimento
**Given** o operador clicou em "Sugerir regiões"
**When** a request retorna
**Then** o input `n_regions` é preenchido com o valor recomendado (editável).

### AC8 — UI: scores visíveis
**Given** o operador clicou em "Sugerir regiões"
**When** a request retorna
**Then** exibe uma tabela compacta com `k`, `silhouette`, `inertia` para inspeção.

### AC9 — Loading state
**Given** o operador clicou em "Sugerir regiões"
**When** a request está em voo
**Then** o botão fica disabled com texto "Calculando..." e spinner.

### AC10 — Reuso do pipeline
**Given** o endpoint de sugestão
**When** o backend processa
**Then** reusa `services/clustering.py::run_kmeans` (sem duplicação).

## Riscos
- **Custo computacional** — testar 10+ valores de k em datasets grandes pode ser lento. Mitigação: limite `min(15, sqrt(N))` (AC2) + cap no silhouette calc.
- **Silhouette score é O(n²)** — para 50k+ participantes fica caro. Mitigação: usar `sample_size` no silhouette.
- **k=1 não tem silhouette** — começar em k=2 (AC2).

## Métricas de Sucesso
- 70% dos jobs criados passam pelo botão "Sugerir regiões".
- Redução de 50% no número médio de iterações de "rodar job → ajustar k → rodar de novo".
