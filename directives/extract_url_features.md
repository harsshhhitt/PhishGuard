---
description: Extract ML-ready features from a phishing URL CSV dataset
inputs:
  - name: input CSV
    description: Path to the Kaggle phishing URL dataset (e.g. data/phishing_site_urls.csv)
outputs:
  - name: feature CSV
    description: .tmp/features.csv — clean DataFrame with URL features, ready for training
script: execution/extract_url_features.py
---

## Goal
Turn a raw Kaggle phishing-URL CSV into a clean, ML-ready feature DataFrame.

## Steps

1. Download the dataset from Kaggle and place it at `data/<filename>.csv`.
   - Recommended: [Web Page Phishing Detection](https://www.kaggle.com/datasets/shashwatwork/web-page-phishing-detection-dataset)
   - Or: search Kaggle for "phishing URL dataset"

2. Install dependencies (once):
   ```powershell
   pip install pandas tldextract
   ```

3. Run the script:
   ```powershell
   # Preview first 5 rows without saving
   py execution/extract_url_features.py --input data/phishing_site_urls.csv --preview

   # Full run → saves to .tmp/features.csv
   py execution/extract_url_features.py --input data/phishing_site_urls.csv
   ```

4. The output CSV at `.tmp/features.csv` has these columns:

   | Column | Description |
   |---|---|
   | `url` | Original URL string |
   | `url_length` | Total character length |
   | `num_dots` | Number of `.` characters |
   | `num_subdomains` | Subdomain depth via tldextract |
   | `has_keyword` | 1 if URL contains login/secure/verify/account/update/bank/paypal |
   | `has_https` | 1 if scheme is https |
   | `num_special_chars` | Count of `@`, `-`, `_` |
   | `label` | Phishing/legitimate label (if present in source) |
   | ~~`domain_age`~~ | Skipped — requires paid WHOIS/API key |

## Edge cases & notes
- **Column auto-detection**: script recognises `url/URL/address` and `label/status/class/type/result` — no config needed for standard Kaggle datasets.
- **Malformed URLs**: handled per-row via tldextract + urlparse fallback; bad rows get `None` features and are logged as warnings, not crashes.
- **domain_age**: omitted intentionally. To add it, integrate `python-whois` or WHOIS API and add a `--domain-age` flag to the script.
- **Large datasets**: the script uses iterrows which is fine up to ~500k rows; for larger datasets switch to vectorised pandas operations or dask.
