# Product Requirements Document (PRD)
## SAGE - Study Aid Generation Engine  

---

## 📋 Document Information

**Product Name:** SAGE - Study Aid Generation Engine  
**Version:** 1.0  
**Date:** October 26, 2025  
**Purpose:** Educational Tool  
**Tech Stack:** HTML, CSS, JavaScript, Azure AI Foundry (GPT-4o-mini), Firecrawl API  
**Deployment:** GitHub Pages (Static Site)

---

## 🎯 Product Overview

### Vision Statement
An AI-powered exam preparation tool that transforms any online study resource into personalized study materials—study guides, flashcards, and quizzes—with customizable difficulty levels.

### Core Value Proposition
Students can paste any educational URL (blog posts, articles, study guides) and instantly generate comprehensive study materials tailored to their learning needs, powered by AI.

---

## 👥 Target User Persona

**Primary User: High School Student**
- Age: 14-16 years (10th grade)
- Tech-savvy: Familiar with ChatGPT/Copilot basics
- Pain Points:
  - Too much content to study, needs summarization
  - Difficulty creating effective study materials
  - Wants varied practice formats (flashcards, quizzes, questions)
  - Limited time for exam preparation
- Goals:
  - Quick comprehension of study materials
  - Self-testing and knowledge retention
  - Flexible difficulty levels for progressive learning

---

## ✨ Key Features & Requirements

### Feature 1: URL Input & Content Extraction

**Description:** Users input a URL to any educational resource, which is automatically scraped and processed.

