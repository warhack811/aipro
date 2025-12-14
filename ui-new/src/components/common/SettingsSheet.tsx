/**
 * SettingsSheet Component
 * 
 * Main settings modal/bottom sheet with tabbed interface:
 * - Response Style (tone, emoji, length)
 * - Memory & Future Plans
 * - Image Settings
 * 
 * Works as modal on desktop, bottom sheet on mobile
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    X, Settings, MessageSquare, Brain, Image, Calendar,
    Check, ChevronRight, Plus, Trash2, Sparkles, Palette, Sun, Moon, Monitor
} from 'lucide-react'
import { useSettingsStore, PERSONAS, type PersonaMode } from '@/stores/settingsStore'
import { useThemeStore } from '@/stores/themeStore'
import { Button, Input } from '@/components/ui'
import { useIsMobile } from '@/hooks'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export function SettingsSheet() {
    const {
        settingsOpen,
        closeSettings,
        activeSettingsTab,
        setActiveSettingsTab,
    } = useSettingsStore()

    const isMobile = useIsMobile()

    if (!settingsOpen) return null

    const tabs = [
        { id: 'style' as const, label: 'Yanıt Stili', icon: MessageSquare },
        { id: 'appearance' as const, label: 'Görünüm', icon: Palette },
        { id: 'memory' as const, label: 'Hafıza', icon: Brain },
        { id: 'image' as const, label: 'Görsel', icon: Image },
        { id: 'plans' as const, label: 'Planlar', icon: Calendar },
    ]

    return (
        <AnimatePresence>
            {settingsOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={closeSettings}
                        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
                    />

                    {/* Sheet */}
                    <motion.div
                        initial={isMobile ? { y: '100%' } : { opacity: 0, scale: 0.95 }}
                        animate={isMobile ? { y: 0 } : { opacity: 1, scale: 1 }}
                        exit={isMobile ? { y: '100%' } : { opacity: 0, scale: 0.95 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className={cn(
                            "fixed z-50 bg-(--color-bg-surface) border border-(--color-border)",
                            "flex flex-col overflow-hidden",
                            isMobile
                                ? "inset-x-0 bottom-0 rounded-t-3xl max-h-[85vh]"
                                : "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-2xl w-full max-w-2xl max-h-[80vh]"
                        )}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-(--color-border)">
                            {isMobile && (
                                <div className="w-12 h-1 rounded-full bg-(--color-border) absolute top-2 left-1/2 -translate-x-1/2" />
                            )}
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-xl bg-(--color-primary-soft)">
                                    <Settings className="h-5 w-5 text-(--color-primary)" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold">Ayarlar</h2>
                                    <p className="text-xs text-(--color-text-muted)">
                                        AI yanıtlarını kişiselleştir
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={closeSettings}
                                className="p-2 rounded-lg hover:bg-(--color-bg-surface-hover) text-(--color-text-muted)"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-(--color-border) px-2 overflow-x-auto scrollbar-hide">
                            {tabs.map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveSettingsTab(tab.id)}
                                    className={cn(
                                        "flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap",
                                        "border-b-2 transition-colors -mb-[2px]",
                                        activeSettingsTab === tab.id
                                            ? "border-(--color-primary) text-(--color-primary)"
                                            : "border-transparent text-(--color-text-muted) hover:text-(--color-text)"
                                    )}
                                >
                                    <tab.icon className="h-4 w-4" />
                                    {tab.label}
                                </button>
                            ))}
                        </div>

                        <div className="flex-1 overflow-y-auto p-5">
                            {activeSettingsTab === 'style' && <ResponseStyleTab />}
                            {activeSettingsTab === 'appearance' && <AppearanceTab />}
                            {activeSettingsTab === 'memory' && <MemoryTab />}
                            {activeSettingsTab === 'image' && <ImageSettingsTab />}
                            {activeSettingsTab === 'plans' && <FuturePlansTab />}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// RESPONSE STYLE TAB
