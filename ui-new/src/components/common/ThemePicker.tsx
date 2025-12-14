/**
 * Theme Picker Component
 * 
 * Premium theme selection modal with live preview
 */

import { motion } from 'framer-motion'
import { Check, Moon, Sun, Monitor, Palette, X } from 'lucide-react'
import { useThemeStore } from '@/stores'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { ThemeId, ThemeCategory } from '@/types'

interface ThemePickerProps {
    isOpen: boolean
    onClose: () => void
}

// Theme definitions with full color info for previews
const themes: Record<ThemeId, {
    name: string
    icon: string
    category: ThemeCategory
    colors: {
        background: string
        surface: string
        primary: string
        secondary: string
        accent: string
        text: string
    }
}> = {
    warmDark: {
        name: 'Sıcak Karanlık',
        icon: '🌙',
        category: 'dark',
        colors: {
            background: '#0a0a0a',
            surface: '#171717',
            primary: '#7c3aed',
            secondary: '#ec4899',
            accent: '#f59e0b',
            text: '#fafafa'
        }
    },
    oledBlack: {
        name: 'OLED Siyah',
        icon: '⬛',
        category: 'dark',
        colors: {
            background: '#000000',
            surface: '#0a0a0a',
            primary: '#7c3aed',
            secondary: '#ec4899',
            accent: '#f59e0b',
            text: '#ffffff'
        }
    },
    midnight: {
        name: 'Gece Mavisi',
        icon: '🌌',
        category: 'dark',
        colors: {
            background: '#0c1222',
            surface: '#1a2744',
            primary: '#3b82f6',
            secondary: '#06b6d4',
            accent: '#22d3ee',
            text: '#f1f5f9'
        }
    },
    forest: {
        name: 'Orman Gecesi',
        icon: '🌲',
        category: 'dark',
        colors: {
            background: '#0a1210',
            surface: '#132418',
            primary: '#10b981',
            secondary: '#34d399',
            accent: '#a3e635',
            text: '#ecfdf5'
        }
    },
    roseGold: {
        name: 'Rose Gold',
        icon: '🌹',
        category: 'dark',
        colors: {
            background: '#1a1418',
            surface: '#2d2226',
            primary: '#f43f5e',
            secondary: '#fb7185',
            accent: '#fbbf24',
            text: '#fef2f2'
        }
    },
    dracula: {
        name: 'Dracula',
        icon: '🧛',
        category: 'dark',
        colors: {
            background: '#282a36',
            surface: '#44475a',
            primary: '#bd93f9',
            secondary: '#ff79c6',
            accent: '#50fa7b',
            text: '#f8f8f2'
        }
    },
    nord: {
        name: 'Nord',
        icon: '❄️',
        category: 'dark',
        colors: {
            background: '#2e3440',
            surface: '#3b4252',
            primary: '#88c0d0',
            secondary: '#81a1c1',
            accent: '#ebcb8b',
            text: '#eceff4'
        }
    },
    cleanLight: {
        name: 'Temiz Aydınlık',
        icon: '☀️',
        category: 'light',
        colors: {
            background: '#ffffff',
            surface: '#f5f5f5',
            primary: '#7c3aed',
            secondary: '#ec4899',
            accent: '#f59e0b',
            text: '#171717'
        }
    },
    warmCream: {
        name: 'Sıcak Krem',
        icon: '📜',
        category: 'light',
        colors: {
            background: '#fefcf3',
            surface: '#faf5e6',
            primary: '#b45309',
            secondary: '#c2410c',
            accent: '#15803d',
            text: '#1c1917'
        }
    },
    oceanBreeze: {
        name: 'Okyanus Esintisi',
        icon: '🌊',
        category: 'light',
        colors: {
            background: '#f0fdfa',
            surface: '#ccfbf1',
            primary: '#0d9488',
            secondary: '#0891b2',
            accent: '#7c3aed',
            text: '#134e4a'
        }
    },
    lavender: {
        name: 'Lavanta Rüyası',
        icon: '💜',
        category: 'light',
        colors: {
            background: '#faf5ff',
            surface: '#f3e8ff',
            primary: '#9333ea',
            secondary: '#c026d3',
            accent: '#f472b6',
            text: '#3b0764'
        }
    },
    highContrast: {
        name: 'Yüksek Kontrast',
        icon: '👁️',
        category: 'accessibility',
        colors: {
            background: '#000000',
            surface: '#1a1a1a',
            primary: '#ffff00',
            secondary: '#00ffff',
            accent: '#ff00ff',
            text: '#ffffff'
        }
    },
    system: {
        name: 'Sistem Teması',
        icon: '💻',
        category: 'dark', // Will change based on system
        colors: {
            background: '#0a0a0a',
            surface: '#171717',
            primary: '#7c3aed',
            secondary: '#ec4899',
            accent: '#f59e0b',
            text: '#fafafa'
        }
    }
}

