-- =====================================================================
-- Staging: espelho fiel dos CSVs do Portal da Transparência.
--
-- Todas as colunas são TEXT e não há constraint. A carga não pode
-- falhar por causa do dado: tipagem, validação e limpeza acontecem
-- na passagem de staging para DW.
--
-- Ordem das colunas = ordem do CSV. O COPY casa por posição.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS staging;

-- ---------------------------------------------------------------------
-- Empenho — 63 colunas. Grão: 1 documento de empenho.
-- Chave natural confirmada no perfilamento: codigo_empenho (única).
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS staging.stg_empenho;
CREATE TABLE staging.stg_empenho (
    id_empenho                          TEXT,
    codigo_empenho                      TEXT,
    codigo_empenho_resumido             TEXT,
    data_emissao                        TEXT,
    codigo_tipo_documento               TEXT,
    tipo_documento                      TEXT,
    tipo_empenho                        TEXT,
    especie_empenho                     TEXT,
    codigo_orgao_superior               TEXT,
    orgao_superior                      TEXT,
    codigo_orgao                        TEXT,
    orgao                               TEXT,
    codigo_unidade_gestora              TEXT,
    unidade_gestora                     TEXT,
    codigo_gestao                       TEXT,
    gestao                              TEXT,
    codigo_favorecido                   TEXT,
    favorecido                          TEXT,
    observacao                          TEXT,
    codigo_esfera_orcamentaria          TEXT,
    esfera_orcamentaria                 TEXT,
    codigo_tipo_credito                 TEXT,
    tipo_credito                        TEXT,
    codigo_grupo_fonte_recurso          TEXT,
    grupo_fonte_recurso                 TEXT,
    codigo_fonte_recurso                TEXT,
    fonte_recurso                       TEXT,
    codigo_unidade_orcamentaria         TEXT,
    unidade_orcamentaria                TEXT,
    codigo_funcao                       TEXT,
    funcao                              TEXT,
    codigo_subfuncao                    TEXT,
    subfuncao                           TEXT,
    codigo_programa                     TEXT,
    programa                            TEXT,
    codigo_acao                         TEXT,
    acao                                TEXT,
    linguagem_cidada                    TEXT,
    codigo_subtitulo                    TEXT,
    subtitulo                           TEXT,
    codigo_plano_orcamentario           TEXT,
    plano_orcamentario                  TEXT,
    codigo_programa_governo             TEXT,
    nome_programa_governo               TEXT,
    autor_emenda                        TEXT,
    codigo_categoria_despesa            TEXT,
    categoria_despesa                   TEXT,
    codigo_grupo_despesa                TEXT,
    grupo_despesa                       TEXT,
    codigo_modalidade_aplicacao         TEXT,
    modalidade_aplicacao                TEXT,
    codigo_elemento_despesa             TEXT,
    elemento_despesa                    TEXT,
    processo                            TEXT,
    modalidade_licitacao                TEXT,
    inciso                              TEXT,
    amparo                              TEXT,
    referencia_dispensa_inexigibilidade TEXT,
    codigo_convenio                     TEXT,
    contrato_repasse                    TEXT,
    valor_original_empenho              TEXT,
    valor_empenho_convertido            TEXT,
    valor_utilizado_conversao           TEXT,
    _arquivo_origem                     TEXT
);

-- ---------------------------------------------------------------------
-- ItemEmpenho — 18 colunas. Grão: 1 item dentro de um empenho.
--
-- ATENÇÃO: (codigo_empenho, sequencial) NÃO é única. O perfilamento
-- encontrou de 0 a 27 duplicatas por dia. Investigar em SQL antes de
-- definir a PK do fato.
--
-- valor_total fica congelado no valor original da linha; valor_atual
-- reflete reforços e anulações. A medida do fato é valor_atual.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS staging.stg_item_empenho;
CREATE TABLE staging.stg_item_empenho (
    id_empenho                      TEXT,
    codigo_empenho                  TEXT,
    codigo_categoria_despesa        TEXT,
    categoria_despesa               TEXT,
    codigo_grupo_despesa            TEXT,
    grupo_despesa                   TEXT,
    codigo_modalidade_aplicacao     TEXT,
    modalidade_aplicacao            TEXT,
    codigo_elemento_despesa         TEXT,
    elemento_despesa                TEXT,
    codigo_subelemento_despesa      TEXT,
    subelemento_despesa             TEXT,
    descricao                       TEXT,
    quantidade                      TEXT,
    valor_unitario                  TEXT,
    valor_total                     TEXT,
    sequencial                      TEXT,
    valor_atual                     TEXT,
    _arquivo_origem                 TEXT
);

-- ---------------------------------------------------------------------
-- Pagamento — 34 colunas. Grão: 1 documento de pagamento.
-- Chave natural confirmada: codigo_pagamento (única).
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS staging.stg_pagamento;
CREATE TABLE staging.stg_pagamento (
    codigo_pagamento                TEXT,
    codigo_pagamento_resumido       TEXT,
    data_emissao                    TEXT,
    codigo_tipo_documento           TEXT,
    tipo_documento                  TEXT,
    tipo_ob                         TEXT,
    extraorcamentario               TEXT,
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
    processo                        TEXT,
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
    valor_original_pagamento        TEXT,
    valor_pagamento_convertido      TEXT,
    valor_utilizado_conversao       TEXT,
    _arquivo_origem                 TEXT
);

-- ---------------------------------------------------------------------
-- Pagamento_EmpenhosImpactados — 8 colunas. A PONTE.
--
-- Grão: pagamento × empenho × natureza × subitem.
-- Chave confirmada única em 4 dias (192.110 linhas, 0 duplicatas).
--
-- Duas medidas distintas de pagamento:
--   valor_pago      -> quita empenho do exercício corrente
--   valor_rp_pagos  -> quita empenho de exercício anterior (restos)
-- São mutuamente exclusivas por linha. Somar só a primeira subestima
-- o desembolso, e erra mais nos órgãos que mais atrasam.
--
-- subitem é DESCRIÇÃO textual, não código. O código do subitem está
-- nas posições 7-8 de codigo_natureza_despesa.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS staging.stg_pagamento_empenho;
CREATE TABLE staging.stg_pagamento_empenho (
    codigo_pagamento                TEXT,
    codigo_empenho                  TEXT,
    codigo_natureza_despesa         TEXT,
    subitem                         TEXT,
    valor_pago                      TEXT,
    valor_rp_inscritos              TEXT,
    valor_rp_cancelado              TEXT,
    valor_rp_pagos                  TEXT,
    _arquivo_origem                 TEXT
);
