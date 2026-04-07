/**
 * DevBrain Collector — Background Script
 * Listens for developer-related URLs and pushes them to the backend API.
 */

const API_BASE = "http://127.0.0.1:8001/api";

let lastTrackedUrl = "";
let lastTrackTime = 0;

function handleNavigation(details) {
    if (details.frameId === 0) {
        // Add a slight delay to allow SPAs (like YouTube) to update their document.title
        setTimeout(() => {
            chrome.tabs.get(details.tabId, (tab) => {
                if (!tab || !tab.url) return;

                // Ignore system pages, blank tabs, and "New Tab" navigation
                if (tab.url.startsWith("chrome://") ||
                    tab.url.startsWith("edge://") ||
                    tab.url.startsWith("about:") ||
                    tab.title === "New Tab" ||
                    tab.title === "YouTube") { // Also ignore generic YouTube homepage
                    return;
                }

                // Deduplicate rapid fires from browser url omnibox search
                const now = Date.now();
                if (tab.url === lastTrackedUrl && (now - lastTrackTime) < 5000) {
                    return; // Ignore exact same URL fired within 5 seconds
                }
                
                lastTrackedUrl = tab.url;
                lastTrackTime = now;

                syncToDevBrain(tab.url, tab.title);
            });
        }, 1500); // Wait 1.5s for DOM title to settle
    }
}

// 1. Regular static page loads
chrome.webNavigation.onCompleted.addListener(handleNavigation);

// 2. SPA (React/Angular) soft transitions (like clicking a video from the YouTube feed!)
chrome.webNavigation.onHistoryStateUpdated.addListener(handleNavigation);

async function syncToDevBrain(url, title) {
    // 1. Get auth token from extension storage
    const data = await chrome.storage.local.get(['devbrain_token']);
    if (!data.devbrain_token) {
        console.log("[DevBrain] Not logged in. Skipping sync.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/events/browser`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${data.devbrain_token}`
            },
            body: JSON.stringify({
                url: url,
                title: title,
                timestamp: new Date().toISOString()
            })
        });

        if (response.ok) {
            const result = await response.json();
            console.log(`[DevBrain] Synced: ${title} -> ${result.detected.technology}`);
        } else if (response.status === 401) {
            console.warn("[DevBrain] Token expired or invalid. Logging out.");
            await chrome.storage.local.remove('devbrain_token');
        } else {
            console.error(`[DevBrain] Sync returned status: ${response.status}`);
        }
    } catch (error) {
        console.error("[DevBrain] Sync failed:", error);
    }
}
