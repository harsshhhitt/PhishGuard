"""
phishing_detector.py
--------------------
Load a phishing-URL CSV from Kaggle and extract a fixed feature set
ready for ML training.

Usage:
    py execution/phishing_detector.py --input data/phishing_urls.csv --output .tmp/features.csv
    py execution/phishing_detector.py --input data/phishing_urls.csv  # prints preview only

Expected input CSV columns (auto-detected):
    url / URL / address        →  the URL string
    label / status / class     →  phishing / legitimate (optional; kept if present)

Outputs a CSV with columns:
    url, url_length, num_dots, num_subdomains,
    has_keyword, has_https, num_special_chars,
    label  (if source had one)

Exit codes: 0 success | 1 runtime error | 2 bad arguments
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

# ── Bootstrap path so we can import utils from the project root ────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

from utils import get_logger, load_env

load_env()
log = get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

PHISHING_KEYWORDS = {"login", "secure", "verify", "account", "update", "bank", "paypal"}
SPECIAL_CHARS     = set("@-_")

# Candidate column name mappings (lowercase key → original column)
URL_COL_CANDIDATES   = {"url", "address", "urls"}
LABEL_COL_CANDIDATES = {"label", "status", "class", "type", "result"}


# ── URL column detection ───────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, candidates: set[str]) -> str | None:
    """Return the first DataFrame column whose lowercase name is in candidates."""
    for col in df.columns:
        if col.strip().lower() in candidates:
            return col
    return None


# ── Per-URL feature extraction ────────────────────────────────────────────────

def extract_features(url: str) -> dict:
    """
    Return a feature dict for a single URL string.
    Returns a row of NaNs on malformed input so the pipeline never crashes.
    """
    empty = {
        "url_length": None,
        "num_dots": None,
        "num_subdomains": None,
        "has_keyword": None,
        "has_https": None,
        "num_special_chars": None,
    }

    if not isinstance(url, str) or not url.strip():
        return empty

    url = url.strip()

    # Add scheme if missing so urlparse works correctly
    if not url.startswith(("http://", "https://")):
        url_parsed = urlparse("http://" + url)
    else:
        url_parsed = urlparse(url)

    try:
        import tldextract
        extracted = tldextract.extract(url)
        # subdomains is a dot-separated string; split and filter empty parts
        subdomain_parts = [s for s in extracted.subdomain.split(".") if s]
        num_subdomains  = len(subdomain_parts)
    except Exception as exc:
        log.warning("tldextract failed for %r: %s — falling back to netloc split", url, exc)
        netloc        = url_parsed.netloc.lstrip("www.")
        num_subdomains = max(netloc.count(".") - 1, 0)

    url_lower = url.lower()

    return {
        "url_length":      len(url),
        "num_dots":        url.count("."),
        "num_subdomains":  num_subdomains,
        "has_keyword":     int(any(kw in url_lower for kw in PHISHING_KEYWORDS)),
        "has_https":       int(url_parsed.scheme == "https"),
        "num_special_chars": sum(url.count(ch) for ch in SPECIAL_CHARS),
        # domain_age: skipped — requires paid WHOIS API
    }


# ── Main pipeline ──────────────────────────────────────────────────────────────

def load_dataset(csv_path: Path) -> tuple[pd.DataFrame, str | None]:
    """Load CSV and return (df_with_url_col_normalised, label_col_or_None)."""
    log.info("Loading dataset from %s", csv_path)
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as exc:
        log.error("Failed to read CSV: %s", exc)
        sys.exit(1)

    log.info("Loaded %d rows, columns: %s", len(df), list(df.columns))

    url_col = _find_col(df, URL_COL_CANDIDATES)
    if url_col is None:
        log.error(
            "Could not find a URL column. Tried: %s. Found: %s",
            URL_COL_CANDIDATES, list(df.columns)
        )
        sys.exit(1)

    label_col = _find_col(df, LABEL_COL_CANDIDATES)
    if label_col:
        log.info("Label column detected: '%s'", label_col)
    else:
        log.info("No label column found — output will have no 'label' column")

    df = df.rename(columns={url_col: "url"})
    return df, label_col


def build_feature_df(df: pd.DataFrame, label_col: str | None) -> pd.DataFrame:
    """Extract features for every row; return a clean DataFrame."""
    log.info("Extracting features for %d URLs…", len(df))

    records = []
    errors  = 0

    for idx, row in df.iterrows():
        url = row.get("url", "")
        try:
            feat = extract_features(url)
        except Exception as exc:
            log.warning("Row %d: unexpected error for URL %r: %s", idx, url, exc)
            feat   = {k: None for k in
                      ("url_length","num_dots","num_subdomains",
                       "has_keyword","has_https","num_special_chars")}
            errors += 1

        feat["url"] = url
        if label_col:
            feat["label"] = row.get(label_col)
        records.append(feat)

    if errors:
        log.warning("%d rows had extraction errors (set to None)", errors)

    # Column order
    base_cols = ["url","url_length","num_dots","num_subdomains",
                 "has_keyword","has_https","num_special_chars"]
    if label_col:
        base_cols.append("label")

    result = pd.DataFrame(records)[base_cols]

    # Drop rows where ALL feature columns are None
    feature_cols = [c for c in base_cols if c not in ("url","label")]
    before = len(result)
    result = result.dropna(subset=feature_cols, how="all")
    dropped = before - len(result)
    if dropped:
        log.warning("Dropped %d rows with all-None features", dropped)

    log.info("Final DataFrame: %d rows × %d cols", *result.shape)
    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract ML features from a phishing URL dataset CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--input",  "-i", required=True,  help="Path to input CSV (Kaggle phishing dataset)")
    p.add_argument("--output", "-o", default=None,    help="Path to save feature CSV (default: .tmp/features.csv)")
    p.add_argument("--preview",      action="store_true",
                   help="Print the first 5 rows of the feature DataFrame and exit without saving")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        log.error("Input file not found: %s", input_path)
        sys.exit(2)

    df_raw, label_col = load_dataset(input_path)
    features = build_feature_df(df_raw, label_col)

    if args.preview:
        print(features.head().to_string(index=False))
        sys.exit(0)

    output_path = Path(args.output) if args.output else PROJECT_ROOT / ".tmp" / "features.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_path, index=False)
    log.info("Saved to %s", output_path)
    print(output_path)


if __name__ == "__main__":
    main()
