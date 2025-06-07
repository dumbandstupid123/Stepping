// NextStep Healthcare Assistant Frontend with Voice Support
class NextStepApp {
    constructor() {
        this.apiBase = '';
        this.currentCategory = null;
        this.isLoading = false;
        
        // Voice functionality
        this.isVoiceMode = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.isSpeaking = false;
        this.selectedVoice = null;
        this.voiceTone = 'professional'; // Default tone
        this.voiceTones = {
            professional: {
                rate: 1.0,
                pitch: 0.9,
                volume: 0.85,
                preferredVoices: ['Microsoft David', 'Google US English', 'Alex', 'Daniel'],
                description: 'Clear, authoritative, and clinical'
            },
            caring: {
                rate: 0.9,
                pitch: 1.0,
                volume: 0.8,
                preferredVoices: ['Microsoft Zira', 'Google US English Female', 'Samantha', 'Fiona'],
                description: 'Warm, empathetic, and supportive'
            },
            calm: {
                rate: 0.8,
                pitch: 0.95,
                volume: 0.75,
                preferredVoices: ['Samantha', 'Microsoft Zira', 'Fiona', 'Moira'],
                description: 'Slow, peaceful, and therapeutic'
            },
            friendly: {
                rate: 1.1,
                pitch: 1.1,
                volume: 0.9,
                preferredVoices: ['Microsoft Zira', 'Google US English Female', 'Samantha', 'Karen'],
                description: 'Collaborative, approachable, and engaging'
            },
            energetic: {
                rate: 1.2,
                pitch: 1.15,
                volume: 0.9,
                preferredVoices: ['Karen', 'Google US English Female', 'Samantha', 'Microsoft Zira'],
                description: 'Fast, motivational, and encouraging'
            },
            gentle: {
                rate: 0.85,
                pitch: 1.05,
                volume: 0.7,
                preferredVoices: ['Samantha', 'Fiona', 'Microsoft Zira', 'Moira'],
                description: 'Soft, reassuring, and nurturing'
            }
        };
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupVoiceRecognition();
        this.setupTextToSpeech();
        this.loadInitialData();
    }
    
    initializeElements() {
        // Get DOM elements
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.chatContainer = document.getElementById('chat-container');
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.clearChatButton = document.getElementById('clear-chat');
        this.statusText = document.getElementById('status-text');
        this.categoriesList = document.getElementById('categories-list');
        this.totalResources = document.getElementById('total-resources');
        this.totalCategories = document.getElementById('total-categories');
        this.statsContent = document.getElementById('stats-content');
        
        // Voice elements
        this.voiceModeBtn = document.getElementById('voice-mode-btn');
        this.voiceStatus = document.getElementById('voice-status');
        this.voiceIndicator = document.getElementById('voice-indicator');
        this.voiceText = document.getElementById('voice-text');
        this.voiceControls = document.getElementById('voice-controls');
        this.voiceListenBtn = document.getElementById('voice-listen-btn');
        this.voiceStopBtn = document.getElementById('voice-stop-btn');
        this.voiceExitBtn = document.getElementById('voice-exit-btn');
        this.textInputWrapper = document.getElementById('text-input-wrapper');
        this.inputSuggestions = document.getElementById('input-suggestions');
        this.voiceToneSelector = document.getElementById('voice-tone-selector');
        this.voiceToneSelect = document.getElementById('voice-tone-select');
    }
    
