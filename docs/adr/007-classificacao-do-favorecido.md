# ADR 007 — Classificação do favorecido e LGPD

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

A regra inicial do projeto era: "fornecedor é resolvido sempre por
CNPJ, nunca por razão social". O perfilamento revelou que o campo
`Código Favorecido` contém seis padrões distintos.

Distribuição em `Despesas_Pagamento`, quatro dias amostrados:

| Padrão | Exemplo | Faixa |
|---|---|---|
| 14 dígitos — CNPJ | `42644220000106` | 67–81% |
| Mascarado — CPF | `***.410.797-**` | 10–24% |
| ≤6 dígitos — UG | `153010` | 4–7% |
| 9 caracteres com `EX` | `EXAMAZON2` | 0,7–5% |
| Sentinela negativa | `-11`, `-13`, `-1`, `-3` | 1,8–3,0% |
| Agrupador | `RB0000050` | raro |

Sentinelas identificadas: `-11` = informação protegida por sigilo,
`-13` = folha de pagamento, `-1` = sem informação, `-3` = inválido.

Códigos com prefixo `EX` são fornecedores estrangeiros, sem CNPJ:
`EXAMAZON2 = AMAZON ONLINE`, `EXE0D0078 = DIEHL DEFENCE GMBH & CO. KG`,
`EXUNGFUND = UNITED NATIONS GENERAL FUND`.

## Decisão

`dim_favorecido` recebe uma coluna `tipo_favorecido` derivada do
padrão do código:

| tipo | regra | entra na análise de mercado |
|---|---|---|
| `PJ_NACIONAL` | 14 dígitos numéricos | sim |
| `PJ_ESTRANGEIRA` | prefixo `EX` | sim, marcada |
| `ORGAO_PUBLICO` | ≤6 dígitos numéricos | não |
| `PESSOA_FISICA` | contém `*` ou 11 dígitos | não |
| `NAO_IDENTIFICADO` | sentinela negativa ou vazio | não |
| `AGRUPADOR` | prefixo `RB` | não |

**LGPD:** pessoa física é agregada sem identificador. O CPF já vem
mascarado da fonte, e nem o valor mascarado é persistido no modelo
publicado.

**Transferências intragovernamentais** (`ORGAO_PUBLICO`) são excluídas
da análise de concorrência. Incluí-las listaria órgãos públicos na
curva ABC de fornecedores, distorcendo a leitura de mercado.

## Consequência

- **Positiva:** a análise de mercado reflete fornecedores reais.
- **Positiva:** conformidade com LGPD documentada e verificável.
- **Negativa:** o total de despesa do dashboard não bate com o total
  bruto do governo. A diferença precisa ser explicitada no relatório.
- **Revisão:** a regra original "sempre por CNPJ" fica ajustada —
  fornecedor estrangeiro é resolvido pelo código `EX`, que é o único
  identificador disponível.
