# ADR 004 — COPY server-side em vez de \copy

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

Há duas formas de carregar CSV no PostgreSQL:

- `COPY` — comando SQL executado **no servidor**. O caminho do arquivo
  é resolvido no sistema de arquivos do servidor.
- `\copy` — meta-comando do `psql`, executado **no cliente**. O cliente
  lê o arquivo e transmite o conteúdo pela conexão.

Com o PostgreSQL em container, o servidor enxerga apenas o filesystem
do container. Um caminho do host resulta em "arquivo não existe".

O volume esperado é de dezenas de milhões de linhas.

## Decisão

Usar `COPY` server-side, com o diretório de dados montado como bind
mount somente-leitura no container:

```yaml
- ./data:/data:ro
```

`~/b2g-analytics-dw/data/interim/x.csv` no host corresponde a
`/data/interim/x.csv` dentro do container.

## Consequência

- **Positiva:** o dado não trafega pelo socket cliente-servidor.
- **Positiva:** o `:ro` impede o Postgres de escrever no diretório
  de dados do projeto.
- **Negativa:** cria acoplamento entre a localização física dos
  arquivos e a configuração do container. O projeto deixa de ser
  portável para um Postgres remoto sem ajuste.
- **Negativa:** exige que o projeto viva dentro do WSL. Um bind mount
  sobre `/mnt/c/` somaria a camada drvfs, com penalidade de 5 a 10x
  em leitura sequencial.
