/**
 * Text Charismatizer Settings Popup
 * Handles configuration of GitHub PAT token and model selection
 */

document.addEventListener('DOMContentLoaded', () => {
  // Load saved settings from chrome.storage
  chrome.storage.sync.get(['githubPat', 'model'], (result) => {
    document.getElementById('github-pat').value = result.githubPat || '';
    document.getElementById('model').value = result.model || 'gpt-4o-mini';
  });

  /**
   * Display status message to user
   * @param {string} message - The message to display
   * @param {boolean} [isError=false] - Whether this is an error message
   */
  function showStatus(message, isError = false) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = isError ? 'error' : 'success';
    statusEl.style.display = 'block';
    
    // Auto-hide message after 3 seconds
    setTimeout(() => {
      statusEl.style.display = 'none';
    }, 3000);
  }

  // Handle settings form submission
  document.getElementById('save').addEventListener('click', () => {
    const githubPat = document.getElementById('github-pat').value;
    const model = document.getElementById('model').value;
    
    // Validate required fields
    if (!githubPat) {
      showStatus('Please enter your GitHub PAT token', true);
      return;
    }

    if (!model) {
      showStatus('Please enter the model name', true);
      return;
    }
    
    // Save settings to chrome.storage
    chrome.storage.sync.set({
      githubPat,
      model
    }, () => {
      showStatus('Settings saved successfully!');
    });
  });
});