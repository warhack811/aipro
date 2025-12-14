/**
 * useMobileGestures Hook
 * 
 * Mobile gesture support: swipe, pull-to-refresh, long press
 */

import { useRef, useCallback, useEffect, useState } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

type SwipeDirection = 'left' | 'right' | 'up' | 'down' | null

interface SwipeHandlers {
    onSwipeLeft?: () => void
    onSwipeRight?: () => void
    onSwipeUp?: () => void
    onSwipeDown?: () => void
}

interface GestureOptions {
    threshold?: number           // Min distance for swipe (px)
    preventScroll?: boolean      // Prevent scroll during gesture
    enabled?: boolean            // Enable/disable gestures
}

interface UseSwipeResult {
    ref: React.RefObject<HTMLElement>
    direction: SwipeDirection
    isSwiping: boolean
    swipeDistance: { x: number; y: number }
}

// ─────────────────────────────────────────────────────────────────────────────
// USE SWIPE HOOK
// ─────────────────────────────────────────────────────────────────────────────

export function useSwipe(
    handlers: SwipeHandlers,
    options: GestureOptions = {}
): UseSwipeResult {
    const { threshold = 50, preventScroll = false, enabled = true } = options

    const ref = useRef<HTMLElement>(null)
    const [direction, setDirection] = useState<SwipeDirection>(null)
    const [isSwiping, setIsSwiping] = useState(false)
    const [swipeDistance, setSwipeDistance] = useState({ x: 0, y: 0 })

    const startPos = useRef({ x: 0, y: 0 })
    const currentPos = useRef({ x: 0, y: 0 })

    const handleTouchStart = useCallback((e: TouchEvent) => {
        if (!enabled) return
        const touch = e.touches[0]
        startPos.current = { x: touch.clientX, y: touch.clientY }
        currentPos.current = { x: touch.clientX, y: touch.clientY }
        setIsSwiping(true)
        setDirection(null)
    }, [enabled])

    const handleTouchMove = useCallback((e: TouchEvent) => {
        if (!enabled || !isSwiping) return

        const touch = e.touches[0]
        currentPos.current = { x: touch.clientX, y: touch.clientY }

        const deltaX = currentPos.current.x - startPos.current.x
        const deltaY = currentPos.current.y - startPos.current.y

        setSwipeDistance({ x: deltaX, y: deltaY })

        // Determine direction based on larger delta
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            setDirection(deltaX > 0 ? 'right' : 'left')
        } else {
            setDirection(deltaY > 0 ? 'down' : 'up')
        }

        if (preventScroll) {
            e.preventDefault()
        }
    }, [enabled, isSwiping, preventScroll])

    const handleTouchEnd = useCallback(() => {
        if (!enabled || !isSwiping) return

        const deltaX = currentPos.current.x - startPos.current.x
        const deltaY = currentPos.current.y - startPos.current.y

        const absX = Math.abs(deltaX)
        const absY = Math.abs(deltaY)

        // Trigger handlers if threshold met
        if (absX > threshold && absX > absY) {
            if (deltaX > 0) {
                handlers.onSwipeRight?.()
            } else {
                handlers.onSwipeLeft?.()
            }
        } else if (absY > threshold && absY > absX) {
            if (deltaY > 0) {
                handlers.onSwipeDown?.()
            } else {
                handlers.onSwipeUp?.()
            }
        }

        setIsSwiping(false)
        setSwipeDistance({ x: 0, y: 0 })
        setDirection(null)
    }, [enabled, isSwiping, threshold, handlers])

    useEffect(() => {
        const element = ref.current
        if (!element || !enabled) return

        element.addEventListener('touchstart', handleTouchStart, { passive: true })
        element.addEventListener('touchmove', handleTouchMove, { passive: !preventScroll })
        element.addEventListener('touchend', handleTouchEnd, { passive: true })

        return () => {
            element.removeEventListener('touchstart', handleTouchStart)
            element.removeEventListener('touchmove', handleTouchMove)
            element.removeEventListener('touchend', handleTouchEnd)
        }
    }, [enabled, handleTouchStart, handleTouchMove, handleTouchEnd, preventScroll])

    return { ref: ref as React.RefObject<HTMLElement>, direction, isSwiping, swipeDistance }
}

// ─────────────────────────────────────────────────────────────────────────────
// USE LONG PRESS HOOK
// ─────────────────────────────────────────────────────────────────────────────

interface UseLongPressOptions {
    delay?: number
    enabled?: boolean
    onLongPress: () => void
    onPress?: () => void
}

