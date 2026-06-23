# ADR 0002 — CRS Fixo EPSG:31983

**Status:** Aceita
**Data:** 2026-06-21
**Spec:** 001-regionalizador-mvp

## Contexto
Os scripts legados aplicavam KMeans diretamente em latitude/longitude, o que distorce distâncias (1 grau de longitude no equador ≠ 1 grau no polo). Para o MVP, focar no RJ/Sudeste.

## Decisão
Usar **EPSG:31983 (SIRGAS2000 / UTM-23S)** como CRS métrico fixo para clustering e cálculo de distâncias.

## Consequências

### Positivas
- Distâncias em **metros** (KMeans e convex hull corretos).
- Convex hull tem área/distância significativas.
- 1 linha de código: `gdf.to_crs("EPSG:31983")`.

### Negativas
- **Não funciona bem** para municípios fora da zona UTM-23S (oeste de MG, sul do RS, norte do AM).
- Hardcoded — adicionar município de outra zona exige refatoração.

### Mitigação futura (spec 002+)
- Detectar zona UTM automaticamente via centróide do município.
- Suporte a múltiplos CRS por job (`target_crs` como parâmetro, já previsto na spec).
