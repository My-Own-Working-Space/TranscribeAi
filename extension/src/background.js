// background.js - Orchestrates Offscreen Document and Content Script communication

console.log('TranscribeAi Background Initialized');

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
    console.log('TranscribeAi: Icon clicked on tab:', tab.url);
    chrome.tabs.sendMessage(tab.id, { action: 'TOGGLE_SIDEBAR' }).catch(err => {
        console.warn('Could not send message, content script might not be loaded yet:', err);
        // Attempt to inject manually if it fails
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['src/contentScript.js']
        }).then(() => {
            chrome.tabs.sendMessage(tab.id, { action: 'TOGGLE_SIDEBAR' });
        });
    });
});

async function setupOffscreen() {
    try {
        if (chrome.runtime.getContexts) {
            const existingContexts = await chrome.runtime.getContexts({
                contextTypes: ['OFFSCREEN_DOCUMENT']
            });
            if (existingContexts.length > 0) return;
        }
    } catch (e) {
        console.warn('chrome.runtime.getContexts not supported, attempting to create offscreen doc anyway.');
    }

    try {
        await chrome.offscreen.createDocument({
            url: 'src/offscreen.html',
            reasons: ['USER_MEDIA'],
            justification: 'Capturing tab audio for real-time transcription.'
        });
        console.log('Offscreen document created successfully');
    } catch (err) {
        if (!err.message.includes('Only one offscreen document may be created')) {
            console.error('Failed to create offscreen document:', err);
        }
    }
}

chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
    if (request.action === 'START_RECORDING') {
        // 1. Get streamId for the active tab
        chrome.tabCapture.getMediaStreamId({ targetTabId: sender.tab.id }, async (streamId) => {
            // 2. Ensure offscreen document exists
            await setupOffscreen();
            // 3. Signal offscreen to start capture
            chrome.runtime.sendMessage({
                target: 'offscreen',
                action: 'START_RECORDING',
                streamId: streamId
            });
        });
    } else if (request.action === 'STOP_RECORDING') {
        chrome.runtime.sendMessage({
            target: 'offscreen',
            action: 'STOP_RECORDING'
        });
    } else if (request.action === 'NEW_TRANSCRIPTION_FROM_OFFSCREEN') {
        // Forward to all supported tabs (Meet and YouTube)
        chrome.tabs.query({}, (tabs) => {
            tabs.forEach(tab => {
                if (tab.url && (tab.url.includes('meet.google.com') || tab.url.includes('youtube.com'))) {
                    chrome.tabs.sendMessage(tab.id, {
                        action: 'NEW_TRANSCRIPTION',
                        text: request.text,
                        type: request.type || 'TRANSCRIPTION'
                    }).catch(() => { });
                }
            });
        });
    }
});
