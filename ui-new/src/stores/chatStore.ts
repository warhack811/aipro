/**
 * Chat Store - Zustand
 * 
 * Sohbet, mesajlar ve konuşmalar için merkezi state
 */

import { create } from 'zustand'
import type { Message, Conversation } from '@/types'
import { generateId } from '@/lib/utils'

interface ChatState {
    // Current state
    currentConversationId: string | null
    messages: Message[]
    conversations: Conversation[]

    // Input state
    inputValue: string
    isTyping: boolean
    isStreaming: boolean
    streamingMessageId: string | null

    // UI state
    isSidebarOpen: boolean
    isLoadingHistory: boolean

    // Actions - Conversations
    setCurrentConversation: (id: string | null, keepMessages?: boolean) => void
    createConversation: () => string
    deleteConversation: (id: string) => void
    updateConversationTitle: (id: string, title: string) => void
    setConversations: (conversations: Conversation[]) => void

    // Actions - Messages
    // id, timestamp ve extra_metadata opsiyonel - backend'den gelirse kullan
    addMessage: (message: Omit<Message, 'id' | 'timestamp'> & Partial<Pick<Message, 'id' | 'timestamp' | 'extra_metadata'>>) => string
    updateMessage: (id: string, updates: Partial<Message>) => void
    deleteMessage: (id: string) => void
    setMessages: (messages: Message[]) => void
    clearMessages: () => void

    // Actions - Streaming
    startStreaming: (messageId: string) => void
    appendToStreaming: (content: string) => void
    stopStreaming: () => void

    // Actions - Input
    setInputValue: (value: string) => void
    setIsTyping: (isTyping: boolean) => void

    // Actions - UI
    toggleSidebar: () => void
    setSidebarOpen: (isOpen: boolean) => void
    setLoadingHistory: (isLoading: boolean) => void
}

export const useChatStore = create<ChatState>()((set, get) => ({
    // Initial state
    currentConversationId: null,
    messages: [],
    conversations: [],
    inputValue: '',
    isTyping: false,
    isStreaming: false,
    streamingMessageId: null,
    isSidebarOpen: true,
    isLoadingHistory: false,

    // Conversation actions
    setCurrentConversation: (id, keepMessages = false) => {
        if (keepMessages) {
            // Just update the ID, keep existing messages (for new conversations)
            set({ currentConversationId: id })
        } else {
            // Change conversation, clear messages (for switching conversations)
            set({ currentConversationId: id, messages: [] })
        }
    },

    createConversation: () => {
        // ID üretmiyoruz, null yapıyoruz (Backend ilk mesajda üretecek)
        // Böylece 500 hatası ve çöp kayıt oluşumu engellenir.

        set((state) => ({
            // Yeni sohbeti listeye eklemiyoruz, ilk mesaj atılınca eklenecek
            // conversations: [newConversation, ...state.conversations], 

            currentConversationId: null, // ÖNEMLİ: ID yok, backend bekleyecek
            messages: [],
            inputValue: '' // Varsa yazılanı da temizle
        }))

        // Geriye boş string dönüyoruz çünkü ID henüz yok
        return ''
    },

    deleteConversation: (id) => {
        set((state) => ({
            conversations: state.conversations.filter((c) => c.id !== id),
            currentConversationId: state.currentConversationId === id
                ? null
                : state.currentConversationId,
            messages: state.currentConversationId === id ? [] : state.messages
        }))
    },

    updateConversationTitle: (id, title) => {
        set((state) => ({
            conversations: state.conversations.map((c) =>
                c.id === id ? { ...c, title, updatedAt: new Date().toISOString() } : c
            )
        }))
    },

    setConversations: (conversations) => {
        set({ conversations })
    },

    // Message actions
    // id ve extra_metadata opsiyonel - backend'den gelirse kullan, gelmezse üret
    addMessage: (message) => {
        // Backend'den id geldiyse kullan, yoksa local üret
        const id = message.id || generateId('msg')
        const timestamp = message.timestamp || new Date().toISOString()

        const newMessage: Message = {
            ...message,
            id,
            timestamp,
            conversationId: message.conversationId || get().currentConversationId || '',
            extra_metadata: message.extra_metadata, // Backend'den gelen metadata
        }

        set((state) => ({
            messages: [...state.messages, newMessage]
        }))

        // Update conversation
        const convId = get().currentConversationId
        if (convId) {
            set((state) => ({
                conversations: state.conversations.map((c) =>
                    c.id === convId
                        ? {
                            ...c,
                            messageCount: c.messageCount + 1,
                            preview: message.content.slice(0, 100),
                            updatedAt: timestamp
                        }
                        : c
                )
            }))
        }

        return id
    },

    updateMessage: (id, updates) => {
        set((state) => ({
            messages: state.messages.map((m) =>
                m.id === id
                    ? {
                        ...m,
                        ...updates,
                        // Deep merge extra_metadata to preserve existing fields
                        extra_metadata: updates.extra_metadata
                            ? { ...m.extra_metadata, ...updates.extra_metadata }
                            : m.extra_metadata
                    }
                    : m
            )
        }))
    },

    deleteMessage: (id) => {
        set((state) => ({
            messages: state.messages.filter((m) => m.id !== id)
        }))
    },

    setMessages: (messages) => {
        set({ messages })
    },

    clearMessages: () => {
        set({ messages: [] })
    },

    // Streaming actions
    startStreaming: (messageId) => {
        set({ isStreaming: true, streamingMessageId: messageId })
    },

    appendToStreaming: (content) => {
        const { streamingMessageId } = get()
        if (!streamingMessageId) return

        set((state) => ({
            messages: state.messages.map((m) =>
                m.id === streamingMessageId
                    ? { ...m, content: m.content + content }
                    : m
            )
        }))
    },

    stopStreaming: () => {
        const { streamingMessageId } = get()
        if (streamingMessageId) {
            set((state) => ({
                messages: state.messages.map((m) =>
                    m.id === streamingMessageId
                        ? { ...m, isStreaming: false }
                        : m
                ),
                isStreaming: false,
                streamingMessageId: null
            }))
        }
    },

    // Input actions
    setInputValue: (value) => {
        set({ inputValue: value })
    },

    setIsTyping: (isTyping) => {
        set({ isTyping })
    },

    // UI actions
    toggleSidebar: () => {
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen }))
    },

    setSidebarOpen: (isOpen) => {
        set({ isSidebarOpen: isOpen })
    },

    setLoadingHistory: (isLoading) => {
        set({ isLoadingHistory: isLoading })
    }
}))
