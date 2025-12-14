/**
 * Enhanced Markdown Renderer
 * 
 * Custom marked renderer with:
 * - Syntax highlighted code blocks
 * - GitHub-style alerts
 * - Enhanced tables
 * - Smart links
 */

import { marked, Renderer } from 'marked'
import type { Tokens } from 'marked'
import DOMPurify from 'dompurify'
import { highlightCode, getLanguageDisplayName } from './codeHighlighter'

// Create custom renderer
const renderer = new Renderer()

// Code blocks with syntax highlighting
renderer.code = function ({ text, lang }: Tokens.Code): string {
    const language = lang || 'plaintext'
    const highlighted = highlightCode(text, language)
    const displayLang = getLanguageDisplayName(language)

    return `
        <div class="code-block-wrapper">
            <div class="code-block-header">
                <span class="code-lang">${displayLang}</span>
                <button class="code-copy-btn" data-code="${encodeURIComponent(text)}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                    <span>Kopyala</span>
                </button>
            </div>
            <pre class="code-block-content"><code class="language-${language}">${highlighted}</code></pre>
        </div>
    `
}

// Inline code
renderer.codespan = function ({ text }: Tokens.Codespan): string {
    return `<code class="inline-code">${text}</code>`
}

// GitHub-style alerts in blockquotes
renderer.blockquote = function ({ text }: Tokens.Blockquote): string {
    const alertPatterns = [
        { regex: /\[!NOTE\]/i, type: 'note', icon: 'ℹ️', title: 'Not' },
        { regex: /\[!TIP\]/i, type: 'tip', icon: '💡', title: 'İpucu' },
        { regex: /\[!IMPORTANT\]/i, type: 'important', icon: '❗', title: 'Önemli' },
        { regex: /\[!WARNING\]/i, type: 'warning', icon: '⚠️', title: 'Uyarı' },
        { regex: /\[!CAUTION\]/i, type: 'caution', icon: '🚨', title: 'Dikkat' }
    ]

    for (const pattern of alertPatterns) {
        if (pattern.regex.test(text)) {
            const content = text.replace(pattern.regex, '').trim()
            return `
                <div class="alert alert-${pattern.type}">
                    <div class="alert-header">
                        <span class="alert-icon">${pattern.icon}</span>
                        <span class="alert-title">${pattern.title}</span>
                    </div>
                    <div class="alert-content">${content}</div>
                </div>
            `
        }
    }

    return `<blockquote class="quote-block">${text}</blockquote>`
}

// Enhanced links
renderer.link = function ({ href, title, text }: Tokens.Link): string {
    const titleAttr = title ? ` title="${title}"` : ''
    const isExternal = href.startsWith('http')
    const externalAttr = isExternal ? ' target="_blank" rel="noopener noreferrer"' : ''
    const icon = isExternal ? '<svg class="link-external-icon" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>' : ''

    return `<a href="${href}"${titleAttr}${externalAttr} class="enhanced-link">${text}${icon}</a>`
}

// Enhanced tables
renderer.table = function ({ header, rows }: Tokens.Table): string {
    const headerHtml = header.map(cell => `<th>${cell.text}</th>`).join('')
    const bodyHtml = rows.map(row =>
        `<tr>${row.map(cell => `<td>${cell.text}</td>`).join('')}</tr>`
    ).join('')

    return `
        <div class="table-wrapper">
            <table class="enhanced-table">
                <thead><tr>${headerHtml}</tr></thead>
                <tbody>${bodyHtml}</tbody>
            </table>
        </div>
    `
}

// Configure marked
marked.use({
    renderer,
    gfm: true,
    breaks: true,
})

/**
 * Render markdown to safe HTML
 */
export function renderMarkdown(content: string): string {
    if (!content) return ''

    const rawHtml = marked.parse(content) as string

    // Sanitize but allow our custom classes
    return DOMPurify.sanitize(rawHtml, {
        ADD_TAGS: ['button'],
        ADD_ATTR: ['data-code', 'target', 'rel'],
    })
}

/**
 * Handle code copy button clicks
 */
export function setupCodeCopyButtons(container: HTMLElement): void {
    const buttons = container.querySelectorAll('.code-copy-btn')

    buttons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const code = decodeURIComponent(btn.getAttribute('data-code') || '')
            try {
                await navigator.clipboard.writeText(code)
                const span = btn.querySelector('span')
                if (span) {
                    const original = span.textContent
                    span.textContent = 'Kopyalandı!'
                    setTimeout(() => {
                        span.textContent = original
                    }, 2000)
                }
            } catch (e) {
                console.error('Copy failed:', e)
            }
        })
    })
}
