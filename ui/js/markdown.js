// =============================================================================
// MARKDOWN CONFIGURATION & RENDERING
// =============================================================================

import { escapeHtml } from './utils.js';

// =============================================================================
// SECURITY: DOMPurify Configuration (XSS Prevention)
// =============================================================================

export const DOMPURIFY_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'br', 'hr',
    'strong', 'em', 'b', 'i', 'u', 's', 'del',
    'h1', 'h2', 'h3', 'h4',
    'ul', 'ol', 'li',
    'code', 'pre',
    'blockquote',
    'a',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'div', 'span', 'button'
  ],
  ALLOWED_ATTR: [
    'href', 'target', 'rel', 'class', 'title',
    'style',
    'data-bound'
  ],
  ADD_ATTR: ['target', 'rel'],
  FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'img'],
  FORBID_ATTR: ['onerror', 'onload', 'onmouseover', 'onfocus', 'onblur']
};

// =============================================================================
// Markdown Configuration
// =============================================================================

export function initMarkdown() {
  marked.setOptions({
    breaks: true,
    gfm: true,
    mangle: false,
    headerIds: false,
    smartLists: true,
    xhtml: false,
    pedantic: false
  });

  const renderer = new marked.Renderer();

  renderer.code = function (code, lang) {
    lang = (lang || 'text').toLowerCase().trim();
    if (!lang || lang === 'plaintext') lang = 'text';

    const safeCode = String(code || '').trim();
    if (!safeCode) return '';

    let highlighted = safeCode;
    if (typeof Prism !== 'undefined') {
      const validLang = Prism.languages[lang] ? lang : 'plaintext';
      try {
        highlighted = Prism.highlight(safeCode, Prism.languages[validLang], validLang);
      } catch (e) {
        console.warn('Syntax highlighting error:', e);
        highlighted = safeCode;
      }
    }

    const langNames = {
      'js': 'JavaScript',
      'javascript': 'JavaScript',
      'py': 'Python',
      'python': 'Python',
      'html': 'HTML',
      'css': 'CSS',
      'bash': 'Bash',
      'sh': 'Shell',
      'json': 'JSON',
      'sql': 'SQL',
      'plaintext': 'Text'
    };

    const displayLang = langNames[lang.toLowerCase()] || lang.toUpperCase();

    return `
      <div class="code-wrapper">
        <div class="code-header">
          <div class="mac-dots">
            <div class="mac-dot" style="background:#ff5f56"></div>
            <div class="mac-dot" style="background:#ffbd2e"></div>
            <div class="mac-dot" style="background:#27c93f"></div>
            <span class="lang-label">${displayLang}</span>
          </div>
          <button class="copy-btn" title="Kodu kopyala">
            <span>📋</span>
            <span>Kopyala</span>
          </button>
        </div>
        <pre class="language-${lang}"><code>${highlighted}</code></pre>
      </div>
    `;
  };

  renderer.codespan = function (text) {
    return `<code style="background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; font-size: 0.88em; color: #e06c75; border: 1px solid rgba(255,255,255,0.05); font-weight: 500;">${text}</code>`;
  };

  renderer.paragraph = function (text) {
    const codeMatch = text.match(/^(python|javascript|js|bash|sql|html|css)\s+((?:print|def|import|from|const|let|var|function|class|SELECT|INSERT|sudo|npm|pip|<|<!DOCTYPE)\b.*)$/s);

    if (codeMatch) {
      const lang = codeMatch[1];
      const content = codeMatch[2];
      return renderer.code(content, lang);
    }
    return `<p>${text}</p>`;
  };

  renderer.blockquote = function (quote) {
    const cleanQuote = quote.replace(/<p>|<\/p>/g, '').trim();
    const match = cleanQuote.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/);

    if (match) {
      const type = match[1].toLowerCase();
      const content = cleanQuote.replace(match[0], '').trim();
      const typeDisplay = type.charAt(0).toUpperCase() + type.slice(1);

      return `
        <div class="markdown-alert alert-${type}">
          <div class="markdown-alert-title">${typeDisplay}</div>
          <div>${content}</div>
        </div>
      `;
    }

    return `<blockquote>${quote}</blockquote>`;
  };

  marked.use({ renderer });
}

// =============================================================================
// Sanitize HTML to prevent XSS attacks
// =============================================================================

export function sanitizeMarkdown(text) {
  if (!text) return '';

  if (typeof marked === 'undefined') {
    console.error('marked is not defined - returning escaped text');
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

    const clean = DOMPurify.sanitize(html, DOMPURIFY_CONFIG);
    DOMPurify.removeHook('afterSanitizeAttributes');

    return clean;
  }

  console.warn('DOMPurify not available - returning unsanitized HTML');
  return html;
}