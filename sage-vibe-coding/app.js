// ============================================
// Application State
// ============================================

const appState = {
    extractedContent: '',
    currentUrl: '',
    currentTool: null,
    flashcards: [],
    currentCardIndex: 0,
    masteredCards: new Set(),
    quiz: {
        questions: [],
        currentQuestionIndex: 0,
        score: 0,
        userAnswers: [],
        answered: false
    }
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Initializing SAGE (Study Aid Generation Engine)...');
    
    // Initialize configuration manager
    const configReady = await ConfigManager.init();
    
    if (!configReady) {
        console.error('❌ Failed to initialize configuration');
        return;
    }
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('✅ SAGE initialized successfully!');
});

function setupEventListeners() {
    // Settings button
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            ConfigManager.openSettings();
        });
    }
    // URL Input
    const scrapeBtn = document.getElementById('scrape-btn');
    const urlInput = document.getElementById('url-input');
    
    if (scrapeBtn) {
        scrapeBtn.addEventListener('click', handleScrapeContent);
    }
    
    if (urlInput) {
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleScrapeContent();
            }
        });
    }
    
    // Sample URL chips
    const chips = document.querySelectorAll('.chip');
    chips.forEach(chip => {
        chip.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            urlInput.value = url;
        });
    });
    
    // Tool selection buttons
    const studyGuideBtn = document.getElementById('study-guide-btn');
    const flashcardsBtn = document.getElementById('flashcards-btn');
    const quizBtn = document.getElementById('quiz-btn');
    
    if (studyGuideBtn) {
        studyGuideBtn.addEventListener('click', () => showTool('study-guide'));
    }
    if (flashcardsBtn) {
        flashcardsBtn.addEventListener('click', () => showTool('flashcards'));
    }
    if (quizBtn) {
        quizBtn.addEventListener('click', () => showTool('quiz'));
    }
    
    // Study Guide
    const copyGuideBtn = document.getElementById('copy-guide-btn');
    if (copyGuideBtn) {
        copyGuideBtn.addEventListener('click', handleCopyStudyGuide);
    }
    
    // Flashcards
    const flashcardCountSlider = document.getElementById('flashcard-count');
    const cardCountDisplay = document.getElementById('card-count-display');
    
    if (flashcardCountSlider && cardCountDisplay) {
        flashcardCountSlider.addEventListener('input', function() {
            cardCountDisplay.textContent = this.value;
        });
    }
    
    const generateFlashcardsBtn = document.getElementById('generate-flashcards-btn');
    if (generateFlashcardsBtn) {
        generateFlashcardsBtn.addEventListener('click', handleGenerateFlashcards);
    }
    
    const flipCardBtn = document.getElementById('flip-card-btn');
    const prevCardBtn = document.getElementById('prev-card-btn');
    const nextCardBtn = document.getElementById('next-card-btn');
    const shuffleBtn = document.getElementById('shuffle-btn');
    const markMasteredBtn = document.getElementById('mark-mastered-btn');
    const flashcardElement = document.getElementById('current-flashcard');
    
    if (flipCardBtn) {
        flipCardBtn.addEventListener('click', flipCard);
    }
    if (prevCardBtn) {
        prevCardBtn.addEventListener('click', () => navigateCard(-1));
    }
    if (nextCardBtn) {
        nextCardBtn.addEventListener('click', () => navigateCard(1));
    }
    if (shuffleBtn) {
        shuffleBtn.addEventListener('click', shuffleFlashcards);
    }
    if (markMasteredBtn) {
        markMasteredBtn.addEventListener('click', toggleMastered);
    }
    if (flashcardElement) {
        flashcardElement.addEventListener('click', flipCard);
    }
    
    // Quiz
    const generateQuizBtn = document.getElementById('generate-quiz-btn');
    if (generateQuizBtn) {
        generateQuizBtn.addEventListener('click', handleGenerateQuiz);
    }
    
    const submitAnswerBtn = document.getElementById('submit-answer-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    
    if (submitAnswerBtn) {
        submitAnswerBtn.addEventListener('click', handleSubmitAnswer);
    }
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', handleNextQuestion);
    }
    
    const retakeQuizBtn = document.getElementById('retake-quiz-btn');
    const newQuizBtn = document.getElementById('new-quiz-btn');
    
    if (retakeQuizBtn) {
        retakeQuizBtn.addEventListener('click', handleRetakeQuiz);
    }
    if (newQuizBtn) {
        newQuizBtn.addEventListener('click', () => showTool('quiz'));
    }
}

