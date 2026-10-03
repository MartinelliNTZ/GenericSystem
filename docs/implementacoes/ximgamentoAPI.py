import requests
import time

def gerar_insulto():
    # Timestamp evita cache
    url = "https://evilinsult.com/generate_insult.php"
    params = {
        "lang": "en",
        "type": "json",
        "_": int(time.time() * 1000)
    }

    response = requests.get(
        url,
        params=params,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        },
        timeout=10
    )
    response.raise_for_status()

    data = response.json()
    return data["insult"]

def traduzir(texto):
    translate_url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "pt",
        "dt": "t",
        "q": texto
    }

    response = requests.get(translate_url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()[0][0][0]

# Gera 5 insultos para testar
for i in range(15):
    insulto_en = gerar_insulto()
    insulto_pt = traduzir(insulto_en)

    print(f"\n--- Insulto {i + 1} ---")
    print("EN:", insulto_en)
    print("PT:", insulto_pt)

    time.sleep(0.5)