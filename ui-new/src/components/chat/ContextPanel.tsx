/**
 * Context Panel Component
 * 
 * Collapsible panel showing sources, memory, and context used for AI response
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    ChevronDown,
    ChevronUp,
    Link2,
    Brain,
    FileText,
    Clock,
    ExternalLink,
    BookOpen
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface Source {
    title: string
    url: string
    snippet?: string
    date?: string
    favicon?: string
}

interface Memory {
    id: string
    text: string
    importance: number
    createdAt: string
}

interface ContextPanelProps {
    sources?: Source[]
    memories?: Memory[]
    documentChunks?: { title: string; snippet: string }[]
    isOpen?: boolean
    onToggle?: () => void
    className?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// CONTEXT PANEL
// ─────────────────────────────────────────────────────────────────────────────

export function ContextPanel({
    sources = [],
    memories = [],
    documentChunks = [],
    isOpen = false,
    onToggle,
    className
}: ContextPanelProps) {
    const [expanded, setExpanded] = useState(isOpen)

    const totalItems = sources.length + memories.length + documentChunks.length

    if (totalItems === 0) return null

    const handleToggle = () => {
        setExpanded(!expanded)
        onToggle?.()
    }

    return (
        <div className={cn(
            "rounded-xl border border-(--color-border) bg-(--color-bg-surface)",
            "overflow-hidden",
            className
        )}>
            {/* Header */}
            <button
                onClick={handleToggle}
                className={cn(
                    "w-full flex items-center justify-between px-4 py-3",
                    "hover:bg-(--color-bg-surface-hover) transition-colors",
                    "text-left"
                )}
            >
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-(--color-primary-soft)">
                        <BookOpen className="h-4 w-4 text-(--color-primary)" />
                    </div>
                    <div>
                        <span className="text-sm font-medium">Kullanılan Kaynaklar</span>
                        <span className="ml-2 text-xs text-(--color-text-muted)">
                            ({totalItems} kaynak)
                        </span>
                    </div>
                </div>

                <motion.div
                    animate={{ rotate: expanded ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                >
                    <ChevronDown className="h-5 w-5 text-(--color-text-muted)" />
                </motion.div>
            </button>

            {/* Content */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="border-t border-(--color-border)"
                    >
                        <div className="p-4 space-y-4 max-h-75 overflow-y-auto scrollbar-thin">
                            {/* Web Sources */}
                            {sources.length > 0 && (
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <Link2 className="h-4 w-4 text-(--color-info)" />
                                        <span className="text-xs font-medium text-(--color-text-muted) uppercase tracking-wider">
                                            Web Kaynakları
                                        </span>
                                    </div>
                                    <div className="space-y-2">
                                        {sources.map((source, i) => (
                                            <SourceCard key={i} source={source} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Memories */}
                            {memories.length > 0 && (
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <Brain className="h-4 w-4 text-(--color-secondary)" />
                                        <span className="text-xs font-medium text-(--color-text-muted) uppercase tracking-wider">
                                            Hatırlanan Bilgiler
                                        </span>
                                    </div>
                                    <div className="space-y-2">
                                        {memories.map((memory) => (
                                            <MemoryCard key={memory.id} memory={memory} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Document Chunks */}
                            {documentChunks.length > 0 && (
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <FileText className="h-4 w-4 text-(--color-accent)" />
                                        <span className="text-xs font-medium text-(--color-text-muted) uppercase tracking-wider">
                                            Doküman Parçaları
                                        </span>
                                    </div>
                                    <div className="space-y-2">
                                        {documentChunks.map((chunk, i) => (
                                            <DocumentChunkCard key={i} chunk={chunk} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// SUB COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

function SourceCard({ source }: { source: Source }) {
    const domain = new URL(source.url).hostname.replace('www.', '')

    return (
        <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
                "block p-3 rounded-lg",
                "bg-(--color-bg) border border-(--color-border)",
                "hover:border-(--color-primary) transition-colors group"
            )}
        >
            <div className="flex items-start gap-3">
                {source.favicon ? (
                    <img src={source.favicon} alt="" className="w-4 h-4 mt-0.5 rounded" />
                ) : (
                    <Link2 className="w-4 h-4 mt-0.5 text-(--color-text-muted)" />
                )}

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate group-hover:text-(--color-primary)">
                            {source.title}
                        </span>
                        <ExternalLink className="h-3 w-3 text-(--color-text-muted) opacity-0 group-hover:opacity-100" />
                    </div>
                    <span className="text-xs text-(--color-text-muted)">{domain}</span>
                    {source.snippet && (
                        <p className="text-xs text-(--color-text-secondary) mt-1 line-clamp-2">
                            {source.snippet}
                        </p>
                    )}
                </div>
            </div>
        </a>
    )
}

function MemoryCard({ memory }: { memory: Memory }) {
    return (
        <div className={cn(
            "p-3 rounded-lg",
            "bg-(--color-bg) border border-(--color-border)"
        )}>
            <p className="text-sm">{memory.text}</p>
            <div className="flex items-center gap-2 mt-2">
                <Clock className="h-3 w-3 text-(--color-text-muted)" />
                <span className="text-xs text-(--color-text-muted)">
                    {new Date(memory.createdAt).toLocaleDateString('tr-TR')}
                </span>
                <span className={cn(
                    "px-1.5 py-0.5 rounded text-xs",
                    memory.importance > 0.7
                        ? "bg-(--color-error-soft) text-(--color-error)"
                        : memory.importance > 0.4
                            ? "bg-(--color-warning-soft) text-(--color-warning)"
                            : "bg-(--color-success-soft) text-(--color-success)"
                )}>
                    {memory.importance > 0.7 ? 'Önemli' : memory.importance > 0.4 ? 'Normal' : 'Düşük'}
                </span>
            </div>
        </div>
    )
}

function DocumentChunkCard({ chunk }: { chunk: { title: string; snippet: string } }) {
    return (
        <div className={cn(
            "p-3 rounded-lg",
            "bg-(--color-bg) border border-(--color-border)"
        )}>
            <div className="flex items-center gap-2 mb-1">
                <FileText className="h-3 w-3 text-(--color-accent)" />
                <span className="text-xs font-medium">{chunk.title}</span>
            </div>
            <p className="text-xs text-(--color-text-secondary) line-clamp-3">
                {chunk.snippet}
            </p>
        </div>
    )
}
