# bookingbot/ia/train_model.py
import json
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BASE_DIR = Path(__file__).resolve().parent

def load_dataset():
    dataset_file = BASE_DIR / "training_data.json"
    if not dataset_file.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {dataset_file}")
    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    texts = [item["text"] for item in data]
    labels = [item["label"] for item in data]
    return texts, labels

def train():
    print("📘 Carregando dataset...")
    texts, labels = load_dataset()

    print(f"⚙️  Exemplos no dataset: {len(texts)}")
    print("🔧 Vetorizando texto...")
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    print("🤖 Treinando modelo (LogisticRegression)...")
    model = LogisticRegression(max_iter=400)
    model.fit(X, labels)

    print("💾 Salvando arquivos (model.pkl / vectorizer.pkl)...")
    pickle.dump(model, open(BASE_DIR / "model.pkl", "wb"))
    pickle.dump(vectorizer, open(BASE_DIR / "vectorizer.pkl", "wb"))

    print("✔ Treinamento concluído com sucesso! Modelos salvos em:", BASE_DIR)


if __name__ == "__main__":
    train()
