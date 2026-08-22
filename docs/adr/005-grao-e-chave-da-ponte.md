# ADR 005 — Grão e chave da ponte pagamento×empenho

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

A relação entre pagamento e empenho é muitos-para-muitos: um pagamento
pode quitar vários empenhos, e um empenho pode ser pago em parcelas.
O arquivo `Despesas_Pagamento_EmpenhosImpactados` materializa essa
relação.

A hipótese inicial era de que o arquivo traria apenas as chaves,
exigindo rateio por critério arbitrário — o que seria o ponto mais
frágil do modelo.

## Decisão

**O arquivo traz `Valor Pago (R$)` no par pagamento×empenho.** Não há
rateio: a ponte é uma tabela de fato com medida aditiva da fonte.

O grão é **pagamento × empenho × natureza da despesa × subitem**.

Chave natural confirmada por perfilamento sobre quatro dias
(20/03/2025, 15/07/2025, 19/11/2025, 12/02/2026), totalizando 192.110
linhas com **zero duplicatas**. A ponte recebe chave primária composta
sobre as quatro colunas, sem surrogate key.

## Consequência

- **Positiva:** o rateio arbitrário sai do escopo, junto com o ADR que
  o justificaria.
- **Positiva:** `Código Natureza Despesa Completa` está presente na
  própria ponte, permitindo analisar valor pago por elemento de despesa
  sem atravessar o fato de empenho — elimina um caminho de fan trap.
- **Atenção:** somar valor empenhado e valor pago no mesmo contexto de
  linha produz fan trap. As medidas não compartilham granularidade.

## Descoberta associada: duas medidas de pagamento

| Coluna | Significado |
|---|---|
| `Valor Pago (R$)` | quita empenho do exercício corrente |
| `Valor Restos a Pagar Pagos (R$)` | quita empenho de exercício anterior |

São mutuamente exclusivas por linha. Usar apenas a primeira subestima
o desembolso — e a subestimação é maior justamente nos órgãos que mais
atrasam, que são o objeto das perguntas 7 e 9.

O modelo expõe três medidas: `valor_pago_exercicio`,
`valor_pago_restos` e `valor_pago_total`.

As colunas `Restos a Pagar Inscritos` e `Cancelado` respondem a
pergunta 9 diretamente da fonte.