// ─────────────────────────────────────────────────────────────────────────────

function ResponseStyleTab() {
    const {
        activePersona,
        setActivePersona,
        responseStyle,
        setResponseStyle
    } = useSettingsStore()

    return (
        <div className="space-y-6">
            {/* Persona/Mode Selection */}
            <section>
                <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-(--color-primary)" />
                    AI Modu
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {PERSONAS.map(persona => (
                        <button
                            key={persona.name}
                            onClick={() => setActivePersona(persona.name)}
                            className={cn(
                                "flex items-center gap-3 p-3 rounded-xl border transition-all text-left",
                                activePersona === persona.name
                                    ? "border-(--color-primary) bg-(--color-primary-soft)"
                                    : "border-(--color-border) hover:border-(--color-primary)/50"
                            )}
                        >
                            <span className="text-xl">{persona.icon}</span>
                            <div className="min-w-0">
                                <div className="text-sm font-medium truncate">{persona.displayName}</div>
                                <div className="text-xs text-(--color-text-muted) truncate">{persona.description}</div>
                            </div>
                            {activePersona === persona.name && (
                                <Check className="h-4 w-4 text-(--color-primary) ml-auto shrink-0" />
                            )}
                        </button>
                    ))}
                </div>
            </section>

            {/* Tone */}
            <section>
                <h3 className="text-sm font-medium mb-3">Ton</h3>
                <div className="flex flex-wrap gap-2">
                    {[
                        { value: 'casual', label: 'Samimi' },
                        { value: 'formal', label: 'Resmi' },
                        { value: 'playful', label: 'Eğlenceli' },
                        { value: 'professional', label: 'Profesyonel' },
                    ].map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => setResponseStyle({ tone: opt.value as any })}
                            className={cn(
                                "px-4 py-2 rounded-full text-sm border transition-all",
                                responseStyle.tone === opt.value
                                    ? "border-(--color-primary) bg-(--color-primary-soft) text-(--color-primary)"
                                    : "border-(--color-border) hover:border-(--color-primary)/50"
                            )}
                        >
                            {opt.label}
                        </button>
                    ))}
                </div>
            </section>

            {/* Emoji Level */}
            <section>
                <h3 className="text-sm font-medium mb-3">Emoji Kullanımı</h3>
                <div className="flex gap-2">
                    {[
                        { value: 'none', label: 'Yok' },
                        { value: 'low', label: 'Az 😊' },
                        { value: 'medium', label: 'Orta 😊👍' },
                        { value: 'high', label: 'Çok 🎉😍✨' },
                    ].map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => setResponseStyle({ emojiLevel: opt.value as any })}
                            className={cn(
                                "flex-1 px-3 py-2 rounded-lg text-sm border transition-all",
                                responseStyle.emojiLevel === opt.value
                                    ? "border-(--color-primary) bg-(--color-primary-soft)"
                                    : "border-(--color-border) hover:border-(--color-primary)/50"
                            )}
                        >
                            {opt.label}
                        </button>
                    ))}
                </div>
            </section>

            {/* Length */}
            <section>
                <h3 className="text-sm font-medium mb-3">Yanıt Uzunluğu</h3>
                <div className="flex gap-2">
                    {[
                        { value: 'short', label: 'Kısa', desc: 'Öz ve net' },
                        { value: 'normal', label: 'Normal', desc: 'Dengeli' },
                        { value: 'detailed', label: 'Detaylı', desc: 'Kapsamlı' },
                    ].map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => setResponseStyle({ length: opt.value as any })}
                            className={cn(
                                "flex-1 p-3 rounded-xl border transition-all text-center",
                                responseStyle.length === opt.value
                                    ? "border-(--color-primary) bg-(--color-primary-soft)"
                                    : "border-(--color-border) hover:border-(--color-primary)/50"
                            )}
                        >
                            <div className="text-sm font-medium">{opt.label}</div>
                            <div className="text-xs text-(--color-text-muted)">{opt.desc}</div>
                        </button>
                    ))}
                </div>
            </section>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// APPEARANCE TAB (Theme Selection - Inline)
