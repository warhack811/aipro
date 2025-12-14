// =============================================================================
// UI MANAGEMENT - Sidebar, Modals, Theme, Search, etc.
// =============================================================================

import { ensureScrolledToBottom } from './utils.js';

// =============================================================================
// THEME MANAGEMENT
// =============================================================================

let themeIndex = 0;
const themes = ['dark', 'light', 'cosmic', 'ocean', 'sunset', 'ocean-deep', 'neon-night', 'minimal-light', 'forest-zen'];

export function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  applyTheme(saved);

  const select = document.getElementById('themeSelect');
  
  // Simple native select approach
  if (select) {
    select.value = saved;
    select.addEventListener('change', (e) => {
      applyTheme(e.target.value);
    });
  }
}

export function applyTheme(theme) {
  const next = themes.includes(theme) ? theme : 'dark';
  themeIndex = themes.indexOf(next);
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  const select = document.getElementById('themeSelect');
  if (select) select.value = next;
  
  // Update dropdown button text
  const textSpan = document.getElementById('themeDropdownText');
  const option = select?.querySelector(`option[value="${next}"]`);
  if (textSpan && option) {
    textSpan.textContent = option.textContent;
  }
  
  // Update active state in dropdown menu
  const menu = document.getElementById('themeDropdownMenu');
  menu?.querySelectorAll('.theme-dropdown-item').forEach(item => {
    item.classList.toggle('active', item.dataset.value === next);
  });
}

export function toggleTheme() {
  const next = themes[(themeIndex + 1) % themes.length];
  applyTheme(next);
}

// =============================================================================
// SIDEBAR MANAGEMENT
// =============================================================================

export function setSidebar(open) {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (!sidebar || !overlay) return;
  if (open) {
    sidebar.classList.add('active');
    overlay.classList.add('show');
  } else {
    sidebar.classList.remove('active');
    overlay.classList.remove('show');
  }
}

export function toggleSidebar(force) {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;
  const shouldOpen = force === true ? true : force === false ? false : !sidebar.classList.contains('active');
  setSidebar(shouldOpen);
}

export function initSidebar() {
  document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!sidebar || !overlay) return;
    const isOpen = sidebar.classList.contains('active');
    if (!isOpen) return;
    if (sidebar.contains(e.target)) return;
    if (e.target.closest('#menuToggle')) return;
    toggleSidebar(false);
  });

  document.getElementById('sidebarOverlay')?.addEventListener('click', () => toggleSidebar(false));
}

// =============================================================================
// MODAL MANAGEMENT
// =============================================================================

export async function closeModal(id) {
  const modal = document.getElementById(id);
  modal?.classList.remove('active');
  modal?.classList.remove('show');
  if (modal) modal.style.display = '';
  if (id === 'galleryModal') {
    const { hideGalleryLightbox } = await import('./images.js');
    hideGalleryLightbox();
  }
}

// =============================================================================
// EMOJI PANEL
// =============================================================================

const emojis = ['😀', '😍', '🎉', '🔥', '👍', '👎', '❤️', '💯', '🤔', '😎', '🥳', '😴', '🤯', '🙏', '👏', '🍕', '☕', '🚀', '💡', '⚡'];

export function toggleEmoji() {
  const p = document.getElementById('emojiPanel');
  p.classList.toggle('active');
  if (!p.children.length) {
    emojis.forEach(e => {
      const s = document.createElement('span');
      s.textContent = e;
      s.onclick = () => {
        document.getElementById('msgInput').value += e;
        p.classList.remove('active');
      };
      p.appendChild(s);
    });
  }
}

export function initEmojiPanel() {
  window.addEventListener('click', e => {
    if (!e.target.closest('#emojiPanel') && !e.target.closest('.icon-btn[title="Emoji"]')) {
      document.getElementById('emojiPanel').classList.remove('active');
    }
  });
}

// =============================================================================
// SEARCH
// =============================================================================

let searchTerm = '';

export function toggleSearch() {
  const box = document.getElementById('searchBox');
  box.style.display = box.style.display === 'none' ? 'inline-block' : 'none';
  if (box.style.display === 'inline-block') box.focus();
}

export function highlightMessages() {
  document.querySelectorAll('.message').forEach(msg => {
    const txt = msg.textContent.toLowerCase();
    if (!searchTerm) {
      msg.style.background = '';
      msg.style.boxShadow = '';
      return;
    }
    if (txt.includes(searchTerm)) {
      msg.style.background = 'rgba(99, 102, 241, 0.2)';
      msg.style.boxShadow = '0 0 0 2px var(--primary)';
      msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      msg.style.background = '';
      msg.style.boxShadow = '';
    }
  });
}

export function initSearch() {
  document.getElementById('searchBox')?.addEventListener('input', e => {
    searchTerm = e.target.value.toLowerCase();
    highlightMessages();
  });
}

// =============================================================================
// CHAT EXPORT
// =============================================================================

export async function exportChat(format, currentConvId) {
  if (!currentConvId) return alert('Aktif sohbet yok.');
  const res = await fetch(`/api/v1/user/conversations/${currentConvId}`);
  const msgs = await res.json();
  if (format === 'md') {
    let md = `# Sohbet ${currentConvId}\n\n`;
    msgs.forEach(m => {
      md += `**${m.role === 'user' ? 'Kullanıcı' : 'Mami'}** – ${new Date(m.created_at).toLocaleString('tr-TR')}\n\n${m.text}\n\n---\n\n`;
    });
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${currentConvId}.md`;
    a.click();
  }
}

// =============================================================================
// DRAG & DROP FILE UPLOAD
// =============================================================================

export function initDragDrop(uploadCallback) {
  const dropZone = document.body;
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.style.background = 'rgba(99, 102, 241, 0.1)';
  });
  dropZone.addEventListener('dragleave', () => {
    dropZone.style.background = '';
  });
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.style.background = '';
    const files = e.dataTransfer.files;
    if (files.length && uploadCallback) uploadCallback({ files });
  });
}

// =============================================================================
// KEYBOARD SHORTCUTS
// =============================================================================

export function initKeyboardShortcuts(voiceCallback) {
  window.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      if (voiceCallback) voiceCallback();
    }
    if (e.ctrlKey && e.shiftKey && e.key === 'l') {
      e.preventDefault();
      toggleTheme();
    }
  });
}

// =============================================================================
// SCROLL BEHAVIOR
// =============================================================================

let autoScroll = true;

export function initScrollBehavior() {
  const area = document.getElementById('chatArea');
  if (!area) return;
  
  area.addEventListener('scroll', () => {
    const atBottom = area.scrollHeight - area.scrollTop - area.clientHeight < 50;
    autoScroll = atBottom;
  });
}

export function getAutoScroll() {
  return autoScroll;
}

export function setAutoScroll(value) {
  autoScroll = value;
}