// ============================================
// Content Scraping
// ============================================

async function handleScrapeContent() {
    const urlInput = document.getElementById('url-input');
    const url = urlInput.value.trim();
    
    // Validate URL
    if (!url) {
        showError('url-error', 'Please enter a URL');
        return;
    }
    
    if (!isValidURL(url)) {
        showError('url-error', 'Please enter a valid URL (must start with http:// or https://)');
        return;
    }
    
    hideError('url-error');
    setButtonLoading('scrape-btn', true);
    
    // Scrape content
    const result = await scrapeContent(url);
    
    setButtonLoading('scrape-btn', false);
    
    if (result.success) {
        appState.extractedContent = result.content;
        appState.currentUrl = url; // Store the URL
        
        // Show URL and word count
        const sourceUrlElement = document.getElementById('source-url');
        const wordCountElement = document.getElementById('word-count');
        
        if (sourceUrlElement) {
            sourceUrlElement.href = url;
            sourceUrlElement.textContent = url;
        }
        
        if (wordCountElement) {
            wordCountElement.textContent = `📊 Word count: ${result.wordCount} words`;
        }
        
        // Hide hero, show preview
        hideSection('hero-section');
        showSection('preview-section');
        scrollToElement('preview-section');
    } else {
        showError('url-error', result.error || 'Failed to extract content. Please try a different URL.');
    }
}

// ============================================
// Tool Navigation
// ============================================

function showTool(toolName) {
    // Hide all content sections
    hideSection('study-guide-section');
    hideSection('flashcards-section');
    hideSection('quiz-section');
    
    appState.currentTool = toolName;
    
    // Show selected tool
    switch (toolName) {
        case 'study-guide':
            showSection('study-guide-section');
            handleGenerateStudyGuide();
            break;
        case 'flashcards':
            showSection('flashcards-section');
            // Reset flashcard config
            hideSection('flashcards-loading');
            hideSection('flashcards-display');
            document.getElementById('flashcard-config').style.display = 'block';
            break;
        case 'quiz':
            showSection('quiz-section');
            // Reset quiz config
            hideSection('quiz-loading');
            hideSection('quiz-display');
            hideSection('quiz-end');
            document.getElementById('quiz-config').style.display = 'block';
            break;
    }
    
    scrollToElement(`${toolName}-section`);
}

function backToTools() {
    showSection('preview-section');
    hideSection('study-guide-section');
    hideSection('flashcards-section');
    hideSection('quiz-section');
    scrollToElement('preview-section');
}

// ============================================
// Study Guide
// ============================================

async function handleGenerateStudyGuide() {
    const loadingElement = document.getElementById('study-guide-loading');
    const contentElement = document.getElementById('study-guide-content');
    const outputElement = document.getElementById('study-guide-output');
    
    // Show loading
    if (loadingElement) loadingElement.style.display = 'block';
    if (contentElement) contentElement.style.display = 'none';
    
    // Generate study guide
    const result = await generateStudyGuide(appState.extractedContent);
    
    // Hide loading
    if (loadingElement) loadingElement.style.display = 'none';
    
    if (result.success) {
        // Parse and display markdown
        const htmlContent = parseMarkdown(result.content);
        if (outputElement) {
            outputElement.innerHTML = htmlContent;
        }
        if (contentElement) contentElement.style.display = 'block';
    } else {
        if (outputElement) {
            outputElement.innerHTML = `<p style="color: var(--error-color);">❌ ${result.error || 'Failed to generate study guide. Please try again.'}</p>`;
        }
        if (contentElement) contentElement.style.display = 'block';
    }
}

