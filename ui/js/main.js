// =============================================================================
// MAIN ENTRY POINT - Mami AI Chat Interface (ES6 Module)
// =============================================================================
const DEBUG_MODE = false;
if (DEBUG_MODE) console.log("[UI] Modular build v2 loaded");

// =============================================================================
// IMPORTS
// =============================================================================

// Core chat functionality
import {
  connectWebSocket,
  loadConversations,
  send,
  handleEnter,
  addMessage,
  deleteAllConversations,
  deleteConversation,
  loadChat,
  startNewChat,
  logout,
  getCurrentConvId,
  setActivePersona,
  initVisibility,
  initPWA,
  sanitizeMarkdown,
  showToast,
  copyMessage,
  likeMessage,
  dislikeMessage,
  regenerateMessage,
  sendSuggestion,
  updateCharCount
} from './chat-core.js';

// UI components
import {
  initTheme,
  initSidebar,
  initEmojiPanel,
  initSearch,
  initDragDrop,
  initKeyboardShortcuts,
  initScrollBehavior,
  toggleSidebar,
  toggleEmoji,
  toggleSearch,
  toggleTheme,
  closeModal,
  exportChat
} from './ui.js';

// Persona & Settings
import {
  initChatSettings,
  openChatSettings,
  onPersonaChange,
  onToggleChange,
  onModelChange,
  loadPersonas
} from './persona.js';

// Memory management
import {
  openMemoryModal,
  saveMemory,
  editMemory,
  deleteMemory,
  deleteAllMemories
} from './memory.js';

// Gallery & Images
import { openGallery, closeLightbox, downloadLightboxImage, previewGalleryImage, downloadGalleryImage, retryImage, openLightbox, hideGalleryLightbox, refreshImagePendingJobs } from './images.js';

// Utilities
import { copyCode, autoResize } from './utils.js';

// =============================================================================
// VOICE RECOGNITION
// =============================================================================
const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
const rec = Speech ? new Speech() : null;

if (rec) {
  rec.lang = 'tr-TR';
  rec.interimResults = false;
  rec.maxAlternatives = 1;

  rec.onresult = (e) => {
    const text = e.results[0][0].transcript;
    const input = document.getElementById('msgInput');
    if (input) {
      input.value = text;
      send();
    }
  };

  rec.onerror = () => {
    addMessage('bot', '⛔ Ses tanınamadı, lütfen tekrar deneyin.');
  };
}

function startVoice() {
  if (rec) rec.start();
}

// =============================================================================
// GLOBAL FUNCTION EXPOSURE (for HTML onclick handlers)
// =============================================================================

// Core chat
window.send = send;
window.handleEnter = handleEnter;
window.deleteAllConversations = deleteAllConversations;
window.deleteConversation = deleteConversation;
window.loadChat = loadChat;
window.startNewChat = startNewChat;
window.logout = logout;

// UI
window.toggleSidebar = toggleSidebar;
window.toggleEmoji = toggleEmoji;
window.toggleSearch = toggleSearch;
window.toggleTheme = toggleTheme;
window.closeModal = closeModal;
window.exportChat = (format) => exportChat(format, getCurrentConvId());
window.startVoice = startVoice;

// Modern UI features
window.showToast = showToast;
window.copyMessage = copyMessage;
window.likeMessage = likeMessage;
window.dislikeMessage = dislikeMessage;
window.regenerateMessage = regenerateMessage;
window.sendSuggestion = sendSuggestion;
window.updateCharCount = updateCharCount;

// Persona & Settings
window.openChatSettings = openChatSettings;
window.onPersonaChange = async (name) => {
  await onPersonaChange(name);
  setActivePersona(name);
};
window.onToggleChange = onToggleChange;
window.onModelChange = onModelChange;

// Memory
window.openMemoryModal = openMemoryModal;
window.saveMemory = saveMemory;
window.editMemory = editMemory;
window.deleteMemory = deleteMemory;
window.deleteAllMemories = deleteAllMemories;

// Gallery & Images
window.openGallery = openGallery;
window.closeLightbox = closeLightbox;
window.downloadLightboxImage = downloadLightboxImage;
window.previewGalleryImage = previewGalleryImage;
window.downloadGalleryImage = downloadGalleryImage;
window.retryImage = retryImage;
window.openLightbox = openLightbox;
window.hideGalleryLightbox = hideGalleryLightbox;

// Utilities
window.copyCode = copyCode;
window.autoResize = autoResize;

// =============================================================================
// INITIALIZATION
// =============================================================================
window.addEventListener('DOMContentLoaded', async () => {
  if (DEBUG_MODE) console.log('[UI] Initializing modules...');

  // Initialize theme first (visual)
  initTheme();

  // Initialize UI components
  initSidebar();
  initEmojiPanel();
  initSearch();
  initScrollBehavior();

  // Initialize keyboard shortcuts
  initKeyboardShortcuts(startVoice);

  // Initialize drag & drop
  initDragDrop((input) => uploadFile(input, getCurrentConvId(), addMessage));

  // Initialize chat settings (persona, toggles)
  await initChatSettings();

  // Initialize WebSocket
  connectWebSocket();

  // Load conversations
  loadConversations();

  // Refresh image pending jobs
  refreshImagePendingJobs();

  // Initialize visibility tracking
  initVisibility();

  // Initialize PWA
  initPWA();

  if (DEBUG_MODE) console.log('[UI] All modules initialized successfully');
});