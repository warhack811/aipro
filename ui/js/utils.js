// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} value - Text to escape
 * @param {boolean} forAttribute - If true, also escape quotes
 * @returns {string} Escaped text
 */
export function escapeHtml(value, forAttribute = false) {
  const escaped = String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  return forAttribute ? escaped.replace(/"/g, '&quot;') : escaped;
}

/**
 * Escape HTML attributes (backward compatibility)
 */
export function escapeHtmlAttr(value) {
  return escapeHtml(value, true);
}

/**
 * Decode HTML entities
 */
export function decodeHtmlEntities(value) {
  const textarea = document.createElement('textarea');
  textarea.innerHTML = value || '';
  return textarea.value;
}

/**
 * Copy code to clipboard
 */
export function copyCode(btn) {
  const codeBlock = btn.closest('.code-wrapper').querySelector('code');
  if (codeBlock) {
    navigator.clipboard.writeText(codeBlock.textContent).then(() => {
      const originalHtml = btn.innerHTML;
      btn.classList.add('copied');
      btn.innerHTML = '<span>✓</span><span>Kopyalandı</span>';
      setTimeout(() => {
        btn.classList.remove('copied');
        btn.innerHTML = originalHtml;
      }, 2000);
    }).catch(err => {
      console.error('Copy failed:', err);
    });
  }
}

/**
 * Bind copy buttons in a container
 */
export function bindCopyButtons(container) {
  if (!container) return;
  const copyBtns = container.querySelectorAll('.copy-btn');
  copyBtns.forEach(btn => {
    if (!btn.dataset.bound) {
      btn.addEventListener('click', () => copyCode(btn));
      btn.dataset.bound = 'true';
    }
  });
}

/**
 * Highlight code using Prism
 */
export function highlightCodeInContainer(container) {
  if (typeof Prism !== 'undefined' && container) {
    try {
      Prism.highlightAllUnder(container);
    } catch (e) {
      console.warn('Prism highlighting failed:', e);
    }
  }
}

/**
 * Ensure chat area is scrolled to bottom
 */
export function ensureScrolledToBottom() {
  const chatArea = document.getElementById('chatArea');
  if (!chatArea) return;
  chatArea.scrollTop = chatArea.scrollHeight;
}

/**
 * Auto-resize textarea
 */
export function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 200) + 'px';
}

/**
 * Update page title with unread count
 */
export function updateTitle(unread) {
  document.title = unread ? `(${unread}) Mami AI Pro` : 'Mami AI Pro';
}