/**
 * Text Charismatizer Background Service Worker
 * Handles context menu integration and AI text processing.
 */

// Create context menu item on installation and service worker start
function createContextMenu() {
  chrome.contextMenus.create({
    id: 'charismatize',
    title: 'Charismatize 🪄',
    contexts: ['selection']
  });
}

chrome.runtime.onInstalled.addListener(createContextMenu);
// Also create context menu when service worker starts
createContextMenu();

// Handle context menu clicks by sending message to content script
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'charismatize') {
    chrome.tabs.sendMessage(tab.id, { action: 'charismatize' });
  }
});

/**
 * Message handler for text processing requests from content script
 * @listens runtime.onMessage
 * @param {Object} request - Message data containing text to process
 * @param {Object} sender - Information about the script that sent the message
 * @param {Function} sendResponse - Callback to send the response back
 * @returns {boolean} - True to indicate async response
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'processText') {
    processWithAI(request.text)
      .then(result => {
        sendResponse({ success: true, charismatizedText: result });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    return true; // Required for async response
  }
});

/**
 * Process text using AI to make it more charismatic
 * @param {string} text - The text to be processed
 * @returns {Promise<string>} - The processed charismatic text
 * @throws {Error} - If API request fails
 */
async function processWithAI(text) {
  try {
    const settings = await chrome.storage.sync.get(['githubPat', 'model']);
    
    const response = await fetch('https://models.github.ai/inference/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${settings.githubPat}`
      },
      body: JSON.stringify({
        model: "openai/" + (settings.model || 'gpt-4o-mini'),
        messages: [
          {
            role: 'system',
            content: 'You are a charismatic writing assistant that helps make text more engaging and persuasive.'
          },
          {
            role: 'user',
            content: `Rewrite the following in a charismatic tone, with a healthy balance of warmth & competence keywords: ${text}`
          }
        ]
      })
    });

    if (!response.ok) {
      throw new Error('API request failed');
    }

    const data = await response.json();
    return data.choices[0].message.content;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}