**Requirements:**
- **Input Field:**
  - Single text input accepting valid URLs
  - URL validation (must start with http:// or https://)
  - Clear placeholder text: "Paste your study resource URL here (e.g., blog post, article, notes)"
  - Character limit: 2048 characters
  
- **Content Extraction:**
  - Integration with **Firecrawl API** for web scraping
  - Extract main text content (ignore ads, navigation, footers)
  - Handle common website structures (blogs, articles, documentation)
  - Display loading indicator during scraping (estimated 3-10 seconds)
  - Error handling for:
    - Invalid URLs
    - Inaccessible pages (403, 404, 500 errors)
    - Timeout (>30 seconds)
    - Content too short (<100 words)
  
- **Success State:**
  - Show extracted content preview (first 200 words)
  - Display word count of extracted content
  - Show success message: "Content loaded successfully! Choose a study tool below."
  - Enable study tool options

**API Integration:**
- **Firecrawl API Endpoint:** `https://api.firecrawl.dev/v1/scrape`
- **Method:** POST
- **Required Headers:** 
  - `Authorization: Bearer YOUR_FIRECRAWL_API_KEY`
  - `Content-Type: application/json`
- **Request Body:**
```json
{
  "url": "user_provided_url",
  "formats": ["markdown"],
  "onlyMainContent": true
}
```
- **Response Format:** Returns markdown text of main content

---

### Feature 2: Study Guide Generator

**Description:** Generates a comprehensive study guide with key concepts, short answer questions, and essay prompts.

**Requirements:**

**UI Elements:**
- "Generate Study Guide" button
- Appears after successful content extraction
- Loading state while AI generates (estimated 15-30 seconds)

**Output Format:**
1. **Key Concepts Section:**
   - 5-8 main concepts extracted from source
   - Each concept includes:
     - Concept title (bold)
     - 2-3 sentence explanation in simple language
     - Formatted as collapsible/expandable cards

2. **Short Answer Questions (10 questions):**
   - Questions testing understanding of key concepts
   - Range from recall to application level
   - Answer key provided below (initially hidden, toggle to reveal)
   - Answers: 1-2 sentences each

3. **Essay-Type Questions (5 questions):**
   - Higher-order thinking questions
   - Require synthesis, analysis, or evaluation
   - No answers provided (for practice)
   - Include guidance: "Aim for 200-300 words"

**Display Format:**
- Tabbed or sectioned layout for easy navigation
- Copy-to-clipboard button for entire study guide
- Print-friendly formatting
- Download as PDF option (stretch goal)

**LLM Prompt Structure:**
```
You are an expert educator creating study materials for 10th-grade students.

SOURCE CONTENT:
[Extracted content from Firecrawl]

TASK:
Generate a comprehensive study guide with the following sections:

1. KEY CONCEPTS (5-8 concepts)
   - Identify the main ideas from the source
   - For each concept, provide:
     * A clear title
     * A 2-3 sentence explanation using simple language
     * Avoid jargon; use analogies where helpful

2. SHORT ANSWER QUESTIONS (10 questions)
   - Create questions that test understanding of the key concepts
   - Mix question types: definitions, explanations, applications, examples
   - Provide concise answers (1-2 sentences each)
   - Format as:
     Q1: [Question]
     A1: [Answer]

3. ESSAY-TYPE QUESTIONS (5 questions)
   - Create thought-provoking questions requiring synthesis/analysis
   - Questions should require 200-300 word responses
   - Cover different aspects of the content
   - NO answers needed

FORMAT:
Return the output in clean markdown format with clear section headers.
```

**Azure AI Integration:**
- **Model:** GPT-4o-mini via Azure AI Foundry
- **Endpoint:** Custom Azure endpoint (provided in workshop)
- **Max Tokens:** 2000
- **Temperature:** 0.7 (balanced creativity)

---

### Feature 3: Flashcard Generator

**Description:** Creates interactive, customizable flashcards for active recall practice.

**Requirements:**

**UI Elements:**
- "Generate Flashcards" button
- Difficulty selector dropdown:
  - Easy (basic definitions and facts)
  - Medium (concepts requiring understanding)
  - Hard (application and synthesis questions)
- Number of flashcards slider: 10-30 cards (default: 15)
- Loading state during generation

**Flashcard Functionality:**
- **Card Structure:**
  - Front: Question/Prompt
  - Back: Answer/Explanation
  - Flip animation on click/tap
  - Swipe or arrow navigation between cards
  
- **Interactive Features:**
  - Click card to flip
  - Previous/Next buttons
  - Progress indicator: "Card 3 of 15"
  - Shuffle option
  - "Mark as mastered" toggle (visual indicator)
  - Counter showing mastered vs. remaining cards

- **Display Modes:**
  - Single card view (default)
  - Grid view (all cards at once, smaller size)
  - Study mode (auto-advance after 5 seconds)

**Difficulty Level Behavior:**
- **Easy:** Simple definitions, direct facts, one-step recall
- **Medium:** Conceptual understanding, "explain how/why" questions
- **Hard:** Application scenarios, multi-step reasoning, edge cases

**LLM Prompt Structure:**
```
You are creating study flashcards for a 10th-grade student.

SOURCE CONTENT:
[Extracted content from Firecrawl]

DIFFICULTY LEVEL: [Easy/Medium/Hard]
NUMBER OF CARDS: [10-30]

TASK:
Generate [NUMBER] flashcards based on the source content at [DIFFICULTY] level.

DIFFICULTY GUIDELINES:
- EASY: Basic definitions, key terms, simple facts, direct recall
- MEDIUM: Conceptual questions, "explain how/why", relationships between ideas
- HARD: Application problems, scenarios, "what would happen if", synthesis questions

FORMAT:
For each flashcard, provide:
- FRONT: The question/prompt (concise, clear)
- BACK: The answer/explanation (2-4 sentences)

Ensure variety in question types. Make questions engaging and thought-provoking.

Return output in JSON format:
[
  {
    "front": "Question text",
    "back": "Answer text"
  },
  ...
]
```

**Azure AI Integration:**
- **Model:** GPT-4o-mini via Azure AI Foundry
- **Max Tokens:** 1500
- **Temperature:** 0.6 (slightly more focused)

---

### Feature 4: Quiz Generator

**Description:** Creates an interactive multiple-choice quiz with instant feedback and scoring.

**Requirements:**

**UI Elements:**
- "Generate Quiz" button
- Difficulty selector dropdown: Easy / Medium / Hard
- Quiz configuration:
  - Number of questions: Fixed at 10 MCQs
  - Difficulty level selector
- Loading state during generation

**Quiz Functionality:**

**Question Display:**
- One question at a time (card-based layout)
- Question number indicator: "Question 3 of 10"
- Progress bar showing completion
- 4 multiple choice options (A, B, C, D)
- Radio buttons or clickable option cards

**Answer Submission:**
- "Submit Answer" button (enabled after selection)
- Instant feedback after submission:
  - Correct: Green highlight, checkmark, "+1 point"
  - Incorrect: Red highlight, show correct answer in green
  - Brief explanation (1-2 sentences) for why answer is correct
- "Next Question" button appears after submission
- Cannot change answer after submission

**Quiz End Screen:**
- Final score: "You scored 7/10 (70%)"
- Performance message:
  - 90-100%: "Excellent! You've mastered this topic! 🎉"
  - 70-89%: "Great job! You have a solid understanding. 👍"
  - 50-69%: "Good effort! Review the concepts and try again. 📚"
  - Below 50%: "Keep practicing! Study the material and retake the quiz. 💪"
- Question review section:
  - List all questions with user's answer and correct answer
  - Color-coded (green for correct, red for incorrect)
- Buttons:
  - "Retake Quiz" (regenerate with different questions)
  - "Generate New Quiz" (with new difficulty)
  - "Back to Home"

**Difficulty Level Behavior:**
- **Easy:** Straightforward recall, obvious wrong answers
- **Medium:** Requires understanding, plausible distractors
- **Hard:** Application-based, subtle differences between options

**LLM Prompt Structure:**
```
You are creating a multiple-choice quiz for a 10th-grade student.

SOURCE CONTENT:
[Extracted content from Firecrawl]

DIFFICULTY LEVEL: [Easy/Medium/Hard]
NUMBER OF QUESTIONS: 10

TASK:
Generate 10 multiple-choice questions based on the source content at [DIFFICULTY] level.

DIFFICULTY GUIDELINES:
- EASY: Direct recall, one obvious correct answer, clearly wrong distractors
- MEDIUM: Conceptual understanding, plausible distractors, requires careful thought
- HARD: Application/analysis questions, subtle differences between options, challenging distractors

REQUIREMENTS FOR EACH QUESTION:
- Clear, concise question stem
- 4 options (A, B, C, D)
- Only ONE correct answer
- Plausible distractors (wrong options that seem reasonable)
- Brief explanation (1-2 sentences) for why the correct answer is right

Ensure variety:
- Mix of question types (definitions, applications, scenarios)
- Cover different parts of the source content
- Avoid trivial or trick questions

Return output in JSON format:
[
  {
    "question": "Question text",
    "options": {
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    },
    "correct_answer": "A",
    "explanation": "Brief explanation of why this is correct"
  },
  ...
]
```

**Azure AI Integration:**
- **Model:** GPT-4o-mini via Azure AI Foundry
- **Max Tokens:** 1800
- **Temperature:** 0.5 (more deterministic)

---

## 🎨 UI/UX Requirements

### Design System

**Color Palette:**
- Primary: Modern blue gradient (#4F46E5 → #7C3AED)
- Secondary: Soft purple (#A78BFA)
- Success: Green (#10B981)
- Error: Red (#EF4444)
- Warning: Amber (#F59E0B)
- Background: Soft white/light gray (#F9FAFB)
- Card Background: White (#FFFFFF)
- Text: Dark gray (#1F2937)
- Borders: Light gray (#E5E7EB)

**Typography:**
- Headings: Poppins/Inter (Bold, 600-700 weight)
- Body: Inter/System UI (Regular, 400 weight)
- Code/Monospace: Fira Code (if showing any syntax)
- Font Sizes:
  - H1: 32px
  - H2: 24px
  - H3: 20px
  - Body: 16px
  - Small: 14px

**Spacing:**
- Container max-width: 1200px
- Section padding: 60px vertical, 20px horizontal
- Card padding: 24px
- Button padding: 12px 24px
- Element gaps: 16px standard

**Components:**

1. **Landing/Home Page:**
   - Hero section with app title and tagline
   - Clear value proposition
   - URL input prominently featured
   - Sample URL suggestions as clickable chips
   - Simple 3-step process illustration:
     1. Paste URL
     2. Choose tool
     3. Study smarter!

2. **Buttons:**
   - Primary: Solid gradient with subtle hover lift
   - Secondary: Outlined with hover fill
   - Disabled state: Grayed out, no pointer
   - Loading state: Spinner inside button, text changes to "Loading..."

3. **Cards:**
   - Soft shadow: `box-shadow: 0 4px 6px rgba(0,0,0,0.1)`
   - Rounded corners: 12px border-radius
   - Hover state: Slight lift with increased shadow
   - Padding: 24px

4. **Loading States:**
   - Skeleton screens for content loading
   - Spinner with message: "Extracting content..." / "Generating study guide..." / etc.
   - Progress indicator for long operations

5. **Input Fields:**
   - Clean borders with focus state (blue glow)
   - Clear error states (red border + error message)
   - Placeholder text in gray
   - Icons inside inputs where appropriate

6. **Navigation:**
   - Sticky header with app logo/title
   - Breadcrumb or back button for navigation
   - Tool selector tabs after content loaded

7. **Animations:**
   - Smooth transitions (0.3s ease)
   - Card flip animation for flashcards
   - Fade-in for content loading
   - Subtle hover effects
   - Progress bar animations

**Responsive Design:**
- Mobile-first approach
- Breakpoints:
  - Mobile: < 640px
  - Tablet: 640px - 1024px
  - Desktop: > 1024px
- Stack elements vertically on mobile
- Touch-friendly button sizes (min 44px height)
- Readable font sizes on all devices

**Accessibility:**
- Semantic HTML elements
- ARIA labels for interactive elements
- Keyboard navigation support
- Sufficient color contrast (WCAG AA)
- Focus indicators on interactive elements
- Alt text for any images/icons

---

## 🔧 Technical Architecture

### Technology Stack

**Frontend:**
- **HTML5:** Semantic structure
- **CSS3:** Modern styling (Flexbox, Grid, custom properties)
- **Vanilla JavaScript (ES6+):** Core functionality, no frameworks
- **Optional:** Tailwind CSS for rapid styling (via CDN)

**APIs & Services:**
- **Firecrawl API:** Web scraping
- **Azure AI Foundry (GPT-4o-mini):** AI content generation
- **GitHub Pages:** Static site hosting

### File Structure
```
exam-prep-app/
├── index.html              # Main application file
├── styles.css              # Styles (or inline if using Tailwind)
├── app.js                  # Main application logic
├── config.js               # API keys and configuration
├── utils.js                # Helper functions
├── README.md               # Setup and usage instructions
└── .gitignore              # Ignore config.js with API keys
```

**Note:** For workshop demo, API keys will be provided. For production, implement environment variables or backend proxy.

### API Integration Details

**Firecrawl API:**
```javascript
async function scrapeContent(url) {
  const response = await fetch('https://api.firecrawl.dev/v1/scrape', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_FIRECRAWL_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      url: url,
      formats: ['markdown'],
      onlyMainContent: true
    })
  });
  
  const data = await response.json();
  return data.markdown; // Returns extracted content
}
```

**Azure AI Foundry (GPT-4o-mini):**
```javascript
async function callAzureAI(prompt, systemMessage) {
  const response = await fetch('YOUR_AZURE_ENDPOINT', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'api-key': 'YOUR_AZURE_API_KEY'
    },
    body: JSON.stringify({
      messages: [
        { role: 'system', content: systemMessage },
        { role: 'user', content: prompt }
      ],
      max_tokens: 2000,
      temperature: 0.7
    })
  });
  
  const data = await response.json();
  return data.choices[0].message.content;
}
```

### State Management
- Use JavaScript objects to store:
  - Extracted content
  - Current tool (study guide / flashcards / quiz)
  - Quiz state (current question, score, answers)
  - Flashcard state (current card, mastered cards)
- Implement using closure pattern or simple global state object

### Error Handling Strategy
- Try-catch blocks for all API calls
- User-friendly error messages:
  - "Unable to access that URL. Please check the link and try again."
  - "Content extraction failed. Try a different source."
  - "AI generation error. Please try again."
- Fallback UI for failed states
- Retry mechanism for transient failures

---

## 📊 Success Metrics

**For Workshop Demo:**
- Successfully scrapes content from 3+ different website types
- Generates all three content types (study guide, flashcards, quiz) without errors
- Demonstrates difficulty level variations clearly
- Students can complete one full workflow (URL → Quiz) in < 3 minutes
- "Wow factor" achieved (positive verbal reactions)

**For Production Use:**
- 90%+ successful content extractions
- < 20 second average generation time
- Positive student feedback on content quality
- Students report improved study efficiency

---

## 🚀 Development Phases

### Phase 1: Foundation (MVP)
**Deliverables:**
- URL input + validation
- Firecrawl integration
- Basic content preview
- Study guide generation (basic formatting)
- Simple UI with core styling

**Estimated Vibe-Coding Time:** 45-60 minutes

### Phase 2: Enhanced Features
**Deliverables:**
- Flashcard generator with flip animation
- Quiz functionality with scoring
- Difficulty level customization
- Improved UI/UX (cards, animations)

**Estimated Vibe-Coding Time:** 30-45 minutes

### Phase 3: Polish & Edge Cases
**Deliverables:**
- Error handling refinement
- Loading states and skeletons
- Responsive design optimization
- Copy/export features
- Sample URLs and help text

**Estimated Vibe-Coding Time:** 20-30 minutes

**Total Estimated Development Time:** 1.5 - 2.5 hours of vibe-coding

---

## ⚠️ Constraints & Limitations

### Technical Constraints
- **No Backend:** All processing in browser, APIs called client-side
- **API Keys Exposed:** Keys visible in client code (okay for demo, not production)
- **Static Hosting:** GitHub Pages limitations (no server-side processing)
- **Rate Limits:** Firecrawl and Azure APIs have rate limits
- **Content Length:** Very long articles may exceed token limits

### Content Constraints
- Firecrawl may fail on:
  - JavaScript-heavy sites (SPAs without SSR)
  - Paywall-protected content
  - Sites blocking scrapers
  - Dynamic content requiring authentication
- AI may produce:
  - Occasional inaccuracies (hallucinations)
  - Inconsistent difficulty levels
  - Questions not perfectly aligned with content

### Browser Constraints
- Requires modern browser (Chrome/Firefox/Safari latest versions)
- JavaScript must be enabled
- Stable internet connection required
- CORS issues if APIs don't allow browser requests (may need proxy)

---

## 🔐 Security & Privacy Considerations

### For Workshop Demo:
- API keys hardcoded in config (acceptable for controlled demo)
- No user data stored
- Content not persisted beyond session
- URL history not tracked

### For Production Deployment:
- **Must implement:**
  - Backend proxy for API calls
  - Environment variables for keys
  - Rate limiting per user
  - Input sanitization (XSS prevention)
  - Content filtering (inappropriate sources)
  - Privacy policy if storing any data

---

## 📚 Documentation Requirements

### README.md Contents:
1. Project description
2. Features list
3. Setup instructions:
   - Clone repository
   - Add API keys to config.js
   - Open index.html in browser
4. Usage guide with screenshots
5. API documentation links
6. Troubleshooting common issues
7. Credits and license

### In-App Help:
- Tooltip on URL input: "Paste a link to any educational article or blog post"
- FAQ section:
  - What types of URLs work?
  - How accurate are the AI-generated materials?
  - Can I save my study materials?
  - What if the URL doesn't work?

---

## 🎓 Educational Context (Workshop Use)

### Demo Talking Points:
1. **Input Phase:** "Watch how quickly we can extract content from any webpage"
2. **AI Generation:** "The AI is now reading the entire article and creating custom study materials"
3. **Study Guide:** "Notice how it breaks down complex concepts into simple explanations"
4. **Flashcards:** "See how difficulty levels change the question complexity"
5. **Quiz:** "Instant feedback helps you learn from mistakes"

### Student Takeaways:
- AI can transform content, not just create it
- Natural language prompts can generate structured output
- APIs enable powerful integrations without complex backends
- Modern web apps can be built with just HTML/CSS/JS

---

## 🎯 Out of Scope (For v1.0)

**Features NOT included in initial version:**
- User accounts / authentication
- Saving study materials to database
- Collaborative study features
- PDF/document upload (only URLs)
- Spaced repetition algorithms
- Progress tracking over time
- Social sharing features
- Custom prompt templates
- Offline mode
- Mobile native apps
- Integration with learning management systems (LMS)

These features can be considered for future iterations based on user feedback.

---

## 📋 Acceptance Criteria

### Must-Have (P0):
✅ Successfully scrape content from 5 sample educational URLs  
✅ Generate study guide with all three sections  
✅ Generate flashcards at 3 difficulty levels  
✅ Generate quiz with instant feedback and scoring  
✅ Responsive design works on mobile and desktop  
✅ Error messages display for common failures  
✅ Loading states show during async operations  
✅ App deployable to GitHub Pages without errors  

### Should-Have (P1):
✅ Smooth animations and transitions  
✅ Flashcard flip interaction  
✅ Quiz progress indicator  
✅ Content preview after scraping  
✅ Sample URL suggestions  
✅ Copy-to-clipboard functionality  

### Nice-to-Have (P2):
✅ Dark mode toggle  
✅ Export study guide as PDF  
✅ Keyboard shortcuts for navigation  
✅ Study guide sectional navigation  
✅ Quiz review detailed breakdown  

---

## 🚦 Launch Checklist

**Pre-Demo:**
- [ ] Test with 10+ different URLs from various sources
- [ ] Verify API keys work and have sufficient quota
- [ ] Test on multiple browsers (Chrome, Firefox, Safari)
- [ ] Test on mobile device
- [ ] Ensure GitHub Pages deployment works
- [ ] Prepare sample URLs in advance (backup for demo)
- [ ] Screenshot examples for presentation slides
- [ ] Have offline demo ready (screen recording backup)

**Demo Day:**
- [ ] Test internet connectivity at venue
- [ ] Load app before students arrive
- [ ] Have 3 pre-tested URLs ready
- [ ] Brief volunteers on technical troubleshooting
- [ ] Monitor API rate limits during workshop

**Post-Demo:**
- [ ] Collect student feedback
- [ ] Document any bugs discovered
- [ ] Share GitHub repo with students
- [ ] Create video tutorial for future reference

---

## 📞 Support & Resources

**Firecrawl Documentation:** https://docs.firecrawl.dev/  
**Azure AI Foundry Docs:** https://learn.microsoft.com/en-us/azure/ai-services/  
**GitHub Pages Guide:** https://docs.github.com/en/pages  

**Workshop Contact:**
- Technical Issues: [Workshop Volunteer Team]
- API Key Issues: [Workshop Organizer]
- Content Questions: [Facilitator]

---

*This PRD is a living document and will be updated based on development progress and stakeholder feedback.*