/**
 * MessageBubble Component
 * 
 * Premium message bubble with:
 * - Enhanced markdown rendering
 * - Syntax highlighted code blocks
 * - Message reactions
 * - Reply support
 * - Action bar
 * - Image generation support (progress & completed)
 */

import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, ThumbsUp, ThumbsDown, RefreshCw, Check, Sparkles, Reply } from 'lucide-react'
import type { Message, ImageJob } from '@/types'
import { Avatar } from '@/components/ui'
import { MessageReactions } from './MessageReactions'
import { ReplyPreview } from './ReplyPreview'
import { ContextPanel } from './ContextPanel'
import { ImageProgressCard } from './ImageProgressCard'
import { ImageCompletedCard } from './ImageCompletedCard'
import { renderMarkdown, setupCodeCopyButtons } from '@/lib/markdownRenderer'
import { cn, formatTime, copyToClipboard, decodeHtmlEntities } from '@/lib/utils'
import { useChatStore, useUserStore } from '@/stores'
import { useImageProgress } from '@/hooks/useImageProgress'
import { chatApi } from '@/api'

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface MessageBubbleProps {
    message: Message
    onReply?: (message: Message) => void
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPERS - Message Content Detection
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Check if message is an image pending message
 * Backend sometimes strips [IMAGE_PENDING] tag, so we also check for the text
 */
function isImagePendingMessage(content: string): boolean {
    return content.includes('[IMAGE_PENDING]') ||
        content.includes('Görsel isteğiniz kuyruğa alındı')
}

/**
 * Check if message contains a completed image
 */
function isImageCompletedMessage(content: string): boolean {
    return content.includes('IMAGE_PATH:')
}

/**
 * Extract image URL from message content
 */
function extractImageUrl(content: string): string | null {
    const match = content.match(/IMAGE_PATH:\s*(\S+)/)
    return match ? match[1] : null
}

/**
 * Extract prompt from image message
 */
function extractImagePrompt(content: string): string {
    // Try to get prompt from data attribute
    const promptMatch = content.match(/data-prompt="([^"]+)"/)
    if (promptMatch) {
        // Decode HTML entities (&#x27; -> ' etc.)
        return decodeHtmlEntities(promptMatch[1])
    }

    // Fallback: return cleaned content
    return content
        .replace(/\[IMAGE\].*$/m, '')
        .replace(/IMAGE_PATH:\s*\S+/, '')
        .replace(/<[^>]+>/g, '')
        .trim() || 'Görsel'
}

/**
 * Get clean text content (without image markers and system prefixes)
 */
