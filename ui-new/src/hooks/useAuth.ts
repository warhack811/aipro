/**
 * Auth Hook
 * 
 * Hook for authentication state and actions
 */

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, systemApi } from '@/api'
import { useUserStore } from '@/stores'
import type { User, BrandingConfig } from '@/types'

// ─────────────────────────────────────────────────────────────────────────────

interface UseAuthReturn {
    user: User | null
    isLoading: boolean
    isAuthenticated: boolean
    error: Error | null
    login: (username: string, password: string) => Promise<boolean>
    logout: () => Promise<void>
    refreshUser: () => Promise<void>
}

export function useAuth(): UseAuthReturn {
    const queryClient = useQueryClient()
    const setUser = useUserStore((state) => state.setUser)
    const setAuthenticated = useUserStore((state) => state.setAuthenticated)
    const setBranding = useUserStore((state) => state.setBranding)
    const storeUser = useUserStore((state) => state.user)

    // Fetch current user
    const {
        data: user,
        isLoading,
        error,
        refetch
    } = useQuery({
        queryKey: ['currentUser'],
        queryFn: authApi.getCurrentUser,
        retry: false,
        staleTime: 1000 * 60 * 5, // 5 minutes
    })

    // Sync with store
    useEffect(() => {
        if (user) {
            setUser(user)
            setAuthenticated(true)
        } else if (!isLoading && !user) {
            setUser(null)
            setAuthenticated(false)
        }
    }, [user, isLoading, setUser, setAuthenticated])

    // Fetch branding
    const { data: branding } = useQuery({
        queryKey: ['branding'],
        queryFn: systemApi.getBranding,
        enabled: !!user,
        staleTime: 1000 * 60 * 30, // 30 minutes
    })

    useEffect(() => {
        if (branding) {
            setBranding(branding)
        }
    }, [branding, setBranding])

    // Login mutation
    const loginMutation = useMutation({
        mutationFn: ({ username, password }: { username: string; password: string }) =>
            authApi.login(username, password),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['currentUser'] })
        },
    })

    // Logout mutation
    const logoutMutation = useMutation({
        mutationFn: authApi.logout,
        onSuccess: () => {
            setUser(null)
            setAuthenticated(false)
            queryClient.clear()
            // Redirect to login
            window.location.href = '/'
        },
    })

    const login = useCallback(async (username: string, password: string): Promise<boolean> => {
        try {
            await loginMutation.mutateAsync({ username, password })
            return true
        } catch {
            return false
        }
    }, [loginMutation])

    const logout = useCallback(async () => {
        await logoutMutation.mutateAsync()
    }, [logoutMutation])

    const refreshUser = useCallback(async () => {
        await refetch()
    }, [refetch])

    return {
        user: user ?? storeUser,
        isLoading,
        isAuthenticated: !!user,
        error: error as Error | null,
        login,
        logout,
        refreshUser,
    }
}

// ─────────────────────────────────────────────────────────────────────────────

/**
 * Auth initializer - call once on app mount
 */
export function useAuthInit() {
    const { isLoading, isAuthenticated, error } = useAuth()
    const [isInitialized, setIsInitialized] = useState(false)

    useEffect(() => {
        if (!isLoading) {
            setIsInitialized(true)

            // If not authenticated, redirect to login
            if (!isAuthenticated && !error) {
                // Check if we're in the new-ui context
                if (window.location.pathname.startsWith('/new-ui')) {
                    // The backend will handle the redirect
                }
            }
        }
    }, [isLoading, isAuthenticated, error])

    return { isInitialized, isLoading, isAuthenticated }
}