async function handleCopyStudyGuide() {
    const outputElement = document.getElementById('study-guide-output');
    if (outputElement) {
        const text = outputElement.innerText;
        const success = await copyToClipboard(text);
        
        const btn = document.getElementById('copy-guide-btn');
        if (success && btn) {
            const originalText = btn.textContent;
            btn.textContent = '✅ Copied!';
            setTimeout(() => {
                btn.textContent = originalText;
            }, 2000);
        }
    }
}

// ============================================
// Flashcards
// ============================================

async function handleGenerateFlashcards() {
    const difficulty = document.getElementById('flashcard-difficulty').value;
    const count = parseInt(document.getElementById('flashcard-count').value);
    
    // Hide config, show loading
    document.getElementById('flashcard-config').style.display = 'none';
    document.getElementById('flashcards-loading').style.display = 'block';
    hideSection('flashcards-display');
    
    // Generate flashcards
    const result = await generateFlashcards(appState.extractedContent, difficulty, count);
    
    // Hide loading
    document.getElementById('flashcards-loading').style.display = 'none';
    
    if (result.success && result.flashcards && result.flashcards.length > 0) {
        appState.flashcards = result.flashcards;
        appState.currentCardIndex = 0;
        appState.masteredCards.clear();
        
        displayFlashcards();
        showSection('flashcards-display');
    } else {
        alert('❌ Failed to generate flashcards. Please try again.');
        document.getElementById('flashcard-config').style.display = 'block';
    }
}

function displayFlashcards() {
    const totalCards = appState.flashcards.length;
    
    // Update counters
    document.getElementById('current-card-num').textContent = appState.currentCardIndex + 1;
    document.getElementById('total-cards').textContent = totalCards;
    document.getElementById('mastered-count').textContent = appState.masteredCards.size;
    document.getElementById('remaining-count').textContent = totalCards - appState.masteredCards.size;
    
    // Update card content
    const currentCard = appState.flashcards[appState.currentCardIndex];
    document.getElementById('card-front-text').textContent = currentCard.front;
    document.getElementById('card-back-text').textContent = currentCard.back;
    
    // Reset flip state
    const flashcard = document.getElementById('current-flashcard');
    flashcard.classList.remove('flipped');
    
    // Update mastered state
    if (appState.masteredCards.has(appState.currentCardIndex)) {
        flashcard.classList.add('mastered');
    } else {
        flashcard.classList.remove('mastered');
    }
    
    // Update navigation buttons
    document.getElementById('prev-card-btn').disabled = appState.currentCardIndex === 0;
    document.getElementById('next-card-btn').disabled = appState.currentCardIndex === totalCards - 1;
}

function flipCard() {
    const flashcard = document.getElementById('current-flashcard');
    flashcard.classList.toggle('flipped');
}

function navigateCard(direction) {
    const totalCards = appState.flashcards.length;
    appState.currentCardIndex += direction;
    
    // Clamp to valid range
    if (appState.currentCardIndex < 0) appState.currentCardIndex = 0;
    if (appState.currentCardIndex >= totalCards) appState.currentCardIndex = totalCards - 1;
    
    displayFlashcards();
}

function toggleMastered() {
    const currentIndex = appState.currentCardIndex;
    
    if (appState.masteredCards.has(currentIndex)) {
        appState.masteredCards.delete(currentIndex);
    } else {
        appState.masteredCards.add(currentIndex);
    }
    
    displayFlashcards();
}

function shuffleFlashcards() {
    appState.flashcards = shuffleArray(appState.flashcards);
    appState.currentCardIndex = 0;
    appState.masteredCards.clear();
    displayFlashcards();
}

