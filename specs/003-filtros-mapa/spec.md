# Spec — Filtros no Mapa (003)

## Resumo
Adicionar painel de filtros na página do job para o operador controlar visibilidade de layers e filtrar regiões por status. Complementa a spec 002.

## Por quê
A spec 002 entrega o mapa, mas com todas as camadas visíveis por padrão. Em jobs grandes (10+ regiões, 50k participantes) o mapa fica poluído. Filtros permitem focar em problemas (ex.: só `over_capacity`).

## Usuários
- **Operador** — isola regiões com problema para inspeção.
- **Analista** — combina múltiplos jobs com mesmos filtros para comparar.

## Fora de Escopo (003)
- Filtros salvos por usuário (sem auth).
- Filtros no GeoJSON (são apenas no cliente).
- Filtros server-side para reduzir payload.
- Pesquisa textual no painel.
- Combinação de presets ("apenas problemas", "regiões grandes", etc).
- Export do estado do filtro.

## Critérios de Aceite (Given/When/Then)

### AC1 — Painel de filtros
**Given** a página `/jobs/{id}` com mapa renderizado
**When** o mapa carrega
**Then** há um painel lateral (shadcn `<Sheet>` ou `<Card>`) com controles de filtro.

### AC2 — Toggle de visibilidade de layers
**Given** o painel aberto
**When** o operador clica no checkbox de "Escolas"
**Then** a layer de escolas desaparece do mapa; o contador de marcadores visíveis atualiza.

### AC3 — Filtro por status de região
**Given** o painel aberto
**When** o operador desmarca "over_capacity"
**Then** polígonos de regiões com esse status ficam ocultos.

### AC4 — Filtro por capacidade mínima
**Given** um slider "Capacidade mínima" no painel (0-100, default 0)
**When** o operador ajusta para `>50`
**Then** apenas regiões com `capacity >= 50 * capacidade_max` são visíveis.

### AC5 — Filtro por raio máximo
**Given** um input "Raio máximo (km)"
**When** o operador preenche `5`
**Then** regiões com `max_distance_m > 5000` ficam ocultas.

### AC6 — Estado sincronizado com URL
**Given** o operador ajusta filtros
**When** recarrega a página
**Then** os filtros são restaurados (state na URL via `useSearchParams`).

### AC7 — Botão "Limpar filtros"
**Given** filtros aplicados
**When** clica em "Limpar"
**Then** todos os controles voltam ao default; URL é resetada.

### AC8 — Contador de regiões visíveis
**Given** filtros aplicados
**When** o mapa atualiza
**Then** o painel mostra "Mostrando 3 de 7 regiões".

### AC9 — Performance: filtragem client-side
**Given** GeoJSON com 1000 features
**When** filtros mudam
**Then** re-render ocorre em < 200ms (sem roundtrip ao backend).

### AC10 — Testes do painel
**Given** componente `<MapFilters>`
**When** test suite roda
**Then** ≥ 4 testes: renderiza com defaults, toggle de layer funciona, slider de capacidade filtra, botão "Limpar" reseta.

### AC11 — Acessibilidade básica
**Given** o painel renderizado
**When** usuário navega por teclado
**Then** todos os controles são focáveis e respondem a Enter/Space.

## Riscos
- **Re-renders excessivos** com debouncing em sliders para evitar jank.
- **Estado de URL** em SSR — `useSearchParams` no Next 15 tem nuances com `dynamic({ ssr: false })`.
- **Feature flag no mapa** — Leaflet nem sempre respeita `display: none`; usar `<FeatureGroup>` ou render condicional.

## Métricas de Sucesso
- Operador consegue isolar regiões com problema em < 10s.
- Filtros não degradam performance (mantém < 200ms).
