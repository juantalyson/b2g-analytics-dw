"""
Perfilamento dos CSVs de despesa do Portal da Transparencia.

Le os arquivos em data/interim/ em streaming (uma linha por vez, sem
carregar o arquivo em memoria) e produz o relatorio necessario para
escrever o DDL da staging.

Dois modos:
  - Mapeado: usa COLUNAS_FOCO e CHAVES quando o layout ja e conhecido.
  - Descoberta: quando o rotulo nao esta mapeado, imprime o cabecalho
    numerado, detecta colunas de valor pelo nome e testa unicidade de
    combinacoes progressivas das primeiras colunas.

Uso:
    python src/profiling/perfilar.py
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
INTERIM = RAIZ / "data" / "interim"
ENCODING = "latin-1"
DELIM = ";"

MAX_COMBINACAO_CHAVE = 4
LIMITE_DISTINTOS = 100_000

COLUNAS_FOCO = {
    "Empenho": [
        "Código Empenho", "Data Emissão", "Tipo Empenho",
        "Código Órgão Superior", "Código Unidade Gestora",
        "Código Favorecido", "Favorecido", "Código Função",
        "Modalidade de Licitação", "Valor do Empenho Convertido pra R$",
    ],
    "ItemEmpenho": [
        "Código Empenho", "Sequencial", "Código SubElemento de Despesa",
        "Quantidade", "Valor Unitário", "Valor Total", "Valor Atual",
    ],
    "Pagamento": [
        "Código Pagamento", "Data Emissão", "Código Órgão Superior",
        "Código Unidade Gestora", "Código Favorecido",
        "Valor do Pagamento Convertido pra R$",
    ],
    "Pagamento_EmpenhosImpactados": [
        "Código Pagamento", "Código Empenho",
        "Código Natureza Despesa Completa", "Subitem",
        "Valor Pago (R$)", "Valor Restos a Pagar Inscritos (R$)",
        "Valor Restos a Pagar Cancelado (R$)",
        "Valor Restos a Pagar Pagos (R$)",
    ],
    "Liquidacao": [
        "Código Liquidação", "Data Emissão", "Código Órgão Superior",
        "Código Unidade Gestora", "Código Favorecido", "Favorecido",
        "Código Elemento de Despesa",
    ],
    "Liquidacao_EmpenhosImpactados": [
        "Código Liquidação", "Código Empenho",
        "Código Natureza Despesa Completa", "Subitem",
        "Valor Liquidado (R$)", "Valor Restos a Pagar Inscritos (R$)",
        "Valor Restos a Pagar Cancelado (R$)",
        "Valor Restos a Pagar Pagos (R$)",
    ],
}

CHAVES = {
    "Empenho": ["Código Empenho"],
    "ItemEmpenho": ["Código Empenho", "Sequencial"],
    "Pagamento": ["Código Pagamento"],
    "Pagamento_EmpenhosImpactados": [
        "Código Pagamento", "Código Empenho",
        "Código Natureza Despesa Completa", "Subitem",
    ],
    "Liquidacao": ["Código Liquidação"],
    "Liquidacao_EmpenhosImpactados": [
        "Código Liquidação", "Código Empenho",
        "Código Natureza Despesa Completa", "Subitem",
    ],
}

RE_DIGITOS = re.compile(r"^\d+$")
RE_DECIMAL_VIRGULA = re.compile(r"^-?\d+,\d+$")
RE_MILHAR = re.compile(r"^-?\d{1,3}(\.\d{3})+,\d+$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def eh_coluna_numerica(nome: str) -> bool:
    n = nome.lower()
    return "valor" in n or "quantidade" in n


def tipo_favorecido(codigo: str) -> str:
    if not codigo:
        return "vazio"
    if "*" in codigo:
        return "PF mascarado"
    if codigo.startswith("-"):
        return f"sentinela ({codigo})"
    if codigo.upper().startswith("EX"):
        return "PJ estrangeira (EX)"
    n = len(codigo)
    if n == 14:
        return "CNPJ (14)"
    if n == 11:
        return "CPF completo (11)"
    if n <= 6:
        return f"orgao/UG ({n})"
    return f"outro ({n} caracteres)"


def formato_valor(v: str) -> str:
    if not v:
        return "vazio"
    if RE_MILHAR.match(v):
        return "decimal virgula COM separador de milhar"
    if RE_DECIMAL_VIRGULA.match(v):
        return "decimal virgula"
    if RE_DIGITOS.match(v):
        return "so digitos"
    if RE_DATA.match(v):
        return "data DD/MM/AAAA"
    return "outro"


def perfilar(caminho: Path, rotulo: str) -> None:
    print("=" * 72)
    print(f"ARQUIVO: {caminho.name}")

    mapeado = rotulo in COLUNAS_FOCO
    print(f"MODO: {'mapeado' if mapeado else 'DESCOBERTA (layout novo)'}")
    print("=" * 72)

    total = 0
    vazios = Counter()
    distintos = defaultdict(set)
    amostras = defaultdict(list)
    formatos = defaultdict(Counter)
    tipos_fav = Counter()
    nomes_por_tipo = defaultdict(set)
    cr_residual = 0
    negativos = Counter()
    comp_valores = {"iguais": 0, "menor": 0, "maior": 0,
                    "total": 0, "exemplos": []}

    combos_vistos = defaultdict(set)
    combos_dup = Counter()

    with caminho.open(encoding=ENCODING, newline="") as f:
        leitor = csv.DictReader(f, delimiter=DELIM)
        cabecalho = leitor.fieldnames or []

        if not mapeado:
            print("\n-- CABECALHO COMPLETO")
            for i, col in enumerate(cabecalho, start=1):
                marca = " <- numerica" if eh_coluna_numerica(col) else ""
                print(f"   {i:>3}. {col}{marca}")
            focos = cabecalho
            combos = [
                tuple(cabecalho[:n])
                for n in range(1, min(MAX_COMBINACAO_CHAVE, len(cabecalho)) + 1)
            ]
        else:
            focos = COLUNAS_FOCO[rotulo]
            combos = [tuple(CHAVES[rotulo])] if rotulo in CHAVES else []

        for linha in leitor:
            total += 1

            for col, val in linha.items():
                if col is None:
                    continue
                val = val or ""
                if "\r" in val:
                    cr_residual += 1
                if val.strip() == "":
                    vazios[col] += 1

            for col in focos:
                if col not in linha:
                    continue
                val = (linha[col] or "").strip()
                if len(distintos[col]) < LIMITE_DISTINTOS:
                    distintos[col].add(val)
                if val and len(amostras[col]) < 5 and val not in amostras[col]:
                    amostras[col].append(val)
                if eh_coluna_numerica(col):
                    formatos[col][formato_valor(val)] += 1
                    if val.startswith("-"):
                        negativos[col] += 1

            if rotulo == "ItemEmpenho":
                vt = (linha.get("Valor Total") or "").strip()
                va = (linha.get("Valor Atual") or "").strip()
                if vt and va:
                    try:
                        nt = float(vt.replace(".", "").replace(",", "."))
                        na = float(va.replace(".", "").replace(",", "."))
                    except ValueError:
                        pass
                    else:
                        comp_valores["total"] += 1
                        if na == nt:
                            comp_valores["iguais"] += 1
                        else:
                            k = "menor" if na < nt else "maior"
                            comp_valores[k] += 1
                            if len(comp_valores["exemplos"]) < 3:
                                comp_valores["exemplos"].append(f"{vt} -> {va}")

            col_fav = next(
                (c for c in cabecalho if c and "Favorecido" in c
                 and "Código" in c), None
            )
            if col_fav:
                cod = (linha.get(col_fav) or "").strip()
                t = tipo_favorecido(cod)
                tipos_fav[t] += 1
                col_nome = next(
                    (c for c in cabecalho
                     if c and c.strip() == "Favorecido"), None
                )
                nome = (linha.get(col_nome) or "").strip() if col_nome else ""
                if nome and len(nomes_por_tipo[t]) < 3:
                    nomes_por_tipo[t].add(f"{cod} = {nome[:45]}")

            for combo in combos:
                if not all(c in linha for c in combo):
                    continue
                k = tuple((linha[c] or "").strip() for c in combo)
                if k in combos_vistos[combo]:
                    combos_dup[combo] += 1
                else:
                    combos_vistos[combo].add(k)

    print(f"\nLinhas de dados: {total:,}".replace(",", "."))
    print(f"Colunas: {len(cabecalho)}")
    print(f"Campos com CR residual: {cr_residual}")

    if combos:
        print("\n-- TESTE DE UNICIDADE")
        for combo in combos:
            d = len(combos_vistos[combo])
            dup = combos_dup[combo]
            veredito = "UNICA" if dup == 0 else f"{dup} duplicadas"
            rotulo_combo = " + ".join(combo)
            if len(rotulo_combo) > 58:
                rotulo_combo = rotulo_combo[:55] + "..."
            print(f"   {rotulo_combo:<58} {d:>7} distintas  {veredito}")

    print("\n-- COLUNAS")
    print(f"   {'coluna':<44} {'vazios':>8} {'distintos':>10}")
    for col in focos:
        if col not in cabecalho:
            print(f"   {col:<44} {'AUSENTE':>8}")
            continue
        d = len(distintos[col])
        marca = "+" if d >= LIMITE_DISTINTOS else ""
        print(f"   {col:<44} {vazios[col]:>8} {d:>9}{marca}")

    print("\n-- AMOSTRAS")
    for col in focos:
        if amostras[col]:
            vals = " | ".join(amostras[col][:3])
            print(f"   {col:<44} {vals[:66]}")

    if formatos:
        print("\n-- FORMATO DOS CAMPOS NUMERICOS")
        for col, cont in formatos.items():
            fmt = ", ".join(f"{k}={v}" for k, v in cont.most_common(3))
            print(f"   {col:<44} {fmt}")
        if negativos:
            print("\n   negativos encontrados:")
            for col, n in negativos.items():
                print(f"     {col:<42} {n}")

    if rotulo == "ItemEmpenho" and comp_valores["total"]:
        c = comp_valores
        print("\n-- 'Valor Total' VS 'Valor Atual'")
        print(f"   iguais:        {c['iguais']:>8}")
        print(f"   atual < total: {c['menor']:>8}")
        print(f"   atual > total: {c['maior']:>8}")
        if c["exemplos"]:
            print("   exemplos (total -> atual):")
            for ex in c["exemplos"]:
                print(f"     {ex}")

    if tipos_fav:
        print("\n-- CLASSIFICACAO DO FAVORECIDO")
        for t, n in tipos_fav.most_common():
            pct = 100 * n / total if total else 0
            print(f"   {t:<28} {n:>8}  ({pct:5.1f}%)")
        print("\n   exemplos por tipo:")
        for t in tipos_fav:
            for ex in sorted(nomes_por_tipo[t]):
                print(f"     [{t}] {ex}")
    print()


def main() -> None:
    if not INTERIM.exists():
        sys.exit(f"Diretorio nao encontrado: {INTERIM}")

    alvos = [
        ("Empenho", "_Despesas_Empenho.csv"),
        ("ItemEmpenho", "_Despesas_ItemEmpenho.csv"),
        ("Pagamento", "_Despesas_Pagamento.csv"),
        ("Pagamento_EmpenhosImpactados",
         "_Despesas_Pagamento_EmpenhosImpactados.csv"),
        ("Liquidacao", "_Despesas_Liquidacao.csv"),
        ("Liquidacao_EmpenhosImpactados",
         "_Despesas_Liquidacao_EmpenhosImpactados.csv"),
    ]

    for rotulo, sufixo in alvos:
        encontrados = sorted(INTERIM.glob(f"*{sufixo}"))
        if not encontrados:
            print(f"[aviso] nenhum arquivo para {rotulo}")
            continue
        for caminho in encontrados:
            perfilar(caminho, rotulo)


if __name__ == "__main__":
    main()