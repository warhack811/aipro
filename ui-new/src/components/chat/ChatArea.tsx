/**
 * ChatArea Component
 * 
 * Main chat container with messages, typing indicator, reply support, scroll features,
 * and image generation progress tracking.
 */

import { useRef, useEffect, useState, useCallback } from 'react'
import { useChatStore } from '@/stores'
import { useActiveJobCount } from '@/hooks/useImageProgress'
import { chatApi } from '@/api'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { WelcomeScreen } from './WelcomeScreen'
import { ScrollToBottomButton } from './ScrollToBottomButton'
import { ReplyPreview } from './ReplyPreview'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Message } from '@/types'

export function ChatArea() {
    const messages = useChatStore((state) => state.messages)
    const setMessages = useChatStore((state) => state.setMessages)
    const currentConversationId = useChatStore((state) => state.currentConversationId)
    const isStreaming = useChatStore((state) => state.isStreaming)
    const isLoadingHistory = useChatStore((state) => state.isLoadingHistory)
    const scrollRef = useRef<HTMLDivElement>(null)

    // Reply state
    const [replyingTo, setReplyingTo] = useState<Message | null>(null)

    // Track if user has scrolled up
    const [isAtBottom, setIsAtBottom] = useState(true)
    const [showScrollButton, setShowScrollButton] = useState(false)

    // Image job tracking for floating badge - use new hook
    const activeJobCount = useActiveJobCount()

    // ─────────────────────────────────────────────────────────────────────────
    // Reload messages when image completes (backend updated the message)
    // ─────────────────────────────────────────────────────────────────────────
    useEffect(() => {
        const handleImageComplete = async (event: Event) => {
            const customEvent = event as CustomEvent<{ conversationId?: string }>
            const { conversationId } = customEvent.detail || {}

            // Only reload if it's for the current conversation
            if (conversationId && conversationId === currentConversationId) {
                console.log('[ChatArea] Reloading messages after image complete')
                try {
                    const freshMessages = await chatApi.getMessages(conversationId)
                    setMessages(freshMessages)
                } catch (error) {
                    console.error('[ChatArea] Failed to reload messages:', error)
                }
            }
        }

        window.addEventListener('image-complete', handleImageComplete)
        return () => {
            window.removeEventListener('image-complete', handleImageComplete)
        }
    }, [currentConversationId, setMessages])

    // ─────────────────────────────────────────────────────────────────────────
    // Handlers
    // ─────────────────────────────────────────────────────────────────────────

    const handleReply = useCallback((message: Message) => {
        setReplyingTo(message)
    }, [])

    const clearReply = useCallback(() => {
        setReplyingTo(null)
    }, [])

    // Check scroll position
    const handleScroll = useCallback(() => {
        if (!scrollRef.current) return

        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
        const distanceFromBottom = scrollHeight - scrollTop - clientHeight
        const atBottom = distanceFromBottom < 100

        setIsAtBottom(atBottom)
        setShowScrollButton(!atBottom && messages.length > 3)
    }, [messages.length])

    // Scroll to bottom function
    const scrollToBottom = useCallback((smooth = true) => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: smooth ? 'smooth' : 'auto'
            })
        }
    }, [])

    // Auto-scroll on new messages (only if at bottom)
    useEffect(() => {
        if (isAtBottom) {
            scrollToBottom(false)
        }
    }, [messages, isStreaming, isAtBottom, scrollToBottom])

    // Initial scroll
    useEffect(() => {
        scrollToBottom(false)
    }, [scrollToBottom])

    // Force scroll to bottom when conversation changes
    useEffect(() => {
        if (currentConversationId) {
            // Reset scroll state to true whenever we switch conversations.
            // This ensures that when new messages load, the auto-scroll effect will trigger.
            setIsAtBottom(true)

            // If we happen to have messages already (e.g. valid cache), scroll immediately
            if (messages.length > 0) {
                scrollToBottom(false)
            }
        }
    }, [currentConversationId, scrollToBottom])

    // Show welcome only when no conversation selected AND no messages
    const showWelcome = !currentConversationId && messages.length === 0
    // Show loading when loading history
    const showLoading = isLoadingHistory && messages.length === 0

    return (
        <div className="flex-1 flex flex-col overflow-hidden relative">
            {/* Messages Container */}
            <div
                ref={scrollRef}
                onScroll={handleScroll}
                className={cn(
                    "flex-1 overflow-y-auto",
                    "scrollbar-thin"
                )}
            >
                <div className="max-w-(--chat-max-width) mx-auto w-full">
                    {showWelcome ? (
                        <WelcomeScreen />
                    ) : showLoading ? (
                        <div className="flex items-center justify-center h-full py-20">
                            <div className="text-center">
                                <Loader2 className="h-8 w-8 animate-spin text-(--color-primary) mx-auto mb-3" />
                                <p className="text-sm text-(--color-text-muted)">Mesajlar yükleniyor...</p>
                            </div>
                        </div>
                    ) : (
                        <MessageList
                            messages={messages}
                            onReply={handleReply}
                        />
                    )}
                </div>
            </div>

            {/* Scroll to Bottom Button */}
            <ScrollToBottomButton
                visible={showScrollButton}
                onClick={() => scrollToBottom(true)}
            />

            {/* Floating Image Badge - Shows active image jobs count */}
            {
                activeJobCount > 0 && (
                    <div className="fixed bottom-24 right-6 z-40">
                        <div className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-(--color-primary) text-white shadow-lg">
                            <span className="text-sm font-medium">{activeJobCount} görsel üretiliyor</span>
                        </div>
                    </div>
                )
            }

            {/* Reply Preview Above Input */}
            {
                replyingTo && (
                    <div className="px-4 md:px-8 max-w-(--chat-max-width) mx-auto w-full">
                        <ReplyPreview
                            replyTo={replyingTo}
                            onRemove={clearReply}
                            isInline={false}
                        />
                    </div>
                )
            }

            {/* Input Area */}
            <ChatInput replyTo={replyingTo} onClearReply={clearReply} />
        </div >
    )
}
