/**
 * useImageProgress Hook
 * 
 * WebSocket'ten gelen image progress eventlerini dinler.
 * Her mesaj kendi job_id'si ile progress alır.
 * 
 * SIMPLE APPROACH: WebSocket progress + Polling backup
 */

import { useState, useEffect, useCallback, useRef } from 'react'

export interface ImageProgressData {
    status: 'queued' | 'processing' | 'complete' | 'error'
    progress: number
    queuePosition?: number
    estimatedSeconds?: number
    imageUrl?: string
    error?: string
    prompt?: string
}

// Global progress cache - job_id -> progress data
const progressCache = new Map<string, ImageProgressData>()
const listeners = new Set<() => void>()

// Notify all listeners when cache updates
function notifyListeners() {
    listeners.forEach(fn => fn())
}

// Update cache from WebSocket event
export function updateProgressFromWebSocket(data: {
    job_id: string
    status: string
    progress: number
    queue_position?: number
    estimated_seconds?: number
    image_url?: string
    error?: string
    prompt?: string
}) {
    const progressData: ImageProgressData = {
        status: data.status as ImageProgressData['status'],
        progress: data.progress,
        queuePosition: data.queue_position,
        estimatedSeconds: data.estimated_seconds,
        imageUrl: data.image_url,
        error: data.error,
        prompt: data.prompt,
    }

    progressCache.set(data.job_id, progressData)
    notifyListeners()

    // Auto-cleanup completed jobs after 30 seconds
    if (data.status === 'complete' || data.status === 'error') {
        setTimeout(() => {
            progressCache.delete(data.job_id)
            notifyListeners()
        }, 30000)
    }
}

// Get progress for a specific job_id
export function getProgressForJob(jobId: string): ImageProgressData | null {
    return progressCache.get(jobId) || null
}

// Check if any jobs are active
export function hasActiveJobs(): boolean {
    for (const data of progressCache.values()) {
        if (data.status === 'queued' || data.status === 'processing') {
            return true
        }
    }
    return false
}

// Get active job count
export function getActiveJobCount(): number {
    let count = 0
    for (const data of progressCache.values()) {
        if (data.status === 'queued' || data.status === 'processing') {
            count++
        }
    }
    return count
}

/**
 * Hook to get progress for a specific job_id
 */
export function useImageProgress(jobId: string | undefined): ImageProgressData | null {
    const [progress, setProgress] = useState<ImageProgressData | null>(
        jobId ? progressCache.get(jobId) || null : null
    )

    useEffect(() => {
        if (!jobId) {
            setProgress(null)
            return
        }

        // Initial value
        setProgress(progressCache.get(jobId) || null)

        // Listen for updates
        const handleUpdate = () => {
            const data = progressCache.get(jobId)
            setProgress(data || null)
        }

        listeners.add(handleUpdate)
        return () => {
            listeners.delete(handleUpdate)
        }
    }, [jobId])

    return progress
}

/**
 * Hook to check if there are any active jobs
 */
export function useHasActiveJobs(): boolean {
    const [hasActive, setHasActive] = useState(hasActiveJobs())

    useEffect(() => {
        const handleUpdate = () => {
            setHasActive(hasActiveJobs())
        }

        listeners.add(handleUpdate)
        return () => {
            listeners.delete(handleUpdate)
        }
    }, [])

    return hasActive
}

/**
 * Hook to get active job count
 */
export function useActiveJobCount(): number {
    const [count, setCount] = useState(getActiveJobCount())

    useEffect(() => {
        const handleUpdate = () => {
            setCount(getActiveJobCount())
        }

        listeners.add(handleUpdate)
        return () => {
            listeners.delete(handleUpdate)
        }
    }, [])

    return count
}
