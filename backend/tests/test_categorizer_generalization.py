import os
import glob
import json
import hashlib
import pandas as pd
import pytest

from app.services.fallback_classifier import FallbackClassifier
from app.services.categorizer import TransactionCategorizer

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEMO_DIR = os.path.join(ROOT_DIR, "demo_data")
MODELS_DATA_DIR = os.path.join(ROOT_DIR, "backend", "app", "models_data")

def test_training_corpus_strictly_disjoint_from_demo_and_test_data():
    """
    PHASE 8 REQUIREMENT:
    The synthetic TRAINING corpus must use merchants and phrasing templates
    that are written to be disjoint from every demo_data file.
    Add a test that fails if any training description appears verbatim
    in demo_data/ or the fresh test file.
    """
    corpus_json_path = os.path.join(MODELS_DATA_DIR, "synthetic_training_corpus.json")
    assert os.path.exists(corpus_json_path), "synthetic_training_corpus.json must exist"

    with open(corpus_json_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    training_descriptions = {item["description"].strip().upper() for item in corpus}
    assert len(training_descriptions) >= 500, "Corpus must have substantial training examples"

    # Collect all descriptions across all demo_data files
    demo_descriptions = set()
    for csv_file in glob.glob(os.path.join(DEMO_DIR, "*.csv")):
        try:
            df = pd.read_csv(csv_file)
            for col in ["Description", "Narration", "Transaction Description"]:
                if col in df.columns:
                    for d in df[col].dropna():
                        s = str(d).strip().upper()
                        if s:
                            demo_descriptions.add(s)
        except Exception:
            pass

    for json_file in glob.glob(os.path.join(DEMO_DIR, "*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                if "true_categories" in data:
                    for d in data["true_categories"]:
                        demo_descriptions.add(str(d).strip().upper())
                if "planted_events" in data:
                    for ev in data["planted_events"]:
                        if "description" in ev:
                            demo_descriptions.add(str(ev["description"]).strip().upper())
        except Exception:
            pass

    # Check for any verbatim overlaps
    overlapping = training_descriptions.intersection(demo_descriptions)
    assert len(overlapping) == 0, (
        f"Contamination detected! {len(overlapping)} training descriptions overlap verbatim "
        f"with demo/test datasets: {list(overlapping)[:5]}"
    )

def test_fallback_classifier_metadata_and_integrity():
    """Verify fallback model metadata, versioning, and corpus hash consistency."""
    meta = FallbackClassifier.get_metadata()
    assert meta["active"] is True
    assert meta["version"] == "1.0.0"
    assert len(meta["corpus_hash"]) == 64, "Corpus hash must be valid SHA-256"
    assert meta["n_samples"] >= 500

    # Verify that corpus hash matches file on disk
    corpus_json_path = os.path.join(MODELS_DATA_DIR, "synthetic_training_corpus.json")
    with open(corpus_json_path, "rb") as f:
        computed_hash = hashlib.sha256(f.read()).hexdigest()
    assert meta["corpus_hash"] == computed_hash

def test_fallback_classifier_prediction():
    """Test that the offline fallback model accurately predicts categories for unseen patterns."""
    cat, prob = FallbackClassifier.predict("UPI/PUNJAB GRILL CHENNAI/MEAL ORDER")
    assert cat == "Food & Dining"
    assert prob >= 0.30

    cat_med, prob_med = FallbackClassifier.predict("UPI/COLUMBIA ASIA CLINIC/BLOOD TEST")
    assert cat_med == "Healthcare"
    assert prob_med >= 0.30

    cat_edu, prob_edu = FallbackClassifier.predict("UPI/ALLEN CAREER INSTITUTE/BATCH FEE")
    assert cat_edu == "Education"
    assert prob_edu >= 0.30

def test_categorizer_integrates_fallback_for_unrecognized_narratives():
    """Verify categorizer runs rules first and invokes ML fallback when rule is absent."""
    # Known rule merchant (rules take priority)
    cat1, conf1 = TransactionCategorizer.categorize_with_confidence("SWIGGY BANGALORE", debit=350.0)
    assert cat1 == "Food & Dining"
    assert conf1 >= 0.90

    # Unseen merchant (falls through rules to local ML fallback)
    cat2, conf2 = TransactionCategorizer.categorize_with_confidence("MAX HEALTHCARE SAKET/OPD CONSULTATION", debit=1500.0)
    assert cat2 == "Healthcare"
    assert conf2 >= 0.50

    # Completely uninterpretable noise still returns review fallback
    cat3, conf3 = TransactionCategorizer.categorize_with_confidence("ZZXQWY 991823774882 NOISE", debit=100.0)
    assert cat3 == "Uncategorized – review"
    assert conf3 <= 0.30
