/**
 * Enhanced Skeleton Components
 * 
 * Loading skeletons for various UI states
 */

import * as React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// BASE SKELETON
// ─────────────────────────────────────────────────────────────────────────────

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
    shimmer?: boolean
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
    ({ className, shimmer = true, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={cn(
                    `rounded-lg bg-(--color-bg-surface-hover)`,
                    shimmer && "relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-linear-to-r before:from-transparent before:via-white/10 before:to-transparent",
                    className
                )}
                {...props}
            />
        )
    }
)
Skeleton.displayName = 'Skeleton'

// ─────────────────────────────────────────────────────────────────────────────s
// MESSAGE SKELETON
// ─────────────────────────────────────────────────────────────────────────────

interface MessageSkeletonProps {
    isUser?: boolean
    lines?: number
}

const MessageSkeleton: React.FC<MessageSkeletonProps> = ({ isUser = false, lines = 3 }) => (
    <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn('flex gap-3 px-4 py-3', isUser ? 'flex-row-reverse' : 'flex-row')}
    >
        <Skeleton className="h-10 w-10 rounded-full shrink-0" />
        <div className={cn('space-y-2 flex flex-col', isUser ? 'items-end' : 'items-start')}>
            <Skeleton className="h-3 w-20 rounded" />
            <div className="space-y-1.5">
                {Array.from({ length: lines }).map((_, i) => (
                    <Skeleton
                        key={i}
                        className={cn(
                            "h-4 rounded",
                            i === lines - 1 ? "w-32" : i === 0 ? "w-64" : "w-48"
                        )}
                    />
                ))}
            </div>
        </div>
    </motion.div>
)

// ─────────────────────────────────────────────────────────────────────────────
// CONVERSATION LIST SKELETON
// ─────────────────────────────────────────────────────────────────────────────

const ConversationListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
    <div className="space-y-2 p-2">
        {Array.from({ length: count }).map((_, i) => (
            <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 p-3 rounded-xl"
            >
                <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
                <div className="flex-1 space-y-1.5">
                    <Skeleton className={cn("h-4 rounded", i % 2 === 0 ? "w-3/4" : "w-1/2")} />
                    <Skeleton className="h-3 w-16 rounded" />
                </div>
            </motion.div>
        ))}
    </div>
)

// ─────────────────────────────────────────────────────────────────────────────
// CHAT LOADING SKELETON
// ─────────────────────────────────────────────────────────────────────────────

const ChatLoadingSkeleton: React.FC = () => (
    <div className="flex-1 overflow-hidden">
        <div className="max-w-(--chat-max-width) mx-auto py-6 space-y-6">
            <MessageSkeleton isUser={false} lines={2} />
            <MessageSkeleton isUser={true} lines={1} />
            <MessageSkeleton isUser={false} lines={4} />
            <MessageSkeleton isUser={true} lines={2} />
            <MessageSkeleton isUser={false} lines={3} />
        </div>
    </div>
)

// ─────────────────────────────────────────────────────────────────────────────
// SIDEBAR SKELETON
// ─────────────────────────────────────────────────────────────────────────────

const SidebarSkeleton: React.FC = () => (
    <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-(--color-border)">
            <div className="flex items-center gap-3 mb-4">
                <Skeleton className="h-10 w-10 rounded-xl" />
                <div className="space-y-1.5 flex-1">
                    <Skeleton className="h-4 w-24 rounded" />
                    <Skeleton className="h-3 w-32 rounded" />
                </div>
            </div>
            <Skeleton className="h-10 w-full rounded-xl" />
        </div>

        {/* Conversations */}
        <ConversationListSkeleton count={6} />
    </div>
)

// ─────────────────────────────────────────────────────────────────────────────
// CARD SKELETON
// ─────────────────────────────────────────────────────────────────────────────

const CardSkeleton: React.FC<{ hasImage?: boolean }> = ({ hasImage = false }) => (
    <div className="p-4 rounded-2xl border border-(--color-border) bg-(--color-bg-surface)">
        {hasImage && <Skeleton className="h-40 w-full rounded-xl mb-4" />}
        <div className="space-y-3">
            <Skeleton className="h-5 w-3/4 rounded" />
            <Skeleton className="h-4 w-full rounded" />
            <Skeleton className="h-4 w-2/3 rounded" />
        </div>
    </div>
)

// ─────────────────────────────────────────────────────────────────────────────
// TABLE SKELETON
// ─────────────────────────────────────────────────────────────────────────────

const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({ rows = 5, cols = 4 }) => (
    <div className="rounded-xl border border-(--color-border) overflow-hidden">
        {/* Header */}
        <div className="flex gap-4 p-4 bg-(--color-bg-surface)">
            {Array.from({ length: cols }).map((_, i) => (
                <Skeleton key={i} className="h-4 flex-1 rounded" />
            ))}
        </div>
        {/* Rows */}
        {Array.from({ length: rows }).map((_, row) => (
            <div key={row} className="flex gap-4 p-4 border-t border-(--color-border)">
                {Array.from({ length: cols }).map((_, col) => (
                    <Skeleton
                        key={col}
                        className={cn("h-4 flex-1 rounded", col === 0 && "w-1/4 flex-none")}
                    />
                ))}
            </div>
        ))}
    </div>
)

export {
    Skeleton,
    MessageSkeleton,
    ConversationListSkeleton,
    ChatLoadingSkeleton,
    SidebarSkeleton,
    CardSkeleton,
    TableSkeleton
}
