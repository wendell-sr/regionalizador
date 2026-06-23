# Spec — Mapa Interativo (002)

## Resumo
Adicionar visualização geoespacial no frontend (Next.js) com Leaflet para inspeção de resultados de regionalização: polígonos das regiões, marcadores de escolas e clusters de participantes.

## Por quê
A spec 001 entrega XLSX + KML para download, mas o operador precisa abrir arquivos externos para validar o resultado. Um mapa embutido na página do job reduz o ciclo de feedback de minutos para segundos e expõe problemas visuais (regiões isoladas, escolas fora do polígono, etc).

## Usuários
- **Operador de regionalização** — inspeciona visualmente o resultado, identifica regiões com problemas antes de exportar.
- **Analista** — compara dois jobs lado a lado para validar mudanças de parâmetros.

## Fora de Escopo (002)
- Edição interativa de polígonos.
- Filtros por status de região (será feature 003).
- Heatmap de densidade.
- Mapa de calor por capacidade.
- Camada de rotas entre escola e participantes.
- Export do mapa como imagem/PDF.
- Mapa offline / cache de tiles.

## Critérios de Aceite (Given/When/Then)

### AC1 — Página do job exibe mapa
**Given** um job com status `done`
**When** o operador acessa `/jobs/{id}`
**Then** vê um mapa Leaflet abaixo das métricas, com tiles do OpenStreetMap.

### AC2 — Polígonos das regiões
**Given** um job `done` com 5 regiões
**When** o mapa carrega
**Then** renderiza 5 polígonos (convex hull), cada um com cor distinta e popup mostrando `region_id`, `candidates`, `capacity`, `status`.

### AC3 — Cor por status
**Given** regiões com status `ok`, `over_capacity`, `under_capacity`
**When** renderizadas
**Then** `ok` = verde, `over_capacity` = vermelho, `under_capacity` = amarelo, `empty` = cinza, `too_large` = laranja.

### AC4 — Marcadores de escolas
**Given** escolas associadas a regiões
**When** o mapa carrega
**Then** cada escola aparece como marcador com ícone de prédio e popup com `name`, `capacity`, `region_id`.

### AC5 — Cluster de participantes
**Given** 10.000 participantes
**When** renderizados
**Then** agrupados via `react-leaflet-cluster` para não travar o browser; zoom in revela pontos individuais.

### AC6 — Bounds iniciais
**Given** polígonos e marcadores carregados
**When** o mapa termina de renderizar
**Then** ajusta automaticamente o zoom para englobar todos os elementos (`fitBounds`).

### AC7 — Controle de camadas
**Given** o mapa renderizado
**When** o operador usa o controle de camadas (canto superior direito)
**Then** pode alternar visibilidade de: polígonos, escolas, participantes.

### AC8 — Endpoint de GeoJSON
**Given** um job `done`
**When** o frontend faz `GET /jobs/{id}/geojson`
**Then** recebe FeatureCollection com 4 camadas: regions (polígonos), schools (points), participants (points), city (polígono do município).

### AC9 — Falha graciosa em job não-done
**Given** um job com status `loading` ou `failed`
**When** o operador acessa `/jobs/{id}`
**Then** o mapa mostra placeholder com a mensagem do status atual (sem tentar carregar GeoJSON).

### AC10 — Loading state do mapa
**Given** o frontend fez `GET /jobs/{id}/geojson`
**When** a request está em voo
**Then** mostra spinner sobreposto ao placeholder do mapa.

### AC11 — Testes do componente
**Given** o componente `<JobMap />`
**When** o test suite roda (`npm run test`)
**Then** há pelo menos 3 testes: renderiza com GeoJSON válido, mostra placeholder em status não-done, alterna layers.

### AC12 — Sem dependência de API key
**Given** a aplicação rodando
**When** o mapa é inicializado
**Then** não há chamada para serviços pagos ou que exijam token (Mapbox, Google Maps).

## Riscos
- **SSR do Leaflet** — Leaflet depende de `window`; precisa `dynamic import` com `ssr: false` no Next.js.
- **Performance com 50k+ participantes** — mesmo com cluster, gerar GeoJSON grande é custoso. Mitigação: endpoint aceita `?simplify=N` para reduzir pontos.
- **Tiles do OSM** — rate limit se muitos acessos. Para MVP, OK; produção exigirá tile server próprio ou CDN.
- **Bundle size** — Leaflet + plugin cluster adicionam ~150kB. Aceitável.

## Métricas de Sucesso
- Tempo de render inicial do mapa < 2s para job típico (5k participantes).
- Sem regressão de performance na página do job.
- Operador consegue identificar região `over_capacity` visualmente em < 5s.
