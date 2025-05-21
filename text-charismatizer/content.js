/**
 * Text Charismatizer Content Script
 * Handles text selection processing and UI feedback in web pages.
 */

/**
 * Creates and manages the progress indicator for text processing
 * @param {HTMLElement} element - The active element being edited
 * @param {Range} [range] - The selection range for contentEditable elements
 * @returns {Object} - Controller object with stop() method
 */
function createProgressAnimation(element, range) {
  const progressText = '⌛ Processing...';
  let originalRange = range ? range.cloneRange() : null;
  let progressSpan;
  let originalValue;
  let originalStart;

  /**
   * Displays the progress indicator in the appropriate element
   */
  const showProgress = () => {
    if (element.isContentEditable && range) {
      if (!progressSpan) {
        progressSpan = document.createElement('span');
        progressSpan.className = 'progress-animation';
        progressSpan.style.color = '#666';
        range.deleteContents();
        range.insertNode(progressSpan);
      }
      progressSpan.textContent = progressText;
    } else {
      originalValue = element.value;
      originalStart = element.selectionStart;
      const start = element.selectionStart;
      const value = element.value;
      const beforeText = value.substring(0, start);
      const afterText = value.substring(start);
      element.value = beforeText + progressText + afterText;
      element.selectionStart = start + progressText.length;
      element.selectionEnd = element.selectionStart;
    }
  };

  showProgress();

  return {
    /**
     * Removes the progress indicator and restores original state
     */
    stop: () => {
      if (element.isContentEditable && progressSpan) {
        progressSpan.remove();
        if (originalRange) {
          range.setStart(originalRange.startContainer, originalRange.startOffset);
          range.setEnd(originalRange.endContainer, originalRange.endOffset);
        }
      } else if (!element.isContentEditable) {
        const currentValue = element.value;
        const progressIndex = currentValue.indexOf(progressText);
        if (progressIndex !== -1) {
          element.value = currentValue.substring(0, progressIndex) + 
                         currentValue.substring(progressIndex + progressText.length);
          element.selectionStart = originalStart;
          element.selectionEnd = originalStart;
        }
      }
    }
  };
}

// Listen for charismatize requests from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'charismatize') {
    const selectedText = window.getSelection().toString();
    if (!selectedText) {
      return;
    }

    const activeElement = document.activeElement;
    let progressAnimation;

    /**
     * Process text based on the type of editable element
     * Supports both contentEditable elements and form inputs
     */
    if (activeElement.isContentEditable) {
      const selection = window.getSelection();
      const range = selection.getRangeAt(0);
      progressAnimation = createProgressAnimation(activeElement, range);
      
      chrome.runtime.sendMessage({
        action: 'processText',
        text: selectedText
      }, response => {
        progressAnimation.stop();
        if (response.success) {
          const textNode = document.createTextNode(response.charismatizedText);
          range.deleteContents();
          range.insertNode(textNode);
        }
      });
    } else if (activeElement.tagName === 'TEXTAREA' || 
              (activeElement.tagName === 'INPUT' && activeElement.type === 'text')) {
      const start = activeElement.selectionStart;
      const end = activeElement.selectionEnd;
      const originalValue = activeElement.value;
      
      progressAnimation = createProgressAnimation(activeElement);
      
      chrome.runtime.sendMessage({
        action: 'processText',
        text: selectedText
      }, response => {
        progressAnimation.stop();
        if (response.success) {
          const beforeText = originalValue.substring(0, start);
          const afterText = originalValue.substring(end);
          activeElement.value = beforeText + response.charismatizedText + afterText;
          activeElement.selectionStart = start;
          activeElement.selectionEnd = start + response.charismatizedText.length;
        } else {
          activeElement.value = originalValue;
          activeElement.selectionStart = start;
          activeElement.selectionEnd = end;
        }
      });
    }
  }
});