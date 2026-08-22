# ADR 003 — Staging com todas as colunas TEXT

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

Os CSVs da fonte apresentam encoding latin-1, separador `;`, decimal
com vírgula, terminador CRLF e valores sentinela que não são
conversíveis (`-11`, `-13`, `-1`, `-3` no campo de favorecido).

Uma staging tipada faria o `COPY` abortar a transação inteira ao
encontrar o primeiro valor inconversível — sem indicar qual linha,
após dezenas de minutos de carga.

## Decisão

Todas as colunas da staging são `TEXT`, sem constraint, sem chave
primária, sem chave estrangeira e sem índice.

Tipagem, validação e limpeza acontecem na transformação de staging
para DW, em SQL versionado.

## Consequência

- **Positiva:** a carga não falha por causa do dado. Qualquer anomalia
  é investigada com `SELECT` sobre a tabela já carregada.
- **Positiva:** permite quantificar problemas antes de decidir como
  tratá-los — pré-requisito das checagens da Fase 5.
- **Negativa:** ocupa mais espaço que a versão tipada.
- **Negativa:** exige `CAST` explícito em toda consulta sobre staging.

## Alternativa descartada

Tipar na carga e desviar linhas rejeitadas para uma tabela de erro.
Descartada por complexidade desproporcional ao ganho: o `COPY` do
Postgres não oferece tratamento de erro por linha sem extensão externa.
