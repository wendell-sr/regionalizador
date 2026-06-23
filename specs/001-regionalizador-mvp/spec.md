# Spec — Regionalizador MVP (001)

## Resumo
Distribuir participantes em regiões geográficas usando KMeans, com validação de capacidade escolar e geração de artefatos (XLSX, KML).

## Por quê
As 4 versões legadas (Tkinter, Streamlit, ArcGIS) tinham: API key hardcoded, KMeans em lat/lon (distancias distorcidas), código duplicado, sem testes, sem contrato formal. O MVP estabelece a base saudável antes de evoluir o algoritmo.

## Usuários
- **Operador de regionalização** — sobe shapefile, escolas e participantes; baixa resultados.
- **Analista** — consulta métricas de qualidade (silhouette, capacidade) para validar o output.

## Fora de Escopo (MVP)
- Algoritmos além de KMeans (DBSCAN, k-medoids, otimização inteira).
- Auto-sugestão de `n_regions` (elbow method).
- Geocoding automático de escolas sem lat/lon (entrada manual obrigatória).
- Mapa interativo no frontend (download de KML é suficiente).
- Autenticação e multiusuário.

## Critérios de Aceite (Given/When/Then)

### AC1 — Upload e criação de job
**Given** um shapefile (.zip) + escolas (.xlsx) + participantes (.xlsx) + nome de município + n_regiões
**When** o operador faz POST /jobs
**Then** retorna `job_id` em status `pending` e o job é processado em background.

### AC2 — Validação de entrada
**Given** um XLSX com colunas `Nome/Escola/Local`, `Latitude/Lat/Y`, `Longitude/Long/Lng`, `CapacidadeIndicacao/Capacidade`
**When** o backend processa
**Then** normaliza os nomes de coluna e aceita o arquivo (qualquer combinação de aliases).

### AC3 — Filtragem geográfica
**Given** um município selecionado (ex.: "Rio de Janeiro")
**When** a regionalização roda
**Then** apenas participantes e escolas dentro do polígono do município são considerados.

### AC4 — Clustering em CRS métrico
**Given** participantes dentro do município
**When** o KMeans é executado com `n_regions=N`
**Then** as coordenadas são reprojetadas para EPSG:31983 antes do clustering (não usar lat/lon).

### AC5 — Validação de capacidade
**Given** `capacity_factor=1.2`
**When** o total de candidatos excede `capacidade_total * 1.2`
**Then** o job termina em status `failed` com mensagem clara de capacidade insuficiente.

### AC6 — Convex hull por região
**Given** uma região com pelo menos 3 participantes
**When** o resultado é exportado
**Then** o polígono da região é o `convex_hull` dos pontos dos participantes.

### AC7 — Status por região
**Given** o resultado de uma regionalização
**When** o status é consultado
**Then** cada região tem um de: `ok`, `over_capacity`, `under_capacity`, `empty`, `too_large`.

### AC8 — Métricas de qualidade
**Given** um job concluído
**When** o operador consulta o status
**Then** o objeto `metrics` inclui: `total_participants`, `total_schools`, `total_capacity`, `total_candidates`, `capacity_ratio`, `silhouette`.

### AC9 — Artefatos
**Given** um job `done`
**When** o operador baixa os arquivos
**Then** estão disponíveis: `regionalizacao_participantes.xlsx`, `regionalizacao_escolas.xlsx`, `regionalizacao_regioes.xlsx`, `regioes.kml`.

### AC10 — Acompanhamento via polling
**Given** um `job_id`
**When** o frontend faz GET /jobs/{id} a cada 2s
**Then** recebe `status`, `progress` (0-1), `message`, `metrics`.

## Riscos
- **Nominatim rate limit (1 req/s)** — se o MVP incluir geocoding futuro, mitigar com cache + fila.
- **Shapefile grande (>50MB)** — leitura pode travar a request. Solução: mover para worker externo.
- **CRS fora do Rio/Sudeste** — EPSG:31983 é específico para UTM-23S. Outras regiões exigirão CRS dinâmico (futuro).

## Métricas de Sucesso
- Substituir 100% dos scripts legados.
- Cobertura de testes de `services/clustering.py` > 80%.
- Tempo médio de regionalização para 10k participantes < 30s.
