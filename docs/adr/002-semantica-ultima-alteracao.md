# ADR 002 — Semântica de "última alteração" da fonte

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

O dicionário de dados oficial do Portal da Transparência afirma, sobre
o documento de empenho:

> Um empenho pode ter os seus valores atualizados e consta apenas na
> planilha do dia em que houve a última alteração. Assim, em caso de
> atualização, seu registro na planilha antiga é excluído, evitando
> duplicações.

Os arquivos diários **não são um log de eventos**. São um snapshot do
estado corrente, fatiado por data de última alteração. Um documento
migra de arquivo sempre que é alterado.

Isso foi descoberto lendo o dicionário antes de escrever o pipeline —
não durante a carga.

## Decisão

1. O recorte temporal se define por `Data Emissão`, não pela data do
   arquivo. Para obter os documentos emitidos no exercício 2025, é
   necessário baixar os arquivos de 01/01/2025 até a data corrente.
2. Nenhuma lógica de deduplicação é implementada. A fonte já garante
   um registro por documento na união de todos os dias.
3. Os ZIPs são preservados em `data/raw/` após a extração, permitindo
   reprocessar sem novo download.

## Consequência

- **Positiva:** deduplicação sai do escopo, reduzindo o trabalho da
  camada de transformação.
- **Positiva:** exercícios recentes custam menos dias de download.
  2025 exige ~420 dias de arquivo; 2024 exigiria ~650.
- **Negativa:** os arquivos são mutáveis retroativamente. Um dia
  baixado hoje difere do mesmo dia baixado há um ano. O pipeline não
  é reprodutível a partir da fonte — apenas a partir de `data/raw/`.
- **Negativa:** o recorte não é um exercício fechado no sentido
  contábil. Documentos alterados após a última data baixada estão
  ausentes.

## Limitação conhecida

O portal publica com defasagem de aproximadamente 21 dias. Em
21/08/2026, os arquivos de 31/07/2026 em diante retornavam HTTP 403.
Documentado no README como limitação da fonte.
