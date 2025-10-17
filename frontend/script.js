// ===========================================
// Configuration
// ===========================================
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    MAX_MESSAGE_LENGTH: 1000,
    REQUEST_TIMEOUT: 30000, // 30 seconds
};

// ===========================================
// State Management
// ===========================================
let isLoading = false;
let messageHistory = [];

// ===========================================
// DOM Elements
// ===========================================
const elements = {
    messagesContainer: document.getElementById('messages'),
    userInput: document.getElementById('user-input'),
    sendBtn: document.getElementById('send-btn'),
    loadingIndicator: document.getElementById('loading-indicator'),
    errorMessage: document.getElementById('error-message'),
    errorText: document.getElementById('error-text'),
    charCount: document.getElementById('char-count'),
};

// ===========================================
// Initialization
// ===========================================
function init() {
    // Event Listeners
    elements.sendBtn.addEventListener('click', handleSendMessage);
    elements.userInput.addEventListener('keypress', handleKeyPress);
    elements.userInput.addEventListener('input', updateCharCount);
    
    // Focus on input
    elements.userInput.focus();
    
    console.log('✅ Chat application initialized');
}

// ===========================================
// Event Handlers
// ===========================================
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
    }
}

function handleSendMessage() {
    const message = elements.userInput.value.trim();
    
    // Validation
    if (!message) {
        showError('Please enter a message');
        return;
    }
    
    if (message.length > CONFIG.MAX_MESSAGE_LENGTH) {
        showError(`Message is too long. Maximum ${CONFIG.MAX_MESSAGE_LENGTH} characters allowed.`);
        return;
    }
    
    if (isLoading) {
        return; // Prevent multiple submissions
    }
    
    // Send message
    sendMessage(message);
}

function updateCharCount() {
    const length = elements.userInput.value.length;
    elements.charCount.textContent = `${length} / ${CONFIG.MAX_MESSAGE_LENGTH}`;
    
    // Change color if near limit
    if (length > CONFIG.MAX_MESSAGE_LENGTH * 0.9) {
        elements.charCount.style.color = '#c33';
    } else {
        elements.charCount.style.color = '#999';
    }
}

// ===========================================
// Core Functionality
// ===========================================
async function sendMessage(message) {
    try {
        // Update UI state
        setLoadingState(true);
        hideError();
        
        // Add user message to UI
        addMessage(message, 'user');
        
        // Clear input
        elements.userInput.value = '';
        updateCharCount();
        
        // Call API
        const response = await fetchAIResponse(message);
        
        // Add AI response to UI
        addMessage(response.response, 'bot', response.timestamp);
        
        // Update history
        messageHistory.push({
            user: message,
            bot: response.response,
            timestamp: response.timestamp
        });
        
    } catch (error) {
        console.error('Error sending message:', error);
        showError(error.message || 'Failed to get response from AI. Please try again.');
    } finally {
        setLoadingState(false);
        elements.userInput.focus();
    }
}

async function fetchAIResponse(message) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            // Try to get error message from response
            let errorMessage = 'Server error';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch (e) {
                // If parsing fails, use status text
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(`${errorMessage} (Status: ${response.status})`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Request timed out. Please try again.');
        }
        
        if (error.message.includes('Failed to fetch')) {
            throw new Error('Cannot connect to server. Make sure the backend is running.');
        }
        
        throw error;
    }
}

// ===========================================
// UI Functions
// ===========================================
function addMessage(text, sender, timestamp = null) {
    // Remove welcome message if it exists
    const welcomeMessage = elements.messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';
    
    // Content
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(timestamp);
    
    content.appendChild(textDiv);
    content.appendChild(timeDiv);
    
    // Assemble
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    // Add to DOM
    elements.messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
}

function setLoadingState(loading) {
    isLoading = loading;
    
    if (loading) {
        elements.loadingIndicator.style.display = 'flex';
        elements.sendBtn.disabled = true;
        elements.userInput.disabled = true;
        scrollToBottom();
    } else {
        elements.loadingIndicator.style.display = 'none';
        elements.sendBtn.disabled = false;
        elements.userInput.disabled = false;
    }
}

function showError(message) {
    elements.errorText.textContent = message;
    elements.errorMessage.style.display = 'flex';
    
    // Auto-hide after 5 seconds
    setTimeout(hideError, 5000);
}

function hideError() {
    elements.errorMessage.style.display = 'none';
}

function scrollToBottom() {
    const chatContainer = document.getElementById('chat-container');
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);
}

function formatTime(timestamp) {
    if (!timestamp) {
        timestamp = new Date().toISOString();
    }
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// ===========================================
// Initialize on Page Load
// ===========================================
document.addEventListener('DOMContentLoaded', init);

// Make hideError global for HTML onclick
window.hideError = hideError;

