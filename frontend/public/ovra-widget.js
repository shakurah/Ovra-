(function() {
    'use strict';
    
    // Configuration
    const DEFAULT_CONFIG = {
        apiUrl: 'http://167.99.143.136:8000',
        position: 'bottom-right',
        theme: 'auto', // auto, light, dark
        language: 'es',
        buttonColor: '#3b82f6', // Primary blue from theme
        title: 'Asistente Fiscal OVRA'
    };
    
    // Widget class
    class OVRAWidget {
        constructor(config = {}) {
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.isOpen = false;
            this.messages = [];
            this.sessionId = null;
            this.isRegistered = false;
            this.email = '';
            this.isLoading = false;
            
            this.init();
        }
        
        init() {
            this.loadFromStorage();
            this.detectTheme();
            this.createWidget();
            this.attachEventListeners();
            this.setupThemeWatcher();
        }
        
        detectTheme() {
            if (this.config.theme === 'auto') {
                this.isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            } else {
                this.isDark = this.config.theme === 'dark';
            }
        }
        
        setupThemeWatcher() {
            if (this.config.theme === 'auto') {
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                    this.isDark = e.matches;
                    this.updateTheme();
                });
            }
        }
        
        updateTheme() {
            this.container.className = `ovra-widget-container ${this.isDark ? 'dark' : 'light'}`;
        }
        
        loadFromStorage() {
            try {
                const savedEmail = localStorage.getItem('ovra_widget_email');
                const savedSession = localStorage.getItem('ovra_widget_session');
                
                if (savedEmail) {
                    this.email = savedEmail;
                    this.isRegistered = true;
                }
                
                if (savedSession) {
                    this.sessionId = savedSession;
                }
            } catch (error) {
                console.warn('Could not load from localStorage:', error);
            }
        }
        
        createWidget() {
            // Create widget container
            this.container = document.createElement('div');
            this.container.id = 'ovra-widget';
            this.container.className = `ovra-widget-container ${this.isDark ? 'dark' : 'light'}`;
            this.container.innerHTML = this.getWidgetHTML();
            
            // Add CSS
            this.addStyles();
            
            // Append to body
            document.body.appendChild(this.container);
            
            // Get elements
            this.elements = {
                button: this.container.querySelector('.ovra-button'),
                widget: this.container.querySelector('.ovra-widget'),
                closeBtn: this.container.querySelector('.ovra-close'),
                messages: this.container.querySelector('.ovra-messages'),
                input: this.container.querySelector('.ovra-input'),
                sendBtn: this.container.querySelector('.ovra-send'),
                emailForm: this.container.querySelector('.ovra-email-form'),
                emailInput: this.container.querySelector('.ovra-email-input'),
                privacyCheck: this.container.querySelector('.ovra-privacy'),
                termsCheck: this.container.querySelector('.ovra-terms'),
                registerBtn: this.container.querySelector('.ovra-register'),
                chatArea: this.container.querySelector('.ovra-chat-area')
            };
            
            this.updateUI();
        }
        
        getWidgetHTML() {
            return `
                <div class="ovra-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                </div>
                
                <div class="ovra-widget" style="display: none;">
                    <div class="ovra-header">
                        <h3>${this.config.title}</h3>
                        <button class="ovra-close">&times;</button>
                    </div>
                    
                    <div class="ovra-email-form">
                        <div class="ovra-welcome">
                            <h4>¡Bienvenido a OVRA!</h4>
                            <p>Ingresa tu email para comenzar a hacer preguntas sobre impuestos y contabilidad.</p>
                        </div>
                        
                        <input type="email" class="ovra-email-input" placeholder="tu@email.com" />
                        
                        <div class="ovra-checkboxes">
                            <label>
                                <input type="checkbox" class="ovra-privacy" />
                                <span>Acepto la <a href="/privacy" target="_blank">política de privacidad</a></span>
                            </label>
                            <label>
                                <input type="checkbox" class="ovra-terms" />
                                <span>Acepto los <a href="/terms" target="_blank">términos y condiciones</a></span>
                            </label>
                        </div>
                        
                        <button class="ovra-register">Continuar</button>
                    </div>
                    
                    <div class="ovra-chat-area" style="display: none;">
                        <div class="ovra-messages"></div>
                        
                        <div class="ovra-input-area">
                            <input type="text" class="ovra-input" placeholder="Haz tu pregunta sobre impuestos..." />
                            <button class="ovra-send">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                                </svg>
                            </button>
                        </div>
                        
                        <div class="ovra-footer">
                            <small>Powered by ARTISTING</small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        addStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .ovra-widget-container {
                    position: fixed;
                    ${this.config.position === 'bottom-left' ? 'bottom: 16px; left: 16px;' : 'bottom: 16px; right: 16px;'}
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.5;
                    --primary: 221.2 83.2% 53.3%;
                    --primary-foreground: 210 40% 98%;
                    --background: 0 0% 100%;
                    --foreground: 222.2 84% 4.9%;
                    --card: 0 0% 100%;
                    --card-foreground: 222.2 84% 4.9%;
                    --muted: 210 40% 96%;
                    --muted-foreground: 215.4 16.3% 46.9%;
                    --border: 214.3 31.8% 91.4%;
                    --input: 214.3 31.8% 91.4%;
                    --ring: 221.2 83.2% 53.3%;
                    --radius: 0.75rem;
                    transition: all 0.2s ease-in-out;
                }
                
                .ovra-widget-container.dark {
                    --background: 222.2 84% 4.9%;
                    --foreground: 210 40% 98%;
                    --card: 222.2 84% 4.9%;
                    --card-foreground: 210 40% 98%;
                    --muted: 217.2 32.6% 17.5%;
                    --muted-foreground: 215 20.2% 65.1%;
                    --border: 217.2 32.6% 17.5%;
                    --input: 217.2 32.6% 17.5%;
                    --ring: 224.3 76.3% 94.1%;
                }
                
                .ovra-button {
                    width: 56px;
                    height: 56px;
                    background: hsl(var(--foreground));
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: hsl(var(--background));
                    cursor: pointer;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
                    transition: all 0.3s ease;
                    border: none;
                }
                
                .ovra-button:hover {
                    background: hsl(var(--foreground));
                    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.16);
                    transform: translateY(-1px);
                }
                
                .ovra-widget-container.dark .ovra-button {
                    background: hsl(var(--background));
                    color: hsl(var(--foreground));
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                
                .ovra-widget-container.dark .ovra-button:hover {
                    background: hsl(var(--background));
                    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
                }
                
                .ovra-widget {
                    width: 384px;
                    height: 600px;
                    background: hsl(var(--background));
                    border-radius: calc(var(--radius) * 1.5);
                    box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.1), 0 2px 10px -2px rgba(0, 0, 0, 0.05);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    border: 1px solid hsl(var(--border));
                    transition: all 0.2s ease-in-out;
                }
                
                .ovra-widget-container.dark .ovra-widget {
                    box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.4), 0 2px 10px -2px rgba(0, 0, 0, 0.2);
                }
                
                .ovra-header {
                    padding: 16px;
                    background: hsl(var(--muted));
                    border-bottom: 1px solid hsl(var(--border));
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .ovra-header h3 {
                    margin: 0;
                    font-size: 16px;
                    font-weight: 600;
                    color: hsl(var(--foreground));
                }
                
                .ovra-close {
                    background: none;
                    border: none;
                    font-size: 20px;
                    cursor: pointer;
                    color: hsl(var(--muted-foreground));
                    padding: 4px;
                    width: 28px;
                    height: 28px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                    transition: all 0.2s ease;
                }
                
                .ovra-close:hover {
                    color: hsl(var(--foreground));
                    background: hsl(var(--muted));
                }
                
                .ovra-email-form {
                    padding: 24px;
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    background: hsl(var(--background));
                }
                
                .ovra-welcome {
                    text-align: center;
                    margin-bottom: 24px;
                }
                
                .ovra-welcome h4 {
                    margin: 0 0 8px 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: hsl(var(--foreground));
                }
                
                .ovra-welcome p {
                    margin: 0;
                    color: hsl(var(--muted-foreground));
                    font-size: 14px;
                    line-height: 1.5;
                }
                
                .ovra-email-input {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid hsl(var(--border));
                    border-radius: calc(var(--radius) * 0.5);
                    font-size: 14px;
                    margin-bottom: 16px;
                    box-sizing: border-box;
                    background: hsl(var(--background));
                    color: hsl(var(--foreground));
                    transition: border-color 0.2s ease;
                }
                
                .ovra-email-input:focus {
                    outline: none;
                    border-color: #D4AF37;
                    box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
                }
                
                .ovra-checkboxes {
                    margin-bottom: 16px;
                }
                
                .ovra-checkboxes label {
                    display: flex;
                    align-items: flex-start;
                    margin-bottom: 8px;
                    font-size: 12px;
                    color: hsl(var(--muted-foreground));
                    cursor: pointer;
                    line-height: 1.4;
                }
                
                .ovra-checkboxes input[type="checkbox"] {
                    margin-right: 8px;
                    margin-top: 2px;
                    accent-color: #D4AF37;
                }
                
                .ovra-checkboxes a {
                    color: #D4AF37;
                    text-decoration: underline;
                }
                
                .ovra-register {
                    width: 100%;
                    padding: 12px;
                    background: #D4AF37;
                    color: hsl(var(--primary-foreground));
                    border: none;
                    border-radius: calc(var(--radius) * 0.5);
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .ovra-register:hover:not(:disabled) {
                    background: hsl(var(--primary) / 0.9);
                    transform: translateY(-1px);
                }
                
                .ovra-register:disabled {
                    background: hsl(var(--muted));
                    color: hsl(var(--muted-foreground));
                    cursor: not-allowed;
                    transform: none;
                }
                
                .ovra-chat-area {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    background: hsl(var(--background));
                }
                
                .ovra-messages {
                    flex: 1;
                    padding: 16px;
                    overflow-y: auto;
                    max-height: 460px;
                    background: hsl(var(--background));
                }
                
                .ovra-messages::-webkit-scrollbar {
                    width: 6px;
                }
                
                .ovra-messages::-webkit-scrollbar-track {
                    background: hsl(var(--muted));
                }
                
                .ovra-messages::-webkit-scrollbar-thumb {
                    background: hsl(var(--muted-foreground) / 0.3);
                    border-radius: 3px;
                }
                
                .ovra-messages::-webkit-scrollbar-thumb:hover {
                    background: hsl(var(--muted-foreground) / 0.5);
                }
                
                .ovra-message {
                    margin-bottom: 16px;
                    display: flex;
                    align-items: flex-start;
                }
                
                .ovra-message.user {
                    justify-content: flex-end;
                }
                
                .ovra-message-content {
                    max-width: 80%;
                    padding: 12px 16px;
                    border-radius: calc(var(--radius) * 0.75);
                    word-wrap: break-word;
                    line-height: 1.5;
                }
                
                .ovra-message.user .ovra-message-content {
                    background: #D4AF37;
                    color: hsl(var(--primary-foreground));
                }
                
                .ovra-message.assistant .ovra-message-content {
                    background: hsl(var(--muted));
                    color: hsl(var(--foreground));
                }
                
                .ovra-input-area {
                    padding: 16px;
                    border-top: 1px solid hsl(var(--border));
                    display: flex;
                    gap: 8px;
                    background: hsl(var(--background));
                }
                
                .ovra-input {
                    flex: 1;
                    padding: 10px 12px;
                    border: 1px solid hsl(var(--border));
                    border-radius: calc(var(--radius) * 0.5);
                    font-size: 14px;
                    background: hsl(var(--background));
                    color: hsl(var(--foreground));
                    transition: border-color 0.2s ease;
                }
                
                .ovra-input:focus {
                    outline: none;
                    border-color: #D4AF37;
                    box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
                }
                
                .ovra-send {
                    padding: 10px 12px;
                    background: #D4AF37;
                    color: hsl(var(--primary-foreground));
                    border: none;
                    border-radius: calc(var(--radius) * 0.5);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                }
                
                .ovra-send:hover:not(:disabled) {
                    background: hsl(var(--primary) / 0.9);
                    transform: translateY(-1px);
                }
                
                .ovra-send:disabled {
                    background: hsl(var(--muted));
                    color: hsl(var(--muted-foreground));
                    cursor: not-allowed;
                    transform: none;
                }
                
                .ovra-footer {
                    padding: 8px 16px;
                    text-align: center;
                    color: hsl(var(--muted-foreground));
                    font-size: 12px;
                    border-top: 1px solid hsl(var(--border));
                    background: hsl(var(--background));
                }
                
                .ovra-loading {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 16px;
                    background: hsl(var(--muted));
                    border-radius: calc(var(--radius) * 0.75);
                    max-width: 80%;
                }
                
                .ovra-loading-dots {
                    display: flex;
                    gap: 4px;
                }
                
                .ovra-loading-dots div {
                    width: 8px;
                    height: 8px;
                    background: hsl(var(--muted-foreground));
                    border-radius: 50%;
                    animation: ovra-bounce 1.4s infinite ease-in-out both;
                }
                
                .ovra-loading-dots div:nth-child(1) { animation-delay: -0.32s; }
                .ovra-loading-dots div:nth-child(2) { animation-delay: -0.16s; }
                
                @keyframes ovra-bounce {
                    0%, 80%, 100% { 
                        transform: scale(0);
                        opacity: 0.5;
                    }
                    40% { 
                        transform: scale(1);
                        opacity: 1;
                    }
                }
                
                /* Citations styling */
                .ovra-citations {
                    margin-top: 8px;
                    padding-top: 8px;
                    border-top: 1px solid hsl(var(--border) / 0.3);
                    font-size: 12px;
                    opacity: 0.8;
                }
                
                .ovra-citations strong {
                    font-weight: 600;
                    display: block;
                    margin-bottom: 4px;
                }
                
                /* Responsive design */
                @media (max-width: 480px) {
                    .ovra-widget {
                        width: 100vw;
                        height: 100vh;
                        border-radius: 0;
                        ${this.config.position === 'bottom-left' ? 'left: 0;' : 'right: 0;'}
                        bottom: 0;
                    }
                    
                    .ovra-widget-container {
                        ${this.config.position === 'bottom-left' ? 'left: 0;' : 'right: 0;'}
                        bottom: 0;
                    }
                }
                
                /* Better markdown styling */
                .ovra-message-content strong {
                    font-weight: 600;
                }
                
                .ovra-message-content em {
                    font-style: italic;
                }
                
                .ovra-message-content p {
                    margin: 0 0 8px 0;
                }
                
                .ovra-message-content p:last-child {
                    margin-bottom: 0;
                }
                
                .ovra-message-content ul,
                .ovra-message-content ol {
                    margin: 8px 0;
                    padding-left: 20px;
                }
                
                .ovra-message-content li {
                    margin-bottom: 4px;
                }
            `;
            document.head.appendChild(style);
        }
        
        
        attachEventListeners() {
            this.elements.button.addEventListener('click', () => this.toggleWidget());
            this.elements.closeBtn.addEventListener('click', () => this.closeWidget());
            this.elements.registerBtn.addEventListener('click', () => this.handleRegister());
            this.elements.sendBtn.addEventListener('click', () => this.handleSendMessage());
            
            this.elements.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSendMessage();
                }
            });
            
            this.elements.emailInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleRegister();
                }
            });
            
            // Update register button state
            [this.elements.emailInput, this.elements.privacyCheck, this.elements.termsCheck].forEach(el => {
                el.addEventListener('change', () => this.updateRegisterButton());
            });
        }
        
        updateRegisterButton() {
            const email = this.elements.emailInput.value.trim();
            const privacy = this.elements.privacyCheck.checked;
            const terms = this.elements.termsCheck.checked;
            
            this.elements.registerBtn.disabled = !email || !privacy || !terms || this.isLoading;
        }
        
        toggleWidget() {
            this.isOpen = !this.isOpen;
            this.updateUI();
        }
        
        closeWidget() {
            this.isOpen = false;
            this.updateUI();
        }
        
        updateUI() {
            if (this.isOpen) {
                this.elements.button.style.display = 'none';
                this.elements.widget.style.display = 'flex';
                
                if (this.isRegistered) {
                    this.elements.emailForm.style.display = 'none';
                    this.elements.chatArea.style.display = 'flex';
                    
                    if (this.messages.length === 0) {
                        this.addMessage('assistant', '¡Hola! Soy tu asistente fiscal. ¿En qué puedo ayudarte hoy?');
                    }
                } else {
                    this.elements.emailForm.style.display = 'flex';
                    this.elements.chatArea.style.display = 'none';
                }
            } else {
                this.elements.button.style.display = 'flex';
                this.elements.widget.style.display = 'none';
            }
        }
        
        async handleRegister() {
            const email = this.elements.emailInput.value.trim();
            const privacy = this.elements.privacyCheck.checked;
            const terms = this.elements.termsCheck.checked;
            
            if (!email || !privacy || !terms) return;
            
            this.isLoading = true;
            this.elements.registerBtn.textContent = 'Registrando...';
            this.elements.registerBtn.disabled = true;
            
            try {
                const response = await fetch(`${this.config.apiUrl}/widget/register/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        privacy_accepted: privacy,
                        terms_accepted: terms,
                        source_website: window.location.origin,
                    }),
                });
                
                const data = await response.json();
                
                if (data.is_success) {
                    this.email = email;
                    this.isRegistered = true;
                    
                    try {
                        localStorage.setItem('ovra_widget_email', email);
                    } catch (error) {
                        console.warn('Could not save to localStorage:', error);
                    }
                    
                    this.updateUI();
                } else {
                    this.showError('Error al registrar el email. Por favor, verifica tu email e inténtalo de nuevo.');
                }
            } catch (error) {
                console.error('Registration error:', error);
                this.showError('Error de conexión. Por favor, inténtalo de nuevo.');
            } finally {
                this.isLoading = false;
                this.elements.registerBtn.textContent = 'Continuar';
                this.updateRegisterButton();
            }
        }
        
        async handleSendMessage() {
            const message = this.elements.input.value.trim();
            if (!message || this.isLoading) return;
            
            this.addMessage('user', message);
            this.elements.input.value = '';
            
            this.isLoading = true;
            this.elements.sendBtn.disabled = true;
            
            this.showLoadingMessage();
            
            try {
                const response = await fetch(`${this.config.apiUrl}/widget/chat/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: this.sessionId,
                        email: this.email,
                        source_website: window.location.origin,
                    }),
                });
                
                const data = await response.json();
                
                this.hideLoadingMessage();
                
                if (data.message) {
                    this.addMessage('assistant', data.message.content, data.message.metadata?.legal_references);
                    
                    if (data.conversation_id && !this.sessionId) {
                        this.sessionId = data.conversation_id;
                        try {
                            localStorage.setItem('ovra_widget_session', data.conversation_id);
                        } catch (error) {
                            console.warn('Could not save session to localStorage:', error);
                        }
                    }
                } else {
                    this.addMessage('assistant', data.message || 'Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo.');
                }
            } catch (error) {
                console.error('Chat error:', error);
                this.hideLoadingMessage();
                this.addMessage('assistant', 'Lo siento, ha ocurrido un error de conexión. Por favor, inténtalo de nuevo.');
            } finally {
                this.isLoading = false;
                this.elements.sendBtn.disabled = false;
            }
        }
        
        addMessage(role, content, citations = null) {
            const messageEl = document.createElement('div');
            messageEl.className = `ovra-message ${role}`;
            
            const contentEl = document.createElement('div');
            contentEl.className = 'ovra-message-content';
            
            if (role === 'assistant') {
                contentEl.innerHTML = this.formatMessage(content);
            } else {
                contentEl.textContent = content;
            }
            
            if (citations && citations.length > 0) {
                const citationsEl = document.createElement('div');
                citationsEl.className = 'ovra-citations';
                citationsEl.innerHTML = '<strong>Referencias:</strong>' + 
                    citations.map(c => `<div>• ${c.article} - ${c.law}</div>`).join('');
                contentEl.appendChild(citationsEl);
            }
            
            messageEl.appendChild(contentEl);
            this.elements.messages.appendChild(messageEl);
            
            this.messages.push({ role, content, citations });
            this.scrollToBottom();
        }
        
        formatMessage(content) {
            // Basic markdown-like formatting
            return content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
        }
        
        showLoadingMessage() {
            const loadingEl = document.createElement('div');
            loadingEl.className = 'ovra-message assistant';
            loadingEl.innerHTML = `
                <div class="ovra-loading">
                    <div class="ovra-loading-dots">
                        <div></div>
                        <div></div>
                        <div></div>
                    </div>
                    <span>Consultando información...</span>
                </div>
            `;
            loadingEl.id = 'ovra-loading-message';
            this.elements.messages.appendChild(loadingEl);
            this.scrollToBottom();
        }
        
        hideLoadingMessage() {
            const loadingEl = document.getElementById('ovra-loading-message');
            if (loadingEl) {
                loadingEl.remove();
            }
        }
        
        scrollToBottom() {
            this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
        }
        
        showError(message) {
            this.addMessage('assistant', message);
        }
    }
    
    // Global initialization function
    window.initOVRAWidget = function(config) {
        if (window.ovraWidget) {
            console.warn('OVRA Widget already initialized');
            return window.ovraWidget;
        }
        
        window.ovraWidget = new OVRAWidget(config);
        return window.ovraWidget;
    };
    
    // Auto-initialize if configuration exists
    if (window.ovraWidgetConfig) {
        window.initOVRAWidget(window.ovraWidgetConfig);
    } else {
        // Default initialization
        document.addEventListener('DOMContentLoaded', function() {
            if (!window.ovraWidget) {
                window.initOVRAWidget();
            }
        });
    }
})();