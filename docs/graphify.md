# Graphify — Knowledge Graph do Regionalizador

Este projeto usa [graphify](https://pypi.org/project/graphifyy/) para gerar um **grafo de conhecimento consultável** sobre o código, docs e specs. O grafo é gerado localmente e **não é commitado** (exceto artefatos leves).

## Instalação (já feita)

```powershell
uv tool install graphifyy
```

Binários disponíveis:
- `graphify` — CLI
- `graphify-mcp` — MCP server stdio (VS Code Copilot)

## Comandos Rápidos

```powershell
# Gerar grafo completo (1ª vez — usa API OpenAI para semântica)
npm run graph:build

# Atualizar grafo (incremental — só AST, sem custo de API)
npm run graph:update

# Abrir visualização interativa no browser
npm run graph:open

# Query em linguagem natural
npm run graph:query "como funciona o KMeans?"

# Explicar um conceito
npm run graph:explain "RegionalizationResult"

# Caminho entre dois conceitos
npm run graph:path "KMeans" "convex_hull"
```

## Quando Rodar

| Situação | Comando |
|---|---|
| Setup inicial / após refactor grande | `npm run graph:build` |
| Após adicionar função/arquivo novo | `npm run graph:update` |
| Antes de mergear PR grande | `npm run graph:update` |
| Debug de bug "como isso conecta?" | `npm run graph:query` |

## Integração MCP (VS Code Copilot)

Configurado em `.vscode/settings.json`. Com o Copilot Chat aberto:

```
/graphify path app.services.clustering.run_kmeans app.services.clustering.run_dbscan
/graphify explain RegionalizationResult
/graphify query "qual a função de load_shapefile_zip?"
```

## Artefatos Gerados

Em `graphify-out/` (não commitado exceto alguns):
- `graph.json` — grafo principal (consumível pelo MCP)
- `graph.html` — visualização interativa (vis.js)
- `GRAPH_REPORT.md` — resumo em linguagem natural
- `GRAPH_CALLFLOW.html` — call graph visualizado
- `manifest.json` — índice dos arquivos extraídos

## CI

O GitHub Actions **não** roda graphify (é caro em API). O grafo é só para desenvolvimento local.

## Convenções

- **AST extraction** (grátis): pega funções, classes, imports, call graph
- **Semantic extraction** (OpenAI): pega conceitos abstratos, relações semânticas
- Para PR review, use o AST only (`graphify update .` sem flag)
