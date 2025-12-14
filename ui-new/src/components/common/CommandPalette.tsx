/**
 * Command Palette Component
 * 
 * Slash command system (/) with fuzzy search
 * Premium UX inspired by Linear, Raycast
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Pencil, Image, Search, Code, Brain, Settings,
    Globe, Languages, Sparkles, MessageSquare, Trash2,
    FileText, Palette, User, HelpCircle
} from 'lucide-react'
import { useChatStore } from '@/stores'
import { cn } from '@/lib/utils'
import type { Command } from '@/types'

interface CommandPaletteProps {
    query: string
    onSelect: (command: Command) => void
    onClose: () => void
}

export function CommandPalette({ query, onSelect, onClose }: CommandPaletteProps) {
    const [selectedIndex, setSelectedIndex] = useState(0)
    const setInputValue = useChatStore((state) => state.setInputValue)

    // All available commands
    const commands: Command[] = useMemo(() => [
        {
            id: 'image',
            name: 'Görsel Oluştur',
            shortcut: '/görsel',
            icon: '🎨',
            description: 'AI ile resim üret',
            keywords: ['image', 'resim', 'çiz', 'oluştur', 'generate'],
            action: () => setInputValue('/görsel ')
        },
        {
            id: 'search',
            name: 'İnternette Ara',
            shortcut: '/ara',
            icon: '🔍',
            description: 'Web\'de bilgi bul',
            keywords: ['search', 'internet', 'web', 'google', 'bul'],
            action: () => setInputValue('/ara ')
        },
        {
            id: 'summarize',
            name: 'Özetle',
            shortcut: '/özet',
            icon: '📝',
            description: 'Metni veya URL\'yi özetle',
            keywords: ['summary', 'özet', 'kısalt'],
            action: () => setInputValue('/özet ')
        },
        {
            id: 'translate',
            name: 'Çevir',
            shortcut: '/çevir',
            icon: '🌐',
            description: 'Metni başka dile çevir',
            keywords: ['translate', 'çeviri', 'dil', 'language'],
            action: () => setInputValue('/çevir ')
        },
        {
            id: 'code',
            name: 'Kod Yaz',
            shortcut: '/kod',
            icon: '💻',
            description: 'Programlama yardımı',
            keywords: ['code', 'program', 'yazılım', 'script'],
            action: () => setInputValue('/kod ')
        },
        {
            id: 'explain',
            name: 'Açıkla',
            shortcut: '/açıkla',
            icon: '💡',
            description: 'Bir konuyu detaylı açıkla',
            keywords: ['explain', 'açıklama', 'nedir', 'what'],
            action: () => setInputValue('/açıkla ')
        },
        {
            id: 'persona',
            name: 'Mod Değiştir',
            shortcut: '/mod',
            icon: '🎭',
            description: 'AI kişiliğini değiştir',
            keywords: ['persona', 'mod', 'karakter', 'kişilik'],
            action: () => {
                document.dispatchEvent(new CustomEvent('open-settings', { detail: { tab: 'style' } }))
            }
        },
        {
            id: 'memory',
            name: 'Hafıza Ekle',
            shortcut: '/hatırla',
            icon: '🧠',
            description: 'Kalıcı bilgi ekle',
            keywords: ['memory', 'hatıra', 'kaydet', 'remember'],
            action: () => {
                document.dispatchEvent(new CustomEvent('open-memory-manager'))
            }
        },
        {
            id: 'document',
            name: 'Döküman Yükle',
            shortcut: '/döküman',
            icon: '📄',
            description: 'PDF veya metin dosyası yükle',
            keywords: ['document', 'pdf', 'dosya', 'upload'],
            action: () => {
                // Trigger file input click
                const fileInput = document.querySelector('input[type="file"][accept*=".pdf"]') as HTMLInputElement
                fileInput?.click()
            }
        },
        {
            id: 'theme',
            name: 'Tema Değiştir',
            shortcut: '/tema',
            icon: '🎨',
            description: 'Görünümü özelleştir',
            keywords: ['theme', 'tema', 'renk', 'dark', 'light'],
            action: () => {
                document.dispatchEvent(new CustomEvent('open-theme-picker'))
            }
        },
        {
            id: 'clear',
            name: 'Sohbeti Temizle',
            shortcut: '/temizle',
            icon: '🗑️',
            description: 'Bu sohbeti sıfırla',
            keywords: ['clear', 'temizle', 'sil', 'reset'],
            action: () => {
                if (confirm('Bu sohbeti silmek istediğinize emin misiniz?')) {
                    const state = useChatStore.getState()
                    if (state.currentConversationId) {
                        state.deleteConversation(state.currentConversationId)
                    }
                }
            }
        },
        {
            id: 'help',
            name: 'Yardım',
            shortcut: '/yardım',
            icon: '❓',
            description: 'Tüm komutları göster',
            keywords: ['help', 'yardım', 'komutlar', 'commands'],
            action: () => setInputValue('Tüm komutları ve özellikleri listele')
        },
    ], [setInputValue])

    // Filter commands based on query
    const filteredCommands = useMemo(() => {
        if (!query) return commands

        const normalizedQuery = query.toLowerCase().trim()

        return commands.filter(cmd => {
            const searchText = `${cmd.name} ${cmd.shortcut} ${cmd.description} ${cmd.keywords?.join(' ')}`.toLowerCase()
            return searchText.includes(normalizedQuery)
        })
    }, [commands, query])

    // Keyboard navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault()
                setSelectedIndex(prev =>
                    prev < filteredCommands.length - 1 ? prev + 1 : 0
                )
            } else if (e.key === 'ArrowUp') {
                e.preventDefault()
                setSelectedIndex(prev =>
                    prev > 0 ? prev - 1 : filteredCommands.length - 1
                )
            } else if (e.key === 'Enter') {
                e.preventDefault()
                if (filteredCommands[selectedIndex]) {
                    handleSelect(filteredCommands[selectedIndex])
                }
            } else if (e.key === 'Escape') {
                onClose()
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [filteredCommands, selectedIndex, onClose])

    // Reset selection when query changes
    useEffect(() => {
        setSelectedIndex(0)
    }, [query])

    const handleSelect = useCallback((command: Command) => {
        command.action()
        onSelect(command)
    }, [onSelect])

    if (filteredCommands.length === 0) {
        return (
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={cn(
                    "absolute bottom-full left-0 right-0 mb-2",
                    "bg-(--color-bg-surface) border border-(--color-border)",
                    "rounded-xl shadow-xl overflow-hidden"
                )}
            >
                <div className="p-4 text-center text-(--color-text-muted)">
                    <p className="text-sm">Komut bulunamadı</p>
                </div>
            </motion.div>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={cn(
                "absolute bottom-full left-0 right-0 mb-2 z-9999",
                "bg-(--color-bg-surface) border border-(--color-border)",
                "rounded-xl shadow-xl overflow-hidden",
                "max-h-80 overflow-y-auto scrollbar-thin"
            )}
        >
            <div className="p-2">
                <div className="px-3 py-2 text-xs font-medium text-(--color-text-muted) uppercase tracking-wider">
                    Komutlar
                </div>

                {filteredCommands.map((command, index) => (
                    <motion.button
                        key={command.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.02 }}
                        onClick={() => handleSelect(command)}
                        onMouseEnter={() => setSelectedIndex(index)}
                        className={cn(
                            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg",
                            "text-left transition-colors",
                            selectedIndex === index
                                ? "bg-(--color-primary-soft) text-(--color-primary)"
                                : "hover:bg-(--color-bg-surface-hover)"
                        )}
                    >
                        <span className="text-xl w-8 text-center">{command.icon}</span>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="font-medium">{command.name}</span>
                                <span className="text-xs text-(--color-text-muted) font-mono">
                                    {command.shortcut}
                                </span>
                            </div>
                            <p className="text-xs text-(--color-text-muted) truncate">
                                {command.description}
                            </p>
                        </div>
                    </motion.button>
                ))}
            </div>

            {/* Footer hint */}
            <div className="px-4 py-2 border-t border-(--color-border) bg-(--color-bg)">
                <div className="flex items-center justify-between text-xs text-(--color-text-muted)">
                    <span>↑↓ ile gezin</span>
                    <span>Enter ile seç</span>
                    <span>Esc ile kapat</span>
                </div>
            </div>
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

/**
 * Icon mapping helper
 */
export function getCommandIcon(iconName: string) {
    const icons: Record<string, React.ReactNode> = {
        pencil: <Pencil className="h-4 w-4" />,
        image: <Image className="h-4 w-4" />,
        search: <Search className="h-4 w-4" />,
        code: <Code className="h-4 w-4" />,
        brain: <Brain className="h-4 w-4" />,
        settings: <Settings className="h-4 w-4" />,
        globe: <Globe className="h-4 w-4" />,
        languages: <Languages className="h-4 w-4" />,
        sparkles: <Sparkles className="h-4 w-4" />,
        message: <MessageSquare className="h-4 w-4" />,
        trash: <Trash2 className="h-4 w-4" />,
        file: <FileText className="h-4 w-4" />,
        palette: <Palette className="h-4 w-4" />,
        user: <User className="h-4 w-4" />,
        help: <HelpCircle className="h-4 w-4" />,
    }

    return icons[iconName] || <Sparkles className="h-4 w-4" />
}
