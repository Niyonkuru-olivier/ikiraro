const contactForm = document.getElementById('contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const message = document.getElementById('message').value;
    
        // Here you can handle form submission, e.g., send data to your server
        console.log('Form submitted:', { name, email, message });
        
        // Clear the form
        contactForm.reset();
        alert('Thank you for your message! We will get back to you soon.');
    });
}

function escapeHtml(unsafeText) {
    return unsafeText
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

(function initUmuhuzaAssistant() {
    const launcher = document.getElementById('chatbot-launcher');
    const panel = document.getElementById('chatbot-panel');
    const closeButton = document.getElementById('chatbot-close');
    const messagesWrapper = document.getElementById('chatbot-messages');
    const statusElement = document.getElementById('chatbot-status');
    const form = document.getElementById('chatbot-form');
    const input = document.getElementById('chatbot-input');
    const sendButton = document.getElementById('chatbot-send');

    if (!launcher || !panel || !form || !messagesWrapper || !input || !sendButton) {
        return;
    }

    const state = {
        open: false,
        bootstrapped: false,
        pending: false,
        history: []
    };

    const setStatus = (text = '') => {
        if (statusElement) {
            statusElement.textContent = text;
        }
    };

    const togglePanel = (shouldOpen) => {
        const open = typeof shouldOpen === 'boolean' ? shouldOpen : !state.open;
        state.open = open;
        panel.classList.toggle('is-visible', open);
        panel.setAttribute('aria-expanded', open ? 'true' : 'false');
        launcher.setAttribute('aria-pressed', open ? 'true' : 'false');

        if (open && !state.bootstrapped) {
            const welcome = "Muraho! I'm UMUHUZA - Assistant. Ask me about dashboards, inputs, weather, or how to use the platform.";
            appendMessage('assistant', welcome);
            state.history.push({ role: 'assistant', content: welcome });
            state.bootstrapped = true;
        }

        if (open) {
            setTimeout(() => input.focus(), 150);
        }
    };

    const appendMessage = (role, text) => {
        const wrapper = document.createElement('div');
        wrapper.className = `chatbot-message chatbot-message--${role}`;
        const bubble = document.createElement('div');
        bubble.className = 'chatbot-message__bubble';
        bubble.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
        wrapper.appendChild(bubble);
        messagesWrapper.appendChild(wrapper);
        messagesWrapper.scrollTop = messagesWrapper.scrollHeight;
    };

    const setPendingState = (pending) => {
        state.pending = pending;
        sendButton.disabled = pending;
        if (pending) {
            setStatus('UMUHUZA is preparing a response...');
            form.classList.add('is-busy');
        } else {
            form.classList.remove('is-busy');
            setStatus('');
        }
    };

    const sendToAssistant = async (latestUserMessage) => {
        const trimmedHistory = state.history.slice(-8);
        const historyForServer = trimmedHistory.slice(0, -1);
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: latestUserMessage,
                    history: historyForServer
                })
            });

            const payload = await response.json();
            if (response.ok && payload.message) {
                appendMessage('assistant', payload.message);
                state.history.push({ role: 'assistant', content: payload.message });
            } else {
                const errorMessage = payload.error || 'The assistant is unavailable right now.';
                appendMessage('assistant', errorMessage);
            }
        } catch (error) {
            appendMessage('assistant', 'Network issue prevented UMUHUZA from replying. Please try again.');
        } finally {
            setPendingState(false);
        }
    };

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        if (state.pending) {
            return;
        }

        const userMessage = input.value.trim();
        if (!userMessage) {
            return;
        }

        appendMessage('user', userMessage);
        state.history.push({ role: 'user', content: userMessage });
        input.value = '';

        setPendingState(true);
        sendToAssistant(userMessage);
    });

    launcher.addEventListener('click', () => togglePanel());
    closeButton?.addEventListener('click', () => togglePanel(false));

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && state.open) {
            togglePanel(false);
        }
    });
})();
