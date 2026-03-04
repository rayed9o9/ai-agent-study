// ─── State ────────────────────────────────────────────────
let selectedFile = null;
let isLoading = false;

// ─── DOM refs ─────────────────────────────────────────────
const messagesEl = document.getElementById('messages');
const innerEl = document.getElementById('messagesInner');
const welcomeEl = document.getElementById('welcome');
const messageInput = document.getElementById('messageInput');
const imageInput = document.getElementById('imageInput');
const sendBtn = document.getElementById('sendBtn');
const uploadPreview = document.getElementById('uploadPreview');
const previewImg = document.getElementById('previewImg');
const chatList = document.getElementById('chatList');
const sidebar = document.getElementById('sidebar');

// ─── Sidebar toggle (mobile) ─────────────────────────────
function toggleSidebar() { sidebar.classList.toggle('open'); }

// ─── New chat ────────────────────────────────────────────
function newChat() {
    innerEl.innerHTML = '';
    innerEl.appendChild(welcomeEl);
    welcomeEl.style.display = 'flex';
    selectedFile = null;
    uploadPreview.classList.remove('show');
    messageInput.value = '';
    autoResize(messageInput);
}

// ─── Image handling ──────────────────────────────────────
function handleImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (ev) => {
        previewImg.src = ev.target.result;
        uploadPreview.classList.add('show');
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    selectedFile = null;
    imageInput.value = '';
    uploadPreview.classList.remove('show');
}

// ─── Auto-resize textarea ────────────────────────────────
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

// ─── Keyboard shortcut ──────────────────────────────────
function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// ─── Scroll to bottom ───────────────────────────────────
function scrollBottom() {
    messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
}

// ─── Configure marked.js ────────────────────────────────
marked.setOptions({
    breaks: true,       // Convert \n to <br>
    gfm: true,          // GitHub Flavored Markdown
});

// ─── Render a message ───────────────────────────────────
function addMessage(role, text, images = [], uploadedImgSrc = null) {
    // Hide welcome
    welcomeEl.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'msg';

    const avatarClass = role === 'user' ? 'user' : 'assistant';
    const avatarChar = role === 'user' ? '👤' : 'ع';
    const roleName = role === 'user' ? 'You' : 'Arabic AI';

    // User messages: escape HTML. Assistant messages: render markdown.
    let contentHtml;
    if (role === 'user') {
        contentHtml = escapeHtml(text);
    } else {
        contentHtml = marked.parse(text);
    }

    // Show uploaded image inline in user bubble
    if (uploadedImgSrc) {
        contentHtml += `<br/><img class="msg-image-preview" src="${uploadedImgSrc}" alt="uploaded image"/>`;
    }

    // Show output images in assistant bubble
    for (const img of images) {
        contentHtml += `<br/><img src="${img}" alt="rendered output"/>`;
    }

    row.innerHTML = `
    <div class="msg-avatar ${avatarClass}">${avatarChar}</div>
    <div class="msg-body">
      <div class="msg-role">${roleName}</div>
      <div class="msg-content ${role === 'user' ? '' : 'markdown-body'}">${contentHtml}</div>
    </div>
  `;

    innerEl.appendChild(row);
    scrollBottom();
}

// ─── Typing indicator ───────────────────────────────────
function showTyping() {
    const el = document.createElement('div');
    el.className = 'typing';
    el.id = 'typingIndicator';
    el.innerHTML = `
    <div class="msg-avatar assistant" style="background:linear-gradient(135deg,var(--accent),#a78bfa);color:#fff;">ع</div>
    <div class="msg-body">
      <div class="msg-role">Arabic AI</div>
      <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>
  `;
    innerEl.appendChild(el);
    scrollBottom();
}

function hideTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

// ─── Create an empty streaming assistant message ────────
function addStreamingMessage() {
    welcomeEl.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'msg';

    row.innerHTML = `
    <div class="msg-avatar assistant">ع</div>
    <div class="msg-body">
      <div class="msg-role">Arabic AI</div>
      <div class="msg-content markdown-body streaming"></div>
    </div>
  `;

    innerEl.appendChild(row);
    scrollBottom();
    return row.querySelector('.msg-content');
}

// ─── Send message (streaming) ───────────────────────────
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isLoading) return;

    isLoading = true;
    sendBtn.disabled = true;

    // Capture image preview for user bubble
    let uploadedImgSrc = null;
    if (selectedFile) {
        uploadedImgSrc = previewImg.src;
    }

    // Build form data BEFORE clearing the image reference
    const formData = new FormData();
    formData.append('message', text);
    if (selectedFile) {
        formData.append('image', selectedFile);
    }

    addMessage('user', text, [], uploadedImgSrc);

    // Clear input (after FormData is built)
    messageInput.value = '';
    autoResize(messageInput);
    removeImage();

    showTyping();

    try {
        const res = await fetch('/chat', { method: 'POST', body: formData });

        hideTyping();
        const contentEl = addStreamingMessage();

        let fullText = '';
        let images = [];
        let renderPending = false;
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE lines
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line in buffer

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;

                try {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'token') {
                        fullText += data.content;
                        // Batch renders using rAF for smooth performance
                        if (!renderPending) {
                            renderPending = true;
                            requestAnimationFrame(() => {
                                contentEl.innerHTML = marked.parse(fullText);
                                scrollBottom();
                                renderPending = false;
                            });
                        }
                    } else if (data.type === 'done') {
                        images = data.images || [];
                    } else if (data.type === 'error') {
                        contentEl.classList.remove('streaming');
                        contentEl.textContent = data.content;
                    }
                } catch (e) {
                    // ignore parse errors for incomplete JSON
                }
            }
        }

        // Final markdown render + append images
        contentEl.classList.remove('streaming');
        contentEl.innerHTML = marked.parse(fullText);
        for (const img of images) {
            contentEl.innerHTML += `<br/><img src="${img}" alt="rendered output"/>`;
        }
        scrollBottom();

        // Add to sidebar history
        addChatHistoryItem(text);
    } catch (err) {
        hideTyping();
        addMessage('assistant', 'Sorry, something went wrong. Please try again.');
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// ─── Sidebar history ────────────────────────────────────
let historyCounter = 0;
function addChatHistoryItem(text) {
    historyCounter++;
    const item = document.createElement('div');
    item.className = 'chat-list-item' + (historyCounter === 1 ? ' active' : '');
    item.textContent = text.length > 30 ? text.slice(0, 30) + '…' : text;
    chatList.prepend(item);
}

// ─── Helpers ────────────────────────────────────────────
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ─── iOS keyboard handling ──────────────────────────────
// When the virtual keyboard opens on iOS, scroll to keep input visible
if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', () => {
        // Scroll messages to bottom when keyboard opens/closes
        scrollBottom();
        // Ensure the input area stays above the keyboard
        document.documentElement.style.setProperty(
            '--keyboard-offset',
            `${window.innerHeight - window.visualViewport.height}px`
        );
    });
}

