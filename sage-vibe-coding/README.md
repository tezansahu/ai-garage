# SAGE - Study Aid Generation Engine

Transform any online educational resource into personalized study materials with AI-powered tools.

![SAGE Banner](https://img.shields.io/badge/AI-Powered-blue) ![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red) ![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Overview

SAGE (Study Aid Generation Engine) is an AI-powered exam preparation tool that transforms any educational URL (blog posts, articles, study guides) into comprehensive study materials including:

- **📝 Study Guides** - Key concepts, short answer questions, and essay prompts
- **🃏 Flashcards** - Interactive practice cards with customizable difficulty
- **✍️ Quizzes** - Multiple-choice tests with instant feedback and scoring

## ✨ Features

### URL Content Extraction
- Paste any educational URL and automatically scrape main content
- Powered by **Firecrawl API** for clean content extraction
- Validates URLs and handles common errors
- Displays word count and content preview

### Study Guide Generator
- Automatically identifies 5-8 key concepts from source material
- Creates 10 short answer questions with answers
- Generates 5 essay-type questions for deeper thinking
- Clean, organized markdown formatting
- Copy-to-clipboard functionality

### Flashcard Generator
- Create 10-30 interactive flashcards
- Three difficulty levels:
  - **Easy**: Basic definitions and facts
  - **Medium**: Conceptual understanding
  - **Hard**: Application and synthesis
- Flip animation on click
- Track mastered cards
- Shuffle option for varied practice
- Navigation controls

### Quiz Generator
- 10 multiple-choice questions
- Customizable difficulty levels
- Instant feedback with explanations
- Progress tracking and scoring
- Detailed question review after completion
- Performance messages based on score
- Retake option with shuffled questions

## 🚀 Getting Started

### Prerequisites

You'll need API keys for:
1. **Firecrawl API** - For web scraping ([Get it here](https://www.firecrawl.dev/))
2. **Azure AI Foundry** - For GPT-4o-mini access ([Get it here](https://ai.azure.com/))

### Quick Start (No Setup Required!)

1. **Clone and Open**
   ```bash
   git clone https://github.com/yourusername/study-ai.git
   cd study-ai
   open index.html  # or just double-click index.html
   ```

2. **Enter API Keys via UI**
   
   When you first open SAGE, a configuration modal will appear automatically. Simply enter your:
   - Firecrawl API Key
   - Azure AI API Key  
   - Azure AI Endpoint URL
   
   Your credentials are stored securely in your browser's localStorage and never sent anywhere except to the respective APIs.

   You can also click the **⚙️ Settings** button in the header to reconfigure at any time.

### Alternative: Manual Configuration (Optional)

If you prefer to configure via code:

1. **Copy the template**
   ```bash
   cp config.template.js config.js
   ```

2. **Edit `config.js`** and add your API keys:
   
   ```javascript
   const CONFIG = {
       firecrawl: {
           apiKey: 'your_firecrawl_api_key_here',
           endpoint: 'https://api.firecrawl.dev/v1/scrape'
       },
       azureAI: {
           apiKey: 'your_azure_api_key_here',
           endpoint: 'your_azure_endpoint_here',
           model: 'gpt-4o-mini'
       }
   };
   ```

3. **Open in Browser**
   
   ```bash
   open index.html
   ```

**Note:** `config.js` is git-ignored, so your keys won't be accidentally committed.

### Configuration Storage

SAGE uses a smart configuration system:

1. **Checks for `config.js` file** - If present and valid, uses those credentials
2. **Falls back to localStorage** - Credentials entered via the UI modal are saved locally
3. **Prompts user if needed** - Shows a modal to collect credentials if none found

**Benefits:**
- ✅ Works out-of-the-box on GitHub Pages (users enter their own keys)
- ✅ Credentials stored securely in browser localStorage
- ✅ No accidental key commits to git
- ✅ Easy reconfiguration via Settings button

### For GitHub Pages Deployment

SAGE is designed to work seamlessly on GitHub Pages without exposing your API keys:

1. **Push to GitHub** - Just push your code (without `config.js`)
2. **Enable Pages** - Settings → Pages → Source: main branch
3. **Users configure themselves** - Each user enters their own API keys via the modal

When visitors open your deployed app, they'll be prompted to enter their own API credentials, which are stored in their browser only.

**For single-user deployment:** You can still use the UI modal to enter your keys - they'll persist in localStorage across sessions.

## 📖 Usage Guide

### Step 1: Enter a URL
1. Paste any educational URL into the input field
2. Or click one of the sample URL chips
3. Click "Extract Content" to scrape the page

### Step 2: Choose a Study Tool
After successful content extraction, choose from:
- **Study Guide** - Comprehensive overview with questions
- **Flashcards** - Interactive practice cards
- **Quiz** - Test your knowledge

### Step 3: Customize & Generate
- For **Flashcards**: Select difficulty and number of cards (10-30)
- For **Quiz**: Select difficulty level
- Click generate and wait 15-30 seconds for AI processing

### Step 4: Study!
- **Study Guide**: Read, copy, or print your materials
- **Flashcards**: Click to flip, navigate with arrows, mark as mastered
- **Quiz**: Select answers, get instant feedback, review your performance

## 🛠️ Technical Details

### Technology Stack
- **Frontend**: HTML5, CSS3 (CSS Grid, Flexbox), Vanilla JavaScript (ES6+)
- **APIs**: 
  - Firecrawl API for web scraping
  - Azure AI Foundry (GPT-4o-mini) for content generation
- **Hosting**: GitHub Pages (static site)
- **Fonts**: Google Fonts (Inter, Poppins)

### File Structure
```
study-ai/
├── index.html          # Main application structure
├── styles.css          # Complete styling and design system
├── app.js              # Main application logic
├── utils.js            # Helper functions and API calls
├── config.js           # API configuration (add your keys here)
├── README.md           # This file
├── .gitignore          # Prevents committing API keys
└── references/
    └── study-ai-prd.md # Product requirements document
```

### Browser Compatibility
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Requires JavaScript enabled

## 🔧 Configuration Options

Edit `config.js` to customize:

```javascript
app: {
    maxContentLength: 10000,  // Max characters from scraped content
    urlTimeout: 30000,        // Timeout for URL scraping (ms)
    minContentWords: 100      // Minimum words required
}
```

## 🎨 Design System

### Color Palette
- **Primary**: Modern blue gradient (#4F46E5 → #7C3AED)
- **Success**: Green (#10B981)
- **Error**: Red (#EF4444)
- **Background**: Soft white/light gray (#F9FAFB)

### Typography
- **Headings**: Poppins (Bold, 600-700 weight)
- **Body**: Inter (Regular, 400 weight)

### Responsive Design
Mobile-first approach with breakpoints at:
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## 🐛 Troubleshooting

### Content Extraction Fails
- **Check URL**: Ensure it starts with http:// or https://
- **Try different source**: Some sites block scrapers or use heavy JavaScript
- **Check API key**: Verify your Firecrawl API key is correct
- **Rate limits**: You may have exceeded API quota

### AI Generation Fails
- **Check Azure endpoint**: Ensure your endpoint URL is correct
- **Verify API key**: Confirm your Azure AI API key is valid
- **Content length**: Very long articles may exceed token limits
- **Network issues**: Check your internet connection

### Flashcards/Quiz Not Displaying
- **Check console**: Open browser developer tools (F12) for errors
- **JSON parsing**: AI may have returned invalid JSON format
- **Try again**: Click generate again, AI responses can vary

### Sample URLs Not Working
- **External sites**: Some sites may be temporarily down or changed
- **Use your own**: Try educational blogs or Wikipedia articles
- **Content length**: Ensure the page has sufficient text content

## 📚 API Documentation

### Firecrawl API
- **Endpoint**: `https://api.firecrawl.dev/v1/scrape`
- **Method**: POST
- **Headers**: 
  - `Authorization: Bearer YOUR_API_KEY`
  - `Content-Type: application/json`
- **Documentation**: https://docs.firecrawl.dev/

### Azure AI Foundry
- **Model**: GPT-4o-mini
- **Documentation**: https://learn.microsoft.com/en-us/azure/ai-services/
- **Endpoint format**: Custom per deployment

## 🎓 Educational Context

SAGE demonstrates how AI can transform and enhance content for learning:
- Real-world API integrations
- Modern web development with vanilla JavaScript
- Practical applications of AI in education

## 🔐 Security & Privacy

### For Personal/Demo Use
- API keys can be hardcoded in `config.js` (for personal use only)
- No user data is stored
- Content not persisted beyond browser session
- URL history not tracked

### For Production Use
**⚠️ IMPORTANT**: Do NOT expose API keys in client-side code for production!

Implement these security measures:
1. **Backend proxy** for API calls
2. **Environment variables** for API keys
3. **Rate limiting** per user
4. **Input sanitization** to prevent XSS
5. **Content filtering** for inappropriate sources
6. **Privacy policy** if storing any user data

## 🤝 Contributing

This is a workshop project, but improvements are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - feel free to use this project for educational purposes.

## 🙏 Credits

- **Built with**: GitHub Copilot (vibe-coded!)
- **APIs**: Firecrawl, Azure AI Foundry
- **Fonts**: Google Fonts (Inter, Poppins)
- **Icons**: Unicode emojis

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the browser console for error messages

---

**SAGE - Study Aid Generation Engine**

*Transform your study materials. Study smarter, not harder!* 🚀
