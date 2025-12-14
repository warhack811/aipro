// =============================================================================
// PERSONA & SETTINGS MANAGEMENT
// =============================================================================

// Persona listesi cache
let personasCache = [];
let activePersona = 'standard';

// Toggle'lar (localStorage'da saklanır)
const TOGGLE_STORAGE_KEY = 'mami_chat_toggles';
let chatToggles = {
  web: true,
  image: true
};

// Model tercihi
let preferredModel = 'auto';

// HATA #5 FIX: Ortak model select sync fonksiyonu
function syncModelSelectUI() {
  const savedModel = localStorage.getItem('mami_preferred_model') || 'auto';
  preferredModel = savedModel;

  const modelSelect = document.getElementById('modelSelect');
  if (modelSelect) {
    modelSelect.value = savedModel;
  }

  return savedModel;
}

// Persona iconları
const PERSONA_ICONS = {
  'standard': '⚡',
  'friendly': '😊',
  'romantic': '💕',
  'professional': '💼',
  'creative': '🎨',
  'coder': '💻',
  'researcher': '🔬',
  'default': '🤖'
};

// =============================================================================
// PERSONA MANAGEMENT
// =============================================================================

/**
 * Sohbet Ayarları modalını aç
 */
export async function openChatSettings() {
  const modal = document.getElementById('chatSettingsModal');
  if (!modal) return;

  await loadPersonas();
  loadToggles();

  // HATA #5 FIX: Kullanıcı fonksiyon kullanılıyor
  syncModelSelectUI();

  modal.classList.add('show');
  modal.style.display = 'flex';
}

/**
 * Persona listesini API'den yükle
 */
export async function loadPersonas() {
  try {
    const listRes = await fetch('/api/v1/user/personas', {
      credentials: 'include'
    });

    if (listRes.ok) {
      const data = await listRes.json();
      personasCache = data.personas || [];

      const select = document.getElementById('personaSelect');
      if (select) {
        select.innerHTML = personasCache.map(p => {
          const icon = PERSONA_ICONS[p.name] || PERSONA_ICONS['default'];
          return `<option value="${p.name}">${icon} ${p.display_name}</option>`;
        }).join('');
      }
    }

    const activeRes = await fetch('/api/v1/user/personas/active', {
      credentials: 'include'
    });

    if (activeRes.ok) {
      const data = await activeRes.json();
      activePersona = data.active_persona || 'standard';

      const select = document.getElementById('personaSelect');
      if (select) select.value = activePersona;

      updatePersonaBadge(activePersona, data.display_name || 'Standart');
    }
  } catch (err) {
    console.error('Persona yüklenemedi:', err);
  }
}

/**
 * Persona değişikliği
 */
export async function onPersonaChange(personaName) {
  try {
    const res = await fetch('/api/v1/user/personas/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ persona: personaName })
    });

    if (res.ok) {
      const data = await res.json();
      activePersona = personaName;

      const persona = personasCache.find(p => p.name === personaName);
      updatePersonaBadge(personaName, persona?.display_name || personaName);

      const warning = document.getElementById('personaWarning');
      if (warning) warning.style.display = 'none';

      console.log(`[SETTINGS] Persona değiştirildi: ${personaName}`);
    } else {
      const error = await res.json();

      if (res.status === 403) {
        const warning = document.getElementById('personaWarning');
        if (warning) {
          warning.textContent = `⚠️ ${error.detail || 'Bu mod için özel izin gerekli'}`;
          warning.style.display = 'block';
        }

        const select = document.getElementById('personaSelect');
        if (select) select.value = activePersona;
      }
    }
  } catch (err) {
    console.error('Persona değiştirilemedi:', err);
  }
}

/**
 * Persona badge'ini güncelle
 */
export function updatePersonaBadge(personaName, displayName) {
  const icon = PERSONA_ICONS[personaName] || PERSONA_ICONS['default'];

  const iconEl = document.getElementById('personaIcon');
  const nameEl = document.getElementById('personaName');

  // HATA #4 FIX: Element bulunamazsa hata logla
  if (!iconEl || !nameEl) {
    console.error('[PERSONA] Badge elementleri bulunamadı. DOM yüklenmiş mi?', {
      personaIcon: iconEl ? 'var' : 'yok',
      personaName: nameEl ? 'var' : 'yok'
    });
    return;
  }

  iconEl.textContent = icon;
  nameEl.textContent = displayName || personaName;
}

// =============================================================================
// TOGGLES & SETTINGS
// =============================================================================

/**
 * Toggle'ları localStorage'dan yükle
 */
export function loadToggles() {
  try {
    const saved = localStorage.getItem(TOGGLE_STORAGE_KEY);
    if (saved) {
      chatToggles = JSON.parse(saved);
    }
  } catch (e) {
    console.warn('Toggle yüklenemedi:', e);
  }

  const webToggle = document.getElementById('toggleWeb');
  const imageToggle = document.getElementById('toggleImage');

  if (webToggle) webToggle.checked = chatToggles.web !== false;
  if (imageToggle) imageToggle.checked = chatToggles.image !== false;

  // HATA #5 FIX: Ortak fonksiyon kullanılıyor
  syncModelSelectUI();
}

/**
 * Toggle değişikliği
 */
export function onToggleChange(key, value) {
  chatToggles[key] = value;
  localStorage.setItem(TOGGLE_STORAGE_KEY, JSON.stringify(chatToggles));
  console.log(`[SETTINGS] ${key} toggle: ${value}`);
}

/**
 * Model değişikliği
 */
export function onModelChange(value) {
  preferredModel = value;
  localStorage.setItem('mami_preferred_model', value);
  console.log(`[SETTINGS] Model: ${value}`);
}

/**
 * Preferred model'i al
 */
export function getPreferredModel() {
  return preferredModel || localStorage.getItem('mami_preferred_model') || 'auto';
}

// =============================================================================
// INITIALIZATION
// =============================================================================

/**
 * Sayfa yüklendiğinde persona/toggle bilgilerini yükle
 */
export async function initChatSettings() {
  // localStorage'dan model tercihini yükle
  const savedModel = localStorage.getItem('mami_preferred_model') || 'auto';
  preferredModel = savedModel;

  loadToggles();

  try {
    const activeRes = await fetch('/api/v1/user/personas/active', {
      credentials: 'include'
    });

    if (activeRes.ok) {
      const data = await activeRes.json();
      activePersona = data.active_persona || 'standard';
      updatePersonaBadge(activePersona, data.display_name || 'Standart');
    }
  } catch (err) {
    // Sessizce devam et
  }
}