/**
 * Error Message Utilities
 * 
 * Kullanıcı dostu hata mesajları için utility fonksiyonları.
 * Teknik hataları anlaşılır Türkçe mesajlara çevirir.
 */

// Error code mappings
const HTTP_ERROR_MESSAGES: Record<number, string> = {
    400: 'İstek hatalı. Lütfen girdiğiniz bilgileri kontrol edin.',
    401: 'Oturum süreniz doldu. Lütfen tekrar giriş yapın.',
    403: 'Bu işlem için yetkiniz bulunmuyor.',
    404: 'Aradığınız sayfa veya kaynak bulunamadı.',
    408: 'İstek zaman aşımına uğradı. Tekrar deneyin.',
    429: 'Çok fazla istek gönderildi. Lütfen biraz bekleyin.',
    500: 'Sunucu geçici olarak hizmet veremiyor. Birazdan tekrar deneyin.',
    502: 'Sunucu bağlantısında sorun var. Birazdan tekrar deneyin.',
    503: 'Hizmet şu an bakımda. Lütfen daha sonra deneyin.',
    504: 'Sunucu yanıt vermedi. Tekrar deneyin.',
}

const ERROR_PATTERNS: Array<{ pattern: RegExp; message: string }> = [
    { pattern: /network/i, message: 'İnternet bağlantınızı kontrol edin.' },
    { pattern: /timeout/i, message: 'Sunucu yanıt vermedi. Tekrar deneyin.' },
    { pattern: /abort/i, message: 'İşlem iptal edildi.' },
    { pattern: /offline/i, message: 'İnternet bağlantınız yok.' },
    { pattern: /cors/i, message: 'Sunucu bağlantı hatası. Tekrar deneyin.' },
    { pattern: /failed to fetch/i, message: 'Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.' },
]

const DEFAULT_MESSAGE = 'Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.'

/**
 * Teknik hatayı kullanıcı dostu mesaja çevirir
 */
export function getErrorMessage(error: unknown): string {
    // HTTP Error (Response with status)
    if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as { status: number }).status
        if (HTTP_ERROR_MESSAGES[status]) {
            return HTTP_ERROR_MESSAGES[status]
        }
    }

    // Error object with message
    if (error instanceof Error) {
        const msg = error.message.toLowerCase()

        // Check patterns
        for (const { pattern, message } of ERROR_PATTERNS) {
            if (pattern.test(msg)) {
                return message
            }
        }

        // Check for HTTP status in message
        const statusMatch = msg.match(/\b(4\d{2}|5\d{2})\b/)
        if (statusMatch) {
            const status = parseInt(statusMatch[1], 10)
            if (HTTP_ERROR_MESSAGES[status]) {
                return HTTP_ERROR_MESSAGES[status]
            }
        }
    }

    // String error
    if (typeof error === 'string') {
        for (const { pattern, message } of ERROR_PATTERNS) {
            if (pattern.test(error)) {
                return message
            }
        }
    }

    return DEFAULT_MESSAGE
}

/**
 * Hata tipine göre ikon adı döndürür
 */
export function getErrorIcon(error: unknown): 'wifi' | 'server' | 'clock' | 'alert' {
    const message = getErrorMessage(error)

    if (message.includes('İnternet') || message.includes('bağlantı')) {
        return 'wifi'
    }
    if (message.includes('Sunucu') || message.includes('hizmet')) {
        return 'server'
    }
    if (message.includes('zaman') || message.includes('bekle')) {
        return 'clock'
    }

    return 'alert'
}

/**
 * Retry yapılabilir bir hata mı kontrol eder
 */
export function isRetryableError(error: unknown): boolean {
    if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as { status: number }).status
        // 5xx errors and 429 are retryable
        return status >= 500 || status === 429 || status === 408
    }

    if (error instanceof Error) {
        const msg = error.message.toLowerCase()
        return /timeout|network|fetch|offline/i.test(msg)
    }

    return false
}
