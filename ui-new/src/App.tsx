/**
 * Main App Component
 * 
 * Root component with providers and layout
 * Note: Auth is handled by backend - /new-ui redirects if not logged in
 */

import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { initializeTheme, useSettingsStore } from '@/stores'
import {
  ToastProvider,
  ErrorBoundary,
  FullPageLoader,
  BottomNav,
  SettingsSheet
} from '@/components/common'
import { ChatLayout } from '@/components/layout/ChatLayout'
import { useIsMobile, useWebSocket, usePreferences, useMobileKeyboard } from '@/hooks'
import { cn } from '@/lib/utils'
import { Suspense } from 'react'

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

function AppContent() {
  // Initialize theme on mount
  useEffect(() => {
    initializeTheme()
  }, [])

  // WebSocket connection
  useWebSocket()

  // Load preferences from backend (syncs store with backend on mount)
  usePreferences()

  // Mobile keyboard support - tracks keyboard height for CSS variable
  useMobileKeyboard()

  // Mobile detection
  const isMobile = useIsMobile()

  // Settings
  const openSettings = useSettingsStore((state) => state.openSettings)

  return (
    <Suspense fallback={<FullPageLoader />}>
      <div className="h-screen w-screen overflow-hidden bg-(--color-bg)">
        {/* Main Layout - modals are inside ChatLayout now */}
        <div className={cn("h-full", isMobile && "pb-16")}>
          <ChatLayout />
        </div>

        {/* Mobile Bottom Navigation */}
        {isMobile && (
          <BottomNav
            onNewChat={() => { }}
            onMemory={() => document.dispatchEvent(new CustomEvent('open-memory-manager'))}
            onGallery={() => document.dispatchEvent(new CustomEvent('open-gallery'))}
            onSettings={() => openSettings()}
          />
        )}

        {/* Global Settings Sheet */}
        <SettingsSheet />
      </div>
    </Suspense>
  )
}

export default App
