/**
 * QuickSettings Component
 * 
 * Compact settings controls displayed near the chat input:
 * - Persona/Mode selector (dropdown)
 * - Web search toggle
 * - Image generation toggle
 * 
 * Syncs with backend via usePreferences hook
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Globe, Image, ChevronDown, Check, Loader2 } from 'lucide-react'
import { useSettingsStore, PERSONAS } from '@/stores/settingsStore'
import { usePreferences } from '@/hooks'
import { cn } from '@/lib/utils'

export function QuickSettings() {
    const {
        activePersona,
        webSearchEnabled,
        imageGenEnabled,
    } = useSettingsStore()

    // Backend sync
    const {
        savePersona,
        saveWebSearch,
        saveImageGen,
        isSaving,
        isLoading
    } = usePreferences()

    const [personaOpen, setPersonaOpen] = useState(false)
    const dropdownRef = useRef<HTMLDivElement>(null)

    // Close dropdown on outside click
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setPersonaOpen(false)
            }
        }

        if (personaOpen) {
            document.addEventListener('mousedown', handleClickOutside)
            return () => document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [personaOpen])

    const currentPersona = PERSONAS.find(p => p.name === activePersona) || PERSONAS[0]

    return (
        <div className="flex items-center gap-1">
            {/* Loading indicator */}
            {(isLoading || isSaving) && (
                <Loader2 className="h-3 w-3 animate-spin text-(--color-text-muted)" />
            )}

            {/* Persona Selector */}
            <div className="relative" ref={dropdownRef}>
                <button
                    onClick={() => setPersonaOpen(!personaOpen)}
                    className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm",
                        "border border-(--color-border) transition-all",
                        "hover:border-(--color-primary)/50 hover:bg-(--color-bg-surface)",
                        personaOpen && "border-(--color-primary) bg-(--color-bg-surface)"
                    )}
                >
                    <span className="text-base">{currentPersona.icon}</span>
                    <span className="hidden sm:inline text-(--color-text-secondary)">
                        {currentPersona.displayName}
                    </span>
                    <ChevronDown className={cn(
                        "h-3.5 w-3.5 text-(--color-text-muted) transition-transform",
                        personaOpen && "rotate-180"
                    )} />
                </button>

                <AnimatePresence>
                    {personaOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: 5, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 5, scale: 0.95 }}
                            transition={{ duration: 0.15 }}
                            className={cn(
                                "absolute bottom-full left-0 mb-2 z-9999",
                                "w-56 p-2 rounded-xl",
                                "bg-(--color-bg-surface) border border-(--color-border)",
                                "shadow-xl"
                            )}
                        >
                            <div className="text-xs font-medium text-(--color-text-muted) px-2 py-1 mb-1">
                                AI Modu
                            </div>
                            {PERSONAS.map(persona => (
                                <button
                                    key={persona.name}
                                    onClick={() => {
                                        savePersona(persona.name)
                                        setPersonaOpen(false)
                                    }}
                                    className={cn(
                                        "w-full flex items-center gap-3 px-2 py-2 rounded-lg text-left",
                                        "hover:bg-(--color-bg-surface-hover) transition-colors",
                                        activePersona === persona.name && "bg-(--color-primary-soft)"
                                    )}
                                >
                                    <span className="text-lg">{persona.icon}</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium">{persona.displayName}</div>
                                        <div className="text-xs text-(--color-text-muted) truncate">
                                            {persona.description}
                                        </div>
                                    </div>
                                    {activePersona === persona.name && (
                                        <Check className="h-4 w-4 text-(--color-primary)" />
                                    )}
                                </button>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Web Search Toggle */}
            <button
                onClick={() => saveWebSearch(!webSearchEnabled)}
                className={cn(
                    "p-2 rounded-lg transition-all",
                    webSearchEnabled
                        ? "bg-(--color-info-soft) text-(--color-info)"
                        : "text-(--color-text-muted) hover:bg-(--color-bg-surface)"
                )}
                title={webSearchEnabled ? "Web araması açık" : "Web araması kapalı"}
            >
                <Globe className="h-4 w-4" />
            </button>

            {/* Image Gen Toggle */}
            <button
                onClick={() => saveImageGen(!imageGenEnabled)}
                className={cn(
                    "p-2 rounded-lg transition-all",
                    imageGenEnabled
                        ? "bg-(--color-secondary-soft) text-(--color-secondary)"
                        : "text-(--color-text-muted) hover:bg-(--color-bg-surface)"
                )}
                title={imageGenEnabled ? "Görsel üretimi açık" : "Görsel üretimi kapalı"}
            >
                <Image className="h-4 w-4" />
            </button>
        </div>
    )
}
