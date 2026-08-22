# ADR 001 — Ponto de montagem do volume no PostgreSQL 18

**Data:** 2026-08-21 · **Status:** aceito

## Contexto

A imagem oficial do PostgreSQL mudou o layout do diretório de dados a
partir da versão 18. O cluster passou a ficar em um subdiretório
versionado (compatível com `pg_ctlcluster`), e não mais diretamente em
`/var/lib/postgresql/data`.

Montar o volume no caminho antigo faz o container recusar a
inicialização em loop, com a mensagem: *"there appears to be PostgreSQL
data in /var/lib/postgresql/data (unused mount/volume)"*. A imagem
interpreta o volume como resíduo de um upgrade mal executado e aborta
para não corromper dados.

## Decisão

Montar o volume nomeado em `/var/lib/postgresql`, sem o `/data`.

```yaml
volumes:
  - pgdata:/var/lib/postgresql
  - ./data:/data:ro
```

## Consequência

- A imagem cria o subdiretório versionado por conta própria.
- O compose diverge da maioria dos tutoriais, que ainda documentam o
  layout pré-18. Isso exige o comentário no arquivo.
- Fixar a versão da imagem passa a ser obrigatório. `postgres:latest`
  quebraria o ambiente numa futura mudança de layout.
- Ao trocar o ponto de montagem é necessário `docker compose down -v`,
  pois o volume antigo tem estrutura incompatível.

## Lição de método

O erro persistiu por várias tentativas porque a correção foi aplicada
a um arquivo duplicado (`infra/docker-compose.yml`) enquanto o Docker
lia outro (raiz). Regra adotada: após editar arquivo de configuração,
verificar o conteúdo no disco com `grep` ou `cat` antes de reexecutar.
