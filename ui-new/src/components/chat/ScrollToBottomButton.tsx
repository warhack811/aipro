/**
 * ScrollToBottomButton Component
 * 
 * Floating button to scroll to the latest message
 */

import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ScrollToBottomButtonProps {
    visible: boolean
    onClick: () => void
    unreadCount?: number
    className?: string
}

export function ScrollToBottomButton({
    visible,
    onClick,
    unreadCount = 0,
    className
}: ScrollToBottomButtonProps) {
    return (
        <AnimatePresence>
            {visible && (
                <motion.button
                    initial={{ opacity: 0, y: 20, scale: 0.8 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.8 }}
                    transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                    onClick={onClick}
                    className={cn(
                        "fixed bottom-24 right-6 z-40",
                        "w-10 h-10 rounded-full",
                        "bg-(--color-bg-surface) border border-(--color-border)",
                        "shadow-lg hover:shadow-xl",
                        "flex items-center justify-center",
                        "transition-all duration-200",
                        "hover:bg-(--color-bg-surface-hover)",
                        "active:scale-95",
                        className
                    )}
                    aria-label="Aşağı kaydır"
                >
                    <ChevronDown className="h-5 w-5 text-(--color-text-secondary)" />

                    {/* Unread badge */}
                    {unreadCount > 0 && (
                        <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className={cn(
                                "absolute -top-1 -right-1",
                                "min-w-5 h-5 px-1.5",
                                "rounded-full bg-(--color-primary)",
                                "text-white text-xs font-bold",
                                "flex items-center justify-center"
                            )}
                        >
                            {unreadCount > 9 ? '9+' : unreadCount}
                        </motion.span>
                    )}
                </motion.button>
            )}
        </AnimatePresence>
    )
}
