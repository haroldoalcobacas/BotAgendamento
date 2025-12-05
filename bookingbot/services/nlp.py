import re
import datetime
import spacy

nlp = None
try:
    nlp = spacy.load("pt_core_news_sm")
except Exception:
    # se não tiver modelo, o sistema ainda funciona com regex básico
    nlp = None


def _extrair_data_hora_texto(text):
    """
    Retorna (date_str_iso, time_str) ou (None, None)
    Aceita formatos: DD/MM HH:MM  ou DD/MM/YYYY HH:MM
    """
    # procurar padrão dd/mm ou dd/mm/yyyy
    match = re.search(r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(\d{1,2}[:h]\d{2})', text)
    if match:
        date_part = match.group(1)
        time_part = match.group(2).replace('h',':')
        # normalizar data para ISO
        parts = date_part.split('/')
        if len(parts) == 2:
            day, month = parts
            year = datetime.date.today().year
        else:
            day, month, year = parts
            if len(year) == 2:
                year = "20" + year
        try:
            d = datetime.date(int(year), int(month), int(day))
            t = datetime.time(int(time_part.split(':')[0]), int(time_part.split(':')[1]))
            return d.isoformat(), t.strftime("%H:%M")
        except Exception:
            return None, None
    # fallback com spaCy: tentar extrair entidades
    if nlp:
        doc = nlp(text)
        date_ent = None
        time_ent = None
        for ent in doc.ents:
            if ent.label_ == "DATE" and not date_ent:
                date_ent = ent.text
            if ent.label_ == "TIME" and not time_ent:
                time_ent = ent.text
        # Observação: spaCy em PT nem sempre classifica TIME
        # Não implementamos conversão complexa aqui para manter simples
    return None, None


def interpretar_mensagem(text):
    """
    Retorna dicionário: {'intent': 'reservar'|'cancelar'|'desconhecido', 'date': 'YYYY-MM-DD' or None, 'time': 'HH:MM' or None}
    """
    text_low = text.lower()

    if any(w in text_low for w in ["reservar", "marcar", "agendar"]):
        intent = "reservar"
    elif any(w in text_low for w in ["cancelar", "desmarcar"]):
        intent = "cancelar"
    else:
        intent = "desconhecido"

    date_iso, time_str = _extrair_data_hora_texto(text_low)

    return {
        "intent": intent,
        "date": date_iso,
        "time": time_str
    }
