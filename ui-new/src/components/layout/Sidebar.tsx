/**
 * Sidebar Component
 * 
 * Navigation sidebar with conversations list
 * Responsive: drawer on mobile, fixed on desktop
 */

import { motion } from 'framer-motion'
import { Plus, MessageSquare, Settings, LogOut, Brain, Image, Trash2, Loader2, Shield, Search, Download } from 'lucide-react'
import { useChatStore, useBranding, useSettingsStore } from '@/stores'
import { useUserStore } from '@/stores/userStore'
import { useConversations } from '@/hooks'
import { Button } from '@/components/ui'
import { cn, truncate } from '@/lib/utils'
import type { Conversation } from '@/types'

interface SidebarProps {
    onItemSelect?: () => void
    onMemoryOpen?: () => void
    onGalleryOpen?: () => void
    onSettingsOpen?: () => void
    onSearchOpen?: () => void
    onExportOpen?: () => void
    onLogout?: () => void
}

export function Sidebar({
    onItemSelect,
    onMemoryOpen,
    onGalleryOpen,
    onSettingsOpen,
    onSearchOpen,
    onExportOpen,
    onLogout
}: SidebarProps) {
    const branding = useBranding()

    // Load conversations from API
    const { isLoading: isLoadingConversations } = useConversations()

    const conversations = useChatStore((state) => state.conversations)
    const currentConversationId = useChatStore((state) => state.currentConversationId)
    const createConversation = useChatStore((state) => state.createConversation)
    const setCurrentConversation = useChatStore((state) => state.setCurrentConversation)
    const deleteConversation = useChatStore((state) => state.deleteConversation)

    // Settings store
    const openSettings = useSettingsStore((state) => state.openSettings)

    // User info for admin check
    const user = useUserStore((state) => state.user)
    const isAdmin = user?.role === 'admin'

    // Group conversations by date
    const groupedConversations = groupConversationsByDate(conversations)

    const handleNewChat = () => {
        createConversation()
        // Mobilde menüyü kapatmak istersek: onMobileMenuClose() gibi bir sey lazim
        // Simdilik sadece state'i resetliyoruz, bu yeterli.
        if (window.innerWidth < 768) {
            onItemSelect?.() // Mobildeysek menüyü kapat
        }
    }

    const handleSelectConversation = async (id: string) => {
        const store = useChatStore.getState()

        // Set loading state and conversation ID 
        store.setLoadingHistory(true)
        setCurrentConversation(id)
        onItemSelect?.()

        // Then load messages from API
        try {
            const { chatApi } = await import('@/api')
            const messages = await chatApi.getMessages(id)

            // Update messages in store first
            store.setMessages(messages)

            // Refresh pending job statuses in background
            const pendingMessages = messages.filter(m =>
                m.extra_metadata?.job_id &&
                ['queued', 'processing'].includes(m.extra_metadata?.status || '')
            )

            // Update each pending job's status from backend
            for (const msg of pendingMessages) {
                try {
                    const jobStatus = await chatApi.getJobStatus(msg.extra_metadata!.job_id!)
                    if (jobStatus.status !== 'unknown') {
                        store.updateMessage(msg.id, {
                            extra_metadata: {
                                ...msg.extra_metadata,
                                status: jobStatus.status as 'queued' | 'processing',
                                progress: jobStatus.progress,
                                queue_position: jobStatus.queue_position,
                            }
                        })
                        console.log('[Sidebar] Refreshed job status:', msg.id, jobStatus.status, jobStatus.progress + '%')
                    }
                } catch (err) {
                    console.debug('[Sidebar] Failed to refresh job status:', msg.extra_metadata?.job_id)
                }
            }
        } catch (error) {
            console.error('[Sidebar] Failed to load messages:', error)
            // Clear messages on error to show empty state
            store.setMessages([])
        } finally {
            store.setLoadingHistory(false)
        }
    }

    const handleDeleteConversation = async (id: string) => {
        try {
            // First delete from backend
            const { chatApi } = await import('@/api')
            await chatApi.deleteConversation(id)

            // Then update local state
            deleteConversation(id)

            console.log('[Sidebar] Conversation deleted:', id)
        } catch (error) {
            console.error('[Sidebar] Failed to delete conversation:', error)
            // Still remove from UI even if API call fails
            deleteConversation(id)
        }
    }

    const handleLogout = () => {
        if (onLogout) {
            onLogout()
        } else {
            // Default logout - redirect to old UI login
            window.location.href = '/ui/login.html'
        }
    }

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-(--color-border)">
                {/* Logo & Brand */}
                <div className="flex items-center gap-3 mb-4">
                    <motion.div
                        className="w-10 h-10 rounded-xl bg-(--gradient-brand) flex items-center justify-center shadow-lg"
                        animate={{
                            boxShadow: [
                                '0 0 15px rgba(124, 58, 237, 0.3)',
                                '0 0 25px rgba(236, 72, 153, 0.4)',
                                '0 0 15px rgba(124, 58, 237, 0.3)'
                            ]
                        }}
                        transition={{ duration: 3, repeat: Infinity }}
                    >
                        <span className="text-xl">✨</span>
                    </motion.div>
                    <div>
                        <h1 className="font-display font-bold text-lg">{branding.displayName}</h1>
                        <p className="text-xs text-(--color-text-muted)">{branding.shortIntro}</p>
                    </div>
                </div>

                {/* New Chat Button */}
                <Button
                    variant="primary"
                    size="lg"
                    className="w-full"
                    onClick={handleNewChat}
                    leftIcon={<Plus className="h-5 w-5" />}
                >
                    Yeni Sohbet
                </Button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto py-2 scrollbar-thin">
                {isLoadingConversations ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-6 w-6 animate-spin text-(--color-text-muted)" />
                    </div>
                ) : groupedConversations.length > 0 ? (
                    groupedConversations.map((group) => (
                        <div key={group.label} className="mb-4">
                            <div className="px-4 py-2 text-xs font-medium text-(--color-text-muted) uppercase tracking-wider">
                                {group.label}
                            </div>
                            <div className="space-y-1 px-2">
                                {group.conversations.map((conv) => (
                                    <ConversationItem
                                        key={conv.id}
                                        conversation={conv}
                                        isActive={conv.id === currentConversationId}
                                        onClick={() => handleSelectConversation(conv.id)}
                                        onDelete={() => handleDeleteConversation(conv.id)}
                                    />
                                ))}
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-12 px-4">
                        <MessageSquare className="h-12 w-12 mx-auto mb-3 text-(--color-text-muted) opacity-50" />
                        <p className="text-sm text-(--color-text-muted)">
                            Henüz sohbet yok
                        </p>
                        <p className="text-xs text-(--color-text-muted) mt-1">
                            Yeni sohbet başlatın
                        </p>
                    </div>
                )}
            </div>

            {/* Bottom Navigation */}
            <div className="border-t border-(--color-border) p-2 space-y-1">
                <NavButton
                    icon={<Search className="h-4 w-4" />}
                    label="Ara"
                    onClick={() => { onSearchOpen?.(); }}
                />
                <NavButton
                    icon={<Brain className="h-4 w-4" />}
                    label="Hafıza"
                    onClick={() => { onMemoryOpen?.(); onItemSelect?.(); }}
                />
                <NavButton
                    icon={<Image className="h-4 w-4" />}
                    label="Galeri"
                    onClick={() => { onGalleryOpen?.(); onItemSelect?.(); }}
                />
                <NavButton
                    icon={<Download className="h-4 w-4" />}
                    label="Dışa/İçe Aktar"
                    onClick={() => { onExportOpen?.(); }}
                />
                <NavButton
                    icon={<Settings className="h-4 w-4" />}
                    label="Ayarlar"
                    onClick={() => { openSettings(); onItemSelect?.(); }}
                />
                {isAdmin && (
                    <NavButton
                        icon={<Shield className="h-4 w-4" />}
                        label="Admin Paneli"
                        variant="accent"
                        onClick={() => { window.location.href = '/admin.html'; }}
                    />
                )}
                <NavButton
                    icon={<LogOut className="h-4 w-4" />}
                    label="Çıkış"
                    variant="danger"
                    onClick={handleLogout}
                />
            </div>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

interface ConversationItemProps {
    conversation: Conversation
    isActive: boolean
    onClick: () => void
    onDelete: () => void
}

function ConversationItem({ conversation, isActive, onClick, onDelete }: ConversationItemProps) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="group relative"
        >
            <button
                onClick={onClick}
                className={cn(
                    "w-full text-left px-3 py-2.5 rounded-xl transition-all duration-200",
                    "flex items-center gap-3",
                    isActive
                        ? "bg-(--color-primary-soft) text-(--color-primary)"
                        : "hover:bg-(--color-bg-surface-hover) active:scale-[0.98]"
                )}
            >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{conversation.title}</p>
                    {conversation.preview && (
                        <p className="text-xs text-(--color-text-muted) truncate mt-0.5">
                            {truncate(conversation.preview, 50)}
                        </p>
                    )}
                </div>
            </button>

            {/* Delete button - visible on hover */}
            <button
                onClick={(e) => {
                    e.stopPropagation()
                    onDelete()
                }}
                className={cn(
                    "absolute right-2 top-1/2 -translate-y-1/2",
                    "p-1.5 rounded-lg",
                    "opacity-0 group-hover:opacity-100",
                    "hover:bg-(--color-error-soft) text-(--color-error)",
                    "transition-all duration-200"
                )}
            >
                <Trash2 className="h-3.5 w-3.5" />
            </button>
        </motion.div>
    )
}

