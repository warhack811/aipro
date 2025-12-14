/**
 * Conversation Search Component
 * 
 * Search within conversations with:
 * - Real-time search
 * - Message highlighting
 * - Quick navigation
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, X, MessageSquare, ChevronRight, Calendar, Clock } from 'lucide-react'
import { useChatStore } from '@/stores'
import { Input } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { Message, Conversation } from '@/types'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface SearchResult {
    conversationId: string
    conversationTitle: string
    messageId: string
    content: string
    role: 'user' | 'assistant'
    timestamp?: string
    matchIndices: [number, number][]
}

interface ConversationSearchProps {
    isOpen: boolean
    onClose: () => void
    onNavigate?: (conversationId: string, messageId?: string) => void
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export function ConversationSearch({ isOpen, onClose, onNavigate }: ConversationSearchProps) {
    const [query, setQuery] = useState('')
    const [selectedIndex, setSelectedIndex] = useState(0)
    const inputRef = useRef<HTMLInputElement>(null)

    const conversations = useChatStore((state) => state.conversations)
    const messages = useChatStore((state) => state.messages)
    const currentConversationId = useChatStore((state) => state.currentConversationId)

    // Focus input on open
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 100)
            setQuery('')
            setSelectedIndex(0)
        }
    }, [isOpen])

    // Search logic
    const results = useMemo((): SearchResult[] => {
        if (!query.trim() || query.length < 2) return []

        const searchResults: SearchResult[] = []
        const lowerQuery = query.toLowerCase()

        // Search in current conversation messages
        if (currentConversationId) {
            const currentConv = conversations.find(c => c.id === currentConversationId)

            messages.forEach((msg, idx) => {
                if (msg.content?.toLowerCase().includes(lowerQuery)) {
                    const lowerContent = msg.content.toLowerCase()
                    const matchStart = lowerContent.indexOf(lowerQuery)

                    searchResults.push({
                        conversationId: currentConversationId,
                        conversationTitle: currentConv?.title || 'Mevcut Sohbet',
                        messageId: msg.id || `msg-${idx}`,
                        content: msg.content,
                        role: msg.role === 'user' ? 'user' : 'assistant',
                        timestamp: msg.timestamp,
                        matchIndices: [[matchStart, matchStart + query.length]]
                    })
                }
            })
        }

        // Search in conversation titles
        conversations.forEach(conv => {
            if (conv.title?.toLowerCase().includes(lowerQuery)) {
                const lowerTitle = conv.title.toLowerCase()
                const matchStart = lowerTitle.indexOf(lowerQuery)

                searchResults.push({
                    conversationId: conv.id,
                    conversationTitle: conv.title,
                    messageId: '',
                    content: conv.title,
                    role: 'user',
                    matchIndices: [[matchStart, matchStart + query.length]]
                })
            }
        })

        return searchResults.slice(0, 20)
    }, [query, messages, conversations, currentConversationId])

    // Keyboard navigation
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setSelectedIndex(prev => Math.min(prev + 1, results.length - 1))
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setSelectedIndex(prev => Math.max(prev - 1, 0))
        } else if (e.key === 'Enter' && results[selectedIndex]) {
            e.preventDefault()
            handleSelect(results[selectedIndex])
        } else if (e.key === 'Escape') {
            onClose()
        }
    }, [results, selectedIndex, onClose])

    const handleSelect = useCallback((result: SearchResult) => {
        onNavigate?.(result.conversationId, result.messageId)
        onClose()
    }, [onNavigate, onClose])

    if (!isOpen) return null

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-[10vh]"
                onClick={onClose}
            >
                <motion.div
                    initial={{ opacity: 0, y: -20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -20, scale: 0.95 }}
                    onClick={(e) => e.stopPropagation()}
                    className={cn(
                        "w-full max-w-2xl mx-4 rounded-2xl overflow-hidden",
                        "bg-(--color-bg-surface) border border-(--color-border)",
                        "shadow-2xl"
                    )}
                >
                    {/* Search Input */}
                    <div className="flex items-center gap-3 p-4 border-b border-(--color-border)">
                        <Search className="h-5 w-5 text-(--color-text-muted)" />
                        <input
                            ref={inputRef}
                            type="text"
                            value={query}
                            onChange={(e) => {
                                setQuery(e.target.value)
                                setSelectedIndex(0)
                            }}
                            onKeyDown={handleKeyDown}
                            placeholder="Sohbetlerde ara..."
                            className={cn(
                                "flex-1 bg-transparent text-lg outline-none",
                                "placeholder-(--color-text-muted)"
                            )}
                        />
                        {query && (
                            <button
                                onClick={() => setQuery('')}
                                className="p-1 rounded hover:bg-(--color-bg-surface-hover)"
                            >
                                <X className="h-4 w-4 text-(--color-text-muted)" />
                            </button>
                        )}
                    </div>

                    {/* Results */}
                    <div className="max-h-[400px] overflow-y-auto">
                        {query.length < 2 ? (
                            <div className="p-8 text-center text-(--color-text-muted)">
                                <Search className="h-10 w-10 mx-auto mb-3 opacity-50" />
                                <p>En az 2 karakter yazın</p>
                            </div>
                        ) : results.length === 0 ? (
                            <div className="p-8 text-center text-(--color-text-muted)">
                                <MessageSquare className="h-10 w-10 mx-auto mb-3 opacity-50" />
                                <p>Sonuç bulunamadı</p>
                            </div>
                        ) : (
                            <div className="p-2">
                                {results.map((result, idx) => (
                                    <SearchResultItem
                                        key={`${result.conversationId}-${result.messageId}-${idx}`}
                                        result={result}
                                        query={query}
                                        isSelected={idx === selectedIndex}
                                        onClick={() => handleSelect(result)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-3 border-t border-(--color-border) flex items-center justify-between text-xs text-(--color-text-muted)">
                        <div className="flex items-center gap-4">
                            <span>↑↓ Gezin</span>
                            <span>↵ Seç</span>
                            <span>Esc Kapat</span>
                        </div>
                        {results.length > 0 && (
                            <span>{results.length} sonuç</span>
                        )}
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// SEARCH RESULT ITEM
// ─────────────────────────────────────────────────────────────────────────────

interface SearchResultItemProps {
    result: SearchResult
    query: string
    isSelected: boolean
    onClick: () => void
}

function SearchResultItem({ result, query, isSelected, onClick }: SearchResultItemProps) {
    // Highlight matched text
    const highlightText = (text: string) => {
        const lowerText = text.toLowerCase()
        const lowerQuery = query.toLowerCase()
        const index = lowerText.indexOf(lowerQuery)

        if (index === -1) return text

        return (
            <>
                {text.slice(0, index)}
                <mark className="bg-(--color-warning) text-(--color-bg) px-0.5 rounded">
                    {text.slice(index, index + query.length)}
                </mark>
                {text.slice(index + query.length)}
            </>
        )
    }

    // Truncate content around match
    const getContextSnippet = (content: string, maxLength = 100) => {
        const lowerContent = content.toLowerCase()
        const lowerQuery = query.toLowerCase()
        const matchIndex = lowerContent.indexOf(lowerQuery)

        if (matchIndex === -1 || content.length <= maxLength) {
            return content.slice(0, maxLength)
        }

        const start = Math.max(0, matchIndex - 30)
        const end = Math.min(content.length, matchIndex + query.length + 50)

        let snippet = content.slice(start, end)
        if (start > 0) snippet = '...' + snippet
        if (end < content.length) snippet += '...'

        return snippet
    }

    return (
        <button
            onClick={onClick}
            className={cn(
                "w-full flex items-start gap-3 p-3 rounded-xl text-left",
                "transition-colors duration-150",
                isSelected
                    ? "bg-(--color-primary-soft)"
                    : "hover:bg-(--color-bg-surface-hover)"
            )}
        >
            <div className={cn(
                "p-2 rounded-lg shrink-0",
                result.role === 'user'
                    ? "bg-(--color-primary-soft)"
                    : "bg-(--color-secondary-soft)"
            )}>
                <MessageSquare className={cn(
                    "h-4 w-4",
                    result.role === 'user'
                        ? "text-(--color-primary)"
                        : "text-(--color-secondary)"
                )} />
            </div>

            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs text-(--color-text-muted)">
                        {result.conversationTitle}
                    </span>
                </div>
                <p className="text-sm line-clamp-2">
                    {highlightText(getContextSnippet(result.content))}
                </p>
                {result.timestamp && (
                    <div className="flex items-center gap-1 mt-1 text-xs text-(--color-text-muted)">
                        <Clock className="h-3 w-3" />
                        {new Date(result.timestamp).toLocaleDateString('tr-TR')}
                    </div>
                )}
            </div>

            <ChevronRight className={cn(
                "h-4 w-4 shrink-0 text-(--color-text-muted)",
                isSelected && "text-(--color-primary)"
            )} />
        </button>
    )
}
