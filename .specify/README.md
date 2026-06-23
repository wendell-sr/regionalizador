# Spec-Driven Development (Spec-Kit)

Este projeto segue **Spec-Kit** (GitHub) com `.specify/` na raiz.

## Estrutura

```
.specify/
  memory/constitution.md        # Princípios imutáveis
  templates/                    # (vazio — Spec-Kit oficial)
  scripts/
    validate_spec.py            # Valida spec/{NN-slug}/
    check_constitution.py       # Verifica violações
specs/
  001-regionalizador-mvp/
    spec.md                     # Problema, ACs, fora de escopo
    plan.md                     # Arquitetura, componentes, mapeamento
    tasks.md                    # Checklist de execução
    contracts/
      openapi.yaml              # Contrato HTTP (gera cliente TS)
memory/                         # (não usado — mantido em .specify/memory/)
history/
  adr/                          # Architecture Decision Records
  migration-map.md              # Legado → novo
```

## Workflow

1. **Nova feature → nova pasta em `specs/NNN-slug/`** copiando `001-` como template.
2. Escrever `spec.md` com ACs no formato Given/When/Then.
3. Escrever `plan.md` com arquitetura e mapeamento AC → código.
4. Escrever `tasks.md` com checklist de fases.
5. Se a feature expõe API → `contracts/openapi.yaml`.
6. Antes de PR: rodar validadores.

## Validação

```bash
# Valida estrutura e ACs de uma spec
python .specify/scripts/validate_spec.py specs/001-regionalizador-mvp

# Verifica violações da constituição
python .specify/scripts/check_constitution.py
```

## Constituição vs Spec vs Plano

| Doc | Resposta |
|---|---|
| Constituição | **O que NUNCA pode mudar** (stack, padrões) |
| Spec | **O que construir** (ACs, fora de escopo) |
| Plan | **Como construir** (arquitetura, módulos) |
| Tasks | **Quando construir** (checklist de fases) |

Mudanças na **constituição** exigem ADR. Mudanças em **spec/plan** são incrementais (nova spec).

## Convenções

- IDs de spec: `NNN-slug-em-kebab-case` (3 dígitos, zero-padded)
- Status no `tasks.md`: `[ ]` pendente, `[x]` concluído
- ACs numerados: `AC1`, `AC2`, ... (sempre referenciados pelo número)
- ADRs: `NNNN-titulo-curto.md` em `history/adr/`
- Frontend cliente de API pode ser gerado a partir de `contracts/openapi.yaml`:
  ```bash
  npx openapi-typescript-codegen --input specs/001/contracts/openapi.yaml --output frontend/lib/api-generated
  ```
