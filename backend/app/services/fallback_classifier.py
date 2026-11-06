import os
from typing import Tuple, Optional, Dict, Any
import numpy as np
import joblib

class FallbackClassifier:
    """
    Offline local character n-gram + Logistic Regression classifier.
    Invoked as a fallback only when high-precision rules return low confidence
    or 'Uncategorized – review'. Operates 100% offline with zero network calls.
    """
    _model_bundle: Optional[Dict[str, Any]] = None
    _model_path: Optional[str] = None
    _initialized: bool = False

    @classmethod
    def load_model(cls) -> bool:
        if cls._initialized and cls._model_bundle is not None:
            return True

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "models_data", "fallback_classifier_v1.joblib")
        if not os.path.exists(model_path):
            cls._initialized = True
            cls._model_bundle = None
            return False

        try:
            cls._model_bundle = joblib.load(model_path)
            cls._model_path = model_path
            cls._initialized = True
            return True
        except Exception:
            cls._initialized = True
            cls._model_bundle = None
            return False

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        cls.load_model()
        if not cls._model_bundle:
            return {"active": False, "version": "none", "corpus_hash": "none"}
        return {
            "active": True,
            "version": cls._model_bundle.get("version", "1.0.0"),
            "corpus_hash": cls._model_bundle.get("corpus_hash", ""),
            "classes": cls._model_bundle.get("classes", []),
            "n_samples": cls._model_bundle.get("n_samples", 0),
            "created_at": cls._model_bundle.get("created_at", "")
        }

    @classmethod
    def predict(cls, description: str, threshold: float = 0.25) -> Tuple[Optional[str], float]:
        """
        Predicts category and confidence probability for a transaction description.
        Returns:
            (predicted_category, probability) if max probability >= threshold, else (None, prob).
        """
        if not cls.load_model() or cls._model_bundle is None:
            return (None, 0.0)

        pipeline = cls._model_bundle.get("pipeline")
        if not pipeline:
            return (None, 0.0)

        try:
            probs = pipeline.predict_proba([description])[0]
            top_idx = int(np.argmax(probs))
            top_prob = float(probs[top_idx])
            top_class = str(pipeline.classes_[top_idx])

            if top_prob >= threshold:
                return (top_class, top_prob)
            return (None, top_prob)
        except Exception:
            return (None, 0.0)
