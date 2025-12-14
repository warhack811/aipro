/**
 * Image Jobs Store - Zustand
 * 
 * Görsel üretim işlerini merkezi olarak yönetir.
 * WebSocket güncellemelerini global state'e yansıtır.
 * 
 * ÖNEMLİ: Her job bir conversation'a ve bir pending mesaja bağlıdır.
 */

import { create } from 'zustand'
import type { ImageJob } from '@/types'

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface ImageJobsState {
    // Jobs by job_id
    jobs: Record<string, ImageJob>

    // Message ID to Job ID mapping (for linking pending messages to jobs)
    messageToJob: Record<string, string>

    lastUpdate: number

    // Actions
    updateJob: (job: Partial<ImageJob> & { id: string }) => void
    removeJob: (jobId: string) => void
    linkMessageToJob: (messageId: string, jobId: string) => void
    getJobForMessage: (messageId: string) => ImageJob | null
    getActiveJobForConversation: (conversationId: string) => ImageJob | null
    clearCompleted: () => void
}

// Callbacks for when a job completes
type JobCompleteCallback = (job: ImageJob) => void
const jobCompleteCallbacks = new Set<JobCompleteCallback>()

export function onJobComplete(callback: JobCompleteCallback) {
    jobCompleteCallbacks.add(callback)
    return () => jobCompleteCallbacks.delete(callback)
}

// ═══════════════════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════════════════

export const useImageJobsStore = create<ImageJobsState>()((set, get) => ({
    jobs: {},
    messageToJob: {},
    lastUpdate: Date.now(),

    updateJob: (data) => {
        set((state) => {
            const existing = state.jobs[data.id]
            const wasActive = existing && (existing.status === 'queued' || existing.status === 'processing')
            const isNowComplete = data.status === 'complete'

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

            // Create new jobs object (immutable update)
            const newJobs = {
                ...state.jobs,
                [data.id]: updatedJob,
            }

            // Notify callbacks if job just completed
            if (wasActive && isNowComplete) {
                setTimeout(() => {
                    jobCompleteCallbacks.forEach(cb => {
                        try { cb(updatedJob) } catch (e) { console.error(e) }
                    })
                }, 0)
            }

            // Auto-remove completed/error jobs after delay
            if (data.status === 'complete' || data.status === 'error') {
                setTimeout(() => {
                    get().removeJob(data.id)
                }, 10000) // 10 seconds
            }

            return {
                jobs: newJobs,
                lastUpdate: Date.now(),
            }
        })
    },

    removeJob: (jobId) => {
        set((state) => {
            const { [jobId]: _, ...remainingJobs } = state.jobs

            // Also remove message-job mapping
            const newMessageToJob = { ...state.messageToJob }
            for (const [msgId, jId] of Object.entries(newMessageToJob)) {
                if (jId === jobId) {
                    delete newMessageToJob[msgId]
                }
            }

            return {
                jobs: remainingJobs,
                messageToJob: newMessageToJob,
                lastUpdate: Date.now(),
            }
        })
    },

    linkMessageToJob: (messageId, jobId) => {
        set((state) => ({
            messageToJob: {
                ...state.messageToJob,
                [messageId]: jobId,
            },
            lastUpdate: Date.now(),
        }))
    },

    getJobForMessage: (messageId) => {
        const state = get()
        const jobId = state.messageToJob[messageId]
        if (!jobId) return null
        return state.jobs[jobId] || null
    },

    getActiveJobForConversation: (conversationId) => {
        const state = get()
        const jobs = Object.values(state.jobs)
        return jobs.find(
            (job) =>
                job.conversationId === conversationId &&
                (job.status === 'queued' || job.status === 'processing')
        ) || null
    },

    clearCompleted: () => {
        set((state) => {
            const newJobs: Record<string, ImageJob> = {}
            for (const [id, job] of Object.entries(state.jobs)) {
                if (job.status !== 'complete' && job.status !== 'error') {
                    newJobs[id] = job
                }
            }
            return {
                jobs: newJobs,
                lastUpdate: Date.now(),
            }
        })
    },
}))

// ═══════════════════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════════════════

export const selectAllJobs = (state: ImageJobsState): ImageJob[] =>
    Object.values(state.jobs)

export const selectActiveJobs = (state: ImageJobsState): ImageJob[] =>
    Object.values(state.jobs).filter(
        (job) => job.status === 'queued' || job.status === 'processing'
    )

export const selectJobsByConversation = (conversationId: string) =>
    (state: ImageJobsState): ImageJob[] =>
        Object.values(state.jobs).filter(
            (job) => job.conversationId === conversationId
        )

export const selectActiveJobForConversation = (conversationId: string | null) =>
    (state: ImageJobsState): ImageJob | null => {
        if (!conversationId) return null
        const jobs = Object.values(state.jobs)
        return jobs.find(
            (job) =>
                job.conversationId === conversationId &&
                (job.status === 'queued' || job.status === 'processing')
        ) || null
    }
