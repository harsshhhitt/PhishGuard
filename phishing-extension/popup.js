// popup.js - Simple popup for displaying phishing scan results

document.addEventListener('DOMContentLoaded', async () => {
    // Get DOM elements
    const urlDisplay = document.getElementById('url-display');
    const riskScore = document.getElementById('risk-score');
    const riskBar = document.getElementById('risk-bar');
    const verdict = document.getElementById('verdict');
    const reasonsList = document.getElementById('reasons-list');
    const scanAgainBtn = document.getElementById('scan-again-btn');
    const statusMessage = document.getElementById('status-message');

    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
        statusMessage.textContent = 'Error: Could not get current tab';
        return;
    }

    const currentUrl = tab.url;
    const tabId = tab.id;

    // Display URL (truncated if too long)
    const displayUrl = currentUrl.length > 60 
        ? currentUrl.substring(0, 57) + '...' 
        : currentUrl;
    urlDisplay.textContent = displayUrl;
    urlDisplay.title = currentUrl;

    // Load and display result
    async function loadResult() {
        const result = await chrome.storage.local.get(`tab_${tabId}`);
        const scanResult = result[`tab_${tabId}`];

        if (!scanResult) {
            // No result yet - show scanning status
            verdict.textContent = 'Checking...';
            verdict.className = 'verdict-scanning';
            riskScore.textContent = '';
            riskBar.style.width = '0%';
            riskBar.style.background = '#e0e0e0';
            reasonsList.innerHTML = '';
            statusMessage.textContent = 'Scanning...';
            return;
        }

        // Populate data
        const score = scanResult.riskScore || 0;
        const scorePercent = Math.round(score * 100);
        
        riskScore.textContent = `${scorePercent}% Risk Score`;
        riskBar.style.width = `${scorePercent}%`;
        
        // Set bar color and class based on risk
        riskBar.style.width = `${scorePercent}%`;
        riskBar.className = 'risk-bar-fill';
        if (score > 0.6) {
            riskBar.classList.add('phishing');
        } else if (score > 0.3) {
            riskBar.classList.add('suspicious');
        } else {
            riskBar.classList.add('safe');
        }

        // Set verdict with styling
        const verdictText = scanResult.verdict || 'UNKNOWN';
        verdict.textContent = verdictText;
        verdict.className = 'verdict-badge';
        
        if (verdictText === 'SAFE') {
            verdict.classList.add('verdict-safe');
            statusMessage.textContent = 'This site appears safe.';
        } else if (verdictText === 'PHISHING') {
            verdict.classList.add('verdict-phishing');
            statusMessage.textContent = 'Warning: Potential phishing site detected!';
        } else if (verdictText === 'UNAVAILABLE') {
            verdict.classList.add('verdict-suspicious');
            statusMessage.textContent = 'Backend offline – start your local server';
        } else {
            verdict.classList.add('verdict-suspicious');
            statusMessage.textContent = 'Scanning...';
        }

        // Populate reasons
        reasonsList.innerHTML = '';
        if (scanResult.reasons && scanResult.reasons.length > 0) {
            scanResult.reasons.forEach(reason => {
                const li = document.createElement('li');
                li.className = 'reason-item';
                li.textContent = reason;
                reasonsList.appendChild(li);
            });
        }

        // Update button text
        scanAgainBtn.textContent = 'Scan Again';
    }

    // Initial load
    await loadResult();

    // Listen for storage changes to update in real-time
    chrome.storage.onChanged.addListener((changes, namespace) => {
        if (namespace === 'local' && changes[`tab_${tabId}`]) {
            loadResult();
        }
    });

    // Scan again button handler
    scanAgainBtn.addEventListener('click', async () => {
        scanAgainBtn.disabled = true;
        scanAgainBtn.textContent = 'Scanning...';
        statusMessage.textContent = 'Scanning...';
        verdict.textContent = 'Checking...';
        verdict.className = 'verdict-badge verdict-suspicious';

        try {
            const response = await chrome.runtime.sendMessage({
                action: 'checkUrl',
                url: currentUrl,
                tabId: tabId
            });

            if (response.success) {
                await loadResult();
            } else {
                statusMessage.textContent = 'Scan failed: ' + (response.error || 'Unknown error');
                scanAgainBtn.textContent = 'Try Again';
            }
        } catch (error) {
            statusMessage.textContent = 'Error: ' + error.message;
            scanAgainBtn.textContent = 'Try Again';
        } finally {
            scanAgainBtn.disabled = false;
        }
    });
});
