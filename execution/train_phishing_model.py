"""
train_phishing_model.py
-----------------------
Train a Random Forest classifier on the extracted phishing URL features.

Usage:
    py execution/train_phishing_model.py --input .tmp/features.csv

Requires:
    pip install scikit-learn pandas joblib

Expects:
    A CSV with a 'label' column and various numeric feature columns.

Outputs (in .tmp/ by default):
    - model.pkl         : The trained RandomForestClassifier pipeline
    - features.json     : The exact list of columns needed for prediction
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# ── Bootstrap path ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

from utils import get_logger, load_env

load_env()
log = get_logger(__name__)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.model_selection import train_test_split
    import joblib
except ImportError:
    log.error("Missing scikit-learn or joblib. Run: pip install scikit-learn joblib")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train a RF model on phishing features.")
    p.add_argument("--input", "-i", default=str(PROJECT_ROOT / ".tmp" / "features.csv"),
                   help="Path to the extracted features CSV")
    p.add_argument("--outdir", default=str(PROJECT_ROOT / ".tmp"),
                   help="Directory to save the model.pkl and features.json")
    return p.parse_args()


def load_data(csv_path: Path):
    if not csv_path.exists():
        log.error("Dataset not found at %s. Please run extract_url_features.py first.", csv_path)
        sys.exit(1)
        
    log.info("Loading features from %s", csv_path)
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        log.error("Failed to read CSV: %s", exc)
        sys.exit(1)
        
    if "label" not in df.columns:
        log.error("Feature CSV must contain a 'label' column to train.")
        sys.exit(1)
        
    return df


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(input_path)

    # Convert labels to binary (assume 1 = phishing, 0 = safe, handle string labels if needed)
    if df["label"].dtype == "object":
        # simple heuristic if it's strings like "phishing" / "bad" / "malicious"
        bad_words = {"phishing", "bad", "malicious", "spam"}
        df["target"] = df["label"].astype(str).str.lower().apply(lambda x: 1 if any(b in x for b in bad_words) else 0)
    else:
        # assume numerical labels are mostly correct
        df["target"] = (df["label"] > 0).astype(int)

    # Drop non-numeric columns for feature set
    drop_cols = ["url", "label", "target"]
    feature_cols = [c for c in df.columns if c not in drop_cols and pd.api.types.is_numeric_dtype(df[c])]

    if not feature_cols:
        log.error("No numeric feature columns found.")
        sys.exit(1)

    log.info("Using %d features: %s", len(feature_cols), feature_cols)

    X = df[feature_cols]
    y = df["target"]

    # Fill NaNs with 0 (since malformed URLs might have returned NaNs)
    X = X.fillna(0)

    log.info("Splitting data (80/20 train/test)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    log.info("Training Random Forest Classifier on %d samples...", len(X_train))
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    log.info("Evaluating on %d test samples...", len(X_test))
    y_pred = clf.predict(X_test)
    
    # Calculate metrics
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)

    print("\n--- Model Performance ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("-------------------------\n")

    # Save outputs
    model_path = out_dir / "model.pkl"
    feat_path  = out_dir / "features.json"

    joblib.dump(clf, model_path)
    
    with open(feat_path, "w") as f:
        json.dump(feature_cols, f, indent=2)

    log.info("Saved model to %s", model_path)
    log.info("Saved feature names to %s", feat_path)


if __name__ == "__main__":
    main()
