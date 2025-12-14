/**
 * Core TypeScript Types
 * 
 * Merkezi tip tanımları - tüm uygulama genelinde kullanılır
 * "İlk seferinde doğru yap" felsefesiyle, gelecek özellikler için hazır
 */

// ═══════════════════════════════════════════════════════════════════════════
// USER & AUTHENTICATION
// ═══════════════════════════════════════════════════════════════════════════

export interface User {
    id: string
    username: string
    displayName?: string
    role: 'user' | 'vip' | 'admin'
    avatarUrl?: string
    preferences: UserPreferences
    permissions: UserPermissions
    createdAt: string
    lastSeen?: string
}

export interface UserPreferences {
    theme: ThemeId
    language: 'tr' | 'en'
    fontSize: 'sm' | 'md' | 'lg'
    reducedMotion: boolean
    soundEnabled: boolean
    notificationsEnabled: boolean
    preferredModel?: ModelId
    activePersona?: string
}

export interface UserPermissions {
    canUseInternet: boolean
    canUseImage: boolean
    canUseLocalChat: boolean
    dailyInternetLimit: number
    dailyImageLimit: number
    censorshipLevel: 0 | 1 | 2
    isBanned: boolean
}

// ═══════════════════════════════════════════════════════════════════════════
// BRANDING (Dynamic - Admin Panel Controlled)
// ═══════════════════════════════════════════════════════════════════════════

export interface BrandingConfig {
    displayName: string        // "Mami AI" → "[Final İsim]"
    developerName: string      // "Şirket Adı"
    productFamily: string      // "AI Assistant Family"
    shortIntro: string         // Kısa tanıtım metni
    logoUrl?: string           // Özel logo (opsiyonel)
    primaryColor?: string      // Marka ana rengi (opsiyonel)
    forbidProviderMention: boolean
}

// ═══════════════════════════════════════════════════════════════════════════
// THEMES
// ═══════════════════════════════════════════════════════════════════════════

export type ThemeId =
    | 'warmDark'
    | 'oledBlack'
    | 'midnight'
    | 'forest'
    | 'roseGold'
    | 'dracula'
    | 'nord'
    | 'cleanLight'
    | 'warmCream'
    | 'oceanBreeze'
    | 'lavender'
    | 'highContrast'
    | 'system'

export type ThemeCategory = 'dark' | 'light' | 'accessibility'

export interface Theme {
    id: ThemeId
    name: string
    icon: string
    category: ThemeCategory
    colors: ThemeColors
}

export interface ThemeColors {
    background: string
    surface: string
    surfaceHover: string
    primary: string
    secondary: string
    accent: string
    text: string
    textMuted: string
    border: string
}

// ═══════════════════════════════════════════════════════════════════════════
// MESSAGES & CHAT
// ═══════════════════════════════════════════════════════════════════════════

export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
    id: string
    conversationId?: string  // Optional - set when conversation is created
    role: MessageRole
    content: string
    timestamp: string

    // Metadata
    model?: ModelId
    persona?: string
    isStreaming?: boolean
    isEdited?: boolean
    editedAt?: string

    // Rich content
    sources?: Source[]
    images?: MessageImage[]
    attachments?: Attachment[]
    codeBlocks?: CodeBlock[]

    // User feedback
    feedback?: 'like' | 'dislike' | null

    // Reactions
    reactions?: Array<{
        emoji: string
        count: number
        reacted: boolean
    }>

    // Reply
    replyToId?: string

    // Server metadata (from backend extra_metadata field)
    extra_metadata?: {
        job_id?: string
        prompt?: string
        status?: 'queued' | 'processing' | 'complete' | 'error'  // All possible statuses
        progress?: number       // 0-100
        queue_position?: number // Sıra pozisyonu
        [key: string]: unknown
    }
}

export interface Source {
    url: string
    title: string
    domain: string
    snippet?: string
    favicon?: string
}

export interface MessageImage {
    id: string
    url: string
    prompt?: string
    status: 'pending' | 'processing' | 'complete' | 'error'
    progress?: number
    width?: number
    height?: number
}

export interface Attachment {
    id: string
    name: string
    type: string
    size: number
    url: string
}

export interface CodeBlock {
    language: string
    code: string
    filename?: string
}

// ═══════════════════════════════════════════════════════════════════════════
// CONVERSATIONS
// ═══════════════════════════════════════════════════════════════════════════

export interface Conversation {
    id: string
    title: string
    preview?: string
    messageCount: number
    createdAt: string
    updatedAt: string
    isPinned?: boolean
    isArchived?: boolean
    persona?: string
}

export interface ConversationGroup {
    label: string
    conversations: Conversation[]
}

// ═══════════════════════════════════════════════════════════════════════════
// PERSONAS
// ═══════════════════════════════════════════════════════════════════════════

export interface Persona {
    id: string
    name: string
    description: string
    icon: string
    systemPrompt?: string
    isDefault?: boolean
    isNsfw?: boolean
    forceLocal?: boolean
}

// ═══════════════════════════════════════════════════════════════════════════
// MEMORY
// ═══════════════════════════════════════════════════════════════════════════

export interface Memory {
    id: string
    text: string
    importance: number  // 0.0 - 1.0
    category?: 'personal' | 'preference' | 'fact' | 'instruction'
    createdAt: string
    updatedAt: string
    usageCount?: number
    lastUsedAt?: string
}

// ═══════════════════════════════════════════════════════════════════════════
// DOCUMENTS (RAG)
// ═══════════════════════════════════════════════════════════════════════════

export interface Document {
    id: string
    filename: string
    originalName: string
    mimeType: string
    size: number
    uploadedAt: string
    status: 'processing' | 'ready' | 'error'
    chunkCount?: number
    metadata?: Record<string, unknown>
}

// ═══════════════════════════════════════════════════════════════════════════
// MODELS
// ═══════════════════════════════════════════════════════════════════════════

export type ModelId = 'auto' | 'groq' | 'bela' | string

export interface Model {
    id: ModelId
    name: string
    description: string
    icon: string
    isLocal: boolean
    isDefault?: boolean
    maxTokens?: number
    features?: string[]
}

// ═══════════════════════════════════════════════════════════════════════════
// IMAGE GENERATION
// ═══════════════════════════════════════════════════════════════════════════

export interface ImageJob {
    id: string
    conversationId?: string
    prompt: string
    status: 'queued' | 'processing' | 'complete' | 'error'
    progress: number
    queuePosition?: number
    estimatedSeconds?: number
    imageUrl?: string
    error?: string
    createdAt?: string
    completedAt?: string
}

export interface ImageStyle {
    id: string
    name: string
    description: string
    previewUrl?: string
}

// ═══════════════════════════════════════════════════════════════════════════
// WEBSOCKET
// ═══════════════════════════════════════════════════════════════════════════

export type WebSocketMessageType =
    | 'connected'
    | 'image_progress'
    | 'image_complete'
    | 'image_error'
    | 'notification'
    | 'typing'
    | 'error'

export interface WebSocketMessage {
    type: WebSocketMessageType
    data?: Record<string, unknown>
    timestamp?: string
}

// ═══════════════════════════════════════════════════════════════════════════
// UI STATE
// ═══════════════════════════════════════════════════════════════════════════

export interface ModalState {
    isOpen: boolean
    type?: ModalType
    props?: Record<string, unknown>
}

export type ModalType =
    | 'settings'
    | 'memory'
    | 'gallery'
    | 'persona'
    | 'document'
    | 'confirm'
    | 'shortcuts'

export interface Toast {
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message?: string
    duration?: number
}

// ═══════════════════════════════════════════════════════════════════════════
// COMMANDS (/ Shortcuts)
// ═══════════════════════════════════════════════════════════════════════════

export interface Command {
    id: string
    name: string
    shortcut: string
    icon: string
    description: string
    action: () => void
    keywords?: string[]
}

// ═══════════════════════════════════════════════════════════════════════════
// API RESPONSES
// ═══════════════════════════════════════════════════════════════════════════

export interface ApiResponse<T> {
    data: T
    success: boolean
    message?: string
    error?: string
}

export interface PaginatedResponse<T> {
    data: T[]
    total: number
    page: number
    pageSize: number
    hasMore: boolean
}

// ═══════════════════════════════════════════════════════════════════════════
// FORM STATES
// ═══════════════════════════════════════════════════════════════════════════

export interface FormState {
    isSubmitting: boolean
    isValid: boolean
    errors: Record<string, string>
    touched: Record<string, boolean>
}

// ═══════════════════════════════════════════════════════════════════════════
// FEATURE FLAGS (Admin Controlled)
// ═══════════════════════════════════════════════════════════════════════════

export interface FeatureFlags {
    chatEnabled: boolean
    internetEnabled: boolean
    imageEnabled: boolean
    belaEnabled: boolean
    memoryEnabled: boolean
    voiceEnabled: boolean
    collaborationEnabled: boolean
}
