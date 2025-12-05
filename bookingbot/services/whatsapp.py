import requests
from django.conf import settings


def enviar_whatsapp(numero, mensagem):
    """
    Função simples para enviar mensagem via endpoint HTTP do gateway de WhatsApp.
    Ajuste o payload conforme o gateway (WPPConnect, WaSender, etc.)
    """
    url = settings.WHATSAPP_API_URL
    token = settings.WHATSAPP_API_TOKEN

    if not url:
        # para desenvolvimento, apenas print
        print(f"[whatsapp] {numero}: {mensagem}")
        return

    payload = {
        "token": token,
        "to": numero,
        "body": mensagem
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("Erro ao enviar WhatsApp:", e)
        return None
