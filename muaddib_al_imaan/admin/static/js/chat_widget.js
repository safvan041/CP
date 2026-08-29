// Chat widget for Muaddin-al-imaan public layer.

document.addEventListener('DOMContentLoaded', function () {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;

    const form = document.getElementById('chat-form');
    const input = document.getElementById('message-input');
    const chatBox = document.getElementById('chat-box');
    const typingIndicator = document.getElementById('typing-indicator');

    const apiUrl = chatContainer.dataset.apiUrl;
    const fiqha = chatContainer.dataset.fiqha;
    const historyKey = 'chatHistory_' + fiqha;

    function loadHistory() {
        const history = JSON.parse(sessionStorage.getItem(historyKey)) || [];
        if (history.length > 0) {
            chatBox.innerHTML = history.join('');
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    }

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

    function getTimestamp() {
        const now = new Date();
        const timeString = new Intl.DateTimeFormat(undefined, { timeStyle: 'short' }).format(now);
        return '<span class="timestamp">' + timeString + '</span>';
    }

    function renderReferences(references) {
        if (!references || references.length === 0) return '';
        let html = '<div class="references"><strong>References:</strong><ul>';
        references.forEach(function (ref) {
            html += '<li>' + ref.book_name + ' — ' + ref.author_name + ' (' + ref.fiqha + ')';
            if (ref.chain) {
                html += '<br><em>Chain: ' + ref.chain + '</em>';
            }
            html += '</li>';
        });
        html += '</ul></div>';
        return html;
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const msg = input.value.trim();
        if (!msg) return;

        const userHtml = '<div class="msg user-msg"><strong>You:</strong> ' + msg + getTimestamp() + '</div>';
        appendMessage(userHtml);
        input.value = '';
        typingIndicator.style.display = 'block';

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg, fiqha: fiqha })
            });

            if (!response.ok) throw new Error('Server responded with an error.');

            const data = await response.json();
            const botHtml = '<div class="msg bot-msg"><strong>Bot:</strong> ' + data.response +
                renderReferences(data.references) + getTimestamp() + '</div>';
            appendMessage(botHtml);
        } catch (error) {
            console.error('Chat API Error:', error);
            appendMessage('<div class="msg bot-msg error-msg"><strong>Bot:</strong> Sorry, an error occurred.</div>');
        } finally {
            typingIndicator.style.display = 'none';
        }
    });

    loadHistory();
});