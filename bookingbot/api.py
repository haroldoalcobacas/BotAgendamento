import re
import spacy

nlp = spacy.load("pt_core_news_sm")


def interpretar_mensagem(msg):
    msg_lower = msg.lower()

    if "reservar" in msg_lower or "marcar" in msg_lower or "agendar" in msg_lower:
        intent = "reservar"
    elif "cancelar" in msg_lower:
        intent = "cancelar"
    else:
        intent = "desconhecido"

    doc = nlp(msg)
    datas = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    horas = re.findall(r'\d{1,2}:\d{2}', msg)

    return {
        "intent": intent,
        "datas": datas,
        "horas": horas,
    }
