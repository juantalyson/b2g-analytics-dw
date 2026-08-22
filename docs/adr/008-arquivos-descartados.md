# ADR 008 — Arquivos descartados do escopo

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

Cada pacote diário contém 11 arquivos CSV. Tamanhos observados em
15/07/2025 (dia útil típico), descompactados:

| Arquivo | Bytes | % |
|---|---|---|
| Despesas_Pagamento | 38.017.284 | 48,0% |
| Despesas_Liquidacao | 14.456.548 | 18,2% |
| Despesas_Empenho | 8.714.640 | 11,0% |
| Pagamento_EmpenhosImpactados | 6.580.329 | 8,3% |
| ItemEmpenho | 4.710.749 | 5,9% |
| Liquidacao_EmpenhosImpactados | 2.929.539 | 3,7% |
| Pagamento_FavorecidosFinais | 1.829.892 | 2,3% |
| ItemEmpenhoHistorico | 1.743.137 | 2,2% |
| Pagamento_ListaFaturas | 235.708 | 0,3% |
| Pagamento_ListaBancos | 102 | ~0% |
| Pagamento_ListaPrecatorios | 92 | ~0% |

`ListaBancos` e `ListaPrecatorios` contêm apenas o cabeçalho.

## Decisão

Carregar quatro arquivos: `Empenho`, `ItemEmpenho`, `Pagamento` e
`Pagamento_EmpenhosImpactados`.

Descartar: `ListaBancos`, `ListaPrecatorios`, `ListaFaturas`,
`FavorecidosFinais`, `ItemEmpenhoHistorico`, `Liquidacao` e
`Liquidacao_EmpenhosImpactados`.

## Consequência

- **Negativa e assumida:** sem os arquivos de liquidação, a pergunta 7
  (lead time entre fases) é respondida apenas no trecho
  empenho → pagamento. A fase intermediária de liquidação fica fora.
  Decisão de prazo: liquidação adicionaria duas tabelas e uma segunda
  ponte, sem alterar a conclusão de negócio sobre prazo de recebimento.
- **Positiva:** reduz de 11 para 4 tabelas de staging.
- **Reversível:** os ZIPs preservados em `data/raw/` permitem incluir
  liquidação sem novo download, caso sobre tempo.

## Coluna descartada na carga

`Observação` (texto livre) em `Despesas_Pagamento` responde por parte
substancial dos 48% de volume do arquivo. Não responde a nenhuma das
nove perguntas analíticas. Carregada na staging para fidelidade à
fonte, descartada na passagem para o DW.
