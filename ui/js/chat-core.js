// =============================================================================
// CHAT CORE - Core chat functionality (ES6 Module)
// =============================================================================
const DEBUG_MODE = false;

// =============================================================================
// IMPORTS
// =============================================================================
import { escapeHtml, escapeHtmlAttr, highlightCodeInContainer, bindCopyButtons, ensureScrolledToBottom, autoResize, decodeHtmlEntities } from './utils.js';
import { handleImageProgressEvent, addImagePending, removeImagePendingCard, updatePendingProgressBar, showPendingForCurrentConversation, finalizePendingJob } from './images.js';
import { getPreferredModel } from './persona.js';

// =============================================================================
// STATE
// =============================================================================
let currentConvId = null;
let ws = null;
let wsRetryDelay = 1000;
const WS_MAX_RETRY_DELAY = 30000;
let autoScroll = true;
let unread = 0;
let visible = true;
let activePersona = 'standard';

// =============================================================================
// DOMPURIFY CONFIG
// =============================================================================
const DOMPURIFY_CONFIG = {
    ALLOWED_TAGS: [
        'p', 'br', 'hr', 'strong', 'em', 'b', 'i', 'u', 's', 'del',
        'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'code', 'pre',
        'blockquote', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'div', 'span', 'button'
    ],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'title', 'style', 'data-bound'],
    ADD_ATTR: ['target', 'rel'],
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'img'],
    FORBID_ATTR: ['onerror', 'onload', 'onmouseover', 'onfocus', 'onblur']
};

// =============================================================================
// MARKDOWN RENDERING
// =============================================================================

// Custom Renderer
const renderer = new marked.Renderer();

renderer.code = function (code, lang) {
    const language = lang || 'plaintext';
    let highlighted = escapeHtml(code);

    if (typeof Prism !== 'undefined' && Prism.languages[language]) {
        try {
            highlighted = Prism.highlight(code, Prism.languages[language], language);
        } catch (e) { }
    }

    return `<div class="code-wrapper">
    <div class="code-header">
      <span class="code-lang">${escapeHtml(language)}</span>
      <button class="copy-btn" onclick="copyCode(this)">
        <span>📋</span><span>Kopyala</span>
      </button>
    </div>
    <pre><code class="language-${escapeHtml(language)}">${highlighted}</code></pre>
  </div>`;
};

renderer.codespan = function (text) {
    return `<code class="inline-code">${text}</code>`;
};

renderer.paragraph = function (text) {
    const alertTypes = {
        '[!NOTE]': { type: 'note', icon: 'ℹ️' },
        '[!TIP]': { type: 'tip', icon: '💡' },
        '[!IMPORTANT]': { type: 'important', icon: '❗' },
        '[!WARNING]': { type: 'warning', icon: '⚠️' },
        '[!CAUTION]': { type: 'caution', icon: '🚨' }
    };

    for (const [marker, config] of Object.entries(alertTypes)) {
        if (text.includes(marker)) {
            const content = text.replace(marker, '').trim();
            return `<div class="markdown-alert ${config.type}"><span class="alert-icon">${config.icon}</span><div class="alert-content">${content}</div></div>`;
        }
    }
    return `<p>${text}</p>`;
};

renderer.blockquote = function (quote) {
    const alertPatterns = [
        { regex: /\[!NOTE\]/i, type: 'note', icon: 'ℹ️', title: 'Not' },
        { regex: /\[!TIP\]/i, type: 'tip', icon: '💡', title: 'İpucu' },
        { regex: /\[!IMPORTANT\]/i, type: 'important', icon: '❗', title: 'Önemli' },
        { regex: /\[!WARNING\]/i, type: 'warning', icon: '⚠️', title: 'Uyarı' },
        { regex: /\[!CAUTION\]/i, type: 'caution', icon: '🚨', title: 'Dikkat' }
    ];

    for (const pattern of alertPatterns) {
        if (pattern.regex.test(quote)) {
            const content = quote.replace(pattern.regex, '').replace(/^<p>|<\/p>$/g, '').trim();
            return `<div class="markdown-alert ${pattern.type}"><span class="alert-icon">${pattern.icon}</span><div class="alert-content"><strong>${pattern.title}:</strong> ${content}</div></div>`;
        }
    }
    return `<blockquote>${quote}</blockquote>`;
};

marked.use({ renderer });

// Configure marked
marked.setOptions({
    breaks: true,
    gfm: true,
    mangle: false,
    headerIds: false,
    smartLists: true,
    xhtml: false,
    pedantic: false
});