// ─────────────────────────────────────────────────────────────────────────────

// Theme definitions (copied from ThemePicker for inline display)
const THEMES = {
    warmDark: { name: 'Sıcak Karanlık', icon: '🌙', bg: '#0a0a0a', surface: '#171717', primary: '#7c3aed' },
    oledBlack: { name: 'OLED Siyah', icon: '⬛', bg: '#000000', surface: '#0a0a0a', primary: '#7c3aed' },
    midnight: { name: 'Gece Mavisi', icon: '🌌', bg: '#0c1222', surface: '#1a2744', primary: '#3b82f6' },
    forest: { name: 'Orman Gecesi', icon: '🌲', bg: '#0a1210', surface: '#132418', primary: '#10b981' },
    roseGold: { name: 'Rose Gold', icon: '🌹', bg: '#1a1418', surface: '#2d2226', primary: '#f43f5e' },
    dracula: { name: 'Dracula', icon: '🧛', bg: '#282a36', surface: '#44475a', primary: '#bd93f9' },
    nord: { name: 'Nord', icon: '❄️', bg: '#2e3440', surface: '#3b4252', primary: '#88c0d0' },
    cleanLight: { name: 'Temiz Aydınlık', icon: '☀️', bg: '#ffffff', surface: '#f5f5f5', primary: '#7c3aed' },
    warmCream: { name: 'Sıcak Krem', icon: '📜', bg: '#fefcf3', surface: '#faf5e6', primary: '#b45309' },
    oceanBreeze: { name: 'Okyanus Esintisi', icon: '🌊', bg: '#f0fdfa', surface: '#ccfbf1', primary: '#0d9488' },
    lavender: { name: 'Lavanta Rüyası', icon: '💜', bg: '#faf5ff', surface: '#f3e8ff', primary: '#9333ea' },
    highContrast: { name: 'Yüksek Kontrast', icon: '👁️', bg: '#000000', surface: '#1a1a1a', primary: '#ffff00' },
    system: { name: 'Sistem Teması', icon: '💻', bg: '#0a0a0a', surface: '#171717', primary: '#7c3aed' },
} as const

function AppearanceTab() {
    const { theme, setTheme } = useThemeStore()

    return (
        <div className="space-y-4">
            {/* Theme Selection Header */}
            <div className="flex items-center gap-2 mb-2">
                <Palette className="h-4 w-4 text-(--color-primary)" />
                <h3 className="text-sm font-medium">Tema Seçin</h3>
            </div>

            {/* Theme Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(THEMES).map(([id, t]) => (
                    <button
                        key={id}
                        onClick={() => setTheme(id as any)}
                        className={cn(
                            "relative p-3 rounded-xl border-2 transition-all text-left",
                            theme === id
                                ? "border-(--color-primary) ring-2 ring-(--color-primary)/30"
                                : "border-(--color-border) hover:border-(--color-border-hover)"
                        )}
                        style={{ backgroundColor: t.surface }}
                    >
                        {/* Color Preview */}
                        <div className="flex gap-1 mb-2">
                            <div
                                className="w-4 h-4 rounded-full border border-white/20"
                                style={{ backgroundColor: t.primary }}
                            />
                            <div
                                className="w-4 h-4 rounded-full border border-white/20"
                                style={{ backgroundColor: t.bg }}
                            />
                        </div>

                        {/* Name */}
                        <div className="flex items-center gap-1.5">
                            <span className="text-sm">{t.icon}</span>
                            <span
                                className="text-xs font-medium truncate"
                                style={{ color: t.bg === '#ffffff' || t.bg.startsWith('#f') ? '#171717' : '#fafafa' }}
                            >
                                {t.name}
                            </span>
                        </div>

                        {/* Active Indicator */}
                        {theme === id && (
                            <div className="absolute top-1.5 right-1.5 p-0.5 rounded-full bg-(--color-primary)">
                                <Check className="h-2.5 w-2.5 text-white" />
                            </div>
                        )}
                    </button>
                ))}
            </div>

            {/* Info */}
            <div className="text-xs text-(--color-text-muted) p-3 rounded-lg bg-(--color-info-soft)">
                💡 Tema tercihiniz bu cihazda kaydedilir.
            </div>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// MEMORY TAB