const categories: { id: ThemeCategory | 'all'; name: string; icon: React.ReactNode }[] = [
    { id: 'dark', name: 'Karanlık', icon: <Moon className="h-4 w-4" /> },
    { id: 'light', name: 'Aydınlık', icon: <Sun className="h-4 w-4" /> },
    { id: 'accessibility', name: 'Erişilebilirlik', icon: <Monitor className="h-4 w-4" /> },
]

export function ThemePicker({ isOpen, onClose }: ThemePickerProps) {
    const currentTheme = useThemeStore((state) => state.theme)
    const setTheme = useThemeStore((state) => state.setTheme)

    if (!isOpen) return null

    return (
        <>
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-(--z-modal-backdrop)"
            />

            {/* Modal */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                className={cn(
                    "fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
                    "w-full max-w-2xl max-h-[85vh]",
                    "bg-(--color-bg-surface) border border-(--color-border)",
                    "rounded-2xl shadow-2xl overflow-hidden",
                    "z-(--z-modal)"
                )}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-(--color-border)">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-(--gradient-brand)">
                            <Palette className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-lg font-display font-semibold">Tema Seçin</h2>
                            <p className="text-sm text-(--color-text-muted)">
                                Görünümünüzü kişiselleştirin
                            </p>
                        </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[calc(85vh-130px)]">
                    {/* System Theme Option */}
                    <div className="mb-6">
                        <ThemeCard
                            themeId="system"
                            theme={themes.system}
                            isActive={currentTheme === 'system'}
                            onClick={() => setTheme('system')}
                            isSystem
                        />
                    </div>

                    {/* Theme Categories */}
                    {categories.map((category) => {
                        const categoryThemes = Object.entries(themes)
                            .filter(([id, t]) => t.category === category.id && id !== 'system')

                        if (categoryThemes.length === 0) return null

                        return (
                            <div key={category.id} className="mb-6">
                                <h3 className="text-sm font-medium text-(--color-text-muted) mb-3 flex items-center gap-2">
                                    {category.icon}
                                    {category.name} Temalar
                                </h3>

                                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    {categoryThemes.map(([id, theme]) => (
                                        <ThemeCard
                                            key={id}
                                            themeId={id as ThemeId}
                                            theme={theme}
                                            isActive={currentTheme === id}
                                            onClick={() => setTheme(id as ThemeId)}
                                        />
                                    ))}
                                </div>
                            </div>
                        )
                    })}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-(--color-border) bg-(--color-bg)">
                    <p className="text-xs text-(--color-text-muted) text-center">
                        Tema tercihiniz bu cihazda kaydedilir
                    </p>
                </div>
            </motion.div>
        </>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

interface ThemeCardProps {
    themeId: ThemeId
    theme: typeof themes[ThemeId]
    isActive: boolean
    onClick: () => void
    isSystem?: boolean
}

function ThemeCard({ themeId, theme, isActive, onClick, isSystem }: ThemeCardProps) {
    return (
        <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className={cn(
                "relative p-3 rounded-xl border-2 transition-all text-left w-full",
                isActive
                    ? "border-(--color-primary) ring-2 ring-(--color-primary)/30"
                    : "border-(--color-border) hover:border-(--color-border-hover)"
            )}
            style={{ backgroundColor: theme.colors.surface }}
        >
            {/* Color Preview */}
            <div className="flex gap-1.5 mb-3">
                <div
                    className="w-5 h-5 rounded-full border border-white/20"
                    style={{ backgroundColor: theme.colors.primary }}
                />
                <div
                    className="w-5 h-5 rounded-full border border-white/20"
                    style={{ backgroundColor: theme.colors.secondary }}
                />
                <div
                    className="w-5 h-5 rounded-full border border-white/20"
                    style={{ backgroundColor: theme.colors.accent }}
                />
            </div>

            {/* Mini Preview */}
            <div
                className="h-12 rounded-lg mb-3 p-2 flex flex-col justify-between"
                style={{ backgroundColor: theme.colors.background }}
            >
                <div
                    className="h-1.5 w-16 rounded-full"
                    style={{ backgroundColor: theme.colors.text, opacity: 0.3 }}
                />
                <div
                    className="h-2 w-10 rounded-full self-end"
                    style={{ backgroundColor: theme.colors.primary }}
                />
            </div>

            {/* Name */}
            <div className="flex items-center gap-2">
                <span className="text-base">{theme.icon}</span>
                <span
                    className="text-sm font-medium truncate"
                    style={{ color: theme.colors.text }}
                >
                    {theme.name}
                </span>
            </div>

            {/* System badge */}
            {isSystem && (
                <div className="mt-2 text-xs text-(--color-text-muted) flex items-center gap-1">
                    <Monitor className="h-3 w-3" />
                    Cihaz ayarını kullan
                </div>
            )}

            {/* Active Indicator */}
            {isActive && (
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute top-2 right-2 p-1 rounded-full bg-(--color-primary)"
                >
                    <Check className="h-3 w-3 text-white" />
                </motion.div>
            )}
        </motion.button>
    )
}