// =============================================================================
// MODEL TAGS
// =============================================================================
const modelTagDefinitions = {
    GROQ: { label: 'GROQ', icon: '&#9889;', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)' },
    BELA: { label: 'BELA', icon: '&#128171;', color: '#a855f7', background: 'rgba(168, 85, 247, 0.12)' },
    NET: { label: 'WEB', icon: '&#127760;', color: '#0ea5e9', background: 'rgba(14, 165, 233, 0.12)' },
    IMAGE: { label: 'ART', icon: '&#128444;', color: '#ec4899', background: 'rgba(236, 72, 153, 0.12)' }
};

function renderModelTag(key) {
    const def = modelTagDefinitions[key];
    if (!def) return `[${key}]`;
    const tooltips = {
        GROQ: 'Groq Cloud AI - Hızlı ve güçlü bulut tabanlı yapay zeka modeli',
        BELA: 'Bela Local Model - Gizlilik odaklı yerel yapay zeka modeli',
        NET: 'Web Araması - İnternet üzerinden güncel bilgi araması',
        IMAGE: 'Görsel Üretimi - AI ile yaratıcı görsel oluşturma'
    };
    return `<span class="msg-tag" data-tooltip="${tooltips[key] || key}" title="" style="--tag-color:${def.color}; --tag-bg:${def.background}"><span class="tag-icon">${def.icon}</span><span class="tag-label">${def.label}</span></span>`;
}

function replaceModelTags(text) {
    const regex = /\[(GROQ|BELA|NET|IMAGE)\]/g;
    let rendered = false;
    return text.replace(regex, (_, tag) => {
        if (rendered) return '';
        rendered = true;
        return `${renderModelTag(tag)} `;
    });
}

// =============================================================================
// SANITIZE MARKDOWN
// =============================================================================
export function sanitizeMarkdown(text) {
    if (!text) return '';
    if (typeof marked === 'undefined') {
        console.error('marked is not defined');
        return escapeHtml(text);
    }
    const html = marked.parse(text);
    if (typeof DOMPurify !== 'undefined') {
        DOMPurify.addHook('afterSanitizeAttributes', function (node) {
            if (node.tagName === 'A') {
                node.setAttribute('target', '_blank');
                node.setAttribute('rel', 'noopener noreferrer');
            }
        });
        try {
            return DOMPurify.sanitize(html, DOMPURIFY_CONFIG);
        } finally {
            DOMPurify.removeHook('afterSanitizeAttributes');
        }
    }
    return html;
}

