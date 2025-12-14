/**
 * useImageJobs Hook
 * 
 * Görsel üretim işlerini yöneten merkezi hook.
 * WebSocket üzerinden gelen güncellemeleri işler.
 * 
 * Özellikler:
 * - Çoklu iş takibi (conversation bazlı)
 * - Otomatik temizlik (tamamlanan işler)
 * - İptal fonksiyonu
 * - Yeniden oluşturma
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import type { ImageJob } from '@/types'

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface ImageJobsState {
    jobs: Map<string, ImageJob>
    lastUpdate: number
}

interface UseImageJobsReturn {
    /** Tüm aktif işler */
    jobs: ImageJob[]
    /** Belirli conversation'ın işleri */
    getJobsByConversation: (conversationId: string) => ImageJob[]
    /** Belirli iş */
    getJob: (jobId: string) => ImageJob | undefined
    /** İş güncelleme (WebSocket'ten çağrılır) */
    updateJob: (data: Partial<ImageJob> & { id: string }) => void
    /** İş tamamlandı olarak işaretle */
    completeJob: (jobId: string, imageUrl: string) => void
    /** İş hatası */
    errorJob: (jobId: string, error: string) => void
    /** İşi kaldır */
    removeJob: (jobId: string) => void
    /** İşi iptal et */
    cancelJob: (jobId: string) => Promise<void>
    /** Aktif iş sayısı */
    activeJobCount: number
}

// ═══════════════════════════════════════════════════════════════════════════
// HOOK
// ═══════════════════════════════════════════════════════════════════════════

export function useImageJobs(): UseImageJobsReturn {
    const [state, setState] = useState<ImageJobsState>({
        jobs: new Map(),
        lastUpdate: Date.now(),
    })

    // Cleanup timer ref
    const cleanupTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    // Get all jobs as array
    const jobs = Array.from(state.jobs.values())

    // Get jobs by conversation
    const getJobsByConversation = useCallback((conversationId: string): ImageJob[] => {
        return jobs.filter(job => job.conversationId === conversationId)
    }, [jobs])

    // Get single job
    const getJob = useCallback((jobId: string): ImageJob | undefined => {
        return state.jobs.get(jobId)
    }, [state.jobs])

    // Update job (from WebSocket)
    const updateJob = useCallback((data: Partial<ImageJob> & { id: string }) => {
        setState(prev => {
            const newJobs = new Map(prev.jobs)
            const existing = newJobs.get(data.id)

            const updatedJob: ImageJob = {
                id: data.id,
                conversationId: data.conversationId ?? existing?.conversationId,
                prompt: data.prompt ?? existing?.prompt ?? '',
                status: data.status ?? existing?.status ?? 'queued',
                progress: data.progress ?? existing?.progress ?? 0,
                queuePosition: data.queuePosition ?? existing?.queuePosition,
                estimatedSeconds: data.estimatedSeconds ?? existing?.estimatedSeconds,
                imageUrl: data.imageUrl ?? existing?.imageUrl,
                error: data.error ?? existing?.error,
                createdAt: existing?.createdAt ?? new Date().toISOString(),
                completedAt: data.status === 'complete'
                    ? new Date().toISOString()
                    : existing?.completedAt,
            }

            newJobs.set(data.id, updatedJob)

            return {
                jobs: newJobs,
                lastUpdate: Date.now(),
            }
        })
    }, [])

    // Complete job
    const completeJob = useCallback((jobId: string, imageUrl: string) => {
        updateJob({
            id: jobId,
            status: 'complete',
            progress: 100,
            imageUrl,
        })

        // Schedule cleanup after 5 seconds
        setTimeout(() => {
            removeJob(jobId)
        }, 5000)
    }, [updateJob])

    // Error job
    const errorJob = useCallback((jobId: string, error: string) => {
        updateJob({
            id: jobId,
            status: 'error',
            error,
        })

        // Schedule cleanup after 10 seconds
        setTimeout(() => {
            removeJob(jobId)
        }, 10000)
    }, [updateJob])

    // Remove job
    const removeJob = useCallback((jobId: string) => {
        setState(prev => {
            const newJobs = new Map(prev.jobs)
            newJobs.delete(jobId)
            return {
                jobs: newJobs,
                lastUpdate: Date.now(),
            }
        })
    }, [])

    // Cancel job (API call)
    const cancelJob = useCallback(async (jobId: string) => {
        try {
            // TODO: Backend'e iptal isteği gönder
            // await fetch(`/api/v1/image/cancel/${jobId}`, { method: 'POST' })

            // Şimdilik sadece local state'i güncelle
            removeJob(jobId)
        } catch (error) {
            console.error('Failed to cancel job:', error)
            throw error
        }
    }, [removeJob])

    // Active job count
    const activeJobCount = jobs.filter(
        j => j.status === 'queued' || j.status === 'processing'
    ).length

    // Cleanup old completed/error jobs periodically
    useEffect(() => {
        cleanupTimerRef.current = setInterval(() => {
            const now = Date.now()
            const maxAge = 60000 // 1 minute

            setState(prev => {
                const newJobs = new Map(prev.jobs)
                let changed = false

                for (const [id, job] of newJobs) {
                    if (job.status === 'complete' || job.status === 'error') {
                        const age = now - new Date(job.completedAt || job.createdAt || now).getTime()
                        if (age > maxAge) {
                            newJobs.delete(id)
                            changed = true
                        }
                    }
                }

                if (changed) {
                    return { jobs: newJobs, lastUpdate: now }
                }
                return prev
            })
        }, 30000) // Check every 30 seconds

        return () => {
            if (cleanupTimerRef.current) {
                clearInterval(cleanupTimerRef.current)
            }
        }
    }, [])

    return {
        jobs,
        getJobsByConversation,
        getJob,
        updateJob,
        completeJob,
        errorJob,
        removeJob,
        cancelJob,
        activeJobCount,
    }
}

export default useImageJobs
