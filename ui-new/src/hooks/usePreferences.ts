/**
 * usePreferences Hook
 * 
 * Syncs settings store with backend preferences API
 * Loads on mount, saves on change
 */

import { useEffect, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { preferencesApi } from '@/api'
import { useSettingsStore, type PersonaMode, type ResponseStyle, type ImageSettings } from '@/stores/settingsStore'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface PreferencesData {
    persona?: string
    tone?: string
    length?: string
    emojiLevel?: string
    useMarkdown?: string
    useCodeBlocks?: string
    webSearch?: string
    imageGen?: string
    imageSize?: string
    imageStyle?: string
    imageAutoEnhance?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// HOOK
// ─────────────────────────────────────────────────────────────────────────────

export function usePreferences() {
    const queryClient = useQueryClient()

    // Store actions
    const setActivePersona = useSettingsStore((s) => s.setActivePersona)
    const setResponseStyle = useSettingsStore((s) => s.setResponseStyle)
    const setImageSettings = useSettingsStore((s) => s.setImageSettings)
    const setWebSearchEnabled = useSettingsStore((s) => s.setWebSearchEnabled)
    const setImageGenEnabled = useSettingsStore((s) => s.setImageGenEnabled)

    // Store values
    const activePersona = useSettingsStore((s) => s.activePersona)
    const responseStyle = useSettingsStore((s) => s.responseStyle)
    const imageSettings = useSettingsStore((s) => s.imageSettings)
    const webSearchEnabled = useSettingsStore((s) => s.webSearchEnabled)
    const imageGenEnabled = useSettingsStore((s) => s.imageGenEnabled)

    // ─── LOAD PREFERENCES FROM BACKEND ───────────────────────────────────────

    const preferencesQuery = useQuery({
        queryKey: ['preferences'],
        queryFn: () => preferencesApi.getPreferences('style'),
        staleTime: 1000 * 60 * 5, // 5 minutes
    })

    const personasQuery = useQuery({
        queryKey: ['personas'],
        queryFn: () => preferencesApi.getPersonas(),
        staleTime: 1000 * 60 * 10, // 10 minutes
    })

    // Apply backend preferences to store on load
    useEffect(() => {
        if (preferencesQuery.data) {
            const prefs = preferencesQuery.data

            if (prefs.tone) setResponseStyle({ tone: prefs.tone as ResponseStyle['tone'] })
            if (prefs.length) setResponseStyle({ length: prefs.length as ResponseStyle['length'] })
            if (prefs.emojiLevel) setResponseStyle({ emojiLevel: prefs.emojiLevel as ResponseStyle['emojiLevel'] })
            if (prefs.useMarkdown) setResponseStyle({ useMarkdown: prefs.useMarkdown === 'true' })
            if (prefs.useCodeBlocks) setResponseStyle({ useCodeBlocks: prefs.useCodeBlocks === 'true' })
            if (prefs.webSearch) setWebSearchEnabled(prefs.webSearch === 'true')
            if (prefs.imageGen) setImageGenEnabled(prefs.imageGen === 'true')
            if (prefs.imageSize) setImageSettings({ defaultSize: prefs.imageSize as ImageSettings['defaultSize'] })
            if (prefs.imageStyle) setImageSettings({ defaultStyle: prefs.imageStyle as ImageSettings['defaultStyle'] })
            if (prefs.imageAutoEnhance) setImageSettings({ autoEnhance: prefs.imageAutoEnhance === 'true' })
        }
    }, [preferencesQuery.data, setResponseStyle, setImageSettings, setWebSearchEnabled, setImageGenEnabled])

    // Apply active persona from backend
    useEffect(() => {
        if (personasQuery.data?.activePersona) {
            setActivePersona(personasQuery.data.activePersona as PersonaMode)
        }
    }, [personasQuery.data, setActivePersona])

    // ─── SAVE MUTATIONS ──────────────────────────────────────────────────────

    const savePreferenceMutation = useMutation({
        mutationFn: ({ key, value }: { key: string; value: string }) =>
            preferencesApi.setPreference(key, value, 'style'),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['preferences'] })
        },
    })

    const savePersonaMutation = useMutation({
        mutationFn: (persona: string) => preferencesApi.setActivePersona(persona),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['personas'] })
        },
    })

    // ─── SAVE HANDLERS ───────────────────────────────────────────────────────

    const savePersona = useCallback((persona: PersonaMode) => {
        setActivePersona(persona)
        savePersonaMutation.mutate(persona)
    }, [setActivePersona, savePersonaMutation])

    const saveResponseStyle = useCallback((style: Partial<ResponseStyle>) => {
        setResponseStyle(style)

        // Save each changed preference
        if (style.tone) savePreferenceMutation.mutate({ key: 'tone', value: style.tone })
        if (style.length) savePreferenceMutation.mutate({ key: 'length', value: style.length })
        if (style.emojiLevel) savePreferenceMutation.mutate({ key: 'emojiLevel', value: style.emojiLevel })
        if (style.useMarkdown !== undefined) savePreferenceMutation.mutate({ key: 'useMarkdown', value: String(style.useMarkdown) })
        if (style.useCodeBlocks !== undefined) savePreferenceMutation.mutate({ key: 'useCodeBlocks', value: String(style.useCodeBlocks) })
    }, [setResponseStyle, savePreferenceMutation])

    const saveImageSettings = useCallback((settings: Partial<ImageSettings>) => {
        setImageSettings(settings)

        if (settings.defaultSize) savePreferenceMutation.mutate({ key: 'imageSize', value: settings.defaultSize })
        if (settings.defaultStyle) savePreferenceMutation.mutate({ key: 'imageStyle', value: settings.defaultStyle })
        if (settings.autoEnhance !== undefined) savePreferenceMutation.mutate({ key: 'imageAutoEnhance', value: String(settings.autoEnhance) })
    }, [setImageSettings, savePreferenceMutation])

    const saveWebSearch = useCallback((enabled: boolean) => {
        setWebSearchEnabled(enabled)
        savePreferenceMutation.mutate({ key: 'webSearch', value: String(enabled) })
    }, [setWebSearchEnabled, savePreferenceMutation])

    const saveImageGen = useCallback((enabled: boolean) => {
        setImageGenEnabled(enabled)
        savePreferenceMutation.mutate({ key: 'imageGen', value: String(enabled) })
    }, [setImageGenEnabled, savePreferenceMutation])

    return {
        // Loading states
        isLoading: preferencesQuery.isLoading || personasQuery.isLoading,
        isSaving: savePreferenceMutation.isPending || savePersonaMutation.isPending,

        // Current values (from store)
        activePersona,
        responseStyle,
        imageSettings,
        webSearchEnabled,
        imageGenEnabled,

        // Available personas from backend
        personas: personasQuery.data?.personas ?? [],

        // Save handlers (updates store + backend)
        savePersona,
        saveResponseStyle,
        saveImageSettings,
        saveWebSearch,
        saveImageGen,

        // Refetch
        refetch: () => {
            preferencesQuery.refetch()
            personasQuery.refetch()
        },
    }
}
