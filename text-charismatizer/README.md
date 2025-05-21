# Text Charismatizer

A browser extension that helps make your text more charismatic using AI. Transform any text into a more engaging and persuasive version with a single click.

## Features

- Right-click context menu option to enhance selected text
- Works in any editable text field on any website:
  - Regular text inputs
  - TextArea fields
  - Rich text editors (contentEditable elements)
- Configurable OpenAI model selection
- Uses GitHub PAT token for authentication
- Clean visual feedback with static progress indicator
- Preserves cursor position and text selection after processing
- Error handling with user feedback
- Settings persistence across browser sessions

## Setup Instructions

1. Install the extension in Edge
2. Click on the extension icon in the toolbar
3. Enter your GitHub PAT token (must have access to OpenAI API)
4. Select your preferred LLM model (default: gpt-4o-mini)
5. Save your settings

## Usage

1. Select any text in an editable field
2. Right-click to open the context menu
3. Click "Charismatize 🪄"
4. Wait for the AI to process your text (a "⌛ Processing..." indicator will appear)
5. The selected text will be automatically replaced with a more charismatic version

## Development

```bash
npm install   # Install dependencies
```

### Project Structure

- `background.js` - Service worker handling context menu and AI processing
- `content.js` - Content script managing text selection and UI feedback
- `popup.js` - Settings management and user interface logic
- `popup.html` - Settings page UI
- `manifest.json` - Extension configuration

### Loading in Edge

1. Go to edge://extensions/
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the extension directory

### Technical Notes

- Uses Chrome Extension Manifest V3
- Implements efficient text replacement for both plain text and rich text editors
- Handles asynchronous API communication with proper error handling
- Maintains state consistency during text processing
- Uses modern JavaScript features and follows best practices

## Browser Compatibility

- Microsoft Edge (primary support)
- Compatible with Chromium-based browsers