import logging
from pathlib import Path
from typing import Optional, Tuple

import joblib
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class BaselineService:
    def __init__(self) -> None:
        self.model = self._load_model()

    def _load_model(self) -> Optional[Pipeline]:
        model_path = Path(__file__).resolve().parents[2] / "models" / "baseline.joblib"
        if not model_path.exists():
            logger.info("Baseline model not found")
            return None
        return joblib.load(model_path)

    def predict(self, text_clean: str) -> Optional[Tuple[str, float]]:
        if not self.model or not text_clean.strip():
            return None
        probabilities = self.model.predict_proba([text_clean])[0]
        best_index = int(probabilities.argmax())
        label = str(self.model.classes_[best_index])
        confidence = float(probabilities[best_index])
        return label, confidence