interface NavButtonProps {
    icon: React.ReactNode
    label: string
    onClick?: () => void
    variant?: 'default' | 'danger' | 'accent'
}

function NavButton({ icon, label, onClick, variant = 'default' }: NavButtonProps) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl",
                "text-sm transition-all duration-200 active:scale-[0.98]",
                variant === 'danger'
                    ? "text-(--color-error) hover:bg-(--color-error-soft)"
                    : variant === 'accent'
                        ? "text-(--color-primary) hover:bg-(--color-primary-soft)"
                        : "text-(--color-text-secondary) hover:bg-(--color-bg-surface-hover) hover:text-(--color-text)"
            )}
        >
            {icon}
            <span>{label}</span>
        </button>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function groupConversationsByDate(conversations: Conversation[]) {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)

    const groups: { label: string; conversations: Conversation[] }[] = [
        { label: 'Bugün', conversations: [] },
        { label: 'Dün', conversations: [] },
        { label: 'Bu Hafta', conversations: [] },
        { label: 'Daha Eski', conversations: [] },
    ]

    conversations.forEach((conv) => {
        const date = new Date(conv.updatedAt)
        if (date >= today) {
            groups[0].conversations.push(conv)
        } else if (date >= yesterday) {
            groups[1].conversations.push(conv)
        } else if (date >= lastWeek) {
            groups[2].conversations.push(conv)
        } else {
            groups[3].conversations.push(conv)
        }
    })

    // Filter out empty groups
    return groups.filter((g) => g.conversations.length > 0)
}