// =============================================================================
// WEBSOCKET
// =============================================================================
export function connectWebSocket() {
    const scheme = (location.protocol === 'https:') ? 'wss' : 'ws';
    const wsUrl = `${scheme}://${location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        if (DEBUG_MODE) console.log('WebSocket connected:', wsUrl);
        wsRetryDelay = 1000;
    };

    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (DEBUG_MODE) console.log('[WS] Received:', data);

        // Handle image progress events
        if (data.type === 'image_progress') {
            handleImageProgressEvent(data, currentConvId);
            if (data.progress >= 100 && data.path) {
                addMessage('bot', `IMAGE_PATH: ${data.path}`);
            }
        }

        // Handle image completion (from Celery if ever re-enabled)
        if (data.type === 'image_complete' && data.image_path) {
            addMessage('bot', `IMAGE_PATH: ${data.image_path}`);
            finalizePendingJob(data.job_id);
        }
    };

    ws.onclose = () => {
        if (DEBUG_MODE) console.log(`WebSocket closed, reconnecting in ${wsRetryDelay / 1000}s...`);
        setTimeout(connectWebSocket, wsRetryDelay);
        wsRetryDelay = Math.min(wsRetryDelay * 2, WS_MAX_RETRY_DELAY);
    };

    ws.onerror = (err) => console.error('WebSocket error:', err);
}

// =============================================================================
// UPDATE TITLE
// =============================================================================
function updateTitle() {
    document.title = unread ? `(${unread}) Mami AI Pro` : 'Mami AI Pro';
}

// =============================================================================
// ADD MESSAGE
// =============================================================================
export function addMessage(role, text) {
    const area = document.getElementById('chatArea');
    if (!area) return;

    // Hide welcome screen when first message appears
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) welcomeScreen.style.display = 'none';

    const div = document.createElement('div');
    div.className = `message ${role}`;
    const messageId = `msg-${Date.now()}`;
    div.id = messageId;

    // Handle image paths - check if text CONTAINS IMAGE_PATH anywhere
    if (text && text.includes('IMAGE_PATH:')) {
        // Extract image path from text
        const match = text.match(/IMAGE_PATH:\s*(\S+)/);
        if (match) {
            const imgPath = match[1].trim();
            
            // Extract prompt from image-prompt span if present
            let prompt = '';
            const promptMatch = text.match(/<span class="image-prompt" data-prompt="([^"]+)"><\/span>/);
            if (promptMatch) {
                prompt = decodeHtmlEntities(promptMatch[1]);
            }

            // Remove pending card since image is ready
            removeImagePendingCard();
            
            // Remove "Görsel isteğiniz kuyruğa alındı..." message if it exists
            const pendingMessages = area.querySelectorAll('.message.bot');
            pendingMessages.forEach(msg => {
                const bubble = msg.querySelector('.msg-bubble');
                if (bubble && (bubble.textContent.includes('kuyruğa alındı') || bubble.textContent.includes('IMAGE_PENDING'))) {
                    msg.remove();
                }
            });

            const promptAttr = prompt ? ` data-prompt="${escapeHtmlAttr(prompt)}"` : '';
            div.innerHTML = `
      <div class="msg-avatar">🎨</div>
      <div class="msg-bubble">
        <div class="pending-title" style="margin-bottom:8px;">🖼️ Resminiz hazır!</div>
        <div class="image-message" onclick="openLightbox('${escapeHtmlAttr(imgPath)}', '${escapeHtmlAttr(prompt)}')"${promptAttr}>
          <img src="${escapeHtmlAttr(imgPath)}" alt="Generated Image" 
               onerror="this.parentElement.innerHTML='<div class=\\'image-error\\'>🖼️ Resim yüklenemedi<br><button onclick=\\'retryImage(&quot;${escapeHtmlAttr(imgPath)}&quot;, this)\\'>Tekrar Dene</button></div>'" />
        </div>
        <span class="msg-time">${new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</span>
      </div>`;
            area.appendChild(div);
            ensureScrolledToBottom();
            return;
        }
    }

    // Sanitize and render message
    const processedText = replaceModelTags(text || '');
    const sanitizedHtml = sanitizeMarkdown(processedText);

    // Build action bar for bot messages
    const actionBar = role === 'bot' ? `
      <div class="msg-actions">
        <button class="msg-action" onclick="copyMessage('${messageId}')" title="Kopyala">📋</button>
        <button class="msg-action" onclick="likeMessage('${messageId}')" title="Beğen">👍</button>
        <button class="msg-action" onclick="dislikeMessage('${messageId}')" title="Beğenme">👎</button>
        <button class="msg-action" onclick="regenerateMessage('${messageId}')" title="Yeniden üret">🔄</button>
      </div>
    ` : '';

    div.innerHTML = `
    <div class="msg-avatar">${role === 'user' ? '👤' : '🤖'}</div>
    <div class="msg-bubble">
      ${sanitizedHtml}
      <span class="msg-time">${new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</span>
      ${actionBar}
    </div>`;

    area.appendChild(div);

    // Post-processing
    const bubble = div.querySelector('.msg-bubble');
    if (bubble) {
        highlightCodeInContainer(bubble);
        bindCopyButtons(bubble);
    }
    
    // Wrap images with lightbox functionality (async to avoid circular dependency)
    setTimeout(async () => {
        const { wrapImages } = await import('./images.js');
        wrapImages();
    }, 0);

    if (!visible && role === 'bot') {
        unread++;
        updateTitle();
    }

    ensureScrolledToBottom();
}

// =============================================================================
// TYPING INDICATOR
// =============================================================================
export function showTyping() {
    const area = document.getElementById('chatArea');
    if (!area) return;
    const div = document.createElement('div');
    div.id = 'typing';
    div.className = 'message bot';
    div.innerHTML = `<div class="msg-bubble" style="display:flex; gap:4px; align-items:center;"><span></span><span></span><span></span></div>`;
    area.appendChild(div);
    ensureScrolledToBottom();
}

export function hideTyping() {
    const t = document.getElementById('typing');
    if (t) t.remove();
}

// =============================================================================
// SEND MESSAGE
// =============================================================================
export async function send() {
    const input = document.getElementById('msgInput');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;

    addMessage('user', text);
    input.value = '';
    autoResize(input);
    showTyping();

    // Persona-based force local
    const PERSONAS_REQUIRING_LOCAL = ['romantic', 'roleplay'];
    const shouldForceLocal = PERSONAS_REQUIRING_LOCAL.includes(activePersona);

    const modelPref = getPreferredModel();
    const forceLocal = shouldForceLocal || (modelPref === 'bela');
    const requestedModel = modelPref !== 'auto' ? modelPref : null;

    try {
        const res = await fetch('/api/v1/user/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                force_local: forceLocal,
                requested_model: requestedModel,
                conversation_id: currentConvId,
                stream: true
            })
        });

        if (res.ok && res.headers.get('content-type')?.includes('text/plain') && res.body) {
            const convHeader = res.headers.get('x-conversation-id');
            if (convHeader) currentConvId = convHeader;

            let streamMsg = null;
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';
            const streamTagKey = forceLocal ? 'BELA' : 'GROQ';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;

                if (!streamMsg) {
                    hideTyping();
                    streamMsg = document.createElement('div');
                    streamMsg.className = 'message bot streaming';
                    streamMsg.innerHTML = `<div class="msg-avatar">🤖</div><div class="msg-bubble"><span class="stream-content"></span></div>`;
                    document.getElementById('chatArea')?.appendChild(streamMsg);
                }

                const displayText = `[${streamTagKey}] ${fullText}`;
                const processedText = replaceModelTags(displayText);
                const sanitized = sanitizeMarkdown(processedText);
                const contentSpan = streamMsg.querySelector('.stream-content');
                if (contentSpan) contentSpan.innerHTML = sanitized;
                ensureScrolledToBottom();
            }

            if (streamMsg) {
                streamMsg.classList.remove('streaming');
                const msgId = `msg-${Date.now()}`;
                streamMsg.id = msgId;
                const bubble = streamMsg.querySelector('.msg-bubble');
                if (bubble) {
                    const time = document.createElement('span');
                    time.className = 'msg-time';
                    time.textContent = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
                    bubble.appendChild(time);

                    // Add action bar
                    const actionBar = document.createElement('div');
                    actionBar.className = 'msg-actions';
                    actionBar.innerHTML = `
                        <button class="msg-action" onclick="copyMessage('${msgId}')" title="Kopyala">📋</button>
                        <button class="msg-action" onclick="likeMessage('${msgId}')" title="Beğen">👍</button>
                        <button class="msg-action" onclick="dislikeMessage('${msgId}')" title="Beğenme">👎</button>
                        <button class="msg-action" onclick="regenerateMessage('${msgId}')" title="Yeniden üret">🔄</button>
                    `;
                    bubble.appendChild(actionBar);

                    highlightCodeInContainer(bubble);
                    bindCopyButtons(bubble);
                }
            }

            loadConversations();
        } else {
            hideTyping();
            const data = await res.json();
            const message = data.message || data.error || '⚠️ Hata oluştu.';

            // Check for IMAGE_PENDING - show pending card immediately
            if (message.includes('[IMAGE_PENDING]') || message.includes('kuyruğa alındı')) {
                // Import and show pending card
                const queuePos = data.queue_pos || 1;
                addImagePending(queuePos, data.job_id || null, 0);
                // Don't add text message, pending card is the message
            } else {
                addMessage('bot', message);
            }

            if (data.conversation_id) currentConvId = data.conversation_id;
            loadConversations();
        }
    } catch (e) {
        hideTyping();
        addMessage('bot', `⛔ Sistem Hatası: ${e.message}`);
    }
}

// =============================================================================
// HANDLE ENTER
// =============================================================================
export function handleEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
    }
}

// =============================================================================
// CONVERSATIONS
// =============================================================================
export async function loadConversations() {
    try {
        const res = await fetch('/api/v1/user/conversations');
        const list = await res.json();
        const convList = document.getElementById('convList');
        if (convList) {
            convList.innerHTML = list.map(c =>
                `<div class="conv-item ${c.id == currentConvId ? 'active' : ''}" onclick="loadChat('${c.id}')">
          <span>${escapeHtml(c.title || 'Yeni Sohbet')}</span>
          <button class="conv-del" onclick="event.stopPropagation(); deleteConversation('${c.id}', event)">×</button>
        </div>`
            ).join('');
        }
    } catch (e) {
        console.error('Conversations load error:', e);
    }
}

export async function deleteAllConversations() {
    if (!confirm('Tüm sohbetleri silmek istediğinize emin misiniz?')) return;
    try {
        await fetch('/api/v1/user/conversations/all-delete', { method: 'DELETE' });
        currentConvId = null;
        const chatArea = document.getElementById('chatArea');
        if (chatArea) chatArea.innerHTML = '<div class="welcome-message"><h2>Mami AI Pro</h2><p>Merhaba! Size nasıl yardımcı olabilirim?</p></div>';
        loadConversations();
    } catch (e) {
        console.error('Delete error:', e);
    }
}

export async function deleteConversation(id, event) {
    if (event) event.stopPropagation();
    if (!confirm('Bu sohbeti silmek istediğinize emin misiniz?')) return;
    try {
        await fetch(`/api/v1/user/conversations/${id}`, { method: 'DELETE' });
        if (currentConvId == id) {
            currentConvId = null;
            const chatArea = document.getElementById('chatArea');
            if (chatArea) chatArea.innerHTML = '<div class="welcome-message"><h2>Mami AI Pro</h2><p>Merhaba! Size nasıl yardımcı olabilirim?</p></div>';
        }
        loadConversations();
    } catch (e) {
        console.error('Delete error:', e);
    }
}

export async function loadChat(id) {
    currentConvId = id;
    const chatArea = document.getElementById('chatArea');
    if (!chatArea) return;
    chatArea.innerHTML = '';

    try {
        const res = await fetch(`/api/v1/user/conversations/${id}`);
        const messages = await res.json();
        messages.forEach(m => addMessage(m.role, m.text));
        showPendingForCurrentConversation(currentConvId);
        loadConversations();
    } catch (e) {
        chatArea.innerHTML = '<div class="error-message">Sohbet yüklenemedi</div>';
    }
}

export function startNewChat() {
    currentConvId = null;
    const chatArea = document.getElementById('chatArea');
    if (chatArea) {
        // Restore welcome screen with suggestion cards
        chatArea.innerHTML = `
        <div class="welcome-container" id="welcomeScreen">
            <div class="welcome-logo">🤖</div>
            <h2 class="welcome-title">Mami AI Pro'ya Hoşgeldiniz</h2>
            <p class="welcome-subtitle">RAG, Vektör Hafıza ve Görsel Üretim özellikleriyle donatılmış akıllı asistanınız hazır. Aşağıdaki önerilerden birini seçin veya kendi sorunuzu yazın.</p>
            
            <div class="suggestion-cards">
                <div class="suggestion-card" onclick="sendSuggestion('Bana bir resim çiz')">
                    <span class="suggestion-icon">🎨</span>
                    <span class="suggestion-text">Görsel Oluştur</span>
                    <span class="suggestion-desc">AI ile resim üret</span>
                </div>
                <div class="suggestion-card" onclick="sendSuggestion('Python ile örnek bir kod yaz')">
                    <span class="suggestion-icon">💻</span>
                    <span class="suggestion-text">Kod Yaz</span>
                    <span class="suggestion-desc">Programlama yardımı</span>
                </div>
                <div class="suggestion-card" onclick="sendSuggestion('Güncel haberleri araştır')">
                    <span class="suggestion-icon">🌐</span>
                    <span class="suggestion-text">Web Araması</span>
                    <span class="suggestion-desc">İnternette ara</span>
                </div>
                <div class="suggestion-card" onclick="sendSuggestion('Bana yaratıcı bir fikir öner')">
                    <span class="suggestion-icon">💡</span>
                    <span class="suggestion-text">Fikir Al</span>
                    <span class="suggestion-desc">Beyin fırtınası</span>
                </div>
            </div>
        </div>`;
    }
    loadConversations();
}

// =============================================================================
// LOGOUT
// =============================================================================
export async function logout() {
    await fetch('/api/v1/logout', { method: 'POST' });
    location.href = '/ui/login.html';
}

// =============================================================================
// GETTERS
// =============================================================================
export function getCurrentConvId() {
    return currentConvId;
}

export function setActivePersona(persona) {
    activePersona = persona;
}

// =============================================================================
// VISIBILITY
// =============================================================================
export function initVisibility() {
    document.addEventListener('visibilitychange', () => {
        visible = !document.hidden;
        if (visible) {
            unread = 0;
            updateTitle();
        }
    });
}

// =============================================================================
// PWA
// =============================================================================
let deferredPrompt = null;

export function initPWA() {
    window.addEventListener('beforeinstallprompt', e => {
        e.preventDefault();
        deferredPrompt = e;
        showInstallButton();
    });

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/ui/sw.js').catch(() => { });
    }
}

function showInstallButton() {
    let btn = document.getElementById('installBtn');
    if (!btn) {
        btn = document.createElement('button');
        btn.id = 'installBtn';
        btn.textContent = '📲 Yükle';
        btn.style.cssText = 'position:fixed;bottom:80px;right:16px;padding:10px 16px;background:var(--primary);color:#fff;border:none;border-radius:8px;cursor:pointer;z-index:1000;';
        document.body.appendChild(btn);
        btn.onclick = async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                deferredPrompt = null;
                btn.remove();
            }
        };
    }
}

// =============================================================================
// TOAST NOTIFICATIONS
// =============================================================================
export function showToast(message, type = 'info') {
    let toast = document.getElementById('globalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'globalToast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// =============================================================================
// MESSAGE ACTIONS
// =============================================================================
export function copyMessage(messageId) {
    const msg = document.getElementById(messageId);
    if (!msg) return;
    const bubble = msg.querySelector('.msg-bubble');
    if (!bubble) return;

    // Get text content without action buttons
    const clone = bubble.cloneNode(true);
    clone.querySelectorAll('.msg-actions, .msg-time').forEach(el => el.remove());
    const text = clone.textContent || clone.innerText;

    navigator.clipboard.writeText(text.trim()).then(() => {
        const btn = msg.querySelector('.msg-action[title="Kopyala"]');
        if (btn) {
            btn.classList.add('copied');
            btn.textContent = '✓';
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.textContent = '📋';
            }, 2000);
        }
        showToast('Mesaj kopyalandı', 'success');
    }).catch(() => {
        showToast('Kopyalama başarısız', 'error');
    });
}

export function likeMessage(messageId) {
    const msg = document.getElementById(messageId);
    if (!msg) return;
    const btn = msg.querySelector('.msg-action[title="Beğen"]');
    if (btn) {
        btn.classList.toggle('active');
        // Remove dislike if active
        const dislikeBtn = msg.querySelector('.msg-action[title="Beğenme"]');
        if (dislikeBtn) dislikeBtn.classList.remove('active');
    }
    // TODO: Send feedback to API
    showToast('Geri bildirim kaydedildi', 'success');
}

export function dislikeMessage(messageId) {
    const msg = document.getElementById(messageId);
    if (!msg) return;
    const btn = msg.querySelector('.msg-action[title="Beğenme"]');
    if (btn) {
        btn.classList.toggle('active');
        // Remove like if active
        const likeBtn = msg.querySelector('.msg-action[title="Beğen"]');
        if (likeBtn) likeBtn.classList.remove('active');
    }
    // TODO: Send feedback to API
    showToast('Geri bildirim kaydedildi', 'success');
}

export function regenerateMessage(messageId) {
    const msg = document.getElementById(messageId);
    if (!msg) return;

    // Find the previous user message
    let prev = msg.previousElementSibling;
    while (prev && !prev.classList.contains('user')) {
        prev = prev.previousElementSibling;
    }

    if (prev) {
        const bubble = prev.querySelector('.msg-bubble');
        if (bubble) {
            const clone = bubble.cloneNode(true);
            clone.querySelectorAll('.msg-time').forEach(el => el.remove());
            const userText = clone.textContent || clone.innerText;

            // Remove the bot message
            msg.remove();

            // Re-send
            const msgInput = document.getElementById('msgInput');
            if (msgInput) {
                msgInput.value = userText.trim();
                // Trigger send (will be handled by the send function)
                showToast('Yeniden üretiliyor...', 'info');
            }
        }
    }
}

// =============================================================================
// SUGGESTION CARDS
// =============================================================================
export function sendSuggestion(text) {
    const msgInput = document.getElementById('msgInput');
    if (msgInput) {
        msgInput.value = text;
        // Update char count
        updateCharCount(msgInput);
        // Hide welcome screen
        const welcome = document.getElementById('welcomeScreen');
        if (welcome) welcome.style.display = 'none';
        // Focus on input
        msgInput.focus();
    }
}

// =============================================================================
// CHARACTER COUNTER
// =============================================================================
export function updateCharCount(textarea) {
    const counter = document.getElementById('charCount');
    if (!counter || !textarea) return;

    const current = textarea.value.length;
    const max = parseInt(textarea.getAttribute('maxlength')) || 10000;

    counter.textContent = `${current} / ${max}`;

    // Apply warning/danger classes
    counter.classList.remove('warning', 'danger');
    if (current >= max * 0.95) {
        counter.classList.add('danger');
    } else if (current >= max * 0.8) {
        counter.classList.add('warning');
    }
}
