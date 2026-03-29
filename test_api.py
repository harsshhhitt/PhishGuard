"""
test_api.py - Simple test script for the Phishing Detection API
------------------------------------------------------------------
Tests the FastAPI endpoints with sample URLs.
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the /health endpoint."""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_prediction_endpoint(url: str):
    """Test the /predict-url endpoint with a sample URL."""
    print(f"\n🔍 Testing /predict-url with: {url}")
    try:
        payload = {"url": url}
        response = requests.post(
            f"{API_BASE_URL}/predict-url",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting API tests...")
    print("Make sure the API server is running: python main.py")
    print("=" * 50)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    # Wait a moment between requests
    time.sleep(1)
    
    # Test with sample URLs
    test_urls = [
        "https://www.google.com",  # Should be SAFE
        "http://secure-login-paypal.verify-account-update.com/login",  # Should be PHISHING
        "https://github.com",  # Should be SAFE
        "http://bit.ly/3xyz123",  # Suspicious short URL
    ]
    
    prediction_results = []
    for url in test_urls:
        result = test_prediction_endpoint(url)
        prediction_results.append(result)
        time.sleep(0.5)  # Small delay between requests
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Prediction Tests: {sum(prediction_results)}/{len(prediction_results)} passed")
    
    if all(prediction_results) and health_ok:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check the API server and model files")

if __name__ == "__main__":
    main()