export function useLongPress(options: UseLongPressOptions) {
    const { delay = 500, enabled = true, onLongPress, onPress } = options

    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const isLongPress = useRef(false)

    const start = useCallback(() => {
        if (!enabled) return
        isLongPress.current = false
        timerRef.current = setTimeout(() => {
            isLongPress.current = true
            onLongPress()
        }, delay)
    }, [enabled, delay, onLongPress])

    const cancel = useCallback(() => {
        if (timerRef.current) {
            clearTimeout(timerRef.current)
            timerRef.current = null
        }
        if (!isLongPress.current && onPress) {
            onPress()
        }
    }, [onPress])

    return {
        onMouseDown: start,
        onMouseUp: cancel,
        onMouseLeave: cancel,
        onTouchStart: start,
        onTouchEnd: cancel,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// USE ENHANCED PULL TO REFRESH (extends existing)
// ─────────────────────────────────────────────────────────────────────────────

interface UsePullToRefreshOptions {
    onRefresh: () => Promise<void>
    threshold?: number
    enabled?: boolean
}

export function useEnhancedPullToRefresh(options: UsePullToRefreshOptions) {
    const { onRefresh, threshold = 80, enabled = true } = options

    const [isRefreshing, setIsRefreshing] = useState(false)
    const [pullDistance, setPullDistance] = useState(0)
    const [canRefresh, setCanRefresh] = useState(false)

    const containerRef = useRef<HTMLDivElement>(null)
    const startY = useRef(0)
    const isPulling = useRef(false)

    const handleTouchStart = useCallback((e: TouchEvent) => {
        if (!enabled || isRefreshing) return

        const container = containerRef.current
        if (!container || container.scrollTop > 0) return

        startY.current = e.touches[0].clientY
        isPulling.current = true
    }, [enabled, isRefreshing])

    const handleTouchMove = useCallback((e: TouchEvent) => {
        if (!enabled || !isPulling.current || isRefreshing) return

        const currentY = e.touches[0].clientY
        const distance = Math.max(0, (currentY - startY.current) * 0.5) // 0.5 = resistance

        setPullDistance(distance)
        setCanRefresh(distance >= threshold)

        if (distance > 0) {
            e.preventDefault()
        }
    }, [enabled, isRefreshing, threshold])

    const handleTouchEnd = useCallback(async () => {
        if (!enabled || !isPulling.current) return

        isPulling.current = false

        if (canRefresh && !isRefreshing) {
            setIsRefreshing(true)
            try {
                await onRefresh()
            } finally {
                setIsRefreshing(false)
            }
        }

        setPullDistance(0)
        setCanRefresh(false)
    }, [enabled, canRefresh, isRefreshing, onRefresh])

    useEffect(() => {
        const container = containerRef.current
        if (!container || !enabled) return

        container.addEventListener('touchstart', handleTouchStart, { passive: true })
        container.addEventListener('touchmove', handleTouchMove, { passive: false })
        container.addEventListener('touchend', handleTouchEnd, { passive: true })

        return () => {
            container.removeEventListener('touchstart', handleTouchStart)
            container.removeEventListener('touchmove', handleTouchMove)
            container.removeEventListener('touchend', handleTouchEnd)
        }
    }, [enabled, handleTouchStart, handleTouchMove, handleTouchEnd])

    return {
        containerRef,
        isRefreshing,
        pullDistance,
        canRefresh,
        pullProgress: Math.min(1, pullDistance / threshold),
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// USE DISMISS GESTURE (for modals/drawers)
// ─────────────────────────────────────────────────────────────────────────────

interface UseDismissGestureOptions {
    onDismiss: () => void
    direction?: 'down' | 'right'
    threshold?: number
    enabled?: boolean
}

export function useDismissGesture(options: UseDismissGestureOptions) {
    const { onDismiss, direction = 'down', threshold = 100, enabled = true } = options

    const [offset, setOffset] = useState(0)
    const [isDragging, setIsDragging] = useState(false)

    const startPos = useRef(0)

    const handleTouchStart = useCallback((e: TouchEvent) => {
        if (!enabled) return
        const touch = e.touches[0]
        startPos.current = direction === 'down' ? touch.clientY : touch.clientX
        setIsDragging(true)
    }, [enabled, direction])

    const handleTouchMove = useCallback((e: TouchEvent) => {
        if (!enabled || !isDragging) return
        const touch = e.touches[0]
        const current = direction === 'down' ? touch.clientY : touch.clientX
        const delta = current - startPos.current

        // Only allow positive offset (dragging in dismiss direction)
        setOffset(Math.max(0, delta))
    }, [enabled, isDragging, direction])

    const handleTouchEnd = useCallback(() => {
        if (!enabled) return
        setIsDragging(false)

        if (offset >= threshold) {
            onDismiss()
        }
        setOffset(0)
    }, [enabled, offset, threshold, onDismiss])

    const bindEvents = useCallback((element: HTMLElement | null) => {
        if (!element) return

        element.addEventListener('touchstart', handleTouchStart, { passive: true })
        element.addEventListener('touchmove', handleTouchMove, { passive: true })
        element.addEventListener('touchend', handleTouchEnd, { passive: true })

        return () => {
            element.removeEventListener('touchstart', handleTouchStart)
            element.removeEventListener('touchmove', handleTouchMove)
            element.removeEventListener('touchend', handleTouchEnd)
        }
    }, [handleTouchStart, handleTouchMove, handleTouchEnd])

    return {
        offset,
        isDragging,
        bindEvents,
        progress: Math.min(1, offset / threshold),
    }
}
