# AGENTS

## graphify

Este projeto tem um knowledge graph em `graphify-out/` com god nodes, estrutura de comunidades e relações cross-file.

### Integrações

- **Plugin opencode**: `.opencode/plugins/graphify.js` injeta lembrete antes de comandos bash quando o grafo existe
- **MCP Server (opencode)**: configurado em `.opencode/opencode.json` como `mcp.graphify` — expõe `query`, `path` e `explain` ao agente
- **MCP Server (VS Code Copilot)**: configurado em `.vscode/settings.json` como `github.copilot.chat.mcp.servers.graphify` — mesma API no Copilot

### Como usar

| Comando | Descrição |
|---------|-----------|
| `npm run graph:build` | Pipeline completa (requer `OPENCODE_GO_API_KEY` ou similar) |
| `npm run graph:update` | Reextrair código e atualizar grafo (AST-only, sem custo) |
| `graphify query "<pergunta>"` | Busca BFS no grafo (contexto amplo) |
| `graphify path "<A>" "<B>"` | Caminho mais curto entre dois símbolos |
| `graphify explain "<conceito>"` | Explicação em linguagem natural de um nó |
| `graphify affected "<X>"` | Nós impactados por X (traversal reverso) |
| `npm run graph:open` | Abre `graph.html` no browser |
| `npm run graph:opencode-install` | Instala/atualiza `.opencode/opencode.json` + plugin |

### Rules

- **Para perguntas sobre o código**, use primeiro `graphify query "<question>"` (via terminal ou MCP). Retorna um subgrafo escopado, muito menor que `GRAPH_REPORT.md` ou grep bruto.
- Use `graphify path "<A>" "<B>"` para relações e `graphify explain "<concept>"` para conceitos focados.
- **Após modificar código**, execute `npm run graph:update` para manter o grafo atualizado (AST-only, sem custo de API).
- Leia `graphify-out/GRAPH_REPORT.md` apenas para revisão de arquitetura geral ou quando query/path/explain não forem suficientes.
- O grafo **não é commitado** (`.gitignore`). Cada dev gera o seu com `npm run graph:build` ou `npm run graph:update`.

## Spec-Driven Development (SDD)

Este projeto segue **Spec-Kit**. Veja `.specify/README.md` para o workflow completo.

- Toda feature começa com uma spec em `specs/NNN-slug/spec.md`
- Valide com: `python .specify/scripts/validate_spec.py specs/NNN-slug`
- Verifique a constitution com: `python .specify/scripts/check_constitution.py`
- ADRs em `history/adr/` — toda decisão arquitetural relevante

## Convenções de Código

- **Backend**: `app/services/` é lógica pura (testável sem I/O). `app/api/` é HTTP. `app/db/` é persistência.
- **Frontend**: `components/ui/` shadcn. `components/` composição. `lib/` cliente de API.
- **Não usar ArcGIS** (constitution). Geocoding via Nominatim + AwesomeAPI. Mapa via Leaflet + OSM. Sem tokens pagos.
- **CRS**: EPSG:31983 (SIRGAS2000/UTM-23S) para qualquer cálculo métrico. KMeans opera em (x, y) projetados, não lat/lon.