// ============================================
// Quiz
// ============================================

async function handleGenerateQuiz() {
    const difficulty = document.getElementById('quiz-difficulty').value;
    
    // Hide config, show loading
    document.getElementById('quiz-config').style.display = 'none';
    document.getElementById('quiz-loading').style.display = 'block';
    hideSection('quiz-display');
    hideSection('quiz-end');
    
    // Generate quiz
    const result = await generateQuiz(appState.extractedContent, difficulty);
    
    // Hide loading
    document.getElementById('quiz-loading').style.display = 'none';
    
    if (result.success && result.questions && result.questions.length > 0) {
        appState.quiz.questions = result.questions;
        appState.quiz.currentQuestionIndex = 0;
        appState.quiz.score = 0;
        appState.quiz.userAnswers = [];
        appState.quiz.answered = false;
        
        displayQuestion();
        showSection('quiz-display');
    } else {
        alert('❌ Failed to generate quiz. Please try again.');
        document.getElementById('quiz-config').style.display = 'block';
    }
}

function displayQuestion() {
    const currentQ = appState.quiz.questions[appState.quiz.currentQuestionIndex];
    const totalQuestions = appState.quiz.questions.length;
    
    // Update progress
    const progress = ((appState.quiz.currentQuestionIndex + 1) / totalQuestions) * 100;
    document.getElementById('quiz-progress').style.width = `${progress}%`;
    
    // Update info bar
    document.getElementById('question-number').textContent = `Question ${appState.quiz.currentQuestionIndex + 1} of ${totalQuestions}`;
    document.getElementById('quiz-score').textContent = `Score: ${appState.quiz.score}/${totalQuestions}`;
    
    // Display question
    document.getElementById('question-text').textContent = currentQ.question;
    
    // Display options
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    
    for (const [key, value] of Object.entries(currentQ.options)) {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'option';
        optionDiv.dataset.answer = key;
        optionDiv.innerHTML = `
            <span class="option-label">${key}</span>
            <span class="option-text">${value}</span>
        `;
        
        optionDiv.addEventListener('click', function() {
            if (!appState.quiz.answered) {
                // Remove previous selection
                document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
                // Add selection
                this.classList.add('selected');
                // Enable submit button
                document.getElementById('submit-answer-btn').disabled = false;
            }
        });
        
        optionsContainer.appendChild(optionDiv);
    }
    
    // Reset feedback and buttons
    document.getElementById('answer-feedback').style.display = 'none';
    document.getElementById('submit-answer-btn').style.display = 'inline-flex';
    document.getElementById('submit-answer-btn').disabled = true;
    document.getElementById('next-question-btn').style.display = 'none';
    
    appState.quiz.answered = false;
}

function handleSubmitAnswer() {
    const selectedOption = document.querySelector('.option.selected');
    if (!selectedOption) return;
    
    const userAnswer = selectedOption.dataset.answer;
    const currentQ = appState.quiz.questions[appState.quiz.currentQuestionIndex];
    const correctAnswer = currentQ.correct_answer;
    const isCorrect = userAnswer === correctAnswer;
    
    // Update score
    if (isCorrect) {
        appState.quiz.score++;
        document.getElementById('quiz-score').textContent = `Score: ${appState.quiz.score}/${appState.quiz.questions.length}`;
    }
    
    // Store answer
    appState.quiz.userAnswers.push({
        question: currentQ.question,
        userAnswer: userAnswer,
        correctAnswer: correctAnswer,
        isCorrect: isCorrect,
        explanation: currentQ.explanation
    });
    
    // Highlight correct and incorrect answers
    document.querySelectorAll('.option').forEach(opt => {
        opt.classList.add('disabled');
        if (opt.dataset.answer === correctAnswer) {
            opt.classList.add('correct');
        } else if (opt.dataset.answer === userAnswer && !isCorrect) {
            opt.classList.add('incorrect');
        }
    });
    
    // Show feedback
    const feedbackElement = document.getElementById('answer-feedback');
    feedbackElement.className = 'answer-feedback ' + (isCorrect ? 'correct' : 'incorrect');
    feedbackElement.innerHTML = `
        <strong>${isCorrect ? '✅ Correct!' : '❌ Incorrect'}</strong><br>
        ${currentQ.explanation}
    `;
    feedbackElement.style.display = 'block';
    
    // Update buttons
    document.getElementById('submit-answer-btn').style.display = 'none';
    document.getElementById('next-question-btn').style.display = 'inline-flex';
    
    appState.quiz.answered = true;
}

