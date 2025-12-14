/**
 * ChatInput Component
 * 
 * Premium chat input with attachments, voice, commands, and slash command palette
 */

import { useState, useRef, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Paperclip, Mic, Send, Smile, X, Loader2, Slash, Image as ImageIcon } from 'lucide-react'
import { useChatStore } from '@/stores'
import { chatApi } from '@/api'
import { Button, Textarea } from '@/components/ui'
import { useIsMobile } from '@/hooks'
import { CommandPalette, MultiModalInput, useMultiModal } from '@/components/common'
import { QuickSettings } from './QuickSettings'
import { cn } from '@/lib/utils'
import type { Command, Message } from '@/types'

interface ChatInputProps {
    replyTo?: Message | null
    onClearReply?: () => void
}

export function ChatInput({ replyTo, onClearReply }: ChatInputProps) {
    const inputValue = useChatStore((state) => state.inputValue)
    const setInputValue = useChatStore((state) => state.setInputValue)
    const isStreaming = useChatStore((state) => state.isStreaming)
    const currentConversationId = useChatStore((state) => state.currentConversationId)
    const addMessage = useChatStore((state) => state.addMessage)
    const createConversation = useChatStore((state) => state.createConversation)
    const startStreaming = useChatStore((state) => state.startStreaming)
    const appendToStreaming = useChatStore((state) => state.appendToStreaming)
    const stopStreaming = useChatStore((state) => state.stopStreaming)
    const isMobile = useIsMobile()
    const [isFocused, setIsFocused] = useState(false)
    const [attachments, setAttachments] = useState<File[]>([])
    const [isSending, setIsSending] = useState(false)

    const [showCommands, setShowCommands] = useState(false)
    const textareaRef = useRef<HTMLTextAreaElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Multi-modal image support
    const multiModal = useMultiModal()

    const canSend = (inputValue.trim() || attachments.length > 0 || multiModal.hasImages) && !isSending && !isStreaming

    // Detect slash command
    const commandQuery = useMemo(() => {
        if (!inputValue.startsWith('/')) return null
        const query = inputValue.slice(1) // Remove leading /
        return query
    }, [inputValue])

    // Show palette when typing slash
    const shouldShowPalette = commandQuery !== null && isFocused

    const handleSend = useCallback(async () => {
        if (!canSend) return

        const message = inputValue.trim()
        if (!message) return

        setIsSending(true)
        setInputValue('')
        setShowCommands(false)

        // Clear reply after sending
        onClearReply?.()

        // Use existing conversation ID or null for new conversation
        let convId = currentConversationId

        console.log('[Chat] Sending message:', { message, convId, replyTo: replyTo?.id })

        try {
            // Add user message to UI immediately
            addMessage({
                role: 'user',
                content: message,
                replyToId: replyTo?.id,
            })

            // Add placeholder for assistant message
            const assistantMsgId = addMessage({
                role: 'assistant',
                content: '',
                isStreaming: true,
            })

            startStreaming(assistantMsgId)

            // Send to API - pass null for new conversation, backend will create one
            console.log('[Chat] Calling API...')
            const response = await chatApi.sendMessage({
                message,
                conversationId: convId, // null for new conversation
                stream: true,
            })

            console.log('[Chat] Response status:', response.status, response.headers.get('content-type'))

            // Get conversation ID from response header (backend creates it)
            const newConvId = response.headers.get('X-Conversation-ID')
            if (newConvId && !convId) {
                console.log('[Chat] Got new conversation ID:', newConvId)
                convId = newConvId
                // Set current conversation in store - keep existing messages!
                useChatStore.getState().setCurrentConversation(newConvId, true)
            }

            // Handle streaming response - backend returns plain text chunks
            const reader = response.body?.getReader()
            const decoder = new TextDecoder()
            let fullResponse = ''

            if (reader) {
                let hasContent = false
                while (true) {
                    const { done, value } = await reader.read()
                    if (done) break

                    // Decode chunk - backend sends plain text, not SSE
                    let chunk = decoder.decode(value, { stream: true })

                    // Filter out IMAGE_QUEUED marker - it's for parsing, not display
                    if (chunk.includes('[IMAGE_QUEUED:')) {
                        // Don't show this to user, just track for parsing
                        fullResponse += chunk
                        continue
                    }

                    // Append the chunk directly (backend sends plain text)
                    if (chunk) {
                        hasContent = true
                        fullResponse += chunk
                        appendToStreaming(chunk)
                    }
                }

                // Check if this is an image queued response
                // New format: [IMAGE_QUEUED:job_id:message_id]
                const imageMatch = fullResponse.match(/\[IMAGE_QUEUED:([^:]+):(\d+)\]/)
                const isImageRequest = imageMatch !== null || !hasContent

                if (isImageRequest) {
                    // Delete the streaming placeholder
                    useChatStore.getState().deleteMessage(assistantMsgId)

                    if (imageMatch) {
                        // Parse job_id and message_id from response
                        const [, jobId, messageId] = imageMatch
                        console.log('[Chat] Image request with IDs:', { jobId: jobId.slice(0, 8), messageId })

                        // Add message directly to state with correct IDs!
                        useChatStore.getState().addMessage({
                            id: messageId,  // Backend's real message ID
                            role: 'assistant',
                            content: '[IMAGE_PENDING] Görsel isteğiniz kuyruğa alındı...',
                            conversationId: convId || newConvId || '',
                            extra_metadata: {
                                job_id: jobId,
                                status: 'queued',
                                progress: 0,
                                queue_position: 1,
                            }
                        })
                        console.log('[Chat] Image message added to state:', messageId)
                    } else {
                        // Fallback: reload from DB if no IDs (shouldn't happen)
                        console.log('[Chat] Image request without IDs - reloading from DB')
                        const finalConvId = convId || newConvId
                        if (finalConvId) {
                            try {
                                const freshMessages = await chatApi.getMessages(finalConvId)
                                useChatStore.getState().setMessages(freshMessages)
                            } catch (e) {
                                console.error('[Chat] Failed to reload messages:', e)
                            }
                        }
                    }
                }
            } else {
                console.error('[Chat] No response body reader')
                appendToStreaming('⚠️ Yanıt alınamadı.')
            }
        } catch (error) {
            console.error('[Chat] Send error:', error)
            // Show error in chat with more details
            const errorMessage = error instanceof Error ? error.message : 'Bilinmeyen hata'
            appendToStreaming(`\n\n⚠️ Hata: ${errorMessage}`)
        } finally {
            setIsSending(false)
            stopStreaming()
        }
    }, [canSend, inputValue, currentConversationId, addMessage, createConversation, startStreaming, appendToStreaming, stopStreaming, setInputValue])

    const handleKeyDown = (e: React.KeyboardEvent) => {
        // Don't send if command palette is open - let it handle navigation
        if (shouldShowPalette && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
            return // Let palette handle
        }

        if (e.key === 'Enter' && !e.shiftKey) {
            if (!shouldShowPalette) {
                e.preventDefault()
                handleSend()
            }
        }

        if (e.key === 'Escape' && shouldShowPalette) {
            setInputValue('')
        }
    }

    const handleCommandSelect = useCallback((command: Command) => {
        // Command already executed its action
        setShowCommands(false)
        textareaRef.current?.focus()
    }, [])

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || [])
        setAttachments(prev => [...prev, ...files])
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }

    const removeAttachment = (index: number) => {
        setAttachments(prev => prev.filter((_, i) => i !== index))
    }

    return (
        <div className={cn(
            "sticky bottom-0 px-4 md:px-8 py-4",
            "bg-linear-to-t from-(--color-bg) via-(--color-bg)/95 to-transparent"
        )}>
            {/* Attachment Preview */}
            <AnimatePresence>
                {attachments.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-3 flex gap-2 flex-wrap max-w-(--chat-max-width) mx-auto"
                    >
                        {attachments.map((file, i) => (
                            <AttachmentPreview
                                key={`${file.name}-${i}`}
                                file={file}
                                onRemove={() => removeAttachment(i)}
                            />
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Input Container */}
            <div className="max-w-(--chat-max-width) mx-auto relative">
                {/* Command Palette */}
                <AnimatePresence>
                    {shouldShowPalette && (
                        <CommandPalette
                            query={commandQuery || ''}
                            onSelect={handleCommandSelect}
                            onClose={() => setInputValue('')}
                        />
                    )}
                </AnimatePresence>

                {/* Image Attachments (Multi-Modal) */}
                <input
                    ref={multiModal.fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={multiModal.handleFileChange}
                    className="hidden"
                />
                <MultiModalInput
                    images={multiModal.images}
                    onImagesChange={multiModal.setImages}
                    maxImages={4}
                />

                <div className={cn(
                    "relative flex items-end gap-3 p-3 rounded-2xl",
                    "bg-(--color-bg-surface) border transition-all duration-300",
                    isFocused
                        ? "border-(--color-primary)/50 shadow-lg shadow-(--color-primary)/10"
                        : "border-(--color-border)"
                )}>
                    {/* Left Actions */}
                    <div className="flex items-center gap-1">
                        {/* Slash command hint */}
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => {
                                setInputValue('/')
                                textareaRef.current?.focus()
                            }}
                            className="text-(--color-text-muted) hover:text-(--color-text)"
                            aria-label="Komutlar"
                        >
                            <Slash className="h-5 w-5" />
                        </Button>

                        {/* Attachment Button */}
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            className="hidden"
                            onChange={handleFileSelect}
                            accept=".pdf,.txt,.doc,.docx,.md"
                        />
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => fileInputRef.current?.click()}
                            className="text-(--color-text-muted) hover:text-(--color-text)"
                            aria-label="Dosya ekle"
                        >
                            <Paperclip className="h-5 w-5" />
                        </Button>

                        {/* Image Button (Multi-Modal) */}
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={multiModal.openFilePicker}
                            className={cn(
                                multiModal.hasImages
                                    ? "text-(--color-secondary) bg-(--color-secondary-soft)"
                                    : "text-(--color-text-muted) hover:text-(--color-text)"
                            )}
                            aria-label="Görsel ekle"
                        >
                            <ImageIcon className="h-5 w-5" />
                        </Button>

                        {/* Voice Input Button */}
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            className="text-(--color-text-muted) hover:text-(--color-text)"
                            aria-label="Sesle yaz"
                        >
                            <Mic className="h-5 w-5" />
                        </Button>
                    </div>

                    {/* Text Area */}
                    <div className="flex-1 relative">
                        <Textarea
                            ref={textareaRef}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onFocus={() => setIsFocused(true)}
                            onBlur={() => setIsFocused(false)}
                            onKeyDown={handleKeyDown}
                            placeholder={isMobile ? "Mesaj yazın..." : "Bir mesaj yazın veya / ile komut kullanın..."} rows={1}
                            maxHeight={200}
                            className={cn(
                                "w-full bg-transparent border-0 focus:ring-0 resize-none",
                                "text-(--color-text) text-left",
                                "placeholder-(--color-text-muted) placeholder:text-center placeholder:opacity-40",
                                "min-h-10 px-3 py-2",
                                "flex items-center"
                            )}
                        />
                    </div>

                    {/* Right Actions */}
                    <div className="flex items-center gap-1">
                        {/* Emoji */}
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            className="text-(--color-text-muted) hover:text-(--color-text)"
                            aria-label="Emoji ekle"
                        >
                            <Smile className="h-5 w-5" />
                        </Button>

                        {/* Send Button */}
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            disabled={!canSend}
                            onClick={handleSend}
                            className={cn(
                                "transition-all",
                                canSend
                                    ? "text-(--color-primary) hover:bg-(--color-primary-soft)"
                                    : "text-(--color-text-muted)"
                            )}
                            aria-label="Gönder"
                        >
                            {isSending || isStreaming ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <Send className="h-5 w-5" />
                            )}
                        </Button>
                    </div>
                </div>

                {/* Bottom Bar: Quick Settings + Info */}
                <div className="flex items-center justify-between mt-2 px-1">
                    {/* Quick Settings */}
                    <QuickSettings />

                    {/* Character count & shortcuts */}
                    <div className="flex items-center gap-3 text-xs text-(--color-text-muted)">
                        <span className={cn(
                            inputValue.length > 9000 ? "text-(--color-error)" :
                                inputValue.length > 8000 ? "text-(--color-warning)" : ""
                        )}>
                            {inputValue.length > 0 && `${inputValue.length.toLocaleString('tr-TR')} / 10.000`}
                        </span>
                        <span className="hidden md:inline">
                            Enter: Gönder • / : Komutlar
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

interface AttachmentPreviewProps {
    file: File
    onRemove: () => void
}

function AttachmentPreview({ file, onRemove }: AttachmentPreviewProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg",
                "bg-(--color-bg-surface) border border-(--color-border)"
            )}
        >
            <Paperclip className="h-4 w-4 text-(--color-text-muted)" />
            <span className="text-sm truncate max-w-37.5">{file.name}</span>
            <button
                onClick={onRemove}
                className="p-0.5 rounded hover:bg-(--color-error-soft) text-(--color-text-muted) hover:text-(--color-error) transition-colors"
            >
                <X className="h-3.5 w-3.5" />
            </button>
        </motion.div>
    )
}
