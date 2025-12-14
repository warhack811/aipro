/**
 * WebSocket Hook
 * 
 * Real-time connection for progress updates and notifications.
 * Görsel progress güncellemelerini progress cache'e yazar.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useToast } from '@/components/common'
// progressCache artık kullanılmıyor - state doğrudan güncelleniyor
import { decodeHtmlEntities } from '@/lib/utils'
import type { WebSocketMessage, Message } from '@/types'

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface UseWebSocketReturn {
    isConnected: boolean
    lastMessage: WebSocketMessage | null
    sendMessage: (message: string) => void
    reconnect: () => void
}

// Singleton WebSocket instance
let globalWs: WebSocket | null = null
let connectionPromise: Promise<void> | null = null

// ═══════════════════════════════════════════════════════════════════════════
// MAIN HOOK
// ═══════════════════════════════════════════════════════════════════════════

export function useWebSocket(): UseWebSocketReturn {
    const [isConnected, setIsConnected] = useState(false)
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
    const reconnectTimeoutRef = useRef<number | null>(null)
    const reconnectAttempts = useRef(0)
    const { success, error: toastError } = useToast()

    // Handle incoming messages
    const handleMessage = useCallback((event: MessageEvent) => {
        try {
            const rawData = JSON.parse(event.data)

            // Normalize message
            const message: WebSocketMessage = {
                type: rawData.type as WebSocketMessage['type'],
                data: rawData,
                timestamp: new Date().toISOString(),
            }

            setLastMessage(message)

            // Handle image_progress type (covers all states)
            if (message.type === 'image_progress') {
                const status = String(rawData.status || 'processing')
                const jobId = String(rawData.job_id || 'unknown')
                const progress = Number(rawData.progress || 0)
                const queuePosition = Number(rawData.queue_position || 1)
                const conversationId = rawData.conversation_id as string | undefined

                console.log('[WebSocket] Image progress:', jobId.slice(0, 8), status, progress + '%', 'queuePos:', queuePosition)

                // Update message directly via job_id matching
                import('@/stores/chatStore').then(({ useChatStore }) => {
                    const updateMessageByJobId = () => {
                        const store = useChatStore.getState()
                        const messages = store.messages

                        // Find message by job_id
                        const targetMessage = messages.find(m => m.extra_metadata?.job_id === jobId)

                        if (targetMessage) {
                            // Update extra_metadata with progress info
                            store.updateMessage(targetMessage.id, {
                                extra_metadata: {
                                    ...targetMessage.extra_metadata,
                                    status: status as 'queued' | 'processing' | 'complete' | 'error',
                                    progress: progress,
                                    queue_position: queuePosition,
                                },
                                // If complete/error, also update content
                                ...(status === 'complete' && rawData.image_url ? {
                                    content: `[IMAGE] Resminiz hazır.\nIMAGE_PATH: ${rawData.image_url}`
                                } : {}),
                                ...(status === 'error' ? {
                                    content: `❌ Görsel oluşturulamadı: ${rawData.error || 'Bilinmeyen hata'}`
                                } : {}),
                            })
                            console.log('[WebSocket] Updated message:', targetMessage.id, status, progress + '%')
                            return true
                        }
                        return false
                    }

                    // Try to update immediately
                    if (!updateMessageByJobId()) {
                        // If not found, retry after 300ms (message might be loading from DB)
                        console.log('[WebSocket] Message not found, retrying in 300ms...')
                        setTimeout(() => {
                            if (!updateMessageByJobId()) {
                                console.warn('[WebSocket] Still no message found for job_id:', jobId.slice(0, 8))
                            }
                        }, 300)
                    }
                }).catch(err => console.error('[WebSocket] update error:', err))

                // Show toast when complete/error
                if (status === 'complete') {
                    success('Görsel Hazır', 'Görseliniz başarıyla oluşturuldu')
                    window.dispatchEvent(new CustomEvent('image-complete', {
                        detail: { jobId, conversationId, imageUrl: rawData.image_url }
                    }))
                } else if (status === 'error') {
                    toastError('Görsel Hatası', String(rawData.error || 'Görsel oluşturulamadı'))
                }
            }

            // Handle notifications
            if (message.type === 'notification') {
                const data = message.data || {}
                const notifType = data.type as string

                if (notifType === 'success') {
                    success(String(data.title || 'Başarılı'), String(data.message || ''))
                } else if (notifType === 'error') {
                    toastError(String(data.title || 'Hata'), String(data.message || ''))
                }
            }
        } catch (e) {
            console.error('[WebSocket] Parse error', e)
        }
    }, [success, toastError])

    // Connect to WebSocket
    const connect = useCallback(() => {
        // Prevent duplicate connections
        if (globalWs?.readyState === WebSocket.OPEN) {
            setIsConnected(true)
            return
        }

        // Wait for pending connection
        if (connectionPromise) {
            return
        }

        connectionPromise = new Promise<void>((resolve) => {
            try {
                // Build WebSocket URL
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
                const host = window.location.host
                const wsUrl = `${protocol}//${host}/ws`

                console.log('[WebSocket] Connecting to:', wsUrl)

                globalWs = new WebSocket(wsUrl)

                globalWs.onopen = () => {
                    console.log('[WebSocket] Connected')
                    setIsConnected(true)
                    reconnectAttempts.current = 0
                    connectionPromise = null
                    resolve()
                }

                globalWs.onmessage = handleMessage

                globalWs.onclose = (e) => {
                    console.log('[WebSocket] Disconnected:', e.code, e.reason)
                    setIsConnected(false)
                    globalWs = null
                    connectionPromise = null

                    // Auto-reconnect with exponential backoff
                    if (reconnectAttempts.current < 5) {
                        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
                        console.log(`[WebSocket] Reconnecting in ${delay}ms...`)
                        reconnectTimeoutRef.current = window.setTimeout(() => {
                            reconnectAttempts.current++
                            connect()
                        }, delay)
                    }
                }

                globalWs.onerror = (error) => {
                    console.error('[WebSocket] Error:', error)
                    connectionPromise = null
                }
            } catch (error) {
                console.error('[WebSocket] Connection error:', error)
                connectionPromise = null
                resolve()
            }
        })
    }, [handleMessage])

    // Reconnect function
    const reconnect = useCallback(() => {
        if (globalWs) {
            globalWs.close()
            globalWs = null
        }
        reconnectAttempts.current = 0
        connect()
    }, [connect])

    // Send message
    const sendMessage = useCallback((message: string) => {
        if (globalWs?.readyState === WebSocket.OPEN) {
            globalWs.send(message)
        } else {
            console.warn('[WebSocket] Not connected, cannot send message')
        }
    }, [])

    // Connect on mount
    useEffect(() => {
        connect()

        return () => {
            // Clear reconnect timeout
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current)
            }
        }
    }, [connect])

    return {
        isConnected,
        lastMessage,
        sendMessage,
        reconnect,
    }
}
