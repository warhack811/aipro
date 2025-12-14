// =============================================================================
// IMAGE MANAGEMENT - Upload, Gallery, Lightbox, Progress
// =============================================================================

import { escapeHtmlAttr, decodeHtmlEntities, ensureScrolledToBottom } from './utils.js';

// =============================================================================
// IMAGE PENDING PROGRESS
// =============================================================================

let pendingDiv = null;
let pendingJobId = null;
let pendingJobsCache = {};
const pendingMessagesRemoved = new Set();

export function addImagePending(queuePos = 1, jobId = null, progress = 0) {
  pendingDiv?.remove();
  pendingDiv = document.createElement('div');
  pendingDiv.className = 'message bot image-pending';
  pendingJobId = jobId;
  if (jobId) pendingDiv.dataset.jobId = jobId;

  // Queue text - "Sizde" if progress > 0, otherwise queue position
  const queueText = progress > 0 ? 'Sizde' : queuePos;

  pendingDiv.innerHTML = `
    <div class="msg-avatar">🎨</div>
    <div class="msg-bubble">
      <div class="pending-header">
        <span class="pending-title">🖼️ Görsel Üretimi</span>
        <span class="pending-queue">Sıra: ${queueText}</span>
      </div>
      <div class="pending-status">${progress > 0 ? 'Üretiliyor...' : 'Kuyruğa alındı, sıranız bekleniyor...'}</div>
      <div class="pending-progress-container">
        <div class="pending-progress-bar" style="width:${progress}%"></div>
      </div>
      <div class="pending-progress-text">${progress}%</div>
      <span class="msg-time">${new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</span>
    </div>`;
  document.getElementById('chatArea')?.appendChild(pendingDiv);
  ensureScrolledToBottom();
}

export function updatePendingQueueText(queuePos, progress = 0) {
  const span = pendingDiv?.querySelector('.pending-queue');
  const status = pendingDiv?.querySelector('.pending-status');
  if (span) {
    span.textContent = progress > 0 ? 'Sıra: Sizde' : `Sıra: ${queuePos}`;
  }
  if (status) {
    status.textContent = progress > 0 ? 'Üretiliyor...' : 'Kuyruğa alındı, sıranız bekleniyor...';
  }
}

export function updatePendingProgressBar(progress) {
  const bar = pendingDiv?.querySelector('.pending-progress-bar');
  const text = pendingDiv?.querySelector('.pending-progress-text');
  const queue = pendingDiv?.querySelector('.pending-queue');
  const status = pendingDiv?.querySelector('.pending-status');

  if (bar) bar.style.width = `${Math.min(Math.max(progress, 0), 100)}%`;
  if (text) text.textContent = `${Math.round(progress)}%`;

  // Update queue text when progress starts
  if (progress > 0) {
    if (queue) queue.textContent = 'Sıra: Sizde';
    if (status) status.textContent = 'Üretiliyor...';
  }
}

export function removeImagePendingCard() {
  if (!pendingDiv) return;
  pendingDiv.remove();
  pendingDiv = null;
  pendingJobId = null;
}

export function removeImagePendingChatMessage(jobId) {
  if (!jobId || pendingMessagesRemoved.has(jobId)) return;
  const matches = Array.from(document.querySelectorAll('.message[data-image-pending="true"]'));
  const target = matches.reverse().find(() => true);
  if (target) {
    target.remove();
    pendingMessagesRemoved.add(jobId);
  }
}

export function finalizePendingJob(jobId) {
  if (jobId) {
    delete pendingJobsCache[jobId];
    removeImagePendingChatMessage(jobId);
  }
  removeImagePendingCard();
}

