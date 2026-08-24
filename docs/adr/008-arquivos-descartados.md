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

Carregar seis arquivos: `Empenho`, `ItemEmpenho`, `Pagamento`,
`Pagamento_EmpenhosImpactados`, `Liquidacao` e
`Liquidacao_EmpenhosImpactados`.

Descartar: `ListaBancos`, `ListaPrecatorios`, `ListaFaturas`,
`FavorecidosFinais` e `ItemEmpenhoHistorico`.

## Consequência

- **Positiva:** reduz de 11 para 6 tabelas de staging.
- **Custo da liquidação:** incluir a fase adiciona 2 tabelas de
  staging, 1 ponte adicional no modelo e ~22% de volume.
- **Ganho da liquidação:** permite decompor o lead time em
  empenho → liquidação (execução do contrato, responsabilidade do
  fornecedor) e liquidação → pagamento (atraso do governo). Sem essa
  decomposição, a pergunta 7 somaria as duas responsabilidades num
  número só.
- **Sem novo download:** os arquivos de liquidação já estão dentro dos
  576 ZIPs preservados em `data/raw/`.

## Coluna descartada na carga

`Observação` (texto livre) em `Despesas_Pagamento` responde por parte
substancial dos 48% de volume do arquivo. Não responde a nenhuma das
nove perguntas analíticas. Carregada na staging para fidelidade à
fonte, descartada na passagem para o DW.

## Histórico

Versão inicial deste ADR registrava o descarte da liquidação com
status "aceito". Essa decisão não havia sido tomada. Corrigido em
2026-08-22, quando a inclusão foi decidida explicitamente.