function getCleanContent(content: string): string {
    return content
        // Remove system prefixes
        .replace(/^\[GROQ\]\s*/gm, '')
        .replace(/^\[BELA\]\s*/gm, '')
        // Remove image markers
        .replace(/\[IMAGE_PENDING\].*$/gm, '')
        .replace(/\[IMAGE\].*$/gm, '')
        .replace(/IMAGE_PATH:\s*\S+/g, '')
        .replace(/<span class="image-prompt"[^>]*><\/span>/g, '')
        .trim()
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function MessageBubble({ message, onReply }: MessageBubbleProps) {
    const isUser = message.role === 'user'
    const user = useUserStore((state) => state.user)
    const updateMessage = useChatStore((state) => state.updateMessage)
    const deleteMessage = useChatStore((state) => state.deleteMessage)
    const messages = useChatStore((state) => state.messages)
    const setInputValue = useChatStore((state) => state.setInputValue)
    const currentConversationId = useChatStore((state) => state.currentConversationId)
    const contentRef = useRef<HTMLDivElement>(null)

    const [copied, setCopied] = useState(false)
    const [isHovered, setIsHovered] = useState(false)

    // Detect message type
    const isPending = isImagePendingMessage(message.content)
    const isCompleted = isImageCompletedMessage(message.content)
    const isImageMessage = isPending || isCompleted

    // Get job_id from message metadata
    const jobId = message.extra_metadata?.job_id

    // Get progress from WebSocket cache (if available)
    const progressData = useImageProgress(jobId)

    // Get replied message if exists
    const repliedMessage = useMemo(() => {
        if (!message.replyToId) return null
        return messages.find(m => m.id === message.replyToId)
    }, [message.replyToId, messages])

    // Build current job from message extra_metadata (updated by WebSocket)
    const currentJob = useMemo((): ImageJob | null => {
        if (!isPending) return null

        // Read status directly from extra_metadata (updated by WebSocket handler)
        const metaStatus = message.extra_metadata?.status as 'queued' | 'processing' | 'complete' | 'error' | undefined
        const metaProgress = message.extra_metadata?.progress as number | undefined
        const metaQueuePos = message.extra_metadata?.queue_position as number | undefined

        return {
            id: jobId || `fallback-${message.id}`,
            conversationId: currentConversationId || undefined,
            prompt: (message.extra_metadata?.prompt as string) || extractImagePrompt(message.content) || 'Görsel oluşturuluyor...',
            status: metaStatus || 'queued',
            progress: metaProgress ?? 0,
            queuePosition: metaQueuePos || 1,
        }
    }, [isPending, jobId, message.id, message.extra_metadata, message.content, currentConversationId])

    // Extract image data for completed messages
    const imageData = useMemo(() => {
        if (!isCompleted) return null

        const imageUrl = extractImageUrl(message.content)
        const prompt = extractImagePrompt(message.content)

        return { imageUrl, prompt }
    }, [isCompleted, message.content])

    // Get clean content (for non-image or partial messages)
    const cleanContent = useMemo(() => {
        return getCleanContent(message.content)
    }, [message.content])

    // Parse markdown for assistant messages
    const htmlContent = useMemo(() => {
        if (isUser || !cleanContent || isImageMessage) return cleanContent
        return renderMarkdown(cleanContent)
    }, [cleanContent, isUser, isImageMessage])

    // Setup code copy buttons after render
    useEffect(() => {
        if (contentRef.current && !isUser && !isImageMessage) {
            setupCodeCopyButtons(contentRef.current)
        }
    }, [htmlContent, isUser, isImageMessage])

    // Handlers
    const handleCopy = async () => {
        const success = await copyToClipboard(message.content)
        if (success) {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    const handleFeedback = async (type: 'like' | 'dislike') => {
        try {
            await chatApi.submitFeedback(message.id, type)
            updateMessage(message.id, { feedback: type })
        } catch (error) {
            console.error('Feedback error:', error)
        }
    }

    const handleReact = (emoji: string) => {
        const currentReactions = message.reactions || []
        const existing = currentReactions.find(r => r.emoji === emoji)

        let newReactions
        if (existing) {
            if (existing.reacted) {
                newReactions = currentReactions.map(r =>
                    r.emoji === emoji
                        ? { ...r, count: r.count - 1, reacted: false }
                        : r
                ).filter(r => r.count > 0)
            } else {
                newReactions = currentReactions.map(r =>
                    r.emoji === emoji
                        ? { ...r, count: r.count + 1, reacted: true }
                        : r
                )
            }
        } else {
            newReactions = [...currentReactions, { emoji, count: 1, reacted: true }]
        }

        updateMessage(message.id, { reactions: newReactions })
    }

    const handleCancelImage = useCallback(async (jobId: string) => {
        try {
            // Call cancel API
            const result = await chatApi.cancelJob(jobId)
            console.log('[Cancel] Result:', result)

            if (result.success) {
                // Wait for animation then delete message
                setTimeout(() => {
                    deleteMessage(message.id)
                }, 800)
            }
        } catch (error) {
            console.error('Cancel failed:', error)
        }
    }, [message.id, deleteMessage])

    const handleRegenerateImage = useCallback((prompt: string) => {
        // Set the input value with the regenerate prompt
        // User will need to press send
        setInputValue(`Görsel oluştur: ${prompt}`)
    }, [setInputValue])

    const handleOpenLightbox = useCallback((imageUrl: string) => {
        // TODO: Implement lightbox modal
        window.open(imageUrl, '_blank')
    }, [])

    // ─────────────────────────────────────────────────────────────────────────
    // RENDER: Image Pending (Progress)
    // ─────────────────────────────────────────────────────────────────────────
    if (isPending && currentJob) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="group flex gap-3 px-4 py-3 flex-row"
            >
                {/* Avatar */}
                <Avatar
                    size="md"
                    fallback={<Sparkles className="h-4 w-4" />}
                    className="shrink-0 mt-1"
                />

                {/* Progress Card */}
                <div className="max-w-(--message-max-width)">
                    <ImageProgressCard
                        job={currentJob}
                        onCancel={handleCancelImage}
                    />
                </div>
            </motion.div>
        )
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RENDER: Image Completed
    // ─────────────────────────────────────────────────────────────────────────
    if (isCompleted && imageData?.imageUrl) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="group flex gap-3 px-4 py-3 flex-row"
            >
                {/* Avatar */}
                <Avatar
                    size="md"
                    fallback={<Sparkles className="h-4 w-4" />}
                    className="shrink-0 mt-1"
                />

                {/* Completed Image Card */}
                <div className="flex flex-col gap-1 max-w-(--message-max-width)">
                    <ImageCompletedCard
                        imageUrl={imageData.imageUrl}
                        prompt={imageData.prompt}
                        onRegenerate={handleRegenerateImage}
                        onOpenLightbox={handleOpenLightbox}
                    />

                    {/* Timestamp */}
                    <span className="text-xs text-(--color-text-muted) px-1">
                        {formatTime(message.timestamp)}
                    </span>
                </div>
            </motion.div>
        )
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RENDER: Standard Message
    // ─────────────────────────────────────────────────────────────────────────
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "group flex gap-3 px-4 py-3",
                isUser ? "flex-row-reverse" : "flex-row"
            )}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Avatar */}
            <Avatar
                size="md"
                src={isUser ? user?.avatarUrl : undefined}
                fallback={isUser ? (
                    user?.displayName?.[0] || user?.username?.[0] || 'U'
                ) : (
                    <Sparkles className="h-4 w-4" />
                )}
                className="shrink-0 mt-1"
            />

            {/* Content */}
            <div className={cn(
                "flex flex-col gap-1",
                isUser ? "items-end" : "items-start",
                "max-w-(--message-max-width)"
            )}>
                {/* Model Badge (for assistant) */}
                {!isUser && message.model && (
                    <div className="flex items-center gap-2 mb-0.5">
                        <span className={cn(
                            "px-2 py-0.5 rounded-full text-xs font-medium",
                            "bg-(--color-primary-soft) text-(--color-primary)"
                        )}>
                            {message.model.toUpperCase()}
                        </span>
                    </div>
                )}

                {/* Reply Preview */}
                {repliedMessage && (
                    <ReplyPreview replyTo={repliedMessage} />
                )}

                {/* Message Bubble */}
                <div className={cn(
                    "relative px-4 py-3 rounded-2xl",
                    isUser ? [
                        "rounded-tr-sm",
                        "bg-(--color-msg-user) border border-(--color-msg-user-border)",
                        "text-(--color-msg-user-text)"
                    ] : [
                        "rounded-tl-sm",
                        "bg-(--color-msg-bot) border border-(--color-msg-bot-border)",
                        "text-(--color-msg-bot-text)"
                    ]
                )}>
                    {/* Content */}
                    {isUser ? (
                        <p className="text-base leading-relaxed whitespace-pre-wrap">{cleanContent}</p>
                    ) : (
                        <>
                            <div
                                ref={contentRef}
                                className="prose prose-sm max-w-none message-content"
                                dangerouslySetInnerHTML={{ __html: htmlContent }}
                            />

                            {/* Streaming Cursor */}
                            {message.isStreaming && (
                                <span className="inline-block w-0.75 h-[1.2em] bg-(--color-primary) rounded-sm ml-1 animate-pulse" />
                            )}
                        </>
                    )}

                    {/* Hover Actions */}
                    <AnimatePresence>
                        {isHovered && !message.isStreaming && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                className={cn(
                                    "absolute -top-10 flex items-center gap-0.5 p-1 rounded-lg",
                                    "bg-(--color-bg-surface) border border-(--color-border)",
                                    "shadow-lg",
                                    isUser ? "right-0" : "left-0"
                                )}
                            >
                                {onReply && (
                                    <ActionButton
                                        icon={<Reply className="h-3.5 w-3.5" />}
                                        onClick={() => onReply(message)}
                                        label="Yanıtla"
                                    />
                                )}
                                <ActionButton
                                    icon={copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                                    onClick={handleCopy}
                                    label="Kopyala"
                                    active={copied}
                                />
                                {!isUser && (
                                    <>
                                        <ActionButton
                                            icon={<ThumbsUp className="h-3.5 w-3.5" />}
                                            onClick={() => handleFeedback('like')}
                                            label="Beğen"
                                            active={message.feedback === 'like'}
                                        />
                                        <ActionButton
                                            icon={<ThumbsDown className="h-3.5 w-3.5" />}
                                            onClick={() => handleFeedback('dislike')}
                                            label="Beğenme"
                                            active={message.feedback === 'dislike'}
                                        />
                                        <ActionButton
                                            icon={<RefreshCw className="h-3.5 w-3.5" />}
                                            onClick={() => {/* TODO: regenerate */ }}
                                            label="Yeniden oluştur"
                                        />
                                    </>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Context Panel - Sources for assistant messages */}
                {!isUser && message.sources && message.sources.length > 0 && (
                    <ContextPanel
                        sources={message.sources.map(s => ({
                            title: s.title,
                            url: s.url,
                            snippet: s.snippet,
                            favicon: s.favicon
                        }))}
                        className="mt-2"
                    />
                )}

                {/* Footer: Timestamp & Reactions */}
                <div className={cn(
                    "flex items-center gap-2 px-1",
                    isUser ? "flex-row-reverse" : "flex-row"
                )}>
                    {/* Timestamp */}
                    <span className="text-xs text-(--color-text-muted)">
                        {formatTime(message.timestamp)}
                        {message.isEdited && (
                            <span className="ml-1 italic">(düzenlendi)</span>
                        )}
                    </span>

                    {/* Reactions */}
                    <MessageReactions
                        messageId={message.id}
                        reactions={message.reactions}
                        onReact={handleReact}
                    />
                </div>
            </div>
        </motion.div>
    )
}

// ═══════════════════════════════════════════════════════════════════════════
// ACTION BUTTON
// ═══════════════════════════════════════════════════════════════════════════

interface ActionButtonProps {
    icon: React.ReactNode
    onClick: () => void
    label: string
    active?: boolean
}

function ActionButton({ icon, onClick, label, active }: ActionButtonProps) {
    return (
        <button
            onClick={onClick}
            aria-label={label}
            title={label}
            className={cn(
                "p-2 rounded-md transition-all duration-200",
                active
                    ? "bg-(--color-primary-soft) text-(--color-primary)"
                    : "hover:bg-(--color-bg-surface-hover) text-(--color-text-muted)"
            )}
        >
            {icon}
        </button>
    )
}