export function handleImageProgressEvent(data, currentConvId) {
  if (!data || data.type !== 'image_progress') return;
  if (!data.conversation_id || data.conversation_id !== currentConvId) return;
  const queuePos = data.queue_pos ?? 1;
  const progress = typeof data.progress === 'number' ? data.progress : 0;
  const jobId = data.job_id || pendingJobId || null;
  if (jobId) {
    pendingJobsCache[jobId] = {
      job_id: jobId,
      conversation_id: data.conversation_id,
      queue_pos: queuePos,
      progress,
    };
  }
  if (!pendingDiv || pendingJobId !== jobId) {
    addImagePending(queuePos, jobId);
  } else {
    updatePendingQueueText(queuePos);
  }
  updatePendingProgressBar(progress);
  if (progress >= 100) {
    finalizePendingJob(jobId);
  }
}

export async function refreshImagePendingJobs() {
  try {
    const res = await fetch('/api/v1/user/image/status');
    if (!res.ok) return;
    const data = await res.json();
    pendingJobsCache = {};
    (data.pending_jobs || []).forEach(job => {
      if (job.job_id) {
        pendingJobsCache[job.job_id] = job;
      }
    });
  } catch (error) {
    console.error(error);
  }
}

export function showPendingForCurrentConversation(currentConvId) {
  if (!currentConvId) return;
  const job = Object.values(pendingJobsCache).find(j => j.conversation_id === currentConvId);
  if (job) {
    handleImageProgressEvent({
      type: 'image_progress',
      conversation_id: job.conversation_id,
      queue_pos: job.queue_pos,
      progress: job.progress ?? 0,
      job_id: job.job_id,
    }, currentConvId);
  } else if (pendingDiv) {
    removeImagePendingCard();
  }
}

// =============================================================================
// LIGHTBOX
// =============================================================================

export function openLightbox(src, prompt = '') {
  document.activeElement?.blur();
  const box = document.getElementById('lightbox');
  const img = document.getElementById('lightboxImg');
  const promptEl = document.getElementById('lightboxPrompt');
  const downloadBtn = document.getElementById('lightboxDownload');
  if (img) img.src = src || '';
  if (promptEl) promptEl.textContent = prompt || 'Prompt bilgisi yok.';
  if (downloadBtn) {
    if (src) {
      downloadBtn.disabled = false;
      downloadBtn.setAttribute('data-url', src);
    } else {
      downloadBtn.disabled = true;
      downloadBtn.removeAttribute('data-url');
    }
  }
  box?.classList.add('active');
}

export function closeLightbox() {
  const box = document.getElementById('lightbox');
  if (!box) return;
  box.classList.remove('active');
  const img = document.getElementById('lightboxImg');
  if (img) img.src = '';
  const promptEl = document.getElementById('lightboxPrompt');
  if (promptEl) promptEl.textContent = 'Prompt bilgisi yok.';
  const downloadBtn = document.getElementById('lightboxDownload');
  if (downloadBtn) {
    downloadBtn.disabled = true;
    downloadBtn.removeAttribute('data-url');
  }
}

