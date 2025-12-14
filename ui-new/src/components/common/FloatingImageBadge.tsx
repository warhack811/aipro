/**
 * FloatingImageBadge Component
 * 
 * Ekranın sağ alt köşesinde görünen küçük badge.
 * Aktif görsel üretimlerini gösterir.
 * 
 * Özellikler:
 * - Aktif iş sayısı
 * - Tıklanınca detay popup
 * - Mobile uyumlu
 * - Animasyonlu
 */

import { useState, memo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ImageIcon, X, ChevronUp, ChevronDown } from 'lucide-react'
import type { ImageJob } from '@/types'

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface FloatingImageBadgeProps {
    jobs: ImageJob[]
    onJobClick?: (job: ImageJob) => void
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export const FloatingImageBadge = memo(function FloatingImageBadge({
    jobs,
    onJobClick,
}: FloatingImageBadgeProps) {
    const [isExpanded, setIsExpanded] = useState(false)

    // Filter only active jobs (not complete, not error)
    const activeJobs = jobs.filter(j => j.status === 'queued' || j.status === 'processing')

    // Don't render if no active jobs
    if (activeJobs.length === 0) return null

    const processingJobs = activeJobs.filter(j => j.status === 'processing')
    const queuedJobs = activeJobs.filter(j => j.status === 'queued')

    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
            {/* Expanded Panel */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        transition={{ duration: 0.2, ease: 'easeOut' }}
                        className="w-72 max-h-80 overflow-hidden rounded-xl
                            bg-(--color-surface)/95 backdrop-blur-lg
                            border border-(--color-border)
                            shadow-2xl shadow-black/20"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-4 py-3 border-b border-(--color-border)">
                            <div className="flex items-center gap-2">
                                <ImageIcon className="w-4 h-4 text-(--color-primary)" />
                                <span className="text-sm font-semibold text-(--color-text)">
                                    Görsel Üretimi
                                </span>
                            </div>
                            <button
                                onClick={() => setIsExpanded(false)}
                                className="p-1 rounded-lg hover:bg-(--color-surface-hover) transition-colors"
                            >
                                <X className="w-4 h-4 text-(--color-text-muted)" />
                            </button>
                        </div>

                        {/* Job List */}
                        <div className="max-h-60 overflow-y-auto p-2 space-y-2">
                            {activeJobs.map((job) => (
                                <JobItem
                                    key={job.id}
                                    job={job}
                                    onClick={() => onJobClick?.(job)}
                                />
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Badge Button */}
            <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-full
                    bg-(--color-primary) text-white
                    shadow-lg shadow-(--color-primary)/30
                    transition-all duration-200
                    hover:shadow-xl hover:shadow-(--color-primary)/40"
            >
                {/* Pulse Ring (when processing) */}
                {processingJobs.length > 0 && (
                    <span className="absolute inset-0 rounded-full animate-ping bg-(--color-primary)/30" />
                )}

                <ImageIcon className="w-4 h-4 relative z-10" />

                <span className="text-sm font-medium relative z-10">
                    {processingJobs.length > 0
                        ? `${processingJobs.length} işleniyor`
                        : `${queuedJobs.length} kuyrukta`
                    }
                </span>

                {/* Expand/Collapse Icon */}
                <span className="relative z-10">
                    {isExpanded
                        ? <ChevronDown className="w-4 h-4" />
                        : <ChevronUp className="w-4 h-4" />
                    }
                </span>
            </motion.button>
        </div>
    )
})

// ═══════════════════════════════════════════════════════════════════════════
// JOB ITEM
// ═══════════════════════════════════════════════════════════════════════════

interface JobItemProps {
    job: ImageJob
    onClick?: () => void
}

const JobItem = memo(function JobItem({ job, onClick }: JobItemProps) {
    const isProcessing = job.status === 'processing'
    const truncatedPrompt = job.prompt.length > 40
        ? job.prompt.slice(0, 40) + '...'
        : job.prompt

    return (
        <motion.div
            whileHover={{ scale: 1.01 }}
            onClick={onClick}
            className="p-3 rounded-lg bg-(--color-surface-hover)/50 
                hover:bg-(--color-surface-hover) 
                cursor-pointer transition-colors"
        >
            <div className="flex items-center justify-between mb-2">
                <span className={`
                    px-2 py-0.5 rounded-full text-xs font-medium
                    ${isProcessing
                        ? 'bg-(--color-primary)/20 text-(--color-primary)'
                        : 'bg-amber-500/20 text-amber-400'
                    }
                `}>
                    #{job.queuePosition} {isProcessing ? 'İşleniyor' : 'Kuyrukta'}
                </span>
                {isProcessing && (
                    <span className="text-xs font-medium text-(--color-primary)">
                        {job.progress}%
                    </span>
                )}
            </div>

            <p className="text-xs text-(--color-text-muted) line-clamp-2">
                {truncatedPrompt}
            </p>

            {/* Mini Progress Bar */}
            {isProcessing && (
                <div className="mt-2 h-1 bg-(--color-border) rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-(--color-primary) rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${job.progress}%` }}
                        transition={{ duration: 0.3 }}
                    />
                </div>
            )}
        </motion.div>
    )
})

export default FloatingImageBadge
