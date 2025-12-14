/**
 * Responsive Hooks
 * 
 * Premium hooks for responsive design and media queries
 */

import { useState, useEffect, useCallback } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// MEDIA QUERY HOOK
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Hook to detect media query matches
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(false)

    useEffect(() => {
        if (typeof window === 'undefined') return

        const mediaQuery = window.matchMedia(query)
        setMatches(mediaQuery.matches)

        const handler = (e: MediaQueryListEvent) => setMatches(e.matches)
        mediaQuery.addEventListener('change', handler)

        return () => mediaQuery.removeEventListener('change', handler)
    }, [query])

    return matches
}

// ─────────────────────────────────────────────────────────────────────────────
// BREAKPOINT HOOKS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Tailwind breakpoint sizes
 */
const breakpoints = {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    '2xl': 1536,
} as const

export type Breakpoint = keyof typeof breakpoints

/**
 * Check if viewport is mobile (<768px)
 */
export function useIsMobile(): boolean {
    return useMediaQuery(`(max-width: ${breakpoints.md - 1}px)`)
}

/**
 * Check if viewport is tablet (768px - 1024px)
 */
export function useIsTablet(): boolean {
    return useMediaQuery(`(min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`)
}

/**
 * Check if viewport is desktop (>=1024px)
 */
export function useIsDesktop(): boolean {
    return useMediaQuery(`(min-width: ${breakpoints.lg}px)`)
}

/**
 * Get current breakpoint name
 */
export function useBreakpoint(): Breakpoint {
    const isSm = useMediaQuery(`(min-width: ${breakpoints.sm}px)`)
    const isMd = useMediaQuery(`(min-width: ${breakpoints.md}px)`)
    const isLg = useMediaQuery(`(min-width: ${breakpoints.lg}px)`)
    const isXl = useMediaQuery(`(min-width: ${breakpoints.xl}px)`)
    const is2xl = useMediaQuery(`(min-width: ${breakpoints['2xl']}px)`)

    if (is2xl) return '2xl'
    if (isXl) return 'xl'
    if (isLg) return 'lg'
    if (isMd) return 'md'
    if (isSm) return 'sm'
    return 'sm'
}

// ─────────────────────────────────────────────────────────────────────────────
// TOUCH & GESTURE HOOKS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Detect if device supports touch
 */
export function useIsTouchDevice(): boolean {
    const [isTouch, setIsTouch] = useState(false)

    useEffect(() => {
        setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0)
    }, [])

    return isTouch
}

/**
 * Hook for pull-to-refresh gesture
 */
export function usePullToRefresh(onRefresh: () => Promise<void>) {
    const [isPulling, setIsPulling] = useState(false)
    const [pullProgress, setPullProgress] = useState(0)
    const [isRefreshing, setIsRefreshing] = useState(false)

    const handleTouchStart = useCallback((e: TouchEvent) => {
        if (window.scrollY === 0) {
            setIsPulling(true)
        }
    }, [])

    const handleTouchMove = useCallback((e: TouchEvent) => {
        if (!isPulling) return

        const touch = e.touches[0]
        const progress = Math.min(touch.clientY / 150, 1)
        setPullProgress(progress)
    }, [isPulling])

    const handleTouchEnd = useCallback(async () => {
        if (pullProgress >= 1 && !isRefreshing) {
            setIsRefreshing(true)
            await onRefresh()
            setIsRefreshing(false)
        }
        setIsPulling(false)
        setPullProgress(0)
    }, [pullProgress, isRefreshing, onRefresh])

    useEffect(() => {
        document.addEventListener('touchstart', handleTouchStart, { passive: true })
        document.addEventListener('touchmove', handleTouchMove, { passive: true })
        document.addEventListener('touchend', handleTouchEnd)

        return () => {
            document.removeEventListener('touchstart', handleTouchStart)
            document.removeEventListener('touchmove', handleTouchMove)
            document.removeEventListener('touchend', handleTouchEnd)
        }
    }, [handleTouchStart, handleTouchMove, handleTouchEnd])

    return { isPulling, pullProgress, isRefreshing }
}