export function downloadLightboxImage(btn) {
  const url = btn?.getAttribute('data-url');
  if (!url) return;
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = url.split('/').pop()?.split('?')[0] || 'mami-image.png';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

export function wrapImages() {
  document.querySelectorAll('.message img').forEach(img => {
    img.style.cursor = 'zoom-in';
    const baseMessage = img.closest('.message');
    const promptHolder = baseMessage?.querySelector('.image-prompt');
    const datasetPrompt = baseMessage?.dataset.imagePrompt || '';
    const rawPrompt = promptHolder?.getAttribute('data-prompt') || datasetPrompt;
    const promptText = rawPrompt ? decodeHtmlEntities(rawPrompt) : '';
    img.dataset.prompt = promptText;
    img.onclick = () => openLightbox(img.src, promptText);
  });
}

export function retryImage(src, btn) {
  const img = btn.previousElementSibling;
  img.src = src + '?retry=' + Date.now();
  img.style.display = 'block';
  btn.style.display = 'none';
  img.onload = () => btn.remove();
  img.onerror = () => btn.style.display = 'block';
}

// =============================================================================
// GALLERY
// =============================================================================

export async function openGallery() {
  document.getElementById('galleryModal')?.classList.add('active');
  hideGalleryLightbox();
  try {
    const res = await fetch('/api/v1/user/images?limit=20');
    if (!res.ok) throw new Error('Görseller yüklenemedi.');
    const data = await res.json();
    const grid = document.getElementById('galleryGrid');
    if (!grid) return;
    if (!Array.isArray(data) || !data.length) {
      grid.innerHTML = '<div class="gallery-placeholder">Henüz görsel geçmişi bulunamadı.</div>';
      return;
    }
    grid.innerHTML = data.map(img => {
      const prompt = img.prompt || '';
      const snippet = prompt.length > 30 ? `${prompt.slice(0, 30)}...` : prompt;
      const rawUrl = img.image_url || '';
      const safeUrl = escapeHtmlAttr(rawUrl);
      const safeSnippet = escapeHtmlAttr(snippet || 'Prompt yok');
      return `<div class="gallery-item" data-url="${encodeURIComponent(rawUrl)}" data-prompt="${encodeURIComponent(prompt)}" onclick="previewGalleryImage(this)">
            <img src="${safeUrl}" loading="lazy" alt="Galeriden görsel" />
            <div class="gallery-thumb-prompt">${safeSnippet}</div>
          </div>`;
    }).join('');
  } catch (error) {
    const grid = document.getElementById('galleryGrid');
    if (grid) {
      grid.innerHTML = '<div class="gallery-placeholder">Galeriler yüklenemedi.</div>';
    }
    console.error(error);
  }
}

export function openGalleryLightbox(url, prompt) {
  if (!url) return;
  const overlay = document.getElementById('galleryLightbox');
  const img = document.getElementById('galleryLightboxImg');
  const promptEl = document.getElementById('galleryLightboxPrompt');
  const downloadBtn = document.getElementById('galleryLightboxDownload');
  if (img) img.src = url;
  if (promptEl) promptEl.textContent = prompt || 'Prompt bilgisi yok.';
  if (downloadBtn) {
    downloadBtn.setAttribute('data-url', url);
    downloadBtn.disabled = false;
  }
  overlay?.classList.add('active');
}

export function hideGalleryLightbox() {
  const overlay = document.getElementById('galleryLightbox');
  const img = document.getElementById('galleryLightboxImg');
  const downloadBtn = document.getElementById('galleryLightboxDownload');
  if (img) img.src = '';
  if (downloadBtn) {
    downloadBtn.setAttribute('data-url', '');
    downloadBtn.disabled = true;
  }
  overlay?.classList.remove('active');
}

export function previewGalleryImage(item) {
  if (!item) return;
  const encodedUrl = item.getAttribute('data-url');
  if (!encodedUrl) return;
  const url = decodeURIComponent(encodedUrl);
  const rawPrompt = item.getAttribute('data-prompt') || '';
  openGalleryLightbox(url, decodeURIComponent(rawPrompt) || 'Prompt bilgisi yok.');
}

export function downloadGalleryImage(btn) {
  const url = btn?.getAttribute('data-url');
  if (!url) return;
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = url.split('/').pop()?.split('?')[0] || 'mami-image.png';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

// =============================================================================
// FILE UPLOAD
// =============================================================================

export async function uploadFile(input, currentConvId, addMessageCallback) {
  const file = input.files?.[0] || input[0];
  if (!file) return;
  addMessageCallback('user', `📎 Dosya Yükleniyor: ${file.name}`);
  const formData = new FormData();
  formData.append('file', file);
  if (currentConvId) formData.append('conversation_id', currentConvId);
  try {
    const res = await fetch('/api/v1/user/upload', { method: 'POST', body: formData });
    const data = await res.json();
    addMessageCallback('bot', res.ok ? `✅ **${data.filename}** analiz edildi ve RAG sistemine eklendi.` : `❌ Hata: ${data.detail}`);
  } catch (e) {
    addMessageCallback('bot', `❌ Hata: ${e}`);
  }
  if (input.target) input.value = '';
}