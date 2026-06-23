# Spec — Geocoding Automático (005)

## Resumo
Adicionar job assíncrono que resolve CEP/endereço → lat/lon para escolas e/ou participantes que estejam sem coordenadas. Resolve o problema do operador ter que pré-geocodificar o XLSX manualmente.

## Por quê
Hoje (spec 001), escolas sem lat/lon são descartadas silenciosamente. Em dados reais do INEP/ENEM, é comum ter 5-15% de registros sem coordenadas. Geocoding automático elimina pré-processamento manual.

## Usuários
- **Operador** — sobe XLSX "sujo" (com CEP mas sem lat/lon), recebe XLSX corrigido.
- **Analista** — quando a base original tem endereços textuais mas sem geocodificação prévia.

## Fora de Escopo (005)
- Geocoding reverso (lat/lon → endereço).
- Validação de CEP via API própria (usar AwesomeAPI + Nominatim).
- Cache distribuído (cache em memória no processo é suficiente).
- Fallback para Google Maps API.
- Interface para revisar/editar resultados antes de aceitar.

## Critérios de Aceite (Given/When/Then)

### AC1 — Job de geocoding dedicado
**Given** um XLSX com coluna `CEP` (e opcionalmente `Bairro`, `Cidade`, `UF`) e sem `Latitude`/`Longitude`
**When** o operador faz `POST /jobs/geocode`
**Then** recebe `job_id` que processa em background e atualiza o status periodicamente.

### AC2 — Cache em memória
**Given** o serviço de geocoding
**When** o mesmo CEP é consultado 2x
**Then** a 2ª consulta é instantânea (cache hit, sem chamada HTTP).

### AC3 — Rate limit
**Given** o serviço
**When** processa 100 CEPs
**Then** respeita 1 req/s contra Nominatim (configurável via env).

### AC4 — Retry com backoff
**Given** uma chamada que retorna 5xx ou timeout
**When** o serviço tenta de novo
**Then** aplica backoff exponencial (1s, 2s, 4s) — máx 3 tentativas.

### AC5 — Fallback AwesomeAPI → Nominatim
**Given** um CEP
**When** AwesomeAPI retorna vazio
**Then** tenta Nominatim com `${Bairro}, ${Cidade}, ${UF}, Brazil`.

### AC6 — Resultado por linha
**Given** o job concluído
**When** o operador consulta `GET /jobs/{id}/geocoded`
**Then** recebe lista com `index`, `input`, `lat`, `lon`, `source`, `success` para cada linha.

### AC7 — Download do XLSX corrigido
**Given** um job de geocoding `done`
**When** o operador faz `GET /jobs/{id}/files/geocoded.xlsx`
**Then** recebe o XLSX original com colunas `Latitude` e `Longitude` preenchidas onde foi possível; coluna `GeocodingSource` indica a origem.

### AC8 — Relatório de falhas
**Given** um job com 1000 linhas, 50 sem sucesso
**When** o job termina
**Then** o `message` final indica "950/1000 resolvidos (95% sucesso)" e o operador pode baixar `failed_only.xlsx`.

### AC9 — UI: novo card no formulário
**Given** o formulário de criação de job
**When** o operador olha
**Then** vê um card separado "Geocoding de escolas" com upload opcional, ao lado do card principal.

### AC10 — UI: progresso
**Given** o operador iniciou o job de geocoding
**When** navega para `/jobs/{id}`
**Then** vê `<Progress>` com % de linhas processadas e contador "X de Y resolvidos".

### AC11 — Testes de cache e rate limit
**Given** o `GeocodingService`
**When** test suite roda
**Then** ≥ 3 testes: cache hit, rate limit respeitado, retry após 503.

### AC12 — Sem hardcode de API key
**Given** o serviço
**When** inspecionado
**Then** nenhuma chave de API está hardcoded (Nominatim só exige User-Agent, configurável via env).

## Riscos
- **Nominatim down** — sem fallback além do cache. Mitigação: mensagem clara na UI.
- **Volume alto** — geocoding de 10k CEPs = ~3h no rate limit de 1 req/s. Mitigação: Aceitar `?rate=10` para testes locais (não abusar em prod).
- **CEP inválido** — AwesomeAPI retorna 200 com payload vazio. Tratamento explícito.
- **Endereço ambíguo** — Nominatim pode retornar ponto errado. Mitigação: armazenar `source` para auditoria.

## Métricas de Sucesso
- 90% dos jobs com CEP são resolvidos.
- Tempo médio de geocoding para 1k CEPs < 20min.
