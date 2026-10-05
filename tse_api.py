import requests


BASE_URL = "https://resultados.tse.jus.br"


def consultar_url(url):
    try:
        resposta = requests.get(
            url,
            timeout=15
        )

        if resposta.status_code == 200:
            return resposta.json()

        if resposta.status_code == 304:
            return None

        print(f"HTTP {resposta.status_code}")

    except requests.RequestException as erro:
        print(f"Erro de conexão: {erro}")

    except ValueError:
        print("O TSE não retornou um JSON válido.")

    return None