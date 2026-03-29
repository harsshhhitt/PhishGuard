"""train.py - Phishing Detection Model Training for Render.com
------------------------------------------------------------
Trains a Random Forest classifier on phishing URL data.
Automatically downloads dataset if not present.
Uses only re, urllib, and tldextract for feature extraction.

Usage:
    python train.py
"""

import json
import random
import re
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.model_selection import train_test_split
import tldextract


# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "model.pkl"
FEATURES_PATH = PROJECT_ROOT / "features.json"
DATASET_PATH = PROJECT_ROOT / "phishing_dataset.csv"

# Feature extraction constants
PHISHING_KEYWORDS = {"login", "secure", "verify", "account", "update", "bank", "paypal", "verify", "confirm"}
SPECIAL_CHARS = set("@-_")
FEATURE_ORDER = ["url_length", "num_dots", "num_subdomains", "has_keyword", "has_https", "num_special_chars"]

# Dataset URLs to try (reliable sources)
DATASET_URLS = [
    "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links-NEW-today.txt",
    "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links-ACTIVE.txt",
]


def extract_features(url: str) -> Dict[str, int]:
    """
    Extract features from a URL using only re, urllib, and tldextract.
    Returns a dictionary with the 6 required features.
    """
    features = {feature: 0 for feature in FEATURE_ORDER}
    
    if not isinstance(url, str) or not url.strip():
        return features
    
    url = url.strip()
    
    # Add scheme if missing for proper parsing
    if not url.startswith(("http://", "https://")):
        url_parsed = urlparse("http://" + url)
    else:
        url_parsed = urlparse(url)
    
    # Extract subdomains using tldextract
    try:
        extracted = tldextract.extract(url)
        subdomain_parts = [s for s in extracted.subdomain.split(".") if s]
        num_subdomains = len(subdomain_parts)
    except Exception:
        # Fallback: count dots in netloc (excluding www)
        netloc = url_parsed.netloc.lstrip("www.")
        num_subdomains = max(netloc.count(".") - 1, 0)
    
    url_lower = url.lower()
    
    # Count special characters using regex
    special_count = len(re.findall(r'[@\-_]', url))
    
    # Extract all features
    features = {
        "url_length": len(url),
        "num_dots": url.count("."),
        "num_subdomains": num_subdomains,
        "has_keyword": int(any(kw in url_lower for kw in PHISHING_KEYWORDS)),
        "has_https": int(url_parsed.scheme == "https"),
        "num_special_chars": special_count,
    }
    
    return features


def download_phishing_data() -> bool:
    """
    Download phishing URL dataset from reliable sources.
    Returns True if successful, False otherwise.
    """
    print("📥 Downloading phishing dataset...")
    
    for url in DATASET_URLS:
        try:
            print(f"   Trying: {url[:60]}...")
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                # Parse URLs from content
                urls = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract URL-like strings
                        if line.startswith('http'):
                            urls.append(line)
                
                if len(urls) < 100:
                    print(f"   ⚠️  Only found {len(urls)} URLs, trying next source...")
                    continue
                
                print(f"   ✅ Downloaded {len(urls)} phishing URLs")
                
                # Save to CSV format
                df = pd.DataFrame({'url': urls, 'label': ['phishing'] * len(urls)})
                
                # Add legitimate URLs (common safe domains)
                legit_urls = generate_legitimate_urls(min(len(urls), 5000))
                legit_df = pd.DataFrame({'url': legit_urls, 'label': ['legitimate'] * len(legit_urls)})
                
                # Combine and shuffle
                df = pd.concat([df, legit_df], ignore_index=True)
                df = df.sample(frac=1, random_state=42).reset_index(drop=True)
                
                # Save dataset
                df.to_csv(DATASET_PATH, index=False)
                print(f"   � Saved dataset to {DATASET_PATH}")
                return True
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            continue
    
    return False


def generate_legitimate_urls(count: int) -> List[str]:
    """Generate legitimate URLs for training balance."""
    legitimate_domains = [
        "google.com", "youtube.com", "facebook.com", "twitter.com", "instagram.com",
        "linkedin.com", "github.com", "stackoverflow.com", "wikipedia.org", "reddit.com",
        "amazon.com", "netflix.com", "microsoft.com", "apple.com", "adobe.com",
        "spotify.com", "zoom.us", "slack.com", "discord.com", "twitch.tv"
    ]
    
    paths = ["/", "/home", "/login", "/dashboard", "/profile", "/settings", "/help", "/about"]
    
    urls = []
    for _ in range(count):
        domain = random.choice(legitimate_domains)
        path = random.choice(paths)
        scheme = "https" if random.random() > 0.1 else "http"
        urls.append(f"{scheme}://{domain}{path}")
    
    return urls


