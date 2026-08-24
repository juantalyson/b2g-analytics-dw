"""
Carrega os ZIPs de data/raw/ para as tabelas de staging no Postgres.

Para cada dia: extrai os seis CSVs, executa COPY em cada tabela, marca
_arquivo_origem e apaga os CSVs. Um dia por transacao — ou entra tudo,
ou nao entra nada.

A lista de colunas de cada COPY e lida do catalogo do banco, na ordem
de declaracao, ignorando colunas de controle (prefixo _). O DDL segue
sendo a fonte unica da verdade.

Uso:
    python src/load/carregar.py
    python src/load/carregar.py --limite 5     # testa com 5 dias
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
INTERIM = RAIZ / "data" / "interim"
CHECKPOINT = RAW / "_checkpoint_carga.json"

CONTAINER = "b2g_postgres"
DB_USER = os.environ.get("POSTGRES_USER", "b2g")
DB_NAME = os.environ.get("POSTGRES_DB", "b2g_dw")

# sufixo do CSV -> tabela de destino
MAPA = {
    "_Despesas_Empenho.csv": "stg_empenho",
    "_Despesas_ItemEmpenho.csv": "stg_item_empenho",
    "_Despesas_Pagamento.csv": "stg_pagamento",
    "_Despesas_Pagamento_EmpenhosImpactados.csv": "stg_pagamento_empenho",
    "_Despesas_Liquidacao.csv": "stg_liquidacao",
    "_Despesas_Liquidacao_EmpenhosImpactados.csv": "stg_liquidacao_empenho",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(RAIZ / "data" / "raw" / "_carga.log",
                            encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def psql(sql: str) -> str:
    """Executa SQL no container e devolve a saida."""
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", CONTAINER.replace("b2g_", ""),
         "psql", "-U", DB_USER, "-d", DB_NAME, "-v", "ON_ERROR_STOP=1",
         "-t", "-A", "-c", sql],
        cwd=RAIZ, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql falhou:\n{r.stderr.strip()}")
    return r.stdout.strip()


def colunas_da_tabela(tabela: str) -> list[str]:
    """Le as colunas do catalogo, na ordem do DDL, sem as de controle."""
    sql = (
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema='staging' AND table_name='{tabela}' "
        "AND column_name NOT LIKE '\\_%' ORDER BY ordinal_position;"
    )
    return [c for c in psql(sql).splitlines() if c]


def carregar_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    return {}


def salvar_checkpoint(estado: dict) -> None:
    CHECKPOINT.write_text(
        json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def extrair(zip_path: Path) -> list[Path]:
    """Extrai apenas os seis CSVs de interesse. Devolve os caminhos."""
    extraidos = []
    with zipfile.ZipFile(zip_path) as z:
        for nome in z.namelist():
            if not any(nome.endswith(s) for s in MAPA):
                continue
            destino = INTERIM / Path(nome).name
            with z.open(nome) as origem, destino.open("wb") as saida:
                saida.write(origem.read())
            extraidos.append(destino)
    return extraidos


def montar_sql(arquivos: list[Path], colunas: dict[str, list[str]]) -> str:
    """Monta a transacao com os COPY e os UPDATE de origem."""
    partes = ["BEGIN;"]
    for csv_path in sorted(arquivos):
        sufixo = next(s for s in MAPA if csv_path.name.endswith(s))
        tabela = MAPA[sufixo]
        cols = ", ".join(colunas[tabela])
        caminho_container = f"/data/interim/{csv_path.name}"
        partes.append(
            f"COPY staging.{tabela} ({cols}) FROM '{caminho_container}' "
            f"WITH (FORMAT csv, HEADER true, DELIMITER ';', "
            f"ENCODING 'LATIN1');"
        )
        partes.append(
            f"UPDATE staging.{tabela} SET _arquivo_origem = "
            f"'{csv_path.name}' WHERE _arquivo_origem IS NULL;"
        )
    partes.append("COMMIT;")
    return "\n".join(partes)


def carregar_dia(zip_path: Path, colunas: dict[str, list[str]]) -> dict:
    chave = zip_path.stem.split("_")[0]
    arquivos = []
    try:
        arquivos = extrair(zip_path)
        if not arquivos:
            return {"status": "vazio", "arquivos": 0}

        psql(montar_sql(arquivos, colunas))
        return {"status": "ok", "arquivos": len(arquivos),
                "em": time.strftime("%Y-%m-%d %H:%M:%S")}

    except Exception as erro:
        log.error("%s falhou: %s", chave, erro)
        return {"status": "erro", "detalhe": str(erro)[:300]}
    finally:
        for f in arquivos:
            f.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=None,
                    help="carrega apenas os N primeiros dias pendentes")
    args = ap.parse_args()

    INTERIM.mkdir(parents=True, exist_ok=True)

    log.info("lendo colunas do catalogo...")
    colunas = {t: colunas_da_tabela(t) for t in MAPA.values()}
    for t, c in colunas.items():
        log.info("  %-24s %d colunas", t, len(c))

    estado = carregar_checkpoint()
    zips = sorted(RAW.glob("*_despesas.zip"))
    pendentes = [
        z for z in zips
        if estado.get(z.stem.split("_")[0], {}).get("status") != "ok"
    ]
    if args.limite:
        pendentes = pendentes[:args.limite]

    log.info("%d ZIPs no disco, %d pendentes", len(zips), len(pendentes))

    inicio = time.time()
    for i, zip_path in enumerate(pendentes, start=1):
        chave = zip_path.stem.split("_")[0]
        registro = carregar_dia(zip_path, colunas)
        estado[chave] = registro
        salvar_checkpoint(estado)

        marca = {"ok": "", "vazio": "  (vazio)"}.get(
            registro["status"], "  FALHOU")
        log.info("[%d/%d] %s%s", i, len(pendentes), chave, marca)

    dur = time.time() - inicio
    ok = sum(1 for v in estado.values() if v["status"] == "ok")
    vazios = sum(1 for v in estado.values() if v["status"] == "vazio")
    erros = sum(1 for v in estado.values() if v["status"] == "erro")
    log.info("Concluido em %.1f min: %d ok, %d vazios, %d erros",
             dur / 60, ok, vazios, erros)


if __name__ == "__main__":
    main()