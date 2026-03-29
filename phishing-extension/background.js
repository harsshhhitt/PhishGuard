// background.js - Service Worker for Phishing Detection Extension
// Handles tab monitoring, API communication, and warning triggers

const API_BASE_URL = 'https://phishguard-api.onrender.com';
const MAX_RETRIES = 3;
const RETRY_DELAY = 500;
const RISK_THRESHOLD = 0.6;

// Helper: Check if URL should be skipped
function shouldSkipUrl(url) {
  if (!url) return true;
  if (url.startsWith('chrome://')) return true;
  if (url.startsWith('about://')) return true;
  if (url.startsWith('about:')) return true;
  if (url.includes('localhost') || url.includes('127.0.0.1')) return true;
  return false;
}

// Helper: Delay for retry logic
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// API call with retry logic
async function checkUrlWithRetry(url, attempt = 1) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API_BASE_URL}/predict-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: url }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (attempt < MAX_RETRIES) {
      await delay(RETRY_DELAY);
      return checkUrlWithRetry(url, attempt + 1);
    }
    throw error;
  }
}

// Main function: Scan URL and handle results
async function scanUrl(tabId, url) {
  // Store scanning status
  await chrome.storage.local.set({
    [`tab_${tabId}`]: {
      url: url,
      status: 'SCANNING',
      timestamp: Date.now()
    }
  });

  try {
    const result = await checkUrlWithRetry(url);
    const riskScore = result.risk_score || result.phishing_probability || 0;
    
    // Store the result
    const scanResult = {
      url: url,
      status: 'COMPLETED',
      verdict: result.verdict || result.prediction || 'UNKNOWN',
      riskScore: riskScore,
      confidence: result.confidence || 0,
      timestamp: Date.now()
    };
    
    await chrome.storage.local.set({ [`tab_${tabId}`]: scanResult });

    // If high risk, send message to content script
    if (riskScore > RISK_THRESHOLD) {
      try {
        await chrome.tabs.sendMessage(tabId, {
          action: 'showWarning',
          data: scanResult
        });
      } catch (error) {
        // Content script may not be loaded yet
        console.log('Could not send message to tab:', tabId, error.message);
      }
    }

    return scanResult;
  } catch (error) {
    console.error('API call failed after retries:', error);
    
    // Store unavailable status
    const unavailableResult = {
      url: url,
      status: 'ERROR',
      verdict: 'UNAVAILABLE',
      riskScore: 0,
      error: error.message,
      timestamp: Date.now()
    };
    
    await chrome.storage.local.set({ [`tab_${tabId}`]: unavailableResult });
    return unavailableResult;
  }
}

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only process when page finishes loading
  if (changeInfo.status !== 'complete') return;
  
  const url = tab.url;
  
  // Skip excluded URLs
  if (shouldSkipUrl(url)) {
    console.log('Skipping scan for:', url);
    return;
  }

  console.log('Tab loaded, scanning URL:', url);
  scanUrl(tabId, url);
});

// Clean up storage when tab is closed
chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.local.remove(`tab_${tabId}`);
});

// Listen for messages from popup or content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request);
  
  if (request.action === 'checkUrl') {
    const tabId = sender.tab?.id || request.tabId;
    if (tabId && request.url) {
      scanUrl(tabId, request.url)
        .then(result => sendResponse({ success: true, data: result }))
        .catch(error => sendResponse({ success: false, error: error.message }));
    } else {
      sendResponse({ success: false, error: 'Missing tabId or url' });
    }
    return true;
  }
  
  if (request.action === 'getScanResult') {
    const tabId = request.tabId;
    chrome.storage.local.get(`tab_${tabId}`, (data) => {
      sendResponse({ success: true, data: data[`tab_${tabId}`] || null });
    });
    return true;
  }
  
  if (request.action === 'getAllResults') {
    chrome.storage.local.get(null, (data) => {
      const results = {};
      for (const key in data) {
        if (key.startsWith('tab_')) {
          results[key] = data[key];
        }
      }
      sendResponse({ success: true, data: results });
    });
    return true;
  }
});

// Initialize on install
chrome.runtime.onInstalled.addListener(() => {
  console.log('Phishing Detection Extension installed');
  
  chrome.storage.sync.set({
    apiEndpoint: API_BASE_URL,
    autoScan: true,
    showNotifications: true,
    riskThreshold: RISK_THRESHOLD
  });
});

// Clean old entries periodically
chrome.alarms?.create?.('cleanup', { periodInMinutes: 60 });
chrome.alarms?.onAlarm?.addListener((alarm) => {
  if (alarm.name === 'cleanup') {
    cleanupOldEntries();
  }
});

async function cleanupOldEntries() {
  const data = await chrome.storage.local.get(null);
  const now = Date.now();
  const oneHour = 60 * 60 * 1000;
  const keysToRemove = [];
  
  for (const key in data) {
    if (key.startsWith('tab_')) {
      const entry = data[key];
      if (entry.timestamp && (now - entry.timestamp > oneHour)) {
        keysToRemove.push(key);
      }
    }
  }
  
  if (keysToRemove.length > 0) {
    await chrome.storage.local.remove(keysToRemove);
    console.log('Cleaned up', keysToRemove.length, 'old entries');
  }
}
