/**
 * Hooks Barrel Export
 */

// Responsive
export {
    useMediaQuery,
    useIsMobile,
    useIsTablet,
    useIsDesktop,
    useBreakpoint,
    useIsTouchDevice,
    usePullToRefresh,
    useScrollDirection,
    useScrollAtBottom,
    useIsKeyboardOpen,
    useSafeAreaInsets,
    useOrientation,
    type Breakpoint,
    type Orientation
} from './useResponsive'

// WebSocket
export { useWebSocket } from './useWebSocket'

// Image Progress (new simple approach)
export {
    useImageProgress,
    useHasActiveJobs,
    useActiveJobCount,
    updateProgressFromWebSocket,
    getProgressForJob,
    type ImageProgressData
} from './useImageProgress'

// Image Jobs (legacy)
export { useImageJobs } from './useImageJobs'

// Conversations
export { useConversations } from './useConversations'

// Mobile Gestures
export {
    useSwipe,
    useLongPress,
    useEnhancedPullToRefresh,
    useDismissGesture
} from './useMobileGestures'

// Preferences
export { usePreferences } from './usePreferences'

// Mobile Keyboard
export { useMobileKeyboard, scrollInputIntoView } from './useMobileKeyboard'
