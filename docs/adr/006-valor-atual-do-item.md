# ADR 006 — Medida do item de empenho: valor_atual

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

`Despesas_ItemEmpenho` traz duas colunas de valor: `Valor Total` e
`Valor Atual`. O perfilamento sobre quatro dias mostrou divergência
sistemática:

| Arquivo | iguais | atual > total | atual < total |
|---|---|---|---|
| 20250320 | 677 | 9.920 | 5.635 |
| 20250715 | 1.177 | 11.106 | 429 |
| 20251119 | 1.988 | 18.558 | 618 |
| 20260212 | 880 | 8.065 | 25 |

A cardinalidade reforça: em 20250715, `Valor Total` tem 407 valores
distintos em 12.712 linhas, contra 7.033 de `Valor Atual`.

Exemplos observados: `2865000,00000 → 0,00` e `0,00 → 794,80000`.

## Decisão

A medida de `fato_empenho_item` é **`valor_atual`**.

`valor_total` é carregado na staging para rastreabilidade, mas não
alimenta o fato.

## Consequência

- **Positiva:** o valor empenhado reflete reforços e anulações, sendo
  consistente com o saldo real do empenho.
- **Negativa:** o valor perde comparabilidade com o momento da emissão
  original. Análises de "valor originalmente contratado" exigiriam
  `valor_total`, que fica disponível na staging.

## Interpretação

`Valor Total` é o valor da linha no momento da emissão, congelado.
`Valor Atual` reflete o histórico de alterações — coerente com o
projeto Empenho Web, que a partir de 2021 passou a registrar alterações
em `ItemEmpenhoHistorico` em vez de gerar documentos de reforço
separados. Usar `Valor Total` subestimaria o empenho em mais de 80%
das linhas.
