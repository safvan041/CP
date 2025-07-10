// statics/js/chat_widget.js (Final, Simplified String Version)

document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-container');

    if (!chatContainer) {
        return; // Exit if the chat container isn't on the page
    }

    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');
    const chatBox = document.getElementById('chat-box');
    const typingIndicator = document.getElementById('typing-indicator');

    const apiUrl = chatContainer.dataset.apiUrl;
    const csrfToken = chatContainer.dataset.csrfToken;
    const historyKey = 'chatHistory_' + apiUrl;

    // --- Load Chat History ---
    function loadHistory() {
        const history = JSON.parse(sessionStorage.getItem(historyKey)) || [];
        if (history.length > 0) {
            chatBox.innerHTML = history.join('');
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Append Message ---
    function appendMessage(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html.trim();
        const messageElement = tempDiv.firstChild;

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;

        let history = JSON.parse(sessionStorage.getItem(historyKey)) || [];
        history.push(messageElement.outerHTML);
        sessionStorage.setItem(historyKey, JSON.stringify(history));
    }

    // --- Get Timestamp ---
    function getTimestamp() {
        const now = new Date();
        const timeString = new Intl.DateTimeFormat(undefined, { timeStyle: 'short' }).format(now);
        return '<span class="timestamp">' + timeString + '</span>';
    }

    // --- Form Submission Handler ---
    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // Stop page reload

        const msg = input.value.trim();
        if (!msg) return;

        // Construct user message string using standard concatenation
        const userHtml = '<div class="msg user-msg"><strong>You:</strong> ' + msg + getTimestamp() + '</div>';
        appendMessage(userHtml);
        input.value = '';

        typingIndicator.style.display = 'block';

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ message: msg })
            });

            if (!response.ok) {
                throw new Error('Server responded with an error.');
            }

            const data = await response.json();
            // Construct bot message string using standard concatenation
            const botHtml = '<div class="msg bot-msg"><strong>Bot:</strong> ' + data.response + getTimestamp() + '</div>';
            appendMessage(botHtml);

        } catch (error) {
            console.error('Chat API Error:', error);
            const errorHtml = '<div class="msg bot-msg error-msg"><strong>Bot:</strong> Sorry, an error occurred.</div>';
            appendMessage(errorHtml);
        } finally {
            typingIndicator.style.display = 'none';
        }
    });

    // --- Initial Load ---
    loadHistory();
});