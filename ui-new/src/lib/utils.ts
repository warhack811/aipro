/**
 * Utility Functions - cn() and other helpers
 * 
 * cn() combines clsx and tailwind-merge for optimal class handling
 */

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Combines class names with clsx and merges Tailwind classes
 * Use this everywhere for conditional and merged classes
 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

/**
 * Format relative time (e.g., "2 dakika önce")
 */
export function formatRelativeTime(date: Date | string): string {
    const now = new Date()
    const then = new Date(date)
    const diffMs = now.getTime() - then.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)

    if (diffSec < 60) return 'Az önce'
    if (diffMin < 60) return `${diffMin} dakika önce`
    if (diffHour < 24) return `${diffHour} saat önce`
    if (diffDay < 7) return `${diffDay} gün önce`

    return then.toLocaleDateString('tr-TR', {
        day: 'numeric',
        month: 'short'
    })
}

/**
 * Format time (e.g., "14:30")
 */
export function formatTime(date: Date | string): string {
    return new Date(date).toLocaleTimeString('tr-TR', {
        hour: '2-digit',
        minute: '2-digit'
    })
}

/**
 * Format date (e.g., "12 Aralık 2024")
 */
export function formatDate(date: Date | string): string {
    return new Date(date).toLocaleDateString('tr-TR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    })
}

/**
 * Get time of day for personalized greetings
 */
export function getTimeOfDay(): 'morning' | 'afternoon' | 'evening' | 'night' {
    const hour = new Date().getHours()
    if (hour >= 5 && hour < 12) return 'morning'
    if (hour >= 12 && hour < 17) return 'afternoon'
    if (hour >= 17 && hour < 21) return 'evening'
    return 'night'
}

/**
 * Get greeting based on time of day
 */
export function getGreeting(): string {
    const greetings = {
        morning: 'Günaydın',
        afternoon: 'İyi günler',
        evening: 'İyi akşamlar',
        night: 'İyi geceler'
    }
    return greetings[getTimeOfDay()]
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeout: ReturnType<typeof setTimeout> | null = null

    return (...args: Parameters<T>) => {
        if (timeout) clearTimeout(timeout)
        timeout = setTimeout(() => func(...args), wait)
    }
}

/**
 * Throttle function
 */
export function throttle<T extends (...args: Parameters<T>) => ReturnType<T>>(
    func: T,
    limit: number
): (...args: Parameters<T>) => void {
    let inThrottle = false

    return (...args: Parameters<T>) => {
        if (!inThrottle) {
            func(...args)
            inThrottle = true
            setTimeout(() => (inThrottle = false), limit)
        }
    }
}

/**
 * Generate unique ID
 */
export function generateId(prefix = 'id'): string {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength - 3) + '...'
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
    try {
        await navigator.clipboard.writeText(text)
        return true
    } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea')
        textarea.value = text
        textarea.style.position = 'fixed'
        textarea.style.opacity = '0'
        document.body.appendChild(textarea)
        textarea.select()
        try {
            document.execCommand('copy')
            return true
        } finally {
            document.body.removeChild(textarea)
        }
    }
}

/**
 * Sleep for a given duration
 */
export function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Check if device is mobile
 */
export function isMobile(): boolean {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(max-width: 768px)').matches
}

/**
 * Check if device supports touch
 */
export function isTouchDevice(): boolean {
    if (typeof window === 'undefined') return false
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

/**
 * Get file extension
 */
export function getFileExtension(filename: string): string {
    return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2)
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

/**
 * Escape HTML entities
 */
export function escapeHtml(text: string): string {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
}

/**
 * Decode HTML entities
 * Converts &#x27; -> ' and other HTML entities to their character equivalents
 *
 * @param text - Text containing HTML entities
 * @returns Decoded text with entities converted to characters
 *
 * @example
 * decodeHtmlEntities("airplane&#x27;s") // returns "airplane's"
 * decodeHtmlEntities("&lt;div&gt;") // returns "<div>"
 */
export function decodeHtmlEntities(text: string): string {
    if (!text) return text
    const textarea = document.createElement('textarea')
    textarea.innerHTML = text
    return textarea.value
}

/**
 * Extract domain from URL
 */
export function extractDomain(url: string): string {
    try {
        const hostname = new URL(url).hostname
        return hostname.replace('www.', '')
    } catch {
        return url
    }
}
