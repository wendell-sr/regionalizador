# ADR 0004 — K-Medoids implementado nativamente (sem scikit-learn-extra)

**Status:** Aceita (revisada)
**Data:** 2026-06-21
**Spec:** 006-comparativo-algoritmos-ml

## Contexto
Spec 006 precisa de K-Medoids, que não está no scikit-learn core. Alternativas:
- Implementar K-Medoids manualmente (PAM/CLARA)
- Usar `scikit-learn-extra` (MIT, depende de numpy)
- Usar `pyclustering` (MIT, dependência pesada)

## Decisão
**Implementar K-Medoids (PAM) manualmente usando scipy.spatial.distance.cdist**.

Inicialmente considerado `scikit-learn-extra`, mas a versão 0.3.0 importa `distutils.version.LooseVersion` que foi removido no Python 3.12+. Decidiu-se implementar diretamente.

## Consequências

### Positivas
- Sem dependência extra.
- Funciona em qualquer versão do Python.
- Controle total do algoritmo (k-medoids++ init + swap até convergir).
- Performance adequada com subamostragem para N > 2000.

### Negativas
- Implementação manual (~30 linhas) — sem cobertura de comunidade.
- K-Medoids O(n²) — limitamos N ≤ 2000 via subamostragem.
- Não temos otimizações de PAM/CLARA da literatura.

### Neutras
- Mantém o ecossistema leve (sem dependência nova).
