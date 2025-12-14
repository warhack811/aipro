/**
 * Bottom Navigation Component
 * 
 * Mobile bottom navigation bar with haptic-like feedback
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
    MessageSquare, Brain, Image, Settings, Plus,
    Sparkles
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChatStore } from '@/stores'

interface BottomNavProps {
    onNewChat: () => void
    onMemory: () => void
    onGallery: () => void
    onSettings: () => void
}

export function BottomNav({
    onNewChat,
    onMemory,
    onGallery,
    onSettings
}: BottomNavProps) {
    const [activeTab, setActiveTab] = useState<string>('chat')
    const createConversation = useChatStore((state) => state.createConversation)

    const handleNewChat = () => {
        createConversation()
        onNewChat()
        triggerHaptic()
    }

    const tabs = [
        { id: 'chat', icon: MessageSquare, label: 'Sohbet', onClick: () => setActiveTab('chat') },
        { id: 'memory', icon: Brain, label: 'Hafıza', onClick: () => { setActiveTab('memory'); onMemory() } },
        { id: 'new', icon: Plus, label: 'Yeni', onClick: handleNewChat, isSpecial: true },
        { id: 'gallery', icon: Image, label: 'Galeri', onClick: () => { setActiveTab('gallery'); onGallery() } },
        { id: 'settings', icon: Settings, label: 'Ayarlar', onClick: () => { setActiveTab('settings'); onSettings() } },
    ]

    return (
        <nav className={cn(
            "fixed bottom-0 left-0 right-0 z-(--z-fixed)",
            "bg-(--color-bg-surface)/90 backdrop-blur-xl",
            "border-t border-(--color-border)",
            "safe-area-bottom"
        )}>
            <div className="flex items-center justify-around h-16 px-2 max-w-md mx-auto">
                {tabs.map((tab) => (
                    <NavItem
                        key={tab.id}
                        icon={tab.icon}
                        label={tab.label}
                        isActive={activeTab === tab.id}
                        isSpecial={tab.isSpecial}
                        onClick={tab.onClick}
                    />
                ))}
            </div>
        </nav>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

interface NavItemProps {
    icon: React.ElementType
    label: string
    isActive?: boolean
    isSpecial?: boolean
    onClick: () => void
}

function NavItem({ icon: Icon, label, isActive, isSpecial, onClick }: NavItemProps) {
    const handleClick = () => {
        triggerHaptic()
        onClick()
    }

    if (isSpecial) {
        return (
            <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={handleClick}
                className={cn(
                    "relative -mt-6 flex items-center justify-center",
                    "w-14 h-14 rounded-full",
                    "bg-(--gradient-brand) text-white",
                    "shadow-lg shadow-(--color-primary)/30"
                )}
            >
                <Icon className="h-6 w-6" />

                {/* Pulse effect */}
                <span className="absolute inset-0 rounded-full bg-(--gradient-brand) animate-ping opacity-20" />
            </motion.button>
        )
    }

    return (
        <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleClick}
            className={cn(
                "flex flex-col items-center justify-center",
                "w-16 h-full gap-1",
                "transition-colors"
            )}
        >
            <div className={cn(
                "p-2 rounded-xl transition-all",
                isActive
                    ? "bg-(--color-primary-soft) text-(--color-primary)"
                    : "text-(--color-text-muted)"
            )}>
                <Icon className="h-5 w-5" />
            </div>

            <span className={cn(
                "text-[10px] font-medium",
                isActive ? "text-(--color-primary)" : "text-(--color-text-muted)"
            )}>
                {label}
            </span>

            {/* Active indicator */}
            {isActive && (
                <motion.div
                    layoutId="bottomNavIndicator"
                    className="absolute -bottom-px left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-(--color-primary)"
                />
            )}
        </motion.button>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

/**
 * Trigger haptic feedback on mobile
 */
function triggerHaptic() {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
        navigator.vibrate(10) // Subtle 10ms vibration
    }
}
