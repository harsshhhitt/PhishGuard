// content.js - PhishGuard warning banner

(function() {
  'use strict';

  let currentBanner = null;

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'showWarning') {
      handleWarning(request.data);
      sendResponse({ success: true });
    }
    return true;
  });

  function handleWarning(data) {
    // Remove existing banner
    removeBanner();

    const score = data.riskScore || 0;
    const verdict = data.verdict || 'UNKNOWN';

    // Don't show banner for SAFE
    if (verdict === 'SAFE' || score < 0.4) {
      return;
    }

    // Determine banner style
    const isPhishing = score > 0.6;
    const bgColor = isPhishing 
      ? 'linear-gradient(135deg, #f44336, #d32f2f)'  // Red
      : 'linear-gradient(135deg, #ff9800, #f57c00)'; // Yellow

    const title = isPhishing ? '⚠️ PHISHING DETECTED' : '⚠️ SUSPICIOUS SITE';

    // Create banner with all required IDs and inline styles
    currentBanner = document.createElement('div');
    currentBanner.id = 'phishguard-banner';
    currentBanner.innerHTML = `
      <div id="phishguard-title">${title}</div>
      <div id="phishguard-score">Risk Score: ${(score * 100).toFixed(1)}%</div>
      <ul id="phishguard-reasons"></ul>
      <button id="phishguard-dismiss">Dismiss</button>
    `;

    // Main banner styles (all inline with !important)
    currentBanner.style.cssText = `
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      background: ${bgColor} !important;
      color: white !important;
      z-index: 2147483647 !important;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
      padding: 12px 16px !important;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
      box-sizing: border-box !important;
    `;

    // Title styles
    const titleEl = currentBanner.querySelector('#phishguard-title');
    titleEl.style.cssText = `
      font-size: 16px !important;
      font-weight: 600 !important;
      margin-bottom: 4px !important;
      color: white !important;
    `;

    // Score styles
    const scoreEl = currentBanner.querySelector('#phishguard-score');
    scoreEl.style.cssText = `
      font-size: 13px !important;
      margin-bottom: 8px !important;
      opacity: 0.95 !important;
      color: white !important;
    `;

    // Reasons list styles
    const reasonsEl = currentBanner.querySelector('#phishguard-reasons');
    reasonsEl.style.cssText = `
      margin: 0 0 12px 0 !important;
      padding-left: 16px !important;
      font-size: 12px !important;
      color: white !important;
      opacity: 0.9 !important;
    `;

    // Add reasons
    if (data.reasons && data.reasons.length > 0) {
      data.reasons.forEach(reason => {
        const li = document.createElement('li');
        li.textContent = reason;
        li.style.cssText = 'margin-bottom: 2px !important;';
        reasonsEl.appendChild(li);
      });
    }

    // Dismiss button styles
    const dismissEl = currentBanner.querySelector('#phishguard-dismiss');
    dismissEl.style.cssText = `
      background: rgba(255,255,255,0.2) !important;
      border: 1px solid rgba(255,255,255,0.4) !important;
      color: white !important;
      padding: 6px 14px !important;
      border-radius: 4px !important;
      cursor: pointer !important;
      font-size: 12px !important;
      font-family: inherit !important;
    `;

    // Dismiss handler
    dismissEl.addEventListener('click', () => {
      removeBanner();
    });

    // Insert into page
    if (document.body) {
      document.body.insertBefore(currentBanner, document.body.firstChild);
      // Add padding to body to prevent content from being hidden
      const bannerHeight = currentBanner.offsetHeight;
      document.body.style.paddingTop = (parseInt(getComputedStyle(document.body).paddingTop) + bannerHeight) + 'px';
    }
  }

  function removeBanner() {
    if (currentBanner && currentBanner.parentNode) {
      const bannerHeight = currentBanner.offsetHeight;
      currentBanner.remove();
      // Remove padding from body
      const currentPadding = parseInt(getComputedStyle(document.body).paddingTop) || 0;
      document.body.style.paddingTop = Math.max(0, currentPadding - bannerHeight) + 'px';
      currentBanner = null;
    }
  }

  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    removeBanner();
  });
})();