// ─────────────────────────────────────────────────────────────────────────────
// SCROLL HOOKS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Hook to detect scroll direction
 */
export function useScrollDirection(): 'up' | 'down' | null {
    const [scrollDirection, setScrollDirection] = useState<'up' | 'down' | null>(null)
    const [lastScrollY, setLastScrollY] = useState(0)

    useEffect(() => {
        const updateScrollDirection = () => {
            const scrollY = window.scrollY
            const threshold = 10

            if (Math.abs(scrollY - lastScrollY) < threshold) return

            setScrollDirection(scrollY > lastScrollY ? 'down' : 'up')
            setLastScrollY(scrollY)
        }

        window.addEventListener('scroll', updateScrollDirection, { passive: true })
        return () => window.removeEventListener('scroll', updateScrollDirection)
    }, [lastScrollY])

    return scrollDirection
}

/**
 * Hook to check if scroll is at bottom
 */
export function useScrollAtBottom(threshold = 100): boolean {
    const [isAtBottom, setIsAtBottom] = useState(true)

    useEffect(() => {
        const checkScroll = () => {
            const scrollTop = document.documentElement.scrollTop
            const scrollHeight = document.documentElement.scrollHeight
            const clientHeight = document.documentElement.clientHeight

            setIsAtBottom(scrollHeight - scrollTop - clientHeight < threshold)
        }

        window.addEventListener('scroll', checkScroll, { passive: true })
        checkScroll()

        return () => window.removeEventListener('scroll', checkScroll)
    }, [threshold])

    return isAtBottom
}

// ─────────────────────────────────────────────────────────────────────────────
// KEYBOARD HOOKS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Detect if virtual keyboard is open (mobile)
 */
export function useIsKeyboardOpen(): boolean {
    const [isOpen, setIsOpen] = useState(false)

    useEffect(() => {
        if (typeof window === 'undefined') return

        const initialHeight = window.innerHeight

        const checkKeyboard = () => {
            // If viewport height is significantly smaller, keyboard is likely open
            const currentHeight = window.innerHeight
            setIsOpen(currentHeight < initialHeight * 0.75)
        }

        window.addEventListener('resize', checkKeyboard)
        return () => window.removeEventListener('resize', checkKeyboard)
    }, [])

    return isOpen
}

// ─────────────────────────────────────────────────────────────────────────────
// SAFE AREA HOOKS
// ─────────────────────────────────────────────────────────────────────────────

interface SafeAreaInsets {
    top: number
    right: number
    bottom: number
    left: number
}

/**
 * Get safe area insets (for notched devices)
 */
export function useSafeAreaInsets(): SafeAreaInsets {
    const [insets, setInsets] = useState<SafeAreaInsets>({
        top: 0,
        right: 0,
        bottom: 0,
        left: 0
    })

    useEffect(() => {
        const computeInsets = () => {
            const style = getComputedStyle(document.documentElement)
            setInsets({
                top: parseInt(style.getPropertyValue('--sat') || '0', 10) ||
                    parseInt(style.getPropertyValue('env(safe-area-inset-top)') || '0', 10),
                right: parseInt(style.getPropertyValue('--sar') || '0', 10) ||
                    parseInt(style.getPropertyValue('env(safe-area-inset-right)') || '0', 10),
                bottom: parseInt(style.getPropertyValue('--sab') || '0', 10) ||
                    parseInt(style.getPropertyValue('env(safe-area-inset-bottom)') || '0', 10),
                left: parseInt(style.getPropertyValue('--sal') || '0', 10) ||
                    parseInt(style.getPropertyValue('env(safe-area-inset-left)') || '0', 10)
            })
        }

        computeInsets()
        window.addEventListener('resize', computeInsets)
        return () => window.removeEventListener('resize', computeInsets)
    }, [])

    return insets
}

// ─────────────────────────────────────────────────────────────────────────────
// ORIENTATION HOOK
// ─────────────────────────────────────────────────────────────────────────────

export type Orientation = 'portrait' | 'landscape'

export function useOrientation(): Orientation {
    const isPortrait = useMediaQuery('(orientation: portrait)')
    return isPortrait ? 'portrait' : 'landscape'
}
