/**
 * Code Highlighter - Prism.js integration
 * 
 * Syntax highlighting for code blocks in messages
 */

import Prism from 'prismjs'

// Import common languages
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-jsx'
import 'prismjs/components/prism-tsx'
import 'prismjs/components/prism-css'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-sql'
import 'prismjs/components/prism-markdown'
import 'prismjs/components/prism-yaml'

// Language aliases
const languageAliases: Record<string, string> = {
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'sh': 'bash',
    'shell': 'bash',
    'yml': 'yaml',
}

/**
 * Highlight code with Prism
 */
export function highlightCode(code: string, language: string): string {
    const lang = languageAliases[language] || language || 'plaintext'

    if (Prism.languages[lang]) {
        try {
            return Prism.highlight(code, Prism.languages[lang], lang)
        } catch (e) {
            console.warn(`[Prism] Failed to highlight ${lang}:`, e)
        }
    }

    // Fallback: escape HTML
    return escapeHtml(code)
}

/**
 * Get language display name
 */
export function getLanguageDisplayName(lang: string): string {
    const displayNames: Record<string, string> = {
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'python': 'Python',
        'jsx': 'React JSX',
        'tsx': 'React TSX',
        'css': 'CSS',
        'json': 'JSON',
        'bash': 'Bash',
        'sql': 'SQL',
        'markdown': 'Markdown',
        'yaml': 'YAML',
        'html': 'HTML',
        'plaintext': 'Text',
    }

    const normalized = languageAliases[lang] || lang || 'plaintext'
    return displayNames[normalized] || lang.toUpperCase()
}

/**
 * Escape HTML entities
 */
function escapeHtml(text: string): string {
    const map: Record<string, string> = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    }
    return text.replace(/[&<>"']/g, (m) => map[m])
}

/**
 * Copy code to clipboard
 */
export async function copyCode(code: string): Promise<boolean> {
    try {
        await navigator.clipboard.writeText(code)
        return true
    } catch {
        return false
    }
}
