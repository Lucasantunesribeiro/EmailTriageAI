import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def load_dataset(path: Path) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text = (row.get("text") or "").strip()
            label = (row.get("label") or "").strip()
            if text and label:
                texts.append(text)
                labels.append(label)
    return texts, labels


def train() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    dataset_path = base_dir / "data" / "emails_seed.csv"
    model_path = base_dir / "models" / "baseline.joblib"

    texts, labels = load_dataset(dataset_path)
    if len(texts) < 10:
        raise RuntimeError("Dataset pequeno demais")

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.3, random_state=42, stratify=labels
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=4000, ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )

    pipeline.fit(x_train, y_train)
    preds = pipeline.predict(x_test)
    print("Accuracy:", accuracy_score(y_test, preds))
    print(classification_report(y_test, preds))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    print("Model saved to", model_path)


if __name__ == "__main__":
    train()
