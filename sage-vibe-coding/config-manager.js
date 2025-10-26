// ============================================
// Configuration Manager
// ============================================
// Handles loading, validating, and storing API configuration
// Prompts user via modal if configuration is missing or invalid

const ConfigManager = {
    config: null,
    isConfigured: false,
    
    /**
     * Initialize configuration
     * Tries to load from config.js, falls back to localStorage, then prompts user
     */
    async init() {
        console.log('🔧 Initializing configuration...');
        
        // Try to load from config.js file
        if (typeof CONFIG !== 'undefined') {
            console.log('📄 Found config.js file');
            if (this.validateConfig(CONFIG)) {
                this.config = CONFIG;
                this.isConfigured = true;
                this.saveToLocalStorage();
                console.log('✅ Configuration loaded from config.js');
                return true;
            } else {
                console.warn('⚠️ config.js found but invalid');
            }
        }
        
        // Try to load from localStorage
        const storedConfig = this.loadFromLocalStorage();
        if (storedConfig && this.validateConfig(storedConfig)) {
            this.config = storedConfig;
            this.isConfigured = true;
            console.log('✅ Configuration loaded from localStorage');
            return true;
        }
        
        // No valid configuration found - prompt user
        console.log('❌ No valid configuration found - prompting user');
        await this.showConfigModal();
        return this.isConfigured;
    },
    
    /**
     * Validate configuration object
     */
    validateConfig(config) {
        if (!config) return false;
        
        const errors = [];
        
        // Check Firecrawl API key
        if (!config.firecrawl?.apiKey || config.firecrawl.apiKey.trim() === '') {
            errors.push('Firecrawl API key is missing');
        }
        
        // Check Azure AI API key
        if (!config.azureAI?.apiKey || config.azureAI.apiKey.trim() === '') {
            errors.push('Azure AI API key is missing');
        }
        
        // Check Azure AI endpoint
        if (!config.azureAI?.endpoint || config.azureAI.endpoint.trim() === '') {
            errors.push('Azure AI endpoint is missing');
        }
        
        // Validate endpoint URL format
        if (config.azureAI?.endpoint && !config.azureAI.endpoint.startsWith('https://')) {
            errors.push('Azure AI endpoint must start with https://');
        }
        
        if (errors.length > 0) {
            console.warn('⚠️ Configuration validation errors:', errors);
            return false;
        }
        
        return true;
    },
    
    /**
     * Save configuration to localStorage
     */
    saveToLocalStorage() {
        try {
            localStorage.setItem('sage_config', JSON.stringify(this.config));
            console.log('💾 Configuration saved to localStorage');
        } catch (error) {
            console.error('Failed to save configuration:', error);
        }
    },
    
    /**
     * Load configuration from localStorage
     */
    loadFromLocalStorage() {
        try {
            const stored = localStorage.getItem('sage_config');
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (error) {
            console.error('Failed to load configuration from localStorage:', error);
        }
        return null;
    },
    
    /**
     * Clear stored configuration
     */
    clearConfiguration() {
        try {
            localStorage.removeItem('sage_config');
            this.config = null;
            this.isConfigured = false;
            console.log('🗑️ Configuration cleared');
        } catch (error) {
            console.error('Failed to clear configuration:', error);
        }
    },
    
    /**
     * Show configuration modal to user
     */
    showConfigModal() {
        return new Promise((resolve) => {
            const modal = document.getElementById('config-modal');
            const overlay = document.getElementById('config-modal-overlay');
            
            if (!modal || !overlay) {
                console.error('Configuration modal not found in DOM');
                resolve(false);
                return;
            }
            
            // Pre-fill from localStorage if available
            const storedConfig = this.loadFromLocalStorage();
            if (storedConfig) {
                document.getElementById('firecrawl-key-input').value = storedConfig.firecrawl?.apiKey || '';
                document.getElementById('azure-key-input').value = storedConfig.azureAI?.apiKey || '';
                document.getElementById('azure-endpoint-input').value = storedConfig.azureAI?.endpoint || '';
            }
            
            // Show modal
            modal.style.display = 'block';
            overlay.style.display = 'block';
            document.body.style.overflow = 'hidden';
            
            // Clear any previous errors
            this.hideConfigError();
            
            // Handle save button
            const saveBtn = document.getElementById('save-config-btn');
            const handleSave = () => {
                const firecrawlKey = document.getElementById('firecrawl-key-input').value.trim();
                const azureKey = document.getElementById('azure-key-input').value.trim();
                const azureEndpoint = document.getElementById('azure-endpoint-input').value.trim();
                
                // Create config object
                const newConfig = {
                    firecrawl: {
                        apiKey: firecrawlKey,
                        endpoint: 'https://api.firecrawl.dev/v1/scrape'
                    },
                    azureAI: {
                        apiKey: azureKey,
                        endpoint: azureEndpoint,
                        model: 'gpt-4o-mini'
                    },
                    app: {
                        maxContentLength: 10000,
                        urlTimeout: 30000,
                        minContentWords: 100
                    }
                };
                
                // Validate
                if (!this.validateConfig(newConfig)) {
                    this.showConfigError('Please fill in all required fields with valid values.');
                    return;
                }
                
                // Save configuration
                this.config = newConfig;
                this.isConfigured = true;
                this.saveToLocalStorage();
                
                // Hide modal
                this.hideConfigModal();
                
                // Clean up event listener
                saveBtn.removeEventListener('click', handleSave);
                
                console.log('✅ Configuration saved successfully');
                resolve(true);
            };
            
            saveBtn.addEventListener('click', handleSave);
            
            // Handle Enter key in inputs
            const inputs = modal.querySelectorAll('input');
            inputs.forEach(input => {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        handleSave();
                    }
                });
            });
        });
    },
    
    /**
     * Hide configuration modal
     */
    hideConfigModal() {
        const modal = document.getElementById('config-modal');
        const overlay = document.getElementById('config-modal-overlay');
        
        if (modal) modal.style.display = 'none';
        if (overlay) overlay.style.display = 'none';
        document.body.style.overflow = 'auto';
    },
    
    /**
     * Show error in configuration modal
     */
    showConfigError(message) {
        const errorElement = document.getElementById('config-modal-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    },
    
    /**
     * Hide error in configuration modal
     */
    hideConfigError() {
        const errorElement = document.getElementById('config-modal-error');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    },
    
    /**
     * Get current configuration
     */
    getConfig() {
        if (!this.isConfigured) {
            console.error('Configuration not initialized. Call init() first.');
            return null;
        }
        return this.config;
    },
    
    /**
     * Check if configuration is valid and ready
     */
    isReady() {
        return this.isConfigured && this.config !== null;
    },
    
    /**
     * Open settings modal to reconfigure
     */
    openSettings() {
        this.showConfigModal();
    }
};

// Make it globally accessible
if (typeof window !== 'undefined') {
    window.ConfigManager = ConfigManager;
}
