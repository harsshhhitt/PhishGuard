"""main.py - FastAPI Backend for Phishing Detection
-------------------------------------------------
REST API endpoint for phishing URL detection using trained Random Forest model.

Features:
- Loads model.pkl and features.json on startup with retry mechanism
- POST /predict-url endpoint for URL classification
- GET /health endpoint for service health checks
- CORS enabled for chrome-extension:// origins
- Comprehensive error handling and logging
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "model.pkl"
FEATURES_PATH = PROJECT_ROOT / "features.json"

# Global variables for model and features
model = None
features_config = None
model_loaded = False


class URLRequest(BaseModel):
    """Request model for URL prediction."""
    url: str = Field(..., min_length=1, description="URL to analyze for phishing")


class PredictionResponse(BaseModel):
    """Response model for URL prediction."""
    url: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score between 0 (safe) and 1 (phishing)")
    verdict: str = Field(..., pattern="^(PHISHING|SAFE)$", description="Classification verdict")
    reasons: List[str] = Field(default_factory=list, description="List of reasons for the verdict")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    features_loaded: bool
    uptime_seconds: float


# Initialize FastAPI app
app = FastAPI(
    title="Phishing Detection API",
    description="API for detecting phishing URLs using machine learning",
    version="1.0.0"
)

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Feature extraction constants (matching the training script)
PHISHING_KEYWORDS = {"login", "secure", "verify", "account", "update", "bank", "paypal"}
SPECIAL_CHARS = set("@-_")
START_TIME = time.time()


def extract_url_features(url: str) -> Dict[str, Any]:
    """
    Extract features from a URL matching the training pipeline.
    Returns the same feature set used during model training.
    """
    from urllib.parse import urlparse
    import tldextract
    
    empty_features = {
        "url_length": 0,
        "num_dots": 0,
        "num_subdomains": 0,
        "has_keyword": 0,
        "found_keywords": [],
        "has_https": 0,
        "num_special_chars": 0,
    }
    
    if not isinstance(url, str) or not url.strip():
        return empty_features
    
    url = url.strip()
    
    # Add scheme if missing for proper parsing
    if not url.startswith(("http://", "https://")):
        url_parsed = urlparse("http://" + url)
    else:
        url_parsed = urlparse(url)
    
    try:
        extracted = tldextract.extract(url)
        subdomain_parts = [s for s in extracted.subdomain.split(".") if s]
        num_subdomains = len(subdomain_parts)
    except Exception:
        # Fallback to netloc parsing
        netloc = url_parsed.netloc.lstrip("www.")
        num_subdomains = max(netloc.count(".") - 1, 0)
    
    url_lower = url.lower()
    
    # Find which keywords are present
    found_keywords = [kw for kw in PHISHING_KEYWORDS if kw in url_lower]
    
    return {
        "url_length": len(url),
        "num_dots": url.count("."),
        "num_subdomains": num_subdomains,
        "has_keyword": int(bool(found_keywords)),
        "found_keywords": found_keywords,
        "has_https": int(url_parsed.scheme == "https"),
        "num_special_chars": sum(url.count(ch) for ch in SPECIAL_CHARS),
    }


def generate_reasons(features: Dict[str, Any], risk_score: float) -> List[str]:
    """
    Generate human-readable reasons for the prediction.
    Only flags genuine suspicious signals, not false positives.
    """
    reasons = []
    
    # Check for unusual URL length (only flag if very long)
    if features["url_length"] > 100:
        reasons.append(f"URL is unusually long ({features['url_length']} chars)")
    
    # Check for suspicious keywords - only flag if NO HTTPS (reduces false positives)
    if features["has_keyword"] and features.get("found_keywords"):
        if not features["has_https"]:
            keyword = features["found_keywords"][0]
            reasons.append(f"Contains '{keyword}' without HTTPS")
    
    # Check for multiple subdomains - only flag if MORE than 3
    if features["num_subdomains"] > 3:
        reasons.append(f"Too many subdomains ({features['num_subdomains']})")
    
    # Check for missing HTTPS - only flag for high-risk sites
    if not features["has_https"] and features["has_keyword"]:
        reasons.append("No HTTPS on suspicious domain")
    
    # Check for multiple special characters
    if features["num_special_chars"] > 2:
        reasons.append("Multiple special characters")
    
    # Check for excessive dots
    if features["num_dots"] > 5:
        reasons.append(f"Too many dots ({features['num_dots']})")
    
    return reasons[:3] if reasons else ["No suspicious indicators detected"]


def load_model_with_retry(max_retries: int = 3, delay: float = 2.0) -> bool:
    """
    Load model and features with retry mechanism (ralph loop).
    Returns True if successful, False otherwise.
    """
    global model, features_config, model_loaded
    
    for attempt in range(max_retries):
        try:
            print(f"Loading model and features (attempt {attempt + 1}/{max_retries})...")
            
            # Load features configuration
            if FEATURES_PATH.exists():
                with open(FEATURES_PATH, 'r') as f:
                    features_config = json.load(f)
                print(f"Features loaded from {FEATURES_PATH}")
            else:
                print(f"Warning: {FEATURES_PATH} not found, using default feature order")
                features_config = {
                    "features": ["url_length", "num_dots", "num_subdomains", 
                               "has_keyword", "has_https", "num_special_chars"]
                }
            
            # Load model
            if MODEL_PATH.exists():
                model = joblib.load(MODEL_PATH)
                print(f"Model loaded from {MODEL_PATH}")
                model_loaded = True
                return True
            else:
                print(f"Error: {MODEL_PATH} not found")
                return False
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 1.5  # Exponential backoff
    
    print("Failed to load model after all retries")
    return False


@app.on_event("startup")
async def startup_event():
    """Initialize the API on startup using ralph loop for model loading."""
    success = load_model_with_retry()
    if not success:
        print("Warning: API started but model not loaded. Predictions will fail.")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - START_TIME
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        features_loaded=features_config is not None,
        uptime_seconds=uptime
    )


@app.post("/predict-url", response_model=PredictionResponse)
async def predict_url(request: URLRequest):
    """
    Predict if a URL is phishing.
    
    Args:
        request: URLRequest containing the URL to analyze
        
    Returns:
        PredictionResponse with risk score, verdict, and reasons
        
    Raises:
        HTTPException: If model is not loaded or URL is invalid
    """
    if not model_loaded or model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Service unavailable."
        )
    
    if not features_config:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Features configuration not loaded. Service unavailable."
        )
    
    try:
        # Extract features
        features = extract_url_features(request.url)
        
        # Prepare features for model (ensure correct order)
        feature_order = features_config.get("features", [])
        if not feature_order:
            feature_order = ["url_length", "num_dots", "num_subdomains", 
                           "has_keyword", "has_https", "num_special_chars"]
        
        # Create feature vector in the correct order
        feature_vector = [features.get(feature, 0) for feature in feature_order]
        
        # Make prediction
        X = pd.DataFrame([feature_vector], columns=feature_order)
        
        # Get probability for phishing class (assuming binary classification)
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(X)
            risk_score = float(probabilities[0][1])  # Probability of class 1 (phishing)
        else:
            # Fallback to decision function or direct prediction
            if hasattr(model, 'decision_function'):
                decision = model.decision_function(X)[0]
                risk_score = float(1 / (1 + (decision * -1)))  # Convert to probability-like score
            else:
                prediction = model.predict(X)[0]
                risk_score = float(prediction)
        
        # Ensure risk_score is in [0, 1] range
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine verdict (using 0.7 as threshold for PHISHING, 0.4 for SUSPICIOUS)
        if risk_score > 0.7:
            verdict = "PHISHING"
        elif risk_score > 0.4:
            verdict = "SUSPICIOUS"
        else:
            verdict = "SAFE"
        
        # Generate reasons
        reasons = generate_reasons(features, risk_score)
        
        return PredictionResponse(
            url=request.url,
            risk_score=risk_score,
            verdict=verdict,
            reasons=reasons
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing URL: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Phishing Detection API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict-url",
            "docs": "/docs"
        },
        "status": "model_loaded" if model_loaded else "model_not_loaded"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Try to load model before starting server (ralph loop)
    if load_model_with_retry():
        print("✅ Model loaded successfully")
    else:
        print("⚠️  Model not loaded - API will return errors for predictions")
    
    print("🚀 Starting FastAPI server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