function handleNextQuestion() {
    appState.quiz.currentQuestionIndex++;
    
    if (appState.quiz.currentQuestionIndex < appState.quiz.questions.length) {
        displayQuestion();
    } else {
        showQuizResults();
    }
}

function showQuizResults() {
    hideSection('quiz-display');
    showSection('quiz-end');
    
    const score = appState.quiz.score;
    const total = appState.quiz.questions.length;
    const percentage = Math.round((score / total) * 100);
    
    // Display final score
    document.getElementById('final-score-text').textContent = `${score}/${total} (${percentage}%)`;
    
    // Performance message
    let message = '';
    if (percentage >= 90) {
        message = "Excellent! You've mastered this topic! 🎉";
    } else if (percentage >= 70) {
        message = "Great job! You have a solid understanding. 👍";
    } else if (percentage >= 50) {
        message = "Good effort! Review the concepts and try again. 📚";
    } else {
        message = "Keep practicing! Study the material and retake the quiz. 💪";
    }
    document.getElementById('performance-message').textContent = message;
    
    // Display review
    const reviewContainer = document.getElementById('quiz-review-container');
    reviewContainer.innerHTML = '';
    
    appState.quiz.userAnswers.forEach((answer, index) => {
        const reviewItem = document.createElement('div');
        reviewItem.className = `review-item ${answer.isCorrect ? 'correct' : 'incorrect'}`;
        
        const currentQ = appState.quiz.questions[index];
        const userAnswerText = currentQ.options[answer.userAnswer];
        const correctAnswerText = currentQ.options[answer.correctAnswer];
        
        reviewItem.innerHTML = `
            <div class="review-question"><strong>Q${index + 1}:</strong> ${answer.question}</div>
            <div class="review-answer">
                <strong>Your answer:</strong> ${answer.userAnswer}. ${userAnswerText}<br>
                ${!answer.isCorrect ? `<strong>Correct answer:</strong> ${answer.correctAnswer}. ${correctAnswerText}<br>` : ''}
                <em>${answer.explanation}</em>
            </div>
        `;
        
        reviewContainer.appendChild(reviewItem);
    });
    
    scrollToElement('quiz-end');
}

function handleRetakeQuiz() {
    // Shuffle questions
    appState.quiz.questions = shuffleArray(appState.quiz.questions);
    appState.quiz.currentQuestionIndex = 0;
    appState.quiz.score = 0;
    appState.quiz.userAnswers = [];
    appState.quiz.answered = false;
    
    hideSection('quiz-end');
    showSection('quiz-display');
    displayQuestion();
    scrollToElement('quiz-display');
}

// ============================================
// Helper: Make functions globally accessible
// ============================================

function resetToHome() {
    // Clear state
    appState.extractedContent = '';
    appState.currentUrl = '';
    appState.currentTool = null;
    
    // Clear URL input
    const urlInput = document.getElementById('url-input');
    if (urlInput) {
        urlInput.value = '';
    }
    
    // Hide all sections except hero
    hideSection('preview-section');
    hideSection('study-guide-section');
    hideSection('flashcards-section');
    hideSection('quiz-section');
    
    // Show hero section
    showSection('hero-section');
    scrollToElement('hero-section');
}

window.backToTools = backToTools;
window.resetToHome = resetToHome;
