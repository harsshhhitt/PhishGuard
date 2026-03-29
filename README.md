# Phishing Detection API

FastAPI backend for detecting phishing URLs using a trained Random Forest model.

## Features

- **POST /predict-url**: Analyze URLs for phishing characteristics
- **GET /health**: Service health check
- **CORS enabled**: Works with Chrome extensions
- **Retry mechanism**: Robust model loading with exponential backoff
- **Comprehensive responses**: Risk scores, verdicts, and detailed reasons

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Model Files

The API expects these files in the project root:
- `model.pkl` - Trained Random Forest model
- `features.json` - Feature configuration (feature order and metadata)

### 3. Start the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "features_loaded": true,
  "uptime_seconds": 123.45
}
```

### URL Prediction

```http
POST /predict-url
Content-Type: application/json

{
  "url": "https://example.com"
}
```

Response:
```json
{
  "url": "https://example.com",
  "risk_score": 0.15,
  "verdict": "SAFE",
  "reasons": ["No obvious risk factors detected"]
}
```

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Testing

Run the test script to verify the API:

```bash
# Start the API server first
python main.py

# In another terminal, run tests
python test_api.py
```

## Feature Extraction

The API extracts the same features used during model training:

1. **url_length**: Total length of the URL
2. **num_dots**: Number of dots in the URL
3. **num_subdomains**: Number of subdomains
4. **has_keyword**: Contains suspicious keywords (login, secure, verify, etc.)
5. **has_https**: Uses HTTPS protocol
6. **num_special_chars**: Count of special characters (@, -, _)

## Risk Assessment

- **Risk Score**: Float between 0.0 (safe) and 1.0 (phishing)
- **Verdict**: "PHISHING" if score > 0.5, otherwise "SAFE"
- **Reasons**: Human-readable explanations for the decision

## CORS Configuration

The API is configured to accept requests from:
- Chrome extensions (`chrome-extension://*`)
- Firefox extensions (`moz-extension://*`)
- Local development (`http://localhost:*`, `https://localhost:*`)

## Error Handling

- **503 Service Unavailable**: Model or features not loaded
- **400 Bad Request**: Invalid URL format
- **500 Internal Server Error**: Processing errors

## Development

### Project Structure

```
research enthusiast/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── test_api.py         # API test script
├── model.pkl           # Trained model (to be created)
├── features.json       # Feature config (to be created)
└── execution/
    └── extract_url_features.py  # Feature extraction logic
```

### Model Loading

The API includes a robust retry mechanism for model loading:
- Up to 3 attempts with exponential backoff
- Graceful degradation if model files are missing
- Detailed logging for troubleshooting

## Integration with Chrome Extension

The API is ready for Chrome extension integration:

```javascript
const response = await fetch('http://localhost:8000/predict-url', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: currentUrl })
});

const result = await response.json();
console.log(result.verdict, result.risk_score, result.reasons);
```
