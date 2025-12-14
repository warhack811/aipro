/**
 * Theme Store - Zustand
 * 
 * Tema yönetimi için merkezi state
 * localStorage ile persistence
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ThemeId } from '@/types'

interface ThemeState {
    // Current theme
    theme: ThemeId
    systemTheme: 'light' | 'dark'

    // Actions
    setTheme: (theme: ThemeId) => void
    setSystemTheme: (theme: 'light' | 'dark') => void

    // Computed
    effectiveTheme: () => ThemeId
}

export const useThemeStore = create<ThemeState>()(
    persist(
        (set, get) => ({
            theme: 'warmDark',
            systemTheme: 'dark',

            setTheme: (theme) => {
                set({ theme })
                // Apply theme to document
                const effectiveThemeId = theme === 'system'
                    ? (get().systemTheme === 'dark' ? 'warmDark' : 'cleanLight')
                    : theme
                applyTheme(effectiveThemeId)
            },

            setSystemTheme: (systemTheme) => {
                set({ systemTheme })
                if (get().theme === 'system') {
                    // Map system theme to actual theme
                    const mappedTheme = systemTheme === 'dark' ? 'warmDark' : 'cleanLight'
                    applyTheme(mappedTheme)
                }
            },

            effectiveTheme: () => {
                const state = get()
                if (state.theme === 'system') {
                    return state.systemTheme === 'dark' ? 'warmDark' : 'cleanLight'
                }
                return state.theme
            }
        }),
        {
            name: 'theme-storage',
            partialize: (state) => ({ theme: state.theme })
        }
    )
)

/**
 * Apply theme to document root
 */
function applyTheme(themeId: ThemeId) {
    if (typeof document === 'undefined') return
    document.documentElement.setAttribute('data-theme', themeId)
}

/**
 * Initialize theme on app start
 */
export function initializeTheme() {
    if (typeof window === 'undefined') return

    const store = useThemeStore.getState()

    // Detect system preference
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    store.setSystemTheme(mediaQuery.matches ? 'dark' : 'light')

    // Listen for system theme changes
    mediaQuery.addEventListener('change', (e) => {
        store.setSystemTheme(e.matches ? 'dark' : 'light')
    })

    // Apply initial theme
    applyTheme(store.effectiveTheme())
}
