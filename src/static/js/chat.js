/**
 * Chat interface WebSocket client for Fluxion00API
 */

class ChatClient {
    constructor() {
        this.ws = null;
        this.clientId = this.generateClientId();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;

        // DOM elements
        this.messagesContainer = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-btn');
        this.clearButton = document.getElementById('clear-btn');
        this.statusBadge = document.getElementById('connection-status');
        this.typingIndicator = document.getElementById('typing-indicator');

        // Bind event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.clearButton.addEventListener('click', () => this.clearHistory());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });

        // Connect to WebSocket
        this.connect();
    }

    generateClientId() {
        return 'client_' + Math.random().toString(36).substring(2, 15);
    }

    connect() {
        this.updateStatus('connecting');

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateStatus('connected');
                this.reconnectAttempts = 0;
                this.sendButton.disabled = false;
            };

            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateStatus('disconnected');
                this.sendButton.disabled = true;
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('disconnected');
            };

        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateStatus('disconnected');
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.addMessage('system', 'Connection lost. Please refresh the page to reconnect.');
        }
    }

    updateStatus(status) {
        this.statusBadge.className = `status-badge ${status}`;
        this.statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }

    handleMessage(message) {
        const { type, content } = message;

        switch (type) {
            case 'system':
                this.addMessage('system', content);
                break;

            case 'user_echo':
                // User message already added when sending
                break;

            case 'agent_message':
                this.addMessage('agent', content);
                break;

            case 'error':
                this.addMessage('error', content);
                break;

            case 'typing':
                this.showTypingIndicator(content);
                break;

            case 'pong':
                console.log('Pong received');
                break;

            default:
                console.log('Unknown message type:', type);
        }
    }

    sendMessage() {
        const content = this.messageInput.value.trim();

        if (!content || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        // Add user message to UI
        this.addMessage('user', content);

        // Send to server
        this.ws.send(JSON.stringify({
            type: 'user_message',
            content: content
        }));

        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.messageInput.focus();
    }

    clearHistory() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        // Send clear history command
        this.ws.send(JSON.stringify({
            type: 'clear_history'
        }));

        // Clear UI
        this.messagesContainer.innerHTML = '';
    }

    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';

        // Set avatar emoji based on type
        if (type === 'user') {
            avatarDiv.textContent = '👤';
        } else if (type === 'agent') {
            avatarDiv.textContent = '🤖';
        } else if (type === 'system') {
            avatarDiv.textContent = 'ℹ️';
        } else if (type === 'error') {
            avatarDiv.textContent = '⚠️';
        }

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator(show) {
        if (show) {
            this.typingIndicator.style.display = 'flex';
        } else {
            this.typingIndicator.style.display = 'none';
        }
        this.scrollToBottom();
    }

    scrollToBottom() {
        const chatContainer = this.messagesContainer.parentElement;
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    ping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'ping'
            }));
        }
    }
}

// Initialize chat client when page loads
let chatClient;
document.addEventListener('DOMContentLoaded', () => {
    chatClient = new ChatClient();

    // Send ping every 30 seconds to keep connection alive
    setInterval(() => {
        if (chatClient) {
            chatClient.ping();
        }
    }, 30000);
});