def generate_sample_data(num_samples: int = 3000) -> pd.DataFrame:
    """
    Generate synthetic phishing and legitimate URLs for offline training.
    Used as fallback when download fails.
    """
    print(f"⚙️  Generating {num_samples} synthetic URLs...")
    
    urls = []
    labels = []
    
    # Generate legitimate URLs (50%)
    legit_count = num_samples // 2
    legit_urls = generate_legitimate_urls(legit_count)
    urls.extend(legit_urls)
    labels.extend(['legitimate'] * legit_count)
    
    # Generate phishing URLs (50%)
    phishing_patterns = [
        "secure-login", "verify-account", "update-payment", "bank-secure",
        "paypal-confirm", "auth-required", "suspicious-activity", "emergency-verify",
        "account-locked", "security-alert", "verify-identity", "payment-update"
    ]
    phishing_tlds = [".com", ".net", ".org", ".info", ".xyz", ".click", ".link"]
    suspicious_subdomains = ["secure", "login", "verify", "account", "update", "bank", "confirm"]
    
    phishing_count = num_samples - legit_count
    for _ in range(phishing_count):
        pattern = random.choice(phishing_patterns)
        tld = random.choice(phishing_tlds)
        
        if random.random() > 0.5:
            subdomain = random.choice(suspicious_subdomains)
            domain = random.choice(["google", "facebook", "paypal", "amazon", "microsoft"])
            url = f"http://{subdomain}.{domain}{tld}/{pattern}?id={random.randint(1000, 9999)}"
        else:
            domain = f"{pattern}-{random.randint(100, 999)}{tld}"
            url = f"http://{domain}/login"
        
        urls.append(url)
        labels.append('phishing')
    
    df = pd.DataFrame({'url': urls, 'label': labels})
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"✅ Generated {len(df)} synthetic URLs")
    return df


def load_or_create_dataset() -> pd.DataFrame:
    """
    Load existing dataset or download/create new one.
    """
    # Check if dataset already exists
    if DATASET_PATH.exists():
        print(f"📂 Loading existing dataset from {DATASET_PATH}")
        try:
            df = pd.read_csv(DATASET_PATH)
            if len(df) > 100:
                print(f"   ✅ Loaded {len(df)} URLs from existing dataset")
                return df
        except Exception as e:
            print(f"   ⚠️  Failed to load existing: {e}")
    
    # Try to download
    if download_phishing_data():
        return pd.read_csv(DATASET_PATH)
    
    # Fallback to synthetic data
    print("🔄 Using synthetic data (download failed)")
    return generate_sample_data(3000)


def prepare_training_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extract features from URLs and prepare training data.
    """
    print("🔧 Extracting features from URLs...")
    
    features_list = []
    total = len(df)
    
    for idx, row in df.iterrows():
        url = row['url']
        features = extract_features(url)
        features_list.append(features)
        
        if (idx + 1) % 500 == 0:
            print(f"   Processed {idx + 1}/{total} URLs")
    
    X = pd.DataFrame(features_list)
    y = df['label'].map({'legitimate': 0, 'phishing': 1})
    
    print(f"✅ Feature extraction complete: {X.shape[0]} samples, {X.shape[1]} features")
    return X, y


def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    """
    Train Random Forest classifier.
    """
    print("🤖 Training Random Forest model...")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    start_time = time.time()
    model.fit(X_train, y_train)
    training_time = time.time() - start_time
    
    print(f"✅ Model trained in {training_time:.2f}s")
    
    # Evaluate
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print("\n📊 Model Performance:")
    print(f"   Accuracy:  {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall:    {recall:.4f}")
    print(f"   F1 Score:  {f1:.4f}")
    
    return model


def save_model_and_features(model: RandomForestClassifier) -> None:
    """
    Save trained model and feature configuration.
    """
    print("💾 Saving model and features...")
    
    try:
        # Save model
        joblib.dump(model, MODEL_PATH)
        print(f"   ✅ Model saved: {MODEL_PATH}")
        
        # Save feature config
        features_config = {
            "features": FEATURE_ORDER,
            "feature_descriptions": {
                "url_length": "Total length of the URL",
                "num_dots": "Number of dots in the URL",
                "num_subdomains": "Number of subdomains",
                "has_keyword": "Contains suspicious keywords",
                "has_https": "Uses HTTPS protocol",
                "num_special_chars": "Number of special characters (@, -, _)"
            },
            "model_type": "RandomForestClassifier",
            "threshold": 0.5
        }
        
        with open(FEATURES_PATH, 'w') as f:
            json.dump(features_config, f, indent=2)
        print(f"   ✅ Features saved: {FEATURES_PATH}")
        
    except Exception as e:
        print(f"   ❌ Failed to save: {e}")
        raise


def main() -> None:
    """Main training pipeline."""
    print("=" * 60)
    print("🚀 Phishing Detection Model Training")
    print("=" * 60)
    
    try:
        # Load or create dataset
        df = load_or_create_dataset()
        
        # Prepare data
        X, y = prepare_training_data(df)
        
        # Train model
        model = train_model(X, y)
        
        # Save
        save_model_and_features(model)
        
        print("\n" + "=" * 60)
        print("🎉 Training Complete!")
        print("=" * 60)
        print(f"📁 Output files:")
        print(f"   - {MODEL_PATH}")
        print(f"   - {FEATURES_PATH}")
        print(f"\n🌐 Start server: python main.py")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
