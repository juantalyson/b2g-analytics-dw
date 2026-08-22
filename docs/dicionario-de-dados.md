# Dicionário de Dados

Fonte: Portal da Transparência do Governo Federal
`portaldatransparencia.gov.br/download-de-dados/despesas`

## Características gerais dos arquivos

| Propriedade | Valor |
|---|---|
| Periodicidade | diária, padrão `AAAAMMDD` |
| Formato | ZIP com 11 CSVs |
| Encoding | ISO-8859-1 (latin-1) |
| Separador | `;` |
| Delimitador de texto | `"` em todos os campos |
| Decimal | vírgula, sem separador de milhar |
| Terminador de linha | CRLF |
| Tamanho (dia útil) | ~8,9 MB comprimido, ~79 MB extraído |
| Fim de semana | ZIP válido de ~7 KB, apenas cabeçalhos |

**Semântica temporal:** o documento consta na planilha do dia da sua
última alteração. Ver ADR 002.

## staging.stg_empenho — 63 colunas + controle

Grão: 1 documento de empenho.
Chave natural: `codigo_empenho` (única — verificada em 4 dias).

Colunas que alimentam o DW:

| Coluna | Destino | Tratamento |
|---|---|---|
| `codigo_empenho` | chave de negócio | sem alteração |
| `data_emissao` | FK dim_tempo | `TO_DATE(x,'DD/MM/YYYY')` |
| `tipo_empenho` | atributo do fato | Global, Estimativo, Ordinário |
| `codigo_orgao_superior` | FK dim_orgao | sem alteração |
| `codigo_orgao` | FK dim_orgao | sem alteração |
| `codigo_unidade_gestora` | FK dim_orgao | sem alteração |
| `codigo_favorecido` | FK dim_favorecido | classificar (ADR 007) |
| `favorecido` | dim_favorecido | resolver pelo código |
| `codigo_funcao` .. `codigo_acao` | dim_classificacao | sem alteração |
| `modalidade_licitacao` | dim_modalidade | sem alteração |
| `valor_empenho_convertido` | medida | `REPLACE(',','.')::numeric` |

Descartadas: `observacao` (texto livre), `linguagem_cidada`,
`valor_original_empenho` (moeda da UG emitente — usar o convertido).

Cardinalidade observada: 25–33 órgãos superiores, ~1.000–1.400 UGs,
25–26 funções, 8–10 modalidades de licitação.

## staging.stg_item_empenho — 18 colunas + controle

Grão: 1 item dentro de um empenho.

**`(codigo_empenho, sequencial)` NÃO é única.** Duplicatas observadas:
27 em 16.232 (20/03/2025), 2 em 12.712 (15/07), 5 em 21.164 (19/11),
0 em 8.970 (12/02/2026). Investigar antes de definir a PK do fato.

| Coluna | Destino | Tratamento |
|---|---|---|
| `codigo_empenho` | FK do empenho | sem alteração |
| `sequencial` | parte da chave | `::int` |
| `codigo_subelemento_despesa` | dim_classificacao | nível abaixo do elemento |
| `quantidade` | medida | `REPLACE(',','.')::numeric` |
| `valor_atual` | **medida do fato** | `REPLACE(',','.')::numeric` |
| `valor_total` | não usado | ver ADR 006 |

## staging.stg_pagamento — 34 colunas + controle

Grão: 1 documento de pagamento.
Chave natural: `codigo_pagamento` (única — verificada em 4 dias).

| Coluna | Destino | Tratamento |
|---|---|---|
| `codigo_pagamento` | chave de negócio | sem alteração |
| `data_emissao` | FK dim_tempo | `TO_DATE(x,'DD/MM/YYYY')` |
| `codigo_orgao_*` | FK dim_orgao | 5–17 vazios por dia |
| `codigo_favorecido` | FK dim_favorecido | classificar (ADR 007) |
| `valor_pagamento_convertido` | medida | ~2% de valores negativos |

Descartadas: `observacao`, `valor_original_pagamento`.

## staging.stg_pagamento_empenho — 8 colunas + controle

**A ponte.** Grão: pagamento × empenho × natureza × subitem.
Chave composta única — 192.110 linhas verificadas, zero duplicatas.

| Coluna | Destino | Tratamento |
|---|---|---|
| `codigo_pagamento` | PK / FK | sem alteração |
| `codigo_empenho` | PK / FK | sem alteração |
| `codigo_natureza_despesa` | PK / FK dim_classificacao | 8 dígitos posicionais |
| `subitem` | PK | descrição textual, não código |
| `valor_pago` | medida | exercício corrente |
| `valor_rp_inscritos` | medida | restos a pagar inscritos |
| `valor_rp_cancelado` | medida | restos a pagar cancelados |
| `valor_rp_pagos` | medida | restos a pagar pagos |

### Decomposição da natureza da despesa

`codigo_natureza_despesa` tem 8 dígitos posicionais. Exemplo: `33903704`

| Posição | Componente | Valor |
|---|---|---|
| 1 | categoria econômica | `3` = corrente |
| 2 | grupo de despesa | `3` = outras despesas correntes |
| 3–4 | modalidade de aplicação | `90` = aplicação direta |
| 5–6 | elemento de despesa | `37` = locação de mão de obra |
| 7–8 | subitem | `04` |

A `dim_classificacao_despesa` é derivada por `SUBSTRING`, sem tabela
auxiliar. A coluna `subitem` fornece a descrição correspondente.

### Valores negativos

~2% das linhas em todos os dias amostrados. São anulações registradas
como **linha própria com sinal negativo**, não como ajuste da linha
original. Devem ser somadas, nunca filtradas. Padrão típico:
`-600` seguido de `600` (estorno e reemissão).

## Coluna de controle

`_arquivo_origem` — nome do CSV de origem. Não existe na fonte;
preenchida por `UPDATE` após cada `COPY`. Permite rastrear qualquer
registro até o dia de origem.
