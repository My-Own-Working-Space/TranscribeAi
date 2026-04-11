document.getElementById('btn-toggle').onclick = async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
        chrome.tabs.sendMessage(tab.id, { action: 'TOGGLE_SIDEBAR' }).catch(() => {
            // If it fails, try manual injection
            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ['src/contentScript.js']
            }).then(() => {
                chrome.tabs.sendMessage(tab.id, { action: 'TOGGLE_SIDEBAR' });
            });
        });
    }
};
