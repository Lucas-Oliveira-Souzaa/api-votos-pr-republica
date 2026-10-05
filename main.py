import json
import os
import time

from tse_api import consultar_url


# ============================================================
# CONFIGURAÇÕES
# ============================================================

INTERVALO_ATUALIZACAO = 60

# Configuração oficial das Eleições 2026
URL_CONFIG = (
    "https://resultados.tse.jus.br/"
    "oficial/ele2026/comum/config/ele-c.json"
)

# Eleição Federal 2026
ELEICAO = "6257"

# Cargo 0001 = Presidente da República
CARGO = "0001"


# ============================================================
# TERMINAL
# ============================================================

def limpar_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def mostrar_cabecalho():
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║ 🇧🇷             APURAÇÃO PRESIDENCIAL 2026               ║")
    print("║                                                            ║")
    print("║                 PRESIDENTE DA REPÚBLICA                   ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print("║                                                            ║")
    print("║                 DADOS OFICIAIS DO TSE                     ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()


# ============================================================
# CONFIGURAÇÃO DO TSE
# ============================================================

def consultar_configuracao():
    return consultar_url(URL_CONFIG)


# ============================================================
# URL DOS RESULTADOS
# ============================================================

def montar_url_resultado():
    """
    Monta o endereço do arquivo de resultados
    da eleição presidencial.

    Estrutura:

    /oficial/ele2026/6257/dados/br/
    br-c0001-e006257-u.json
    """

    return (
        "https://resultados.tse.jus.br/"
        f"oficial/ele2026/{ELEICAO}/dados/br/"
        f"br-c{CARGO}-e{ELEICAO.zfill(6)}-u.json"
    )


# ============================================================
# FORMATAÇÃO
# ============================================================

def formatar_numero(numero):
    try:
        return f"{int(numero):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"


def formatar_percentual(valor):
    try:
        return f"{float(valor):.2f}%".replace(".", ",")
    except (ValueError, TypeError):
        return "0,00%"


# ============================================================
# EXTRAÇÃO DOS DADOS
# ============================================================

def extrair_valor(objeto, chaves):
    """
    Procura uma chave dentro de um dicionário.
    """

    if not isinstance(objeto, dict):
        return None

    for chave in chaves:

        if chave in objeto:
            return objeto[chave]

    return None


def procurar_candidatos(objeto):
    """
    Procura recursivamente listas que possam conter candidatos.
    """

    encontrados = []

    if isinstance(objeto, dict):

        for chave, valor in objeto.items():

            chave_lower = str(chave).lower()

            if chave_lower in {
                "cand",
                "candidatos",
                "candidato",
                "candit",
            }:

                if isinstance(valor, list):
                    encontrados.extend(valor)

            elif isinstance(valor, (dict, list)):
                encontrados.extend(
                    procurar_candidatos(valor)
                )

    elif isinstance(objeto, list):

        for item in objeto:
            encontrados.extend(
                procurar_candidatos(item)
            )

    return encontrados


def extrair_candidatos(dados):
    """
    Tenta identificar os candidatos no JSON do TSE.
    """

    candidatos = procurar_candidatos(dados)

    resultado = []

    for candidato in candidatos:

        if not isinstance(candidato, dict):
            continue

        nome = extrair_valor(
            candidato,
            [
                "nm",
                "nome",
                "nm_cand",
                "nome_candidato",
                "nm_candidato",
            ],
        )

        votos = extrair_valor(
            candidato,
            [
                "vap",
                "votos",
                "qt_votos",
                "qtd_votos",
                "votos_validos",
            ],
        )

        percentual = extrair_valor(
            candidato,
            [
                "pvap",
                "percentual",
                "percent",
                "percentual_votos",
            ],
        )

        numero = extrair_valor(
            candidato,
            [
                "n",
                "nr",
                "numero",
                "num",
            ],
        )

        if nome:

            resultado.append(
                {
                    "numero": numero,
                    "nome": nome,
                    "votos": votos or 0,
                    "percentual": percentual or 0,
                }
            )

    return resultado


# ============================================================
# INFORMAÇÕES GERAIS DA APURAÇÃO
# ============================================================

def extrair_informacoes_gerais(dados):
    """
    Extrai as informações gerais da apuração.

    O JSON atual do TSE possui a estrutura:

    "apuracao": {
        "apuradas": 0,
        "percentual": 0.0,
        "total": 19461
    }
    """

    resultado = {
        "apuradas": 0,
        "total": 0,
        "percentual": 0.0,
    }

    # --------------------------------------------------------
    # ESTRUTURA PRINCIPAL
    # --------------------------------------------------------

    if isinstance(dados, dict):

        apuracao = dados.get("apuracao")

        if isinstance(apuracao, dict):

            try:

                resultado["apuradas"] = int(
                    float(
                        apuracao.get(
                            "apuradas",
                            0
                        )
                    )
                )

            except (ValueError, TypeError):

                resultado["apuradas"] = 0

            try:

                resultado["total"] = int(
                    float(
                        apuracao.get(
                            "total",
                            0
                        )
                    )
                )

            except (ValueError, TypeError):

                resultado["total"] = 0

            try:

                resultado["percentual"] = float(
                    apuracao.get(
                        "percentual",
                        0
                    )
                )

            except (ValueError, TypeError):

                resultado["percentual"] = 0.0

            return resultado

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    def percorrer(objeto):

        if isinstance(objeto, dict):

            for chave, valor in objeto.items():

                chave_lower = str(chave).lower()

                # --------------------------------------------
                # APURADAS
                # --------------------------------------------

                if chave_lower in {
                    "s",
                    "secoes",
                    "secoes_apuradas",
                    "secoes_totalizadas",
                    "qtd_secoes",
                    "apuradas",
                }:

                    if isinstance(
                        valor,
                        (int, float, str)
                    ):

                        try:

                            resultado["apuradas"] = int(
                                float(valor)
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            pass

                # --------------------------------------------
                # TOTAL
                # --------------------------------------------

                if chave_lower in {
                    "st",
                    "total_secoes",
                    "secoes_total",
                    "qtd_total_secoes",
                    "total",
                }:

                    if isinstance(
                        valor,
                        (int, float, str)
                    ):

                        try:

                            resultado["total"] = int(
                                float(valor)
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            pass

                # --------------------------------------------
                # PERCENTUAL
                # --------------------------------------------

                if chave_lower in {
                    "p",
                    "percentual",
                    "percentual_apuracao",
                    "perc",
                }:

                    if isinstance(
                        valor,
                        (int, float, str)
                    ):

                        try:

                            resultado["percentual"] = float(
                                valor
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            pass

                # --------------------------------------------
                # RECURSÃO
                # --------------------------------------------

                if isinstance(
                    valor,
                    (dict, list)
                ):

                    percorrer(valor)

        elif isinstance(objeto, list):

            for item in objeto:

                percorrer(item)

    percorrer(dados)

    return resultado


# ============================================================
# EXIBIÇÃO DOS RESULTADOS
# ============================================================

def mostrar_resultado(dados):

    informacoes = extrair_informacoes_gerais(
        dados
    )

    candidatos = extrair_candidatos(
        dados
    )

    print(
        "╔════════════════════════════════════════════════════════════╗"
    )

    print(
        "║ 🇧🇷             APURAÇÃO PRESIDENCIAL 2026               ║"
    )

    print(
        "║                                                            ║"
    )

    print(
        "║                 PRESIDENTE DA REPÚBLICA                   ║"
    )

    print(
        "╠════════════════════════════════════════════════════════════╣"
    )

    print(
        "║                                                            ║"
    )

    # --------------------------------------------------------
    # URNAS APURADAS
    # --------------------------------------------------------

    print(
        f"║  URNAS APURADAS        "
        f"{formatar_numero(informacoes['apuradas'])}"
        f" / "
        f"{formatar_numero(informacoes['total'])}"
        f"                ║"
    )

    # --------------------------------------------------------
    # PERCENTUAL
    # --------------------------------------------------------

    print(
        f"║  APURAÇÃO              "
        f"{formatar_percentual(informacoes['percentual'])}"
        f"                              ║"
    )

    print(
        "║                                                            ║"
    )

    print(
        "║  CANDIDATOS À PRESIDÊNCIA"
    )

    print(
        "║  ────────────────────────────────────────────────────────"
    )

    # --------------------------------------------------------
    # CANDIDATOS
    # --------------------------------------------------------

    if candidatos:

        for candidato in candidatos:

            nome = str(
                candidato["nome"]
            )

            votos = formatar_numero(
                candidato["votos"]
            )

            percentual = formatar_percentual(
                candidato["percentual"]
            )

            print(
                f"║  {nome[:30]:30} "
                f"{votos:>12} votos  "
                f"{percentual:>8}"
            )

    else:

        print(
            "║  Aguardando dados oficiais do TSE..."
        )

    print(
        "║"
    )

    print(
        "╠════════════════════════════════════════════════════════════╣"
    )

    print(
        "║  🟢 TSE: conectado                                         ║"
    )

    print(
        "║  🔄 Atualização automática: ativa                         ║"
    )

    print(
        "║                                                            ║"
    )

    print(
        f"║  Próxima atualização em "
        f"{INTERVALO_ATUALIZACAO:02d} segundos"
        f"                            ║"
    )

    print(
        "╚════════════════════════════════════════════════════════════╝"
    )

    print()


# ============================================================
# MODO DE ESPERA
# ============================================================

def mostrar_aguardando():

    print(
        "╔════════════════════════════════════════════════════════════╗"
    )

    print(
        "║ 🇧🇷             APURAÇÃO PRESIDENCIAL 2026               ║"
    )

    print(
        "║                                                            ║"
    )

    print(
        "║                 PRESIDENTE DA REPÚBLICA                   ║"
    )

    print(
        "╠════════════════════════════════════════════════════════════╣"
    )

    print(
        "║                                                            ║"
    )

    print(
        "║  🟢 TSE: conectado                                         ║"
    )

    print(
        "║                                                            ║"
    )

    print(
        "║  🔄 Aguardando publicação dos resultados oficiais...      ║"
    )

    print(
        "║                                                            ║"
    )

    print(
        "║  O sistema continuará verificando automaticamente.        ║"
    )

    print(
        "║                                                            ║"
    )

    print(
        "╠════════════════════════════════════════════════════════════╣"
    )

    print(
        "║  Atualização automática: 60 segundos                      ║"
    )

    print(
        "╚════════════════════════════════════════════════════════════╝"
    )

    print()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def main():

    print(
        "Iniciando sistema de apuração presidencial..."
    )

    print()

    # --------------------------------------------------------
    # TESTA CONEXÃO
    # --------------------------------------------------------

    config = consultar_configuracao()

    if config:

        print(
            "🟢 Conexão com o TSE estabelecida."
        )

        print()

        time.sleep(2)

    else:

        print(
            "⚠️ Não foi possível consultar "
            "a configuração do TSE."
        )

        print(
            "O sistema continuará tentando automaticamente."
        )

        time.sleep(3)

    # --------------------------------------------------------
    # URL DOS RESULTADOS
    # --------------------------------------------------------

    url_resultado = montar_url_resultado()

    # --------------------------------------------------------
    # LOOP PERMANENTE
    # --------------------------------------------------------

    while True:

        limpar_terminal()

        try:

            dados = consultar_url(
                url_resultado
            )

            if dados:

                mostrar_resultado(
                    dados
                )

            else:

                mostrar_aguardando()

        except KeyboardInterrupt:

            print()

            print(
                "🛑 Sistema encerrado pelo usuário."
            )

            break

        except Exception as erro:

            print(
                "╔════════════════════════════════════════════════════════════╗"
            )

            print(
                "║             APURAÇÃO PRESIDENCIAL 2026                  ║"
            )

            print(
                "╠════════════════════════════════════════════════════════════╣"
            )

            print(
                "║                                                            ║"
            )

            print(
                "║   Não foi possível atualizar os dados.                    ║"
            )

            print(
                "║                                                            ║"
            )

            print(
                f"║  Erro: {str(erro)[:48]:48} ║"
            )

            print(
                "║                                                            ║"
            )

            print(
                "║  🔄 Nova tentativa automática em 60 segundos.             ║"
            )

            print(
                "╚════════════════════════════════════════════════════════════╝"
            )

        time.sleep(
            INTERVALO_ATUALIZACAO
        )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()