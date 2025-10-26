// ============================================
// Configuration Template
// ============================================
// This file contains the structure for API configuration.
// Copy this to config.js and add your actual API keys.

const CONFIG = {
    // Firecrawl API Configuration
    firecrawl: {
        apiKey: '',
        endpoint: 'https://api.firecrawl.dev/v1/scrape'
    },
    
    // Azure AI Foundry Configuration
    azureAI: {
        apiKey: '',
        endpoint: '',
        model: 'gpt-4o-mini'
    },
    
    // App Configuration
    app: {
        maxContentLength: 10000,
        urlTimeout: 30000,
        minContentWords: 100
    }
};
