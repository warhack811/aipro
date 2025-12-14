/**
 * MessageReactions Component
 * 
 * Emoji reactions for messages (like Slack/Discord)
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { SmilePlus } from 'lucide-react'
import { cn } from '@/lib/utils'

// Available reactions
const REACTIONS = [
    { emoji: '👍', label: 'Beğen' },
    { emoji: '❤️', label: 'Sevdim' },
    { emoji: '😂', label: 'Komik' },
    { emoji: '😮', label: 'Şaşırdım' },
    { emoji: '🤔', label: 'Düşünüyorum' },
    { emoji: '🎉', label: 'Harika' },
    { emoji: '👀', label: 'İlginç' },
    { emoji: '🔥', label: 'Ateş' },
]

interface Reaction {
    emoji: string
    count: number
    reacted: boolean
}

interface MessageReactionsProps {
    messageId: string
    reactions?: Reaction[]
    onReact?: (emoji: string) => void
    className?: string
}

export function MessageReactions({
    messageId,
    reactions = [],
    onReact,
    className
}: MessageReactionsProps) {
    const [showPicker, setShowPicker] = useState(false)

    const handleReact = (emoji: string) => {
        onReact?.(emoji)
        setShowPicker(false)
    }

    return (
        <div className={cn("flex items-center gap-1 flex-wrap", className)}>
            {/* Existing reactions */}
            {reactions.map((reaction) => (
                <motion.button
                    key={reaction.emoji}
                    onClick={() => handleReact(reaction.emoji)}
                    className={cn(
                        "flex items-center gap-1 px-2 py-0.5 rounded-full text-xs",
                        "border transition-all duration-200",
                        reaction.reacted
                            ? "bg-(--color-primary-soft) border-(--color-primary) text-(--color-primary)"
                            : "bg-(--color-bg-surface) border-(--color-border) hover:border-(--color-primary)"
                    )}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <span>{reaction.emoji}</span>
                    <span className="font-medium">{reaction.count}</span>
                </motion.button>
            ))}

            {/* Add reaction button */}
            <div className="relative">
                <motion.button
                    onClick={() => setShowPicker(!showPicker)}
                    className={cn(
                        "p-1.5 rounded-full transition-all duration-200",
                        "hover:bg-(--color-bg-surface-hover)",
                        "text-(--color-text-muted)",
                        showPicker && "bg-(--color-bg-surface-hover)"
                    )}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                >
                    <SmilePlus className="h-4 w-4" />
                </motion.button>

                {/* Emoji picker */}
                <AnimatePresence>
                    {showPicker && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 5 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 5 }}
                            className={cn(
                                "absolute bottom-full left-0 mb-2 z-50",
                                "flex gap-1 p-2 rounded-xl",
                                "bg-(--color-bg-surface) border border-(--color-border)",
                                "shadow-lg"
                            )}
                        >
                            {REACTIONS.map((reaction) => (
                                <motion.button
                                    key={reaction.emoji}
                                    onClick={() => handleReact(reaction.emoji)}
                                    className="p-1.5 rounded-lg hover:bg-(--color-bg-surface-hover) text-lg"
                                    whileHover={{ scale: 1.2 }}
                                    whileTap={{ scale: 0.9 }}
                                    title={reaction.label}
                                >
                                    {reaction.emoji}
                                </motion.button>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}