    setupEventListeners() {
        // Send message events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Clear chat
        this.clearChatButton.addEventListener('click', () => this.clearChat());
        
        // Voice mode events
        this.voiceModeBtn.addEventListener('click', () => this.toggleVoiceMode());
        this.voiceListenBtn.addEventListener('click', () => this.startListening());
        this.voiceStopBtn.addEventListener('click', () => this.stopSpeaking());
        this.voiceExitBtn.addEventListener('click', () => this.exitVoiceMode());
        
        // Voice tone change
        this.voiceToneSelect.addEventListener('change', (e) => this.changeVoiceTone(e.target.value));
        
        // Suggestion pills
        document.querySelectorAll('.suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                const text = suggestion.getAttribute('data-text');
                if (this.isVoiceMode) {
                    this.processVoiceInput(text);
                } else {
                    this.messageInput.value = text;
                    this.sendMessage();
                }
            });
        });
        
        // Input focus effects
        this.messageInput.addEventListener('focus', () => {
            document.querySelector('.input-wrapper').classList.add('focused');
        });
        
        this.messageInput.addEventListener('blur', () => {
            document.querySelector('.input-wrapper').classList.remove('focused');
        });
    }
    
    setupVoiceRecognition() {
        // Check for speech recognition support
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateVoiceStatus('listening', 'Listening... speak now');
                this.voiceIndicator.classList.add('listening');
            };
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.processVoiceInput(transcript);
            };
            
            this.recognition.onerror = (event) => {
                this.handleVoiceError(`Speech recognition error: ${event.error}`);
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                this.voiceIndicator.classList.remove('listening');
                if (this.isVoiceMode && !this.isSpeaking) {
                    this.updateVoiceStatus('ready', 'Tap to speak again');
                }
            };
        } else {
            this.showVoiceUnsupported();
        }
    }
    
    setupTextToSpeech() {
        // Wait for voices to load with multiple attempts
        this.voiceLoadAttempts = 0;
        this.maxVoiceLoadAttempts = 10;
        
        this.loadVoicesWithRetry();
    }
    
    loadVoicesWithRetry() {
        const voices = this.synthesis.getVoices();
        console.log(`Voice load attempt ${this.voiceLoadAttempts + 1}: Found ${voices.length} voices`);
        
        if (voices.length === 0 && this.voiceLoadAttempts < this.maxVoiceLoadAttempts) {
            this.voiceLoadAttempts++;
            
            // Try multiple methods to load voices
            if (this.voiceLoadAttempts === 1) {
                // Method 1: Standard event listener
                this.synthesis.addEventListener('voiceschanged', () => {
                    console.log('Voices changed event fired');
                    this.selectBestVoice();
                });
            }
            
            // Method 2: Periodic checking
            setTimeout(() => {
                this.loadVoicesWithRetry();
            }, 100 * this.voiceLoadAttempts); // Increasing delay
            
        } else if (voices.length > 0) {
            console.log('Voices loaded successfully, selecting best voice');
            this.selectBestVoice();
        } else {
            console.warn('No voices available after maximum attempts');
            this.selectedVoice = null;
        }
    }
    
    selectBestVoice() {
        const voices = this.synthesis.getVoices();
        console.log(`Selecting from ${voices.length} available voices`);
        
        if (voices.length === 0) {
            console.warn('No voices available for selection');
            this.selectedVoice = null;
            return;
        }
        
        // Log all available voices for debugging
        voices.forEach((voice, index) => {
            console.log(`Voice ${index}: ${voice.name} (${voice.lang}) ${voice.localService ? '[Local]' : '[Remote]'}`);
        });
        
        const toneConfig = this.voiceTones[this.voiceTone];
        let selectedVoice = null;
        
        // Priority 1: Try preferred voices (non-local first)
        for (const preferredName of toneConfig.preferredVoices) {
            selectedVoice = voices.find(v => v.name.includes(preferredName) && !v.localService);
            if (selectedVoice) {
                console.log(`Selected preferred remote voice: ${selectedVoice.name}`);
                break;
            }
        }
        
        // Priority 2: Try preferred voices (local)
        if (!selectedVoice) {
            for (const preferredName of toneConfig.preferredVoices) {
                selectedVoice = voices.find(v => v.name.includes(preferredName));
                if (selectedVoice) {
                    console.log(`Selected preferred local voice: ${selectedVoice.name}`);
                    break;
                }
            }
        }
        
        // Priority 3: Try any English voice (non-local first)
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith('en') && !v.localService);
            if (selectedVoice) {
                console.log(`Selected English remote voice: ${selectedVoice.name}`);
            }
        }
        
        // Priority 4: Try any English voice (local)
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith('en'));
            if (selectedVoice) {
                console.log(`Selected English local voice: ${selectedVoice.name}`);
            }
        }
        
        // Priority 5: Use first available voice
        if (!selectedVoice && voices.length > 0) {
            selectedVoice = voices[0];
            console.log(`Using first available voice: ${selectedVoice.name}`);
        }
        
        this.selectedVoice = selectedVoice;
        
        if (!this.selectedVoice) {
            console.error('Could not select any voice for speech synthesis');
        } else {
            console.log(`Final voice selection: ${this.selectedVoice.name} (${this.selectedVoice.lang})`);
        }
    }
    
    toggleVoiceMode() {
        if (!this.recognition) {
            this.showVoiceUnsupported();
            return;
        }
        
        this.isVoiceMode = !this.isVoiceMode;
        
        if (this.isVoiceMode) {
            this.enterVoiceMode();
        } else {
            this.exitVoiceMode();
        }
    }
    
    async enterVoiceMode() {
        this.isVoiceMode = true;
        
        // Update UI
        this.voiceModeBtn.classList.add('active');
        this.voiceModeBtn.innerHTML = '<i class="fas fa-microphone-slash"></i><span>Exit Voice Mode</span>';
        
        this.textInputWrapper.style.display = 'none';
        this.voiceControls.style.display = 'flex';
        this.voiceToneSelector.style.display = 'flex';
        this.inputSuggestions.style.display = 'flex';
        
        this.updateVoiceStatus('ready', 'Voice mode active - tap "Tap to Speak" to start');
        
        // Add welcome voice message with delay to ensure voice setup is complete
        setTimeout(() => {
            this.addVoiceWelcomeMessage();
        }, 500);
    }
    
    exitVoiceMode() {
        this.isVoiceMode = false;
        
        // Stop any ongoing speech
        this.stopSpeaking();
        this.stopListening();
        
        // Update UI
        this.voiceModeBtn.classList.remove('active');
        this.voiceModeBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Start Voice Conversation</span>';
        
        this.textInputWrapper.style.display = 'flex';
        this.voiceControls.style.display = 'none';
        this.voiceToneSelector.style.display = 'none';
        
        this.updateVoiceStatus('inactive', 'Click to start talking');
        this.voiceIndicator.className = 'voice-indicator';
    }
    
    startListening() {
        if (!this.recognition || this.isListening || this.isSpeaking) return;
        
        try {
            this.recognition.start();
        } catch (error) {
            this.handleVoiceError('Could not start speech recognition');
        }
    }
    
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    processVoiceInput(transcript) {
        this.updateVoiceStatus('processing', 'Processing your request...');
        
        // Add user voice message
        this.addUserVoiceMessage(transcript);
        
        // Send to assistant
        this.sendVoiceMessage(transcript);
    }
    
    async sendVoiceMessage(message) {
        this.setLoading(true);
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    category: this.currentCategory
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.addAssistantVoiceMessage(data);
            
        } catch (error) {
            console.error('Error sending voice message:', error);
            this.handleVoiceError('Sorry, I had trouble processing your request. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }
    
    speakText(text, onEnd = null, isRetry = false) {
        return new Promise((resolve, reject) => {
            if (!this.synthesis) {
                console.warn('Speech synthesis not available');
                reject(new Error('Speech synthesis not supported'));
                return;
            }
            
            if (this.isSpeaking && !isRetry) {
                console.log('Already speaking, ignoring new request');
                resolve();
                return;
            }
            
            // Clean and validate text
            const cleanText = this.cleanTextForSpeech(text);
            if (!cleanText) {
                console.warn('Empty or invalid text provided to speakText');
                resolve();
                return;
            }
            
            // Stop any current speech
            this.stopSpeaking();
            
            // Wait for speech to stop before starting new one
            setTimeout(() => {
                this.performSpeech(cleanText, onEnd, isRetry, resolve, reject);
            }, isRetry ? 200 : 50);
        });
    }
    
    cleanTextForSpeech(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        
        // Remove or replace problematic characters
        let cleanText = text
            .replace(/[^\w\s.,!?;:()\-'"/]/g, ' ') // Remove special chars except basic punctuation
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim();
        
        // Limit length to prevent browser issues
        if (cleanText.length > 1000) {
            cleanText = cleanText.substring(0, 997) + '...';
        }
        
        return cleanText;
    }
    
    performSpeech(text, onEnd, isRetry, resolve, reject) {
        try {
            // Ensure we have a voice
            if (!this.selectedVoice) {
                console.warn('No voice selected, attempting to select voice');
                this.selectBestVoice();
                if (!this.selectedVoice) {
                    console.error('No voice available for speech synthesis');
                    reject(new Error('No voice available'));
                    return;
                }
            }
            
            const utterance = new SpeechSynthesisUtterance(text);
            const toneConfig = this.voiceTones[this.voiceTone];
            
            // Set voice and parameters with validation
            utterance.voice = this.selectedVoice;
            utterance.rate = this.clampValue(toneConfig.rate, 0.1, 2.0, 1.0);
            utterance.pitch = this.clampValue(toneConfig.pitch, 0.0, 2.0, 1.0);
            utterance.volume = this.clampValue(toneConfig.volume, 0.0, 1.0, 0.8);
            
            console.log(`Speech parameters - Voice: ${utterance.voice.name}, Rate: ${utterance.rate}, Pitch: ${utterance.pitch}, Volume: ${utterance.volume}`);
            
            // Set up event handlers
            utterance.onstart = () => {
                this.isSpeaking = true;
                this.updateVoiceStatus('speaking', `NextStep is speaking (${this.voiceTone} tone)...`);
                this.voiceIndicator.classList.add('speaking');
                console.log('Speech synthesis started successfully');
            };
            
            utterance.onend = () => {
                this.isSpeaking = false;
                this.voiceIndicator.classList.remove('speaking');
                
                if (this.isVoiceMode) {
                    this.updateVoiceStatus('ready', 'Tap to speak again');
                }
                
                console.log('Speech synthesis ended successfully');
                if (onEnd) onEnd();
                resolve();
            };
            
            utterance.onerror = (event) => {
                console.error('Speech synthesis error details:', {
                    error: event.error,
                    type: event.type,
                    voice: utterance.voice?.name,
                    text: text.substring(0, 50) + '...'
                });
                
                this.isSpeaking = false;
                this.voiceIndicator.classList.remove('speaking');
                
                // Handle specific error types
                if (event.error === 'canceled' || event.error === 'interrupted') {
                    console.log('Speech was cancelled or interrupted');
                    resolve(); // Not really an error
                    return;
                }
                
                // Try recovery for other errors
                if (!isRetry && (event.error === 'synthesis-failed' || event.error === 'voice-unavailable')) {
                    console.log('Attempting speech recovery...');
                    
                    // Try to reselect voice and retry
                    setTimeout(() => {
                        this.selectBestVoice();
                        this.speakText(text, onEnd, true)
                            .then(resolve)
                            .catch(reject);
                    }, 500);
                    return;
                }
                
                // Final error handling
                this.handleVoiceError(`Speech failed: ${event.error}`, false);
                reject(new Error(`Speech synthesis failed: ${event.error}`));
            };
            
            // Start speech synthesis
            this.synthesis.speak(utterance);
            console.log('Speech utterance queued:', text.substring(0, 50) + '...');
            
        } catch (error) {
            console.error('Failed to create or queue speech:', error);
            this.isSpeaking = false;
            this.voiceIndicator.classList.remove('speaking');
            this.handleVoiceError('Failed to start speech', false);
            reject(error);
        }
    }
    
    clampValue(value, min, max, defaultValue) {
        if (typeof value !== 'number' || isNaN(value)) {
            return defaultValue;
        }
        return Math.max(min, Math.min(max, value));
    }
    
    stopSpeaking() {
        if (this.synthesis) {
            try {
                this.synthesis.cancel();
                console.log('Speech synthesis cancelled');
            } catch (error) {
                console.warn('Error cancelling speech:', error);
            }
            
            this.isSpeaking = false;
            this.voiceIndicator.classList.remove('speaking');
            
            if (this.isVoiceMode) {
                this.updateVoiceStatus('ready', 'Tap to speak again');
            }
        }
    }
    
    updateVoiceStatus(state, text) {
        this.voiceText.textContent = text;
        
        // Update indicator
        this.voiceIndicator.className = 'voice-indicator';
        if (state !== 'inactive') {
            this.voiceIndicator.classList.add(state);
        }
    }
    
    addVoiceWelcomeMessage() {
        const welcomeText = "Hello! I'm NextStep, your healthcare navigator. Voice mode is now active. Tap 'Tap to Speak' and tell me what kind of help you need.";
        
        // Ensure we have a voice selected
        if (!this.selectedVoice) {
            this.selectBestVoice();
        }
        
        if (this.selectedVoice) {
            this.speakText(welcomeText)
                .then(() => {
                    console.log('Welcome message spoken successfully');
                })
                .catch((error) => {
                    console.warn('Welcome message speech failed:', error);
                    this.updateVoiceStatus('ready', 'Voice mode active - tap "Tap to Speak" to start');
                });
        } else {
            console.warn('No voice available for welcome message');
            this.updateVoiceStatus('ready', 'Voice mode active - tap "Tap to Speak" to start');
        }
    }
    
    addUserVoiceMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-message voice-message';
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-microphone"></i>
            </div>
            <div class="message-content">
                <p>${this.escapeHtml(message)}</p>
            </div>
        `;
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addAssistantVoiceMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'assistant-message speaking-response';
        
        let resourcesHtml = '';
        if (data.top_resources && data.top_resources.length > 0) {
            resourcesHtml = `
                <div class="resources-grid">
                    ${data.top_resources.map(resource => `
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-name">${this.escapeHtml(resource.name)}</div>
                                <div class="resource-score">${Math.round(resource.score * 100)}% match</div>
                            </div>
                            <div class="resource-info">
                                ${resource.address ? `
                                    <div class="resource-info-item">
                                        <i class="fas fa-map-marker-alt"></i>
                                        <span>${this.escapeHtml(resource.address)}</span>
                                    </div>
                                ` : ''}
                                ${resource.phone ? `
                                    <div class="resource-info-item">
                                        <i class="fas fa-phone"></i>
                                        <span>${this.escapeHtml(resource.phone)}</span>
                                    </div>
                                ` : ''}
                                <div class="resource-info-item">
                                    <i class="fas fa-tag"></i>
                                    <span>${this.escapeHtml(resource.category)}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-heart-pulse"></i>
            </div>
            <div class="message-content">
                <div class="assistant-response">${this.formatResponse(data.response)}</div>
                ${resourcesHtml}
                ${data.resources_found > 0 ? `
                    <div class="resources-summary">
                        <small><i class="fas fa-info-circle"></i> Found ${data.resources_found} relevant resources</small>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Speak the response with better error handling
        if (data.response && data.response.trim()) {
            this.speakText(data.response)
                .then(() => {
                    console.log('Assistant response spoken successfully');
                })
                .catch((error) => {
                    console.warn('Assistant response speech failed:', error);
                    // Remove speaking animation if speech failed
                    messageDiv.classList.remove('speaking-response');
                });
        }
    }
    
    handleVoiceError(errorMessage, shouldSpeak = false) {
        console.error('Voice error:', errorMessage);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'voice-error';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${errorMessage}`;
        
        this.chatContainer.appendChild(errorDiv);
        this.scrollToBottom();
        
        this.updateVoiceStatus('error', 'Error occurred - tap to try again');
        
        // Only try to speak error message if explicitly requested and not already in error state
        if (shouldSpeak && !this.isSpeaking) {
            // Use a timeout to avoid cascading errors
            setTimeout(() => {
                this.speakText(`I'm sorry, there was an issue. Please try again.`, null, true);
            }, 500);
        }
    }
    
    showVoiceUnsupported() {
        const unsupportedDiv = document.createElement('div');
        unsupportedDiv.className = 'voice-unsupported';
        unsupportedDiv.innerHTML = `
            <i class="fas fa-microphone-slash"></i>
            Voice conversation is not supported in your browser. Please use a modern browser like Chrome, Edge, or Safari for voice features.
        `;
        
        this.voiceStatus.appendChild(unsupportedDiv);
        this.voiceModeBtn.disabled = true;
        this.voiceModeBtn.style.opacity = '0.5';
    }
    
    async loadInitialData() {
        try {
            // Check health and load categories/stats
            await Promise.all([
                this.checkHealth(),
                this.loadCategories(),
                this.loadStats()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.updateStatus('Offline', false);
        }
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('Online', true);
            } else {
                this.updateStatus('Issues Detected', false);
            }
        } catch (error) {
            this.updateStatus('Offline', false);
            throw error;
        }
    }
    
    async loadCategories() {
        try {
            const response = await fetch('/categories');
            const data = await response.json();
            
            this.renderCategories(data.categories);
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }
    
    async loadStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();
            
            this.renderStats(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }
    
    renderCategories(categories) {
        this.categoriesList.innerHTML = categories.map(category => `
            <div class="category-item" data-category="${category.id}">
                <span class="category-icon">${category.icon}</span>
                <span class="category-name">${category.name}</span>
            </div>
        `).join('');
        
        // Add click listeners
        this.categoriesList.querySelectorAll('.category-item').forEach(item => {
            item.addEventListener('click', () => {
                const categoryId = item.getAttribute('data-category');
                this.selectCategory(categoryId, item);
            });
        });
    }
    
    renderStats(stats) {
        this.totalResources.textContent = stats.total_resources;
        this.totalCategories.textContent = stats.categories;
        
        // Update timestamp
        const timestamp = new Date(stats.last_updated).toLocaleTimeString();
        const timestampEl = document.getElementById('stats-timestamp');
        if (timestampEl) {
            timestampEl.textContent = `Updated: ${timestamp}`;
        }
    }
    
    selectCategory(categoryId, element) {
        // Remove active class from all categories
        this.categoriesList.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Toggle category selection
        if (this.currentCategory === categoryId) {
            this.currentCategory = null;
        } else {
            this.currentCategory = categoryId;
            element.classList.add('active');
        }
    }
    
    updateStatus(text, isOnline) {
        this.statusText.textContent = text;
        const statusDot = document.querySelector('.status-dot');
        
        if (isOnline) {
            statusDot.style.background = '#10b981';
        } else {
            statusDot.style.background = '#ef4444';
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;
        
        // Add user message to chat
        this.addUserMessage(message);
        
        // Clear input
        this.messageInput.value = '';
        
        // Show loading
        this.setLoading(true);
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    category: this.currentCategory
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.addAssistantMessage(data);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addAssistantMessage({
                response: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment, or call 211 for immediate assistance.",
                resources_found: 0,
                top_resources: []
            });
        } finally {
            this.setLoading(false);
        }
    }
    
    addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-message';
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
                <p>${this.escapeHtml(message)}</p>
            </div>
        `;
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addAssistantMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'assistant-message';
        
        let resourcesHtml = '';
        if (data.top_resources && data.top_resources.length > 0) {
            resourcesHtml = `
                <div class="resources-grid">
                    ${data.top_resources.map(resource => `
                        <div class="resource-card">
                            <div class="resource-header">
                                <div class="resource-name">${this.escapeHtml(resource.name)}</div>
                                <div class="resource-score">${Math.round(resource.score * 100)}% match</div>
                            </div>
                            <div class="resource-info">
                                ${resource.address ? `
                                    <div class="resource-info-item">
                                        <i class="fas fa-map-marker-alt"></i>
                                        <span>${this.escapeHtml(resource.address)}</span>
                                    </div>
                                ` : ''}
                                ${resource.phone ? `
                                    <div class="resource-info-item">
                                        <i class="fas fa-phone"></i>
                                        <span>${this.escapeHtml(resource.phone)}</span>
                                    </div>
                                ` : ''}
                                <div class="resource-info-item">
                                    <i class="fas fa-tag"></i>
                                    <span>${this.escapeHtml(resource.category)}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-heart-pulse"></i>
            </div>
            <div class="message-content">
                <div class="assistant-response">${this.formatResponse(data.response)}</div>
                ${resourcesHtml}
                ${data.resources_found > 0 ? `
                    <div class="resources-summary">
                        <small><i class="fas fa-info-circle"></i> Found ${data.resources_found} relevant resources</small>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatResponse(response) {
        // Convert markdown-style formatting to HTML
        return response
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.*)$/, '<p>$1</p>');
    }
    
    clearChat() {
        // Stop any speaking
        this.stopSpeaking();
        
        // Remove all messages except welcome
        const messages = this.chatContainer.querySelectorAll('.user-message, .assistant-message:not(.welcome-message .assistant-message), .voice-error');
        messages.forEach(message => message.remove());
        
        // Reset category selection
        this.currentCategory = null;
        this.categoriesList.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Reset voice mode if active
        if (this.isVoiceMode) {
            this.updateVoiceStatus('ready', 'Voice mode active - tap "Tap to Speak" to start');
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        this.sendButton.disabled = loading;
        
        if (loading) {
            this.loadingOverlay.classList.add('show');
            this.sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        } else {
            this.loadingOverlay.classList.remove('show');
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }, 100);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    changeVoiceTone(tone) {
        this.voiceTone = tone;
        this.selectBestVoice(); // Re-select voice based on new tone
        
        // Update UI with tone description
        const toneConfig = this.voiceTones[tone];
        this.updateVoiceStatus('ready', `Voice tone: ${toneConfig.description}`);
        
        // Test the new voice tone with better error handling
        if (this.isVoiceMode) {
            const testMessage = `Voice tone changed to ${tone}. ${toneConfig.description}.`;
            this.speakText(testMessage)
                .then(() => {
                    console.log(`Voice tone test successful: ${tone}`);
                })
                .catch((error) => {
                    console.warn(`Voice tone test failed: ${tone}`, error);
                    this.updateVoiceStatus('ready', `Voice tone set to: ${toneConfig.description}`);
                });
        }
        
        console.log(`Voice tone changed to: ${tone}`, toneConfig);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.nextStepApp = new NextStepApp();
});

// Add some nice interactions
document.addEventListener('DOMContentLoaded', () => {
    // Add typing indicator effect
    let typingTimeout;
    const messageInput = document.getElementById('message-input');
    
    messageInput.addEventListener('input', () => {
        clearTimeout(typingTimeout);
        
        // Show typing indicator (if you want to add one)
        typingTimeout = setTimeout(() => {
            // Hide typing indicator
        }, 1000);
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (window.nextStepApp && !window.nextStepApp.isVoiceMode) {
                messageInput.focus();
            }
        }
        
        // Spacebar to start listening in voice mode
        if (e.code === 'Space' && window.nextStepApp && window.nextStepApp.isVoiceMode) {
            e.preventDefault();
            window.nextStepApp.startListening();
        }
        
        // Escape to clear category selection or exit voice mode
        if (e.key === 'Escape') {
            if (window.nextStepApp) {
                if (window.nextStepApp.isVoiceMode) {
                    window.nextStepApp.exitVoiceMode();
                } else {
                    const activeCategory = document.querySelector('.category-item.active');
                    if (activeCategory) {
                        activeCategory.classList.remove('active');
                        window.nextStepApp.currentCategory = null;
                    }
                }
            }
        }
    });
    
    // Add loading states for better UX
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            button.style.transform = 'scale(0.98)';
            setTimeout(() => {
                button.style.transform = '';
            }, 150);
        });
    });
}); 