// ─────────────────────────────────────────────────────────────────────────────

function MemoryTab() {
    return (
        <div className="space-y-4">
            <div className="p-4 rounded-xl bg-(--color-bg) border border-(--color-border)">
                <div className="flex items-center gap-3 mb-2">
                    <Brain className="h-5 w-5 text-(--color-secondary)" />
                    <h3 className="font-medium">Hafıza Yönetimi</h3>
                </div>
                <p className="text-sm text-(--color-text-muted) mb-4">
                    AI'ın hatırladığı bilgileri görüntüle ve düzenle.
                </p>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                        // Open Memory Manager modal
                        document.dispatchEvent(new CustomEvent('open-memory-manager'))
                    }}
                >
                    Hafızayı Yönet
                    <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
            </div>

            <div className="text-xs text-(--color-text-muted) p-3 rounded-lg bg-(--color-info-soft)">
                💡 İpucu: Sohbet sırasında "bunu hatırla" diyerek otomatik hafıza ekleyebilirsiniz.
            </div>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// IMAGE SETTINGS TAB
// ─────────────────────────────────────────────────────────────────────────────

function ImageSettingsTab() {
    const { imageSettings, setImageSettings } = useSettingsStore()

    return (
        <div className="space-y-6">
            {/* Default Size */}
            <section>
                <h3 className="text-sm font-medium mb-3">Varsayılan Boyut</h3>
                <div className="flex gap-2">
                    {[
                        { value: '512', label: '512px', desc: 'Hızlı' },
                        { value: '768', label: '768px', desc: 'Dengeli' },
                        { value: '1024', label: '1024px', desc: 'Yüksek kalite' },
                    ].map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => setImageSettings({ defaultSize: opt.value as any })}
                            className={cn(
                                "flex-1 p-3 rounded-xl border transition-all text-center",
                                imageSettings.defaultSize === opt.value
                                    ? "border-(--color-primary) bg-(--color-primary-soft)"
                                    : "border-(--color-border) hover:border-(--color-primary)/50"
                            )}
                        >
                            <div className="text-sm font-medium">{opt.label}</div>
                            <div className="text-xs text-(--color-text-muted)">{opt.desc}</div>
                        </button>
                    ))}
                </div>
            </section>

            {/* Default Style */}
            <section>
                <h3 className="text-sm font-medium mb-3">Varsayılan Stil</h3>
                <div className="grid grid-cols-2 gap-2">
                    {[
                        { value: 'realistic', label: 'Gerçekçi', icon: '📷' },
                        { value: 'artistic', label: 'Sanatsal', icon: '🎨' },
                        { value: 'anime', label: 'Anime', icon: '🎌' },
                        { value: 'sketch', label: 'Çizim', icon: '✏️' },
                    ].map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => setImageSettings({ defaultStyle: opt.value as any })}
                            className={cn(
                                "flex items-center gap-3 p-3 rounded-xl border transition-all",
                                imageSettings.defaultStyle === opt.value
                                    ? "border-(--color-primary) bg-(--color-primary-soft)"
                                    : "border-(--color-border) hover:border-(--color-primary)/50"
                            )}
                        >
                            <span className="text-xl">{opt.icon}</span>
                            <span className="text-sm font-medium">{opt.label}</span>
                            {imageSettings.defaultStyle === opt.value && (
                                <Check className="h-4 w-4 text-(--color-primary) ml-auto" />
                            )}
                        </button>
                    ))}
                </div>
            </section>

            {/* Auto Enhance */}
            <section>
                <div className="flex items-center justify-between p-4 rounded-xl border border-(--color-border)">
                    <div>
                        <div className="font-medium text-sm">Otomatik İyileştirme</div>
                        <div className="text-xs text-(--color-text-muted)">
                            Prompt'u otomatik zenginleştir
                        </div>
                    </div>
                    <button
                        onClick={() => setImageSettings({ autoEnhance: !imageSettings.autoEnhance })}
                        className={cn(
                            "relative w-12 h-6 rounded-full transition-colors",
                            imageSettings.autoEnhance
                                ? "bg-(--color-primary)"
                                : "bg-(--color-border)"
                        )}
                    >
                        <span className={cn(
                            "absolute top-1 w-4 h-4 rounded-full bg-white transition-all",
                            imageSettings.autoEnhance ? "left-7" : "left-1"
                        )} />
                    </button>
                </div>
            </section>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// FUTURE PLANS TAB
// ─────────────────────────────────────────────────────────────────────────────

function FuturePlansTab() {
    const { futurePlans, addFuturePlan, removeFuturePlan } = useSettingsStore()
    const [newPlanText, setNewPlanText] = useState('')
    const [newPlanDate, setNewPlanDate] = useState('')

    const handleAdd = () => {
        if (!newPlanText.trim() || !newPlanDate) return

        addFuturePlan({
            text: newPlanText.trim(),
            date: newPlanDate,
        })

        setNewPlanText('')
        setNewPlanDate('')
    }

    return (
        <div className="space-y-4">
            <div className="p-4 rounded-xl bg-(--color-bg) border border-(--color-border)">
                <h3 className="font-medium mb-2 flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-(--color-accent)" />
                    Gelecek Planları
                </h3>
                <p className="text-sm text-(--color-text-muted) mb-4">
                    AI bu planları hatırlayacak ve uygun zamanda hatırlatacak.
                </p>

                {/* Add New Plan */}
                <div className="space-y-2 mb-4">
                    <Input
                        placeholder="Plan açıklaması..."
                        value={newPlanText}
                        onChange={(e) => setNewPlanText(e.target.value)}
                    />
                    <div className="flex gap-2">
                        <input
                            type="date"
                            value={newPlanDate}
                            onChange={(e) => setNewPlanDate(e.target.value)}
                            className="flex-1 px-3 py-2 rounded-lg border border-(--color-border) bg-(--color-bg-input) text-sm"
                        />
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={handleAdd}
                            disabled={!newPlanText.trim() || !newPlanDate}
                        >
                            <Plus className="h-4 w-4" />
                            Ekle
                        </Button>
                    </div>
                </div>

                {/* Plan List */}
                {futurePlans.length === 0 ? (
                    <div className="text-center py-6 text-(--color-text-muted)">
                        <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Henüz plan eklenmemiş</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {futurePlans.map(plan => (
                            <div
                                key={plan.id}
                                className="flex items-center gap-3 p-3 rounded-lg bg-(--color-bg-surface) border border-(--color-border)"
                            >
                                <Calendar className="h-4 w-4 text-(--color-text-muted) shrink-0" />
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm truncate">{plan.text}</div>
                                    <div className="text-xs text-(--color-text-muted)">
                                        {new Date(plan.date).toLocaleDateString('tr-TR', {
                                            day: 'numeric',
                                            month: 'long',
                                            year: 'numeric'
                                        })}
                                    </div>
                                </div>
                                <button
                                    onClick={() => removeFuturePlan(plan.id)}
                                    className="p-1.5 rounded hover:bg-(--color-error-soft) text-(--color-text-muted) hover:text-(--color-error)"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="text-xs text-(--color-text-muted) p-3 rounded-lg bg-(--color-warning-soft)">
                ⚠️ Planlar cihazınızda saklanır. AI bunları sohbet sırasında kullanır.
            </div>
        </div>
    )
}
