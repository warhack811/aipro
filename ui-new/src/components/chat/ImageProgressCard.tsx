/**
 * ImageProgressCard Component
 * 
 * Görsel üretim sürecini gösteren progress kartı.
 * Chat içinde bot mesajı olarak görünür.
 * 
 * Özellikler:
 * - Shimmer placeholder
 * - Progress bar (gradient animasyonlu)
 * - Kuyruk pozisyonu
 * - Tahmini süre
 * - İptal butonu
 */

import { useState, useCallback, memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Sparkles, Clock, Users, Copy, Check } from 'lucide-react'
import type { ImageJob } from '@/types'

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface ImageProgressCardProps {
    job: ImageJob
    onCancel?: (jobId: string) => void
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export const ImageProgressCard = memo(function ImageProgressCard({
    job,
    onCancel,
}: ImageProgressCardProps) {
    const [isHovered, setIsHovered] = useState(false)
    const [isCancelling, setIsCancelling] = useState(false)
    const [copied, setCopied] = useState(false)

    const isQueued = job.status === 'queued'
    const isProcessing = job.status === 'processing'
    const isError = job.status === 'error'

    // Calculate estimated time based on current state (no timer needed)
    const calculateEstimatedTime = (): number => {
        // Error durumunda 0
        if (isError) return 0

        // Queued: Sıra × 80 saniye
        if (isQueued) {
            return (job.queuePosition || 1) * 80
        }

        // Processing: Progress'e göre kalan
        if (isProcessing) {
            const remaining = Math.ceil((100 - job.progress) * 0.8)
            return Math.max(0, remaining)
        }

        // Complete durumunda 0
        return 0
    }

    // Format time as M:SS
    const formatTime = (seconds: number): string => {
        if (seconds === 0) return '0:00'
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    // Calculate on every render (WebSocket updates trigger re-render)
    const estimatedSeconds = calculateEstimatedTime()

    // Truncate prompt for queued state, show full for processing
    const displayPrompt = isQueued && job.prompt.length > 50
        ? job.prompt.slice(0, 50) + '...'
        : job.prompt

    // Copy prompt to clipboard
    const handleCopyPrompt = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(job.prompt)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        } catch (e) {
            console.error('Copy failed:', e)
        }
    }, [job.prompt])

    // Handle cancel
    const handleCancel = useCallback(async () => {
        console.log('[ImageProgressCard] Cancel clicked, job:', job.id)
        if (isCancelling || !onCancel) return

        setIsCancelling(true)
        try {
            await onCancel(job.id)
            // Animasyon MessageBubble tarafından handle edilecek (deleteMessage)
        } catch (e) {
            console.error('[ImageProgressCard] Cancel failed:', e)
            setIsCancelling(false)
        }
        // Not resetting isCancelling on success - card will be deleted
    }, [job.id, onCancel, isCancelling])

    return (
        <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={isCancelling ? {
                opacity: 0,
                scale: 0.95,
                filter: 'blur(8px)',
            } : {
                opacity: 1,
                y: 0,
                scale: 1
            }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: isCancelling ? 0.8 : 0.3, ease: 'easeOut' }}
            className="image-progress-card"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Card Container */}
            <div className={`
                relative overflow-hidden rounded-2xl
                bg-linear-to-br from-(--color-surface) to-(--color-surface-hover)
                border border-(--color-border)
                backdrop-blur-sm
                transition-all duration-300
                ${isHovered ? 'border-(--color-primary)/50 shadow-lg shadow-(--color-primary)/10' : ''}
            `}>
                {/* Pulse Border Animation (when queued) */}
                {isQueued && (
                    <div className="absolute inset-0 rounded-2xl animate-pulse-border pointer-events-none" />
                )}

                <div className="p-4 space-y-3">
                    {/* Header Row */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {/* Status Icon */}
                            <div className={`
                                flex items-center justify-center w-8 h-8 rounded-lg
                                ${isQueued
                                    ? 'bg-amber-500/20 text-amber-400'
                                    : 'bg-(--color-primary)/20 text-(--color-primary)'
                                }
                            `}>
                                {isQueued ? (
                                    <Users className="w-4 h-4" />
                                ) : (
                                    <Sparkles className="w-4 h-4 animate-pulse" />
                                )}
                            </div>

                            {/* Queue Position + Estimated Time */}
                            <div className="flex items-center gap-1.5">
                                <span className={`
                                    px-2 py-0.5 rounded-full text-xs font-semibold
                                    ${isQueued
                                        ? 'bg-amber-500/20 text-amber-400'
                                        : 'bg-(--color-primary)/20 text-(--color-primary)'
                                    }
                                `}>
                                    {isQueued
                                        ? `#${job.queuePosition || 1} Sırada`
                                        : `%${job.progress} Tamamlandı`
                                    }
                                </span>

                                {/* Countdown Timer */}
                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-violet-500/20 text-violet-400">
                                    <Clock className="w-3 h-3" />
                                    ~{formatTime(estimatedSeconds)}
                                </span>
                            </div>
                        </div>

                        {/* Cancel Button - Always visible, disabled when processing */}
                        <AnimatePresence>
                            {onCancel && (
                                <motion.button
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{
                                        opacity: isQueued ? (isHovered || isCancelling ? 1 : 0.6) : 0.3,
                                        scale: 1
                                    }}
                                    exit={{ opacity: 0, scale: 0.8 }}
                                    whileHover={isQueued ? { scale: 1.1 } : {}}
                                    whileTap={isQueued ? { scale: 0.95 } : {}}
                                    onClick={isQueued ? handleCancel : undefined}
                                    disabled={isCancelling || !isQueued}
                                    className={`
                                        flex items-center justify-center w-7 h-7 rounded-lg
                                        transition-all duration-200
                                        ${isQueued
                                            ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:text-red-300 cursor-pointer'
                                            : 'bg-gray-500/10 text-gray-500 cursor-not-allowed'
                                        }
                                        ${isCancelling ? 'opacity-50' : ''}
                                    `}
                                    title={isQueued ? "İptal et" : "İşlem başladı, iptal edilemez"}
                                >
                                    <X className={`w-4 h-4 ${isCancelling ? 'animate-spin' : ''}`} />
                                </motion.button>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Enhanced Shimmer Placeholder */}
                    <div className="relative w-full aspect-video rounded-xl overflow-hidden mb-3">
                        {/* Base gradient */}
                        <div className="absolute inset-0 bg-gradient-to-br from-[#1a1a2e] to-[#16213e]" />

                        {/* Shimmer effect */}
                        <div className="absolute inset-0 shimmer-animation" />

                        {/* Grid pattern */}
                        <div className="absolute inset-0 grid-pattern opacity-50" />

                        {/* Progress overlay */}
                        <motion.div
                            className="absolute top-0 left-0 h-full bg-gradient-to-r from-indigo-500/20 to-violet-500/20"
                            initial={{ width: '0%' }}
                            animate={{ width: `${job.progress}%` }}
                            transition={{ duration: 0.3, ease: 'easeOut' }}
                        />

                        {/* Center icon */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <motion.div
                                className="text-white/40"
                                animate={{
                                    opacity: [0.4, 0.8, 0.4],
                                    scale: [1, 1.1, 1]
                                }}
                                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                            >
                                {isQueued ? (
                                    <Clock className="w-12 h-12" />
                                ) : (
                                    <Sparkles className="w-12 h-12" />
                                )}
                            </motion.div>
                        </div>

                        {/* Bottom progress bar */}
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
                            <motion.div
                                className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 shadow-[0_0_10px_rgba(99,102,241,0.5)]"
                                initial={{ width: '0%' }}
                                animate={{ width: `${job.progress}%` }}
                                transition={{ duration: 0.3, ease: 'easeOut' }}
                            />
                        </div>
                    </div>

                    {/* Progress Info */}
                    <div className="flex items-center gap-3">
                        {/* Prompt with Copy Button */}
                        <div className="flex items-start gap-2">
                            <p className="flex-1 text-sm text-(--color-text) leading-snug line-clamp-2">
                                {displayPrompt}
                            </p>
                            {isProcessing && (
                                <button
                                    onClick={handleCopyPrompt}
                                    className={`
                                            flex items-center gap-1 px-2 py-1 rounded-md text-xs
                                            transition-all duration-200 shrink-0
                                            ${copied
                                            ? 'bg-green-500/20 text-green-400'
                                            : 'bg-(--color-surface-hover) text-(--color-text-muted) hover:bg-(--color-primary)/20 hover:text-(--color-primary)'
                                        }
                                        `}
                                    title="Prompt'u kopyala"
                                >
                                    {copied ? (
                                        <>
                                            <Check className="w-3 h-3" />
                                            <span>Kopyalandı</span>
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="w-3 h-3" />
                                            <span>Kopyala</span>
                                        </>
                                    )}
                                </button>
                            )}
                        </div>

                        {/* Progress Bar */}
                        <div className="relative h-2 bg-(--color-border) rounded-full overflow-hidden">
                            {isProcessing && (
                                <motion.div
                                    className="absolute inset-y-0 left-0 rounded-full progress-bar-gradient"
                                    initial={{ width: '0%' }}
                                    animate={{ width: `${job.progress}%` }}
                                    transition={{ duration: 0.5, ease: 'easeOut' }}
                                />
                            )}
                            {isQueued && (
                                <div className="absolute inset-0 overflow-hidden">
                                    <div className="w-full h-full queued-bar-animation" />
                                </div>
                            )}
                        </div>

                        {/* Progress Percentage */}
                        <div className="flex items-center justify-between text-xs">
                            <span className="text-(--color-text-muted)">
                                {isQueued ? 'Kuyrukta bekliyor' : 'Oluşturuluyor'}
                            </span>
                            {isProcessing && (
                                <motion.span
                                    key={job.progress}
                                    initial={{ opacity: 0, y: -5 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="font-medium text-(--color-primary)"
                                >
                                    {job.progress}%
                                </motion.span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Styles */}
            <style>{`
                .shimmer-animation {
                    background: linear-gradient(
                        90deg,
                        transparent,
                        rgba(255,255,255,0.1),
                        transparent
                    );
                    background-size: 200% 100%;
                    animation: shimmer 2s infinite;
                }

                @keyframes shimmer {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }

                .grid-pattern {
                    background-image: 
                        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
                    background-size: 20px 20px;
                }

                .progress-bar-gradient {
                    background: linear-gradient(
                        90deg,
                        var(--color-primary),
                        var(--color-accent),
                        var(--color-primary)
                    );
                    background-size: 200% 100%;
                    animation: progressGradient 2s linear infinite;
                }

                @keyframes progressGradient {
                    0% { background-position: 0% 50%; }
                    100% { background-position: 200% 50%; }
                }

                .queued-bar-animation {
                    background: repeating-linear-gradient(
                        -45deg,
                        transparent,
                        transparent 8px,
                        var(--color-primary)/20 8px,
                        var(--color-primary)/20 16px
                    );
                    animation: queuedStripes 1s linear infinite;
                }

                @keyframes queuedStripes {
                    0% { transform: translateX(-32px); }
                    100% { transform: translateX(0); }
                }

                .animate-pulse-border {
                    background: linear-gradient(
                        90deg,
                        transparent,
                        var(--color-primary)/10,
                        transparent
                    );
                    animation: pulseBorder 2s ease-in-out infinite;
                }

                @keyframes pulseBorder {
                    0%, 100% { opacity: 0; }
                    50% { opacity: 1; }
                }
            `}</style>
        </motion.div>
    )
})

export default ImageProgressCard
