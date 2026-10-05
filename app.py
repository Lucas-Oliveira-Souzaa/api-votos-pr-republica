from flask import Flask, jsonify, render_template
from tse_api import consultar_url


app = Flask(__name__)


# ============================================================
# CONFIGURAÇÃO DA ELEIÇÃO
# ============================================================

ELEICAO = "6257"
CARGO = "0001"

URL_RESULTADO = (
    "https://resultados.tse.jus.br/"
    f"oficial/ele2026/{ELEICAO}/dados/br/"
    f"br-c{CARGO}-e{ELEICAO.zfill(6)}-u.json"
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def buscar_chave(objeto, chaves):

    if not isinstance(objeto, dict):
        return None

    for chave in chaves:

        if chave in objeto:
            return objeto[chave]

    return None


# ============================================================
# LOCALIZA OS CANDIDATOS NO JSON DO TSE
# ============================================================

def procurar_candidatos(objeto):

    candidatos = []

    if isinstance(objeto, dict):

        for chave, valor in objeto.items():

            chave_normalizada = str(chave).lower()

            if chave_normalizada in [
                "cand",
                "candidatos",
                "candidato"
            ]:

                if isinstance(valor, list):

                    candidatos.extend(valor)

            elif isinstance(valor, (dict, list)):

                candidatos.extend(
                    procurar_candidatos(valor)
                )

    elif isinstance(objeto, list):

        for item in objeto:

            candidatos.extend(
                procurar_candidatos(item)
            )

    return candidatos


# ============================================================
# EXTRAI CANDIDATOS E CALCULA PERCENTUAIS
# ============================================================

def extrair_candidatos(dados):

    encontrados = procurar_candidatos(dados)

    candidatos = []

    nomes_processados = set()

    for candidato in encontrados:

        if not isinstance(candidato, dict):
            continue

        # ----------------------------------------------------
        # NOME
        # ----------------------------------------------------

        nome = buscar_chave(
            candidato,
            [
                "nm",
                "nome",
                "nm_cand",
                "nm_candidato"
            ]
        )

        if not nome:
            continue

        nome = str(nome).strip()

        # Evita duplicação
        if nome in nomes_processados:
            continue

        nomes_processados.add(nome)

        # ----------------------------------------------------
        # NÚMERO
        # ----------------------------------------------------

        numero = buscar_chave(
            candidato,
            [
                "n",
                "nr",
                "numero",
                "num"
            ]
        )

        # ----------------------------------------------------
        # VOTOS
        # ----------------------------------------------------

        votos = buscar_chave(
            candidato,
            [
                "vap",
                "votos",
                "qt_votos",
                "qtd_votos",
                "votos_validos"
            ]
        )

        try:

            votos = int(float(votos or 0))

        except (ValueError, TypeError):

            votos = 0

        candidatos.append(
            {
                "numero": numero,
                "nome": nome,
                "votos": votos,
                "percentual": 0
            }
        )

    # --------------------------------------------------------
    # ORDENA DO MAIOR PARA O MENOR NÚMERO DE VOTOS
    # --------------------------------------------------------

    candidatos.sort(
        key=lambda candidato: candidato["votos"],
        reverse=True
    )

    # --------------------------------------------------------
    # TOTAL DE VOTOS DOS CANDIDATOS
    # --------------------------------------------------------

    total_votos = sum(
        candidato["votos"]
        for candidato in candidatos
    )

    # --------------------------------------------------------
    # CALCULA PERCENTUAL
    # --------------------------------------------------------

    if total_votos > 0:

        for candidato in candidatos:

            candidato["percentual"] = round(
                (
                    candidato["votos"]
                    / total_votos
                ) * 100,
                2
            )

    return candidatos


# ============================================================
# EXTRAI INFORMAÇÕES DA APURAÇÃO
# ============================================================

# ============================================================
# EXTRAI INFORMAÇÕES DA APURAÇÃO
# ============================================================

def extrair_apuracao(dados):

    resultado = {
        "apuradas": 0,
        "total": 0,
        "percentual": 0
    }

    # --------------------------------------------------------
    # O TSE disponibiliza o andamento no bloco "s"
    #
    # s.ts  = total de seções
    # s.st  = seções totalizadas
    # s.pst = percentual totalizado
    # --------------------------------------------------------

    if isinstance(dados, dict):

        bloco_s = dados.get("s")

        if isinstance(bloco_s, dict):

            # TOTAL DE SEÇÕES
            try:
                resultado["total"] = int(
                    float(bloco_s.get("ts", 0) or 0)
                )
            except (ValueError, TypeError):
                resultado["total"] = 0

            # SEÇÕES APURADAS / TOTALIZADAS
            try:
                resultado["apuradas"] = int(
                    float(bloco_s.get("st", 0) or 0)
                )
            except (ValueError, TypeError):
                resultado["apuradas"] = 0

            # PERCENTUAL OFICIAL DO TSE
            try:
                percentual = bloco_s.get("pst", 0)

                if isinstance(percentual, str):
                    percentual = percentual.replace(",", ".")

                resultado["percentual"] = float(
                    percentual or 0
                )

            except (ValueError, TypeError):
                resultado["percentual"] = 0

    # --------------------------------------------------------
    # SE O TSE NÃO ENTREGAR O PERCENTUAL,
    # CALCULA PELAS SEÇÕES TOTALIZADAS
    # --------------------------------------------------------

    if (
        resultado["percentual"] == 0
        and resultado["total"] > 0
        and resultado["apuradas"] >= 0
    ):

        resultado["percentual"] = round(
            (
                resultado["apuradas"]
                / resultado["total"]
            ) * 100,
            2
        )

    return resultado

# ============================================================
# API DO SISTEMA
# ============================================================

@app.route("/api/resultados")
def resultados():

    dados = consultar_url(
        URL_RESULTADO
    )

    # --------------------------------------------------------
    # TSE AINDA NÃO DISPONIBILIZOU OS DADOS
    # --------------------------------------------------------

    if not dados:

        return jsonify(
            {
                "status": "aguardando",

                "mensagem":
                    "Aguardando dados oficiais do TSE.",

                "candidatos": [],

                "apuracao":
                    {
                        "apuradas": 0,
                        "total": 0,
                        "percentual": 0
                    }
            }
        )

    # --------------------------------------------------------
    # PROCESSAMENTO
    # --------------------------------------------------------

    candidatos = extrair_candidatos(
        dados
    )

    apuracao = extrair_apuracao(
        dados
    )

    # --------------------------------------------------------
    # RETORNO
    # --------------------------------------------------------

    return jsonify(
        {
            "status": "online",

            "eleicao": ELEICAO,

            "cargo":
                "Presidente da República",

            "candidatos":
                candidatos,

            "apuracao":
                apuracao
        }
    )


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🇧🇷 APURAÇÃO PRESIDENCIAL 2026")
    print("=" * 60)
    print()
    print("Servidor iniciado com sucesso!")
    print()
    print("Acesse no navegador:")
    print("http://127.0.0.1:5000")
    print()
    print("API:")
    print("http://127.0.0.1:5000/api/resultados")
    print()
    print("Pressione CTRL+C para encerrar.")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )