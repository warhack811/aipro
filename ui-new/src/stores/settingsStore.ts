/**
 * Settings Store
 * 
 * Centralized state for:
 * - Persona/Mode selection
 * - Feature toggles (web, image)
 * - Response style preferences
 * - Image generation settings
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

export type PersonaMode =
    | 'standard'
    | 'friend'
    | 'romantic'
    | 'researcher'
    | 'artist'
    | 'coder'
    | 'roleplay'

export type ResponseTone = 'formal' | 'casual' | 'playful' | 'professional'
export type ResponseLength = 'short' | 'normal' | 'detailed'
export type EmojiLevel = 'none' | 'low' | 'medium' | 'high'

export interface Persona {
    name: PersonaMode
    displayName: string
    icon: string
    description: string
}

export interface ResponseStyle {
    tone: ResponseTone
    length: ResponseLength
    emojiLevel: EmojiLevel
    useMarkdown: boolean
    useCodeBlocks: boolean
}

export interface ImageSettings {
    defaultSize: '512' | '768' | '1024'
    defaultStyle: 'realistic' | 'artistic' | 'anime' | 'sketch'
    autoEnhance: boolean
}

export interface FuturePlan {
    id: string
    text: string
    date: string
    remindBefore?: number // days before
    isRecurring?: boolean
    createdAt: string
}

interface SettingsState {
    // Persona/Mode
    activePersona: PersonaMode
    personas: Persona[]

    // Feature Toggles
    webSearchEnabled: boolean
    imageGenEnabled: boolean

    // Response Style
    responseStyle: ResponseStyle

    // Image Settings
    imageSettings: ImageSettings

    // Future Plans (local, synced to backend on add)
    futurePlans: FuturePlan[]

    // UI State
    settingsOpen: boolean
    activeSettingsTab: 'style' | 'appearance' | 'memory' | 'image' | 'plans'

    // Actions
    setActivePersona: (persona: PersonaMode) => void
    setWebSearchEnabled: (enabled: boolean) => void
    setImageGenEnabled: (enabled: boolean) => void
    setResponseStyle: (style: Partial<ResponseStyle>) => void
    setImageSettings: (settings: Partial<ImageSettings>) => void
    addFuturePlan: (plan: Omit<FuturePlan, 'id' | 'createdAt'>) => void
    removeFuturePlan: (id: string) => void
    updateFuturePlan: (id: string, updates: Partial<FuturePlan>) => void
    openSettings: (tab?: 'style' | 'appearance' | 'memory' | 'image' | 'plans') => void
    closeSettings: () => void
    setActiveSettingsTab: (tab: 'style' | 'appearance' | 'memory' | 'image' | 'plans') => void
}

// ─────────────────────────────────────────────────────────────────────────────
// DEFAULT VALUES
// ─────────────────────────────────────────────────────────────────────────────

export const PERSONAS: Persona[] = [
    { name: 'standard', displayName: 'Standart', icon: '⚡', description: 'Dengeli ve yardımcı' },
    { name: 'friend', displayName: 'Kanka', icon: '😊', description: 'Samimi ve arkadaş canlısı' },
    { name: 'romantic', displayName: 'Sevgili', icon: '💕', description: 'Sıcak ve sevecen' },
    { name: 'researcher', displayName: 'Araştırmacı', icon: '🔬', description: 'Analitik ve detaylı' },
    { name: 'artist', displayName: 'Sanatçı', icon: '🎨', description: 'Yaratıcı ve ilham verici' },
    { name: 'coder', displayName: 'Yazılımcı', icon: '💻', description: 'Teknik ve kod odaklı' },
    { name: 'roleplay', displayName: 'Roleplay', icon: '🎭', description: 'Karakter canlandırma' },
]

const DEFAULT_RESPONSE_STYLE: ResponseStyle = {
    tone: 'casual',
    length: 'normal',
    emojiLevel: 'medium',
    useMarkdown: true,
    useCodeBlocks: true,
}

const DEFAULT_IMAGE_SETTINGS: ImageSettings = {
    defaultSize: '768',
    defaultStyle: 'realistic',
    autoEnhance: true,
}

// ─────────────────────────────────────────────────────────────────────────────
// STORE
// ─────────────────────────────────────────────────────────────────────────────

export const useSettingsStore = create<SettingsState>()(
    persist(
        (set) => ({
            // Initial State
            activePersona: 'standard',
            personas: PERSONAS,
            webSearchEnabled: true,
            imageGenEnabled: true,
            responseStyle: DEFAULT_RESPONSE_STYLE,
            imageSettings: DEFAULT_IMAGE_SETTINGS,
            futurePlans: [],
            settingsOpen: false,
            activeSettingsTab: 'style',

            // Actions
            setActivePersona: (persona) => set({ activePersona: persona }),

            setWebSearchEnabled: (enabled) => set({ webSearchEnabled: enabled }),

            setImageGenEnabled: (enabled) => set({ imageGenEnabled: enabled }),

            setResponseStyle: (style) => set((state) => ({
                responseStyle: { ...state.responseStyle, ...style }
            })),

            setImageSettings: (settings) => set((state) => ({
                imageSettings: { ...state.imageSettings, ...settings }
            })),

            addFuturePlan: (plan) => set((state) => ({
                futurePlans: [
                    ...state.futurePlans,
                    {
                        ...plan,
                        id: `plan-${Date.now()}`,
                        createdAt: new Date().toISOString(),
                    }
                ]
            })),

            removeFuturePlan: (id) => set((state) => ({
                futurePlans: state.futurePlans.filter(p => p.id !== id)
            })),

            updateFuturePlan: (id, updates) => set((state) => ({
                futurePlans: state.futurePlans.map(p =>
                    p.id === id ? { ...p, ...updates } : p
                )
            })),

            openSettings: (tab = 'style') => set({
                settingsOpen: true,
                activeSettingsTab: tab
            }),

            closeSettings: () => set({ settingsOpen: false }),

            setActiveSettingsTab: (tab) => set({ activeSettingsTab: tab }),
        }),
        {
            name: 'mami-settings',
            partialize: (state) => ({
                activePersona: state.activePersona,
                webSearchEnabled: state.webSearchEnabled,
                imageGenEnabled: state.imageGenEnabled,
                responseStyle: state.responseStyle,
                imageSettings: state.imageSettings,
                futurePlans: state.futurePlans,
            }),
        }
    )
)
