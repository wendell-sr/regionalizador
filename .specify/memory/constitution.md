# Constitution — Regionalizador

> Princípios não-negociáveis. Toda spec, plano e PR deve respeitar.

## 1. Orientação por Especificação
- **Toda feature começa com uma spec em `/specs/{NN-slug}/spec.md`** antes de qualquer código.
- A spec define: problema, usuários, critérios de aceite Given/When/Then, fora de escopo, riscos.
- Sem spec aprovada → sem merge.

## 2. Contratos Primeiro
- **API REST** documentada em `specs/{feature}/contracts/openapi.yaml` **antes** da implementação.
- **Schemas de entrada/saída** são gerados a partir da spec, não improvisados.
- Mudanças de contrato são breaking → exigem nova versão (`/v2/...`).

## 3. Separação de Camadas
- **Backend:** `services/` é lógica pura (testável sem I/O). `api/` é HTTP, `db/` é persistência.
- **Frontend:** `components/ui/` shadcn, `components/{feature}.tsx` composição, `lib/` cliente de API gerado.
- UI nunca acessa DB; backend nunca importa shadcn.

## 4. Padrões Técnicos (imutáveis)
| Camada | Stack |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, GeoPandas, scikit-learn |
| Frontend | Next.js 15, React 19, shadcn/ui (new-york), Tailwind v3 |
| Geocoding | Nominatim + AwesomeAPI (NUNCA ArcGIS) |
| Mapa | Leaflet + react-leaflet + tiles OSM (NUNCA Mapbox/Google) |
| CRS | EPSG:31983 (SIRGAS2000/UTM-23S) para qualquer cálculo métrico |
| ML | KMeans como baseline; silhouette score obrigatório no output |
| Sem API keys | Nenhum serviço pago. Nominatim, AwesomeAPI e OSM são suficientes. |

## 5. Testabilidade
- Toda função de `services/` tem pelo menos 1 teste unitário.
- Specs de feature listam **critérios de aceite verificáveis** (Given/When/Then).
- Antes do PR: `pytest` verde + `ruff check` sem warnings.

## 6. Migração dos Scripts Legados
- **Proibido** reintroduzir lógica de `regionalizador.py`, `prototipobeta.py`, `reg2.py` sem refatoração em `services/`.
- A correspondência antigo→novo está em `history/migration-map.md`.
- Pastas `Regionalizador/`, `Regionalizador_beta/` são **read-only** (consulta histórica).

## 7. Versionamento
- Specs versionadas: `001-regionalizador-mvp`, `002-...`, etc.
- Cada spec produz artefatos: `spec.md`, `plan.md`, `tasks.md`, `contracts/`, `tests/`.
- Mudança em spec aprovada → nova versão da spec, não edição silenciosa.

## 8. Documentação Viva
- `README.md` da raiz é gerado/atualizado quando uma spec é concluída.
- ADRs em `history/adr/` registram decisões arquiteturais relevantes.
- Constituição tem prioridade sobre qualquer outro documento.
