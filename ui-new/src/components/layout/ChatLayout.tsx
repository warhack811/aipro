/**
 * ChatLayout Component
 * 
 * Main layout with responsive sidebar (desktop) and drawer (mobile)
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore, useBranding } from '@/stores'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { ChatArea } from '@/components/chat/ChatArea'
import {
    MobileDrawer,
    ThemePicker,
    MemoryManager,
    ImageGallery,
    ConversationSearch,
    ExportImport
} from '@/components/common'
import { useIsMobile } from '@/hooks'
import { cn } from '@/lib/utils'

export function ChatLayout() {
    const isSidebarOpen = useChatStore((state) => state.isSidebarOpen)
    const branding = useBranding()
    const isMobile = useIsMobile()

    // Mobile drawer state
    const [isDrawerOpen, setDrawerOpen] = useState(false)

    // Modal states - managed here to be accessible from Sidebar
    const [isThemePickerOpen, setThemePickerOpen] = useState(false)
    const [isMemoryManagerOpen, setMemoryManagerOpen] = useState(false)
    const [isGalleryOpen, setGalleryOpen] = useState(false)
    const [isSearchOpen, setSearchOpen] = useState(false)
    const [isExportOpen, setExportOpen] = useState(false)

    const handleMenuToggle = () => {
        if (isMobile) {
            setDrawerOpen(!isDrawerOpen)
        } else {
            useChatStore.getState().toggleSidebar()
        }
    }

    // Sidebar navigation handlers
    const handleMemoryOpen = () => setMemoryManagerOpen(true)
    const handleGalleryOpen = () => setGalleryOpen(true)
    const handleSettingsOpen = () => setThemePickerOpen(true)
    const handleSearchOpen = () => setSearchOpen(true)
    const handleExportOpen = () => setExportOpen(true)

    // Search navigation handler
    const handleSearchNavigate = (conversationId: string, messageId?: string) => {
        // Set conversation and close search
        useChatStore.getState().setCurrentConversation(conversationId)
        // TODO: Scroll to message if messageId provided
    }

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ctrl+K or Cmd+K to open search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault()
                setSearchOpen(true)
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [])

    // Listen for custom events from BottomNav/CommandPalette
    useEffect(() => {
        const handleOpenMemory = () => setMemoryManagerOpen(true)
        const handleOpenGallery = () => setGalleryOpen(true)
        const handleOpenTheme = () => setThemePickerOpen(true)

        document.addEventListener('open-memory-manager', handleOpenMemory)
        document.addEventListener('open-gallery', handleOpenGallery)
        document.addEventListener('open-theme-picker', handleOpenTheme)

        return () => {
            document.removeEventListener('open-memory-manager', handleOpenMemory)
            document.removeEventListener('open-gallery', handleOpenGallery)
            document.removeEventListener('open-theme-picker', handleOpenTheme)
        }
    }, [])

    return (
        <div className="flex h-full w-full">
            {/* Desktop Sidebar */}
            {!isMobile && (
                <AnimatePresence mode="wait">
                    {isSidebarOpen && (
                        <motion.aside
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 280, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                            className="h-full border-r border-(--color-border) bg-(--color-bg-surface) overflow-hidden flex-shrink-0"
                        >
                            <Sidebar
                                onMemoryOpen={handleMemoryOpen}
                                onGalleryOpen={handleGalleryOpen}
                                onSettingsOpen={handleSettingsOpen}
                                onSearchOpen={handleSearchOpen}
                                onExportOpen={handleExportOpen}
                            />
                        </motion.aside>
                    )}
                </AnimatePresence>
            )}

            {/* Mobile Drawer */}
            {isMobile && (
                <MobileDrawer
                    isOpen={isDrawerOpen}
                    onClose={() => setDrawerOpen(false)}
                    side="left"
                >
                    <Sidebar
                        onItemSelect={() => setDrawerOpen(false)}
                        onMemoryOpen={handleMemoryOpen}
                        onGalleryOpen={handleGalleryOpen}
                        onSettingsOpen={handleSettingsOpen}
                        onSearchOpen={handleSearchOpen}
                        onExportOpen={handleExportOpen}
                    />
                </MobileDrawer>
            )}

            {/* Main Content */}
            <main className={cn(
                "flex-1 flex flex-col h-full overflow-hidden",
                "transition-all duration-200"
            )}>
                {/* Header */}
                <Header
                    title={branding.displayName}
                    onMenuClick={handleMenuToggle}
                    onSearchClick={handleSearchOpen}
                />

                {/* Chat Area */}
                <ChatArea />
            </main>

            {/* Modals - Rendered in ChatLayout for Sidebar access */}
            <ThemePicker
                isOpen={isThemePickerOpen}
                onClose={() => setThemePickerOpen(false)}
            />
            <MemoryManager
                isOpen={isMemoryManagerOpen}
                onClose={() => setMemoryManagerOpen(false)}
            />
            <ImageGallery
                isOpen={isGalleryOpen}
                onClose={() => setGalleryOpen(false)}
            />
            <ConversationSearch
                isOpen={isSearchOpen}
                onClose={() => setSearchOpen(false)}
                onNavigate={handleSearchNavigate}
            />
            <ExportImport
                isOpen={isExportOpen}
                onClose={() => setExportOpen(false)}
            />
        </div>
    )
}
