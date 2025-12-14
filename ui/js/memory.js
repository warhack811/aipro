// =============================================================================
// MEMORY MANAGEMENT - CRUD Operations
// =============================================================================

import { escapeHtml, escapeHtmlAttr } from './utils.js';

// =============================================================================
// MEMORY MODAL
// =============================================================================

export async function openMemoryModal() {
  const modal = document.getElementById('memoryModal');
  if (modal) {
    modal.style.display = '';
    modal.classList.add('active');
  }
  await loadMemoryList();
}

// =============================================================================
// MEMORY LIST
// =============================================================================

export async function loadMemoryList() {
  const listEl = document.getElementById('memoryList');
  if (!listEl) return;
  try {
    const res = await fetch('/api/v1/user/memories');
    const data = await res.json();
    if (!Array.isArray(data) || !data.length) {
      listEl.innerHTML = '<div class="memory-card">Henüz hafıza kaydı yok.</div>';
      return;
    }
    listEl.innerHTML = data.map(m => {
      const importance = (typeof m.importance === 'number') ? m.importance.toFixed(2) : '0.50';
      const created = escapeHtml(m.created_at || '');
      const text = escapeHtml(m.text || '');
      return `<div class="memory-card" data-id="${escapeHtmlAttr(m.id)}" data-text="${escapeHtmlAttr(m.text)}">
            <div class="memory-text">${text}</div>
            <div class="memory-meta">
              <span>${created}</span>
              <span>Önem: ${importance}</span>
            </div>
            <div class="memory-actions">
              <button type="button" onclick="editMemory(this)">Güncelle</button>
              <button type="button" onclick="deleteMemory(this)">Sil</button>
            </div>
          </div>`;
    }).join('');
  } catch (error) {
    listEl.innerHTML = '<div class="memory-card">Hafıza yüklenemedi.</div>';
    console.error(error);
  }
}

// =============================================================================
// MEMORY CRUD
// =============================================================================

export async function saveMemory() {
  const input = document.getElementById('memoryInput');
  const importanceEl = document.getElementById('memoryImportance');
  if (!input || !importanceEl) return;
  const text = String(input.value || '').trim();
  if (!text) return;
  const importance = Math.min(1, Math.max(0, parseFloat(importanceEl.value) || 0.5));
  try {
    const res = await fetch('/api/v1/user/memories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, importance }),
    });
    if (!res.ok) throw new Error('Hafıza kaydedilemedi.');
    input.value = '';
    importanceEl.value = '0.5';
    await loadMemoryList();
  } catch (error) {
    alert(error.message || 'Hafıza kaydedilemedi.');
  }
}

export async function editMemory(button) {
  const card = button.closest('.memory-card');
  const id = card?.dataset.id;
  const current = card?.dataset.text || '';
  if (!id) return;
  const text = prompt('Hafızayı güncelle', current);
  if (text === null) return;
  const trimmed = String(text).trim();
  if (!trimmed) return;
  try {
    const res = await fetch(`/api/v1/user/memories/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: trimmed }),
    });
    if (!res.ok) throw new Error('Güncelleme başarısız.');
    await loadMemoryList();
  } catch (error) {
    alert(error.message || 'Hafıza güncellenemedi.');
  }
}

export async function deleteMemory(button) {
  const card = button.closest('.memory-card');
  const id = card?.dataset.id;
  if (!id || !confirm('Bu hafızayı silmek istediğinizden emin misiniz?')) return;
  try {
    const res = await fetch(`/api/v1/user/memories/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Silme başarısız.');
    await loadMemoryList();
  } catch (error) {
    alert(error.message || 'Hafıza silinemedi.');
  }
}

export async function deleteAllMemories() {
  if (!confirm('Tüm hafıza kayıtlarını silmek istediğinizden emin misiniz?')) return;
  try {
    const res = await fetch('/api/v1/user/memories/all-delete', { method: 'DELETE' });
    if (!res.ok) throw new Error('Silme başarısız.');
    await loadMemoryList();
  } catch (error) {
    alert(error.message || 'Hafızalar silinemedi.');
  }
}