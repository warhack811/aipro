/**
 * useConversations Hook
 * 
 * Loads and manages conversation history from API
 */

import { useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { chatApi } from '@/api'
import { useChatStore } from '@/stores'

export function useConversations() {
    const setConversations = useChatStore((state) => state.setConversations)
    const setLoadingHistory = useChatStore((state) => state.setLoadingHistory)

    // Fetch conversations from API
    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['conversations'],
        queryFn: async () => {
            const conversations = await chatApi.getConversations()
            return conversations
        },
        staleTime: 1000 * 60 * 5, // 5 minutes
    })

    // Update store when data changes
    useEffect(() => {
        if (data) {
            setConversations(data)
        }
    }, [data, setConversations])

    // Track loading state
    useEffect(() => {
        setLoadingHistory(isLoading)
    }, [isLoading, setLoadingHistory])

    // Manual refresh
    const refreshConversations = useCallback(() => {
        refetch()
    }, [refetch])

    return {
        conversations: data || [],
        isLoading,
        error,
        refresh: refreshConversations
    }
}
