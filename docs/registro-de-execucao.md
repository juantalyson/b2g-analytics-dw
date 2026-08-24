# Registro de Execução

## Fase 0 — Reconhecimento da fonte

Leitura do dicionário oficial antes de escrever qualquer código.
Descoberta central: a fonte não é log de eventos (ADR 002).

Verificações feitas por `curl -I` sobre a URL de download:
- padrão de URL confirmado: `/download-de-dados/despesas/AAAAMMDD`
- dia útil retorna HTTP 200, `application/x-zip-compressed`, ~8,9 MB
- fim de semana retorna HTTP 200 com ZIP de ~7 KB (só cabeçalhos)
- `unzip -l` revelou 11 arquivos, ~79 MB descompactados

## Fase 1 — Repositório

Estrutura criada, `.gitignore` configurado, Git inicializado e
publicado em `github.com/juantalyson/b2g-analytics-dw`.

Correção necessária: `data/` como regra de exclusão impede o Git de
descer no diretório, tornando inalcançáveis as negações `!data/raw/`.
Substituído por `data/**` com re-inclusão explícita dos diretórios.

## Fase 2 — PostgreSQL em container

PostgreSQL 18 em Docker, exposto em `localhost:5434`.
Porta 5433 já ocupada por outro projeto na mesma máquina.

Problema resolvido: ADR 001 (ponto de montagem do volume).

## Fase 3 — Ingestão

`src/ingest/download.py` — download com checkpoint em JSON, retry com
backoff exponencial, verificação de `content-length` contra o tamanho
gravado, pausa de 1s entre requisições.

Resultado: **576 ZIPs, 3,1 GB**, período 01/01/2025 a 21/08/2026.
22 dias indisponíveis (31/07/2026 a 21/08/2026) — defasagem da fonte,
não falha de download. Retentar em ~3 semanas.

Integridade verificada por amostra aleatória de 5 arquivos (`unzip -t`).

## Fase 4 — Staging (em andamento)

`src/profiling/perfilar.py` — perfilamento sobre 4 dias amostrados
(20/03/2025, 15/07/2025, 19/11/2025, 12/02/2026).

Achados que alteraram o modelo:
- ponte com chave única confirmada (ADR 005)
- `valor_total` do item corrompido, usar `valor_atual` (ADR 006)
- seis padrões de favorecido, incluindo `EX` e sentinelas (ADR 007)
- `(codigo_empenho, sequencial)` não é única em ItemEmpenho — pendente

`sql/01_staging/01_ddl_staging.sql` — quatro tabelas, todas as colunas
`TEXT`, sem constraint (ADR 003).

Validado: 64, 19, 35 e 9 colunas (sempre +1 pelo `_arquivo_origem`).

### Pendências para a próxima sessão

1. Investigar as duplicatas de `(codigo_empenho, sequencial)` — o que
   difere entre as linhas repetidas?
2. Perfilar `Liquidacao` e `Liquidacao_EmpenhosImpactados`:
   cabeçalhos, grão, chave candidata e formato dos valores.
3. Escrever o DDL das duas novas tabelas de staging.
4. Escrever o script de carga: extrair → `COPY` → marcar origem →
   limpar CSV → próximo dia.
5. Migrar o perfilamento restante para SQL sobre a staging, em vez de
   Python sobre CSV.
