-- =====================================================================
-- Staging de liquidação. Complementa 01_ddl_staging.sql.
--
-- Despesas_Liquidacao NÃO tem coluna de valor. O documento é só
-- cabeçalho: quem liquidou, quando, para quem, sob qual classificação.
-- O valor vive integralmente na ponte.
-- Consequência: liquidação entra no modelo como dimensão degenerada,
-- não como fato.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Liquidacao — 28 colunas. Grão: 1 documento de liquidação.
-- Chave natural: codigo_liquidacao (única em 93.164 linhas / 4 dias).
--
-- ATENÇÃO: codigo_elemento_despesa contém valores não numéricos
-- ('MU' = múltiplo, '-1' = sem informação). Não tipar como inteiro.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS staging.stg_liquidacao;
CREATE TABLE staging.stg_liquidacao (
    codigo_liquidacao               TEXT,
    codigo_liquidacao_resumido      TEXT,
    data_emissao                    TEXT,
    codigo_tipo_documento           TEXT,
    tipo_documento                  TEXT,
    codigo_orgao_superior           TEXT,
    orgao_superior                  TEXT,
    codigo_orgao                    TEXT,
    orgao                           TEXT,
    codigo_unidade_gestora          TEXT,
    unidade_gestora                 TEXT,
    codigo_gestao                   TEXT,
    gestao                          TEXT,
    codigo_favorecido               TEXT,
    favorecido                      TEXT,
    observacao                      TEXT,
    codigo_categoria_despesa        TEXT,
    categoria_despesa               TEXT,
    codigo_grupo_despesa            TEXT,
    grupo_despesa                   TEXT,
    codigo_modalidade_aplicacao     TEXT,
    modalidade_aplicacao            TEXT,
    codigo_elemento_despesa         TEXT,
    elemento_despesa                TEXT,
    codigo_plano_orcamentario       TEXT,
    plano_orcamentario              TEXT,
    codigo_programa_governo         TEXT,
    nome_programa_governo           TEXT,
    _arquivo_origem                 TEXT
);

-- ---------------------------------------------------------------------
-- Liquidacao_EmpenhosImpactados — 8 colunas. A SEGUNDA PONTE.
--
-- Grão: liquidação × empenho × natureza × subitem.
-- Chave única confirmada — 106.739 linhas em 4 dias, 0 duplicatas.
-- Estrutura simétrica à ponte de pagamento.
--
-- É aqui que vive o valor liquidado. O lead time da pergunta 7 sai do
-- JOIN entre esta ponte e stg_pagamento_empenho, por codigo_empenho.
--
-- valor_rp_inscritos apresenta negativos (cancelamento de inscrição).
-- Somar, não filtrar.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS staging.stg_liquidacao_empenho;
CREATE TABLE staging.stg_liquidacao_empenho (
    codigo_liquidacao               TEXT,
    codigo_empenho                  TEXT,
    codigo_natureza_despesa         TEXT,
    subitem                         TEXT,
    valor_liquidado                 TEXT,
    valor_rp_inscritos              TEXT,
    valor_rp_cancelado              TEXT,
    valor_rp_pagos                  TEXT,
    _arquivo_origem                 TEXT
);