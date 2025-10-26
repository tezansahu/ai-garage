// ============================================
// Utility Functions
// ============================================

/**
 * URL Validation
 */
function isValidURL(urlString) {
    try {
        const url = new URL(urlString);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (e) {
        return false;
    }
}

/**
 * Show error message
 */
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
}

/**
 * Hide error message
 */
function hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

/**
 * Show loading state on button
 */
function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    const btnText = button.querySelector('.btn-text');
    const btnLoader = button.querySelector('.btn-loader');
    
    if (isLoading) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'flex';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
    }
}

/**
 * Show/hide section
 */
function showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
    }
}

function hideSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'none';
    }
}

/**
 * Scroll to element smoothly
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

/**
 * Truncate text to specified length
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Count words in text
 */
function countWords(text) {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Format text for display (sanitize HTML)
 */
function sanitizeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Parse markdown to HTML (basic implementation)
 */
function parseMarkdown(markdown) {
    let html = markdown;
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    
    // Lists
    html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Line breaks - preserve single line breaks as <br>, double as paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    html = '<p>' + html + '</p>';
    
    // Clean up
    html = html.replace(/<p><h/g, '<h');
    html = html.replace(/<\/h[123]><\/p>/g, '</h3>');
    html = html.replace(/<p><ul>/g, '<ul>');
    html = html.replace(/<\/ul><\/p>/g, '</ul>');
    html = html.replace(/<br><\/p>/g, '</p>');
    html = html.replace(/<p><br>/g, '<p>');
    
    return html;
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        return false;
    }
}

/**
 * Shuffle array (Fisher-Yates algorithm)
 */
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

/**
 * Firecrawl API: Scrape content from URL
 */
async function scrapeContent(url) {
    try {
        const config = ConfigManager.getConfig();
        if (!config) {
            throw new Error('Configuration not initialized');
        }
        
        const response = await fetch(config.firecrawl.endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${config.firecrawl.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                formats: ['markdown'],
                onlyMainContent: true,
                blockAds: true,

            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const json_data = await response.json();
        
        // Extract markdown content
        let content = json_data.data.markdown || json_data.content || '';
        
        // Truncate if too long
        if (content.length > config.app.maxContentLength) {
            content = content.substring(0, config.app.maxContentLength);
        }
        
        // Check minimum word count
        const wordCount = countWords(content);
        if (wordCount < config.app.minContentWords) {
            throw new Error(`Content too short (${wordCount} words). Minimum required: ${config.app.minContentWords} words.`);
        }
        
        return {
            success: true,
            content: content,
            wordCount: wordCount
        };
    } catch (error) {
        console.error('Scraping error:', error);
        return {
            success: false,
            error: error.message || 'Failed to extract content from URL'
        };
    }
}

/**
 * Azure AI API: Call GPT-4o-mini
 */
async function callAzureAI(prompt, systemMessage, maxTokens = 2000, temperature = 0.7) {
    try {
        const config = ConfigManager.getConfig();
        if (!config) {
            throw new Error('Configuration not initialized');
        }
        
        const response = await fetch(config.azureAI.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'api-key': config.azureAI.apiKey
            },
            body: JSON.stringify({
                messages: [
                    { role: 'system', content: systemMessage },
                    { role: 'user', content: prompt }
                ],
                max_tokens: maxTokens,
                temperature: temperature
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const content = data.choices[0].message.content;
        
        return {
            success: true,
            content: content
        };
    } catch (error) {
        console.error('Azure AI error:', error);
        return {
            success: false,
            error: error.message || 'AI generation failed'
        };
    }
}

/**
 * Generate Study Guide
 */
async function generateStudyGuide(sourceContent) {
    const systemMessage = 'You are an expert educator creating comprehensive study materials.';
    
    const prompt = `You are an expert educator creating comprehensive study materials.

SOURCE CONTENT:
${sourceContent}

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
   - Format each Q&A pair with question and answer on SEPARATE lines:
     Q1: [Question]
     A1: [Answer]
     
     Q2: [Question]
     A2: [Answer]
   - Include a blank line between each Q&A pair for readability

3. ESSAY-TYPE QUESTIONS (5 questions)
   - Create thought-provoking questions requiring synthesis/analysis
   - Questions should require 200-300 word responses
   - Cover different aspects of the content
   - NO answers needed

FORMAT:
Return the output in clean markdown format with clear section headers.`;
    
    return await callAzureAI(prompt, systemMessage, 2000, 0.7);
}

/**
 * Generate Flashcards
 */
async function generateFlashcards(sourceContent, difficulty, count) {
    const systemMessage = 'You are creating study flashcards for learners.';
    
    const difficultyGuidelines = {
        'Easy': 'Basic definitions, key terms, simple facts, direct recall',
        'Medium': 'Conceptual questions, "explain how/why", relationships between ideas',
        'Hard': 'Application problems, scenarios, "what would happen if", synthesis questions'
    };
    
    const prompt = `You are creating study flashcards for learners.

SOURCE CONTENT:
${sourceContent}

DIFFICULTY LEVEL: ${difficulty}
NUMBER OF CARDS: ${count}

TASK:
Generate ${count} flashcards based on the source content at ${difficulty} level.

DIFFICULTY GUIDELINES:
- EASY: ${difficultyGuidelines['Easy']}
- MEDIUM: ${difficultyGuidelines['Medium']}
- HARD: ${difficultyGuidelines['Hard']}

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
  }
]`;
    
    const result = await callAzureAI(prompt, systemMessage, 1500, 0.6);
    
    if (result.success) {
        try {
            // Extract JSON from response (might be wrapped in markdown code blocks)
            let jsonText = result.content;
            const jsonMatch = jsonText.match(/\[[\s\S]*\]/);
            if (jsonMatch) {
                jsonText = jsonMatch[0];
            }
            const flashcards = JSON.parse(jsonText);
            return {
                success: true,
                flashcards: flashcards
            };
        } catch (error) {
            console.error('Failed to parse flashcards JSON:', error);
            return {
                success: false,
                error: 'Failed to parse flashcards data'
            };
        }
    }
    
    return result;
}

/**
 * Generate Quiz
 */
async function generateQuiz(sourceContent, difficulty) {
    const systemMessage = 'You are creating a multiple-choice quiz for learners.';
    
    const prompt = `You are creating a multiple-choice quiz for learners.

SOURCE CONTENT:
${sourceContent}

DIFFICULTY LEVEL: ${difficulty}
NUMBER OF QUESTIONS: 10

TASK:
Generate 10 multiple-choice questions based on the source content at ${difficulty} level.

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
  }
]`;

    const result = await callAzureAI(prompt, systemMessage, 1800, 0.5);
    
    if (result.success) {
        try {
            // Extract JSON from response
            let jsonText = result.content;
            const jsonMatch = jsonText.match(/\[[\s\S]*\]/);
            if (jsonMatch) {
                jsonText = jsonMatch[0];
            }
            const questions = JSON.parse(jsonText);
            return {
                success: true,
                questions: questions
            };
        } catch (error) {
            console.error('Failed to parse quiz JSON:', error);
            return {
                success: false,
                error: 'Failed to parse quiz data'
            };
        }
    }
    
    return result;
}

/**
 * Export functions for use in app.js
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        isValidURL,
        showError,
        hideError,
        setButtonLoading,
        showSection,
        hideSection,
        scrollToElement,
        truncateText,
        countWords,
        sanitizeHTML,
        parseMarkdown,
        copyToClipboard,
        shuffleArray,
        scrapeContent,
        callAzureAI,
        generateStudyGuide,
        generateFlashcards,
        generateQuiz
    };
}
