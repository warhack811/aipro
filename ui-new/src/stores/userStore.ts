/**
 * User Store - Zustand
 * 
 * Kullanıcı oturumu ve tercihler için state
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, UserPreferences, BrandingConfig, Persona } from '@/types'

interface UserState {
    // User data
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean

    // Branding (from admin panel)
    branding: BrandingConfig

    // Personas
    personas: Persona[]
    activePersona: string | null

    // Actions
    setUser: (user: User | null) => void
    setAuthenticated: (isAuthenticated: boolean) => void
    updatePreferences: (preferences: Partial<UserPreferences>) => void
    setBranding: (branding: BrandingConfig) => void
    setPersonas: (personas: Persona[]) => void
    setActivePersona: (personaId: string | null) => void
    logout: () => void
    setLoading: (isLoading: boolean) => void
}

const defaultBranding: BrandingConfig = {
    displayName: 'AI Assistant',
    developerName: 'Developer',
    productFamily: 'AI Platform',
    shortIntro: 'Kişisel AI asistanınız',
    forbidProviderMention: false
}

export const useUserStore = create<UserState>()(
    persist(
        (set, get) => ({
            user: null,
            isAuthenticated: false,
            isLoading: true,
            branding: defaultBranding,
            personas: [],
            activePersona: null,

            setUser: (user) => {
                set({
                    user,
                    isAuthenticated: !!user,
                    isLoading: false,
                    activePersona: user?.preferences.activePersona || null
                })
            },

            setAuthenticated: (isAuthenticated) => {
                set({ isAuthenticated })
            },

            updatePreferences: (preferences) => {
                const { user } = get()
                if (!user) return

                set({
                    user: {
                        ...user,
                        preferences: { ...user.preferences, ...preferences }
                    }
                })
            },

            setBranding: (branding) => {
                set({ branding })
            },

            setPersonas: (personas) => {
                set({ personas })
            },

            setActivePersona: (personaId) => {
                set({ activePersona: personaId })

                // Also update user preferences
                const { user } = get()
                if (user) {
                    set({
                        user: {
                            ...user,
                            preferences: { ...user.preferences, activePersona: personaId || undefined }
                        }
                    })
                }
            },

            logout: () => {
                set({
                    user: null,
                    isAuthenticated: false,
                    activePersona: null
                })
            },

            setLoading: (isLoading) => {
                set({ isLoading })
            }
        }),
        {
            name: 'user-storage',
            partialize: (state) => ({
                // Only persist essential user data
                activePersona: state.activePersona
            })
        }
    )
)

/**
 * Hook for accessing branding info
 */
export function useBranding() {
    return useUserStore((state) => state.branding)
}

/**
 * Hook for accessing active persona
 */
export function useActivePersona() {
    const personas = useUserStore((state) => state.personas)
    const activeId = useUserStore((state) => state.activePersona)

    return personas.find((p) => p.id === activeId) || null
}
