# Governança e LGPD

## Base legal dos dados

Dados abertos do Portal da Transparência, publicados pela CGU sob a
Lei de Acesso à Informação (Lei 12.527/2011) e o Decreto 8.777/2016.
Uso livre para qualquer finalidade, sem restrição de licença.

## Pessoa física

Beneficiários pessoa física aparecem com CPF **já mascarado na fonte**
(`***.410.797-**`) — apenas os seis dígitos centrais são visíveis. O
nome completo é publicado.

Entre 10% e 24% dos pagamentos amostrados têm favorecido pessoa física.

### Regra do projeto

O modelo publicado **não persiste identificador nem nome de pessoa
física**. Registros de PF são agregados na categoria `PESSOA_FISICA`
da `dim_favorecido`, sem chave individual.

Motivo: ainda que a fonte seja pública e o CPF mascarado, a combinação
de nome, órgão, valor e data em um modelo dimensional consultável
permite reidentificação e construção de perfil — tratamento que
extrapola a finalidade do projeto, que é análise de mercado B2G.

### O que isso implica

- A curva ABC de fornecedores considera apenas pessoa jurídica.
- Os valores pagos a PF entram nos totais agregados por órgão, sem
  detalhamento por indivíduo.
- Nenhuma página do dashboard permite navegar até uma pessoa física.

## Valores sentinela

O campo `Código Favorecido` contém códigos que não identificam
entidade:

| Código | Significado |
|---|---|
| `-11` | Informação protegida por sigilo |
| `-13` | Dado referente à Folha de Pagamento |
| `-1` | Sem informação |
| `-3` | Inválido |

Tratados como `NAO_IDENTIFICADO`. O código `-13` representa a folha de
pagamento agregada e responde por 1,8% a 3,0% dos pagamentos.

Não são convertidos em nulo: a distinção entre "sigiloso" e "sem
informação" é analiticamente relevante e fica preservada.

## Dados no repositório

Nenhum dado bruto é versionado. O `.gitignore` bloqueia `data/`,
`*.csv`, `*.zip` e `*.parquet`.

Credenciais ficam em `.env`, também ignorado. O repositório contém
`.env.example` com as chaves e sem os valores.

## Limitações declaradas

1. **Defasagem da fonte.** O portal publica com atraso de ~21 dias.
   Em 21/08/2026, arquivos de 31/07/2026 em diante retornavam HTTP 403.
2. **Mutabilidade retroativa.** Ver ADR 002. O recorte reflete o
   estado da fonte na data do download.
3. **Perfilamento pendente da liquidação.** `Liquidacao` e
   `Liquidacao_EmpenhosImpactados` entraram no escopo em 22/08/2026
   (ADR 008), mas ainda não foram perfilados. O lead time decomposto
   em empenho → liquidação → pagamento depende desse passo.
