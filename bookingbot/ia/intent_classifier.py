import re
import pickle
from pathlib import Path
import spacy

# === Carrega SpaCy ===
nlp = spacy.load("pt_core_news_sm")

# Caminhos dos arquivos do modelo
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "vectorizer.pkl"


# ======================================================
# 1️⃣ Carregar modelo treinado (TF-IDF + LogisticRegression)
# ======================================================
def load_trained_model():
    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        return None, None  # modelo ainda não treinado
    model = pickle.load(open(MODEL_PATH, "rb"))
    vectorizer = pickle.load(open(VECTORIZER_PATH, "rb"))
    return model, vectorizer


# ======================================================
# 2️⃣ Extrair dados estruturados (datas e horários)
# ======================================================
def extract_datetime(text):
    doc = nlp(text)

    datas = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    horas = re.findall(r"\d{1,2}:\d{2}", text)

    return datas, horas


# ======================================================
# 3️⃣ Classificação de intenção (treinado ou fallback)
# ======================================================

# fallback simples (caso o modelo ML ainda não exista)
KEYWORD_INTENTS = {
    "reservar": ["reservar", "agendar", "marcar", "fazer reserva", "agende", "quero um horário", "marque", "fazer uma reserva"],
    "cancelar": ["cancelar", "desmarcar", "excluir reserva", "remover reserva", "cancele", "cancela", "desmarque", "remova a reserva"],
    "consultar_disponibilidade": ["horário", "disponível", "disponibilidade", "livre", "quais horários estão disponíveis", "Tem horário", "ver horários", "consultar horários", "horarios vagos", "tem vaga", "está livre", "horários livres", "mostre a agenda", "tem algum horário"],
}


def keyword_fallback(text):
    text_lower = text.lower()
    for intent, keywords in KEYWORD_INTENTS.items():
        if any(k in text_lower for k in keywords):
            return intent
    return "desconhecido"


def classify_intent(text):
    model, vectorizer = load_trained_model()

    # Se não existe modelo treinado → usa fallback
    if model is None:
        return keyword_fallback(text)

    # Usa o modelo treinado
    X = vectorizer.transform([text])
    prediction = model.predict(X)[0]
    return prediction


# ======================================================
# 4️⃣ Função final usada pelo sistema
# ======================================================
def interpretar_mensagem(text):
    intent = classify_intent(text)
    datas, horas = extract_datetime(text)

    if intent == "desconhecido" and (datas or horas):
        intent = "criar_reserva"

    return {
        "intent": intent,
        "datas": datas,
        "horas": horas,
    }


# Teste rápido
if __name__ == "__main__":
    print(interpretar_mensagem("Quero reservar a sala 2 amanhã às 14:00"))
