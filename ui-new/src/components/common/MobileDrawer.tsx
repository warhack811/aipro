/**
 * Mobile Drawer Component
 * 
 * Slide-out drawer for mobile navigation
 * iOS-style with gesture support
 */

import { useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence, useDragControls } from 'framer-motion'
import type { PanInfo } from 'framer-motion'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'

interface MobileDrawerProps {
    isOpen: boolean
    onClose: () => void
    children: React.ReactNode
    side?: 'left' | 'right'
    title?: string
}

export function MobileDrawer({
    isOpen,
    onClose,
    children,
    side = 'left',
    title
}: MobileDrawerProps) {
    const dragControls = useDragControls()
    const constraintsRef = useRef<HTMLDivElement>(null)

    // Close on escape
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose()
        }

        if (isOpen) {
            document.addEventListener('keydown', handleEscape)
            // Prevent body scroll when drawer is open
            document.body.style.overflow = 'hidden'
        }

        return () => {
            document.removeEventListener('keydown', handleEscape)
            document.body.style.overflow = ''
        }
    }, [isOpen, onClose])

    // Handle drag end
    const handleDragEnd = useCallback((event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
        const threshold = 100
        const velocity = 500

        if (side === 'left') {
            if (info.offset.x < -threshold || info.velocity.x < -velocity) {
                onClose()
            }
        } else {
            if (info.offset.x > threshold || info.velocity.x > velocity) {
                onClose()
            }
        }
    }, [side, onClose])

    return (
        <AnimatePresence mode="wait">
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-(--z-modal-backdrop)"
                    />

                    {/* Drawer */}
                    <motion.div
                        ref={constraintsRef}
                        initial={{ x: side === 'left' ? '-100%' : '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: side === 'left' ? '-100%' : '100%' }}
                        transition={{ type: 'spring', damping: 30, stiffness: 400 }}
                        drag="x"
                        dragControls={dragControls}
                        dragConstraints={{
                            left: side === 'left' ? -280 : 0,
                            right: side === 'left' ? 0 : 280
                        }}
                        dragElastic={0.1}
                        onDragEnd={handleDragEnd}
                        className={cn(
                            "fixed top-0 bottom-0 z-(--z-modal)",
                            "w-[280px] max-w-[85vw]",
                            "bg-(--color-bg-surface) border-(--color-border)",
                            "flex flex-col safe-area-top safe-area-bottom",
                            side === 'left'
                                ? "left-0 border-r rounded-r-2xl"
                                : "right-0 border-l rounded-l-2xl"
                        )}
                    >
                        {/* Drag Handle */}
                        <div
                            onPointerDown={(e) => dragControls.start(e)}
                            className={cn(
                                "absolute top-1/2 -translate-y-1/2 w-1 h-16 rounded-full",
                                "bg-(--color-text-muted)/30 cursor-grab active:cursor-grabbing",
                                side === 'left' ? "right-2" : "left-2"
                            )}
                        />

                        {/* Header (optional) */}
                        {title && (
                            <div className="flex items-center justify-between px-4 py-3 border-b border-(--color-border)">
                                <h2 className="font-display font-semibold">{title}</h2>
                                <Button variant="ghost" size="icon-sm" onClick={onClose}>
                                    <X className="h-5 w-5" />
                                </Button>
                            </div>
                        )}

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto scrollbar-thin">
                            {children}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

/**
 * Bottom Sheet Component
 * 
 * iOS-style bottom sheet with snap points
 */

interface BottomSheetProps {
    isOpen: boolean
    onClose: () => void
    children: React.ReactNode
    snapPoints?: number[] // Heights as percentages (e.g., [0.5, 1] for 50% and 100%)
    initialSnap?: number
}

export function BottomSheet({
    isOpen,
    onClose,
    children,
    snapPoints = [0.5, 0.9],
    initialSnap = 0
}: BottomSheetProps) {
    const maxHeight = typeof window !== 'undefined' ? window.innerHeight : 800
    const heights = snapPoints.map(p => maxHeight * p)

    const handleDragEnd = useCallback((event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
        // If dragged down fast enough or far enough, close
        if (info.velocity.y > 500 || info.offset.y > 100) {
            onClose()
        }
    }, [onClose])

    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden'
        }
        return () => {
            document.body.style.overflow = ''
        }
    }, [isOpen])

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-(--z-modal-backdrop)"
                    />

                    {/* Sheet */}
                    <motion.div
                        initial={{ y: '100%' }}
                        animate={{ y: 0 }}
                        exit={{ y: '100%' }}
                        transition={{ type: 'spring', damping: 30, stiffness: 400 }}
                        drag="y"
                        dragConstraints={{ top: 0, bottom: 0 }}
                        dragElastic={{ top: 0, bottom: 0.5 }}
                        onDragEnd={handleDragEnd}
                        className={cn(
                            "fixed bottom-0 left-0 right-0 z-(--z-modal)",
                            "bg-(--color-bg-surface) rounded-t-3xl",
                            "border-t border-(--color-border)",
                            "safe-area-bottom"
                        )}
                        style={{ maxHeight: heights[initialSnap] }}
                    >
                        {/* Drag Handle */}
                        <div className="flex justify-center py-3">
                            <div className="w-10 h-1 rounded-full bg-(--color-text-muted)/40" />
                        </div>

                        {/* Content */}
                        <div className="overflow-y-auto max-h-[calc(100%-40px)] px-4 pb-6 scrollbar-thin">
                            {children}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    )
}
