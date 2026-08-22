"""
Baixa os pacotes diários de despesas do Portal da Transparência.

Cada dia do calendário é um ZIP com 11 CSVs. Fins de semana e feriados
retornam ZIP válido (~7 KB) contendo apenas cabeçalhos — isso é
resultado esperado, não falha.

O progresso é gravado em data/raw/_checkpoint.json a cada arquivo, o
que permite interromper e retomar sem rebaixar o que já foi obtido.
"""

import json
import logging
import sys
import time
from datetime import date, timedelta
from pathlib import Path
import requests

BASE_URL = "https://portaldatransparencia.gov.br/download-de-dados/despesas"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CHECKPOINT = RAW_DIR / "_checkpoint.json"

DATA_INICIO = date(2025, 1, 1)
DATA_FIM = date.today()

PAUSA_SEGUNDOS = 1.0
MAX_TENTATIVAS = 3
TIMEOUT = 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(RAW_DIR / "_download.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def carregar_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    return {}


def salvar_checkpoint(estado: dict) -> None:
    CHECKPOINT.write_text(
        json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def gerar_datas(inicio: date, fim: date):
    atual = inicio
    while atual <= fim:
        yield atual
        atual += timedelta(days=1)


def baixar_dia(dia: date) -> dict:
    """Baixa o ZIP de um dia. Retorna o registro para o checkpoint."""
    chave = dia.strftime("%Y%m%d")
    destino = RAW_DIR / f"{chave}_despesas.zip"
    url = f"{BASE_URL}/{chave}"

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(url, timeout=TIMEOUT, stream=True)
            resposta.raise_for_status()

            tamanho_esperado = int(resposta.headers.get("content-length", 0))

            with destino.open("wb") as f:
                for bloco in resposta.iter_content(chunk_size=65536):
                    f.write(bloco)

            tamanho_real = destino.stat().st_size

            if tamanho_esperado and tamanho_real != tamanho_esperado:
                raise IOError(
                    f"truncado: {tamanho_real} de {tamanho_esperado} bytes"
                )

            return {
                "status": "ok",
                "bytes": tamanho_real,
                "baixado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as erro:
            espera = 2 ** tentativa
            log.warning(
                "%s tentativa %d/%d falhou (%s)",
                chave, tentativa, MAX_TENTATIVAS, erro
            )
            if destino.exists():
                destino.unlink()
            if tentativa < MAX_TENTATIVAS:
                time.sleep(espera)

    return {"status": "erro", "baixado_em": time.strftime("%Y-%m-%d %H:%M:%S")}


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    estado = carregar_checkpoint()

    datas = list(gerar_datas(DATA_INICIO, DATA_FIM))
    pendentes = [
        d for d in datas
        if estado.get(d.strftime("%Y%m%d"), {}).get("status") != "ok"
    ]

    log.info(
        "%d dias no período, %d já baixados, %d pendentes",
        len(datas), len(datas) - len(pendentes), len(pendentes)
    )

    for i, dia in enumerate(pendentes, start=1):
        chave = dia.strftime("%Y%m%d")
        registro = baixar_dia(dia)
        estado[chave] = registro
        salvar_checkpoint(estado)

        if registro["status"] == "ok":
            mb = registro["bytes"] / 1_048_576
            log.info("[%d/%d] %s  %.1f MB", i, len(pendentes), chave, mb)
        else:
            log.error("[%d/%d] %s  FALHOU", i, len(pendentes), chave)

        time.sleep(PAUSA_SEGUNDOS)

    ok = sum(1 for v in estado.values() if v["status"] == "ok")
    erros = sum(1 for v in estado.values() if v["status"] == "erro")
    total_mb = sum(
        v.get("bytes", 0) for v in estado.values()
    ) / 1_048_576

    log.info("Concluído: %d ok, %d erros, %.1f MB", ok, erros, total_mb)


if __name__ == "__main__":
    main()