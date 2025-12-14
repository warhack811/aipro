/**
 * ReplyPreview Component
 * 
 * Shows the replied-to message above the current message
 */

import { motion } from 'framer-motion'
import { CornerDownRight, X } from 'lucide-react'
import { cn, truncate } from '@/lib/utils'
import type { Message } from '@/types'

interface ReplyPreviewProps {
    replyTo: Message
    onClick?: () => void
    onRemove?: () => void
    isInline?: boolean  // True when shown in message, false in input area
    className?: string
}

export function ReplyPreview({
    replyTo,
    onClick,
    onRemove,
    isInline = true,
    className
}: ReplyPreviewProps) {
    const isUser = replyTo.role === 'user'

    return (
        <motion.div
            initial={{ opacity: 0, y: isInline ? 5 : -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: isInline ? 5 : -5 }}
            className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg",
                "border-l-2 border-(--color-primary)",
                isInline
                    ? "bg-(--color-bg-surface)/50 mb-2"
                    : "bg-(--color-bg-surface) mb-2",
                onClick && "cursor-pointer hover:bg-(--color-bg-surface-hover)",
                className
            )}
            onClick={onClick}
        >
            <CornerDownRight className="h-4 w-4 text-(--color-text-muted) flex-shrink-0" />

            <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-(--color-primary)">
                    {isUser ? 'Sen' : 'AI'}
                </div>
                <div className="text-sm text-(--color-text-muted) truncate">
                    {truncate(replyTo.content, 60)}
                </div>
            </div>

            {onRemove && (
                <button
                    onClick={(e) => {
                        e.stopPropagation()
                        onRemove()
                    }}
                    className="p-1 rounded hover:bg-(--color-bg-elevated) text-(--color-text-muted)"
                >
                    <X className="h-4 w-4" />
                </button>
            )}
        </motion.div>
    )
}
