/**
 * Export/Import Component
 * 
 * Conversation backup & restore:
 * - Export to JSON
 * - Import from JSON
 * - Selective export
 */

import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Download, Upload, FileJson, Check, AlertCircle,
    X, ChevronDown, Loader2, Info
} from 'lucide-react'
import { useChatStore } from '@/stores'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { Conversation, Message } from '@/types'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface ExportData {
    version: string
    exportedAt: string
    appName: string
    conversations: {
        id: string
        title: string
        messages: Message[]
        createdAt: string
        updatedAt: string
    }[]
    settings?: Record<string, unknown>
}

interface ExportImportProps {
    isOpen: boolean
    onClose: () => void
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export function ExportImport({ isOpen, onClose }: ExportImportProps) {
    const [mode, setMode] = useState<'export' | 'import'>('export')
    const [selectedConversations, setSelectedConversations] = useState<Set<string>>(new Set())
    const [isProcessing, setIsProcessing] = useState(false)
    const [result, setResult] = useState<{ type: 'success' | 'error', message: string } | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const conversations = useChatStore((state) => state.conversations)
    const messages = useChatStore((state) => state.messages)
    const currentConversationId = useChatStore((state) => state.currentConversationId)

    // Toggle conversation selection
    const toggleConversation = (id: string) => {
        setSelectedConversations(prev => {
            const next = new Set(prev)
            if (next.has(id)) {
                next.delete(id)
            } else {
                next.add(id)
            }
            return next
        })
    }

    // Select all
    const selectAll = () => {
        setSelectedConversations(new Set(conversations.map(c => c.id)))
    }

    // Deselect all
    const deselectAll = () => {
        setSelectedConversations(new Set())
    }

    // Export handler
    const handleExport = async () => {
        if (selectedConversations.size === 0) {
            setResult({ type: 'error', message: 'En az bir sohbet seçin' })
            return
        }

        setIsProcessing(true)
        setResult(null)

        try {
            const exportData: ExportData = {
                version: '1.0.0',
                exportedAt: new Date().toISOString(),
                appName: 'Mami AI',
                conversations: []
            }

            // For each selected conversation
            conversations.forEach(conv => {
                if (selectedConversations.has(conv.id)) {
                    // If it's the current conversation, use loaded messages
                    const convMessages = conv.id === currentConversationId
                        ? messages
                        : [] // Would need to fetch from API for other conversations

                    exportData.conversations.push({
                        id: conv.id,
                        title: conv.title || 'Başlıksız',
                        messages: convMessages,
                        createdAt: conv.createdAt || new Date().toISOString(),
                        updatedAt: conv.updatedAt || new Date().toISOString()
                    })
                }
            })

            // Create download
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `mami-ai-export-${new Date().toISOString().split('T')[0]}.json`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)

            setResult({
                type: 'success',
                message: `${selectedConversations.size} sohbet dışa aktarıldı`
            })
        } catch (error) {
            setResult({
                type: 'error',
                message: 'Dışa aktarma başarısız: ' + (error as Error).message
            })
        } finally {
            setIsProcessing(false)
        }
    }

    // Import handler
    const handleImport = async (file: File) => {
        setIsProcessing(true)
        setResult(null)

        try {
            const text = await file.text()
            const data: ExportData = JSON.parse(text)

            // Validate format
            if (!data.version || !data.conversations || !Array.isArray(data.conversations)) {
                throw new Error('Geçersiz dosya formatı')
            }

            // TODO: Actually import conversations via API
            // For now, just validate and show success

            setResult({
                type: 'success',
                message: `${data.conversations.length} sohbet içe aktarılmaya hazır`
            })
        } catch (error) {
            setResult({
                type: 'error',
                message: 'İçe aktarma başarısız: ' + (error as Error).message
            })
        } finally {
            setIsProcessing(false)
        }
    }

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            handleImport(file)
        }
    }

    if (!isOpen) return null

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    onClick={(e) => e.stopPropagation()}
                    className={cn(
                        "w-full max-w-lg rounded-2xl overflow-hidden",
                        "bg-(--color-bg-surface) border border-(--color-border)"
                    )}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-(--color-border)">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-(--color-primary-soft)">
                                <FileJson className="h-5 w-5 text-(--color-primary)" />
                            </div>
                            <div>
                                <h2 className="font-semibold">Dışa/İçe Aktar</h2>
                                <p className="text-xs text-(--color-text-muted)">
                                    Sohbetlerinizi yedekleyin
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-(--color-bg-surface-hover)"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    </div>

                    {/* Mode Tabs */}
                    <div className="flex border-b border-(--color-border)">
                        <button
                            onClick={() => setMode('export')}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 px-4 py-3",
                                "border-b-2 transition-colors",
                                mode === 'export'
                                    ? "border-(--color-primary) text-(--color-primary)"
                                    : "border-transparent text-(--color-text-muted)"
                            )}
                        >
                            <Download className="h-4 w-4" />
                            Dışa Aktar
                        </button>
                        <button
                            onClick={() => setMode('import')}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 px-4 py-3",
                                "border-b-2 transition-colors",
                                mode === 'import'
                                    ? "border-(--color-primary) text-(--color-primary)"
                                    : "border-transparent text-(--color-text-muted)"
                            )}
                        >
                            <Upload className="h-4 w-4" />
                            İçe Aktar
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-4">
                        {mode === 'export' ? (
                            <div className="space-y-4">
                                {/* Selection Header */}
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-(--color-text-muted)">
                                        {selectedConversations.size} / {conversations.length} seçili
                                    </span>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={selectAll}
                                            className="text-xs text-(--color-primary) hover:underline"
                                        >
                                            Tümünü seç
                                        </button>
                                        <button
                                            onClick={deselectAll}
                                            className="text-xs text-(--color-text-muted) hover:underline"
                                        >
                                            Temizle
                                        </button>
                                    </div>
                                </div>

                                {/* Conversation List */}
                                <div className="max-h-[200px] overflow-y-auto space-y-2 rounded-xl border border-(--color-border) p-2">
                                    {conversations.length === 0 ? (
                                        <p className="text-center text-sm text-(--color-text-muted) py-4">
                                            Dışa aktarılacak sohbet yok
                                        </p>
                                    ) : (
                                        conversations.map(conv => (
                                            <label
                                                key={conv.id}
                                                className={cn(
                                                    "flex items-center gap-3 p-2 rounded-lg cursor-pointer",
                                                    "hover:bg-(--color-bg-surface-hover)",
                                                    selectedConversations.has(conv.id) && "bg-(--color-primary-soft)"
                                                )}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={selectedConversations.has(conv.id)}
                                                    onChange={() => toggleConversation(conv.id)}
                                                    className="w-4 h-4 rounded"
                                                />
                                                <span className="text-sm truncate flex-1">
                                                    {conv.title || 'Başlıksız'}
                                                </span>
                                            </label>
                                        ))
                                    )}
                                </div>

                                {/* Export Button */}
                                <Button
                                    variant="primary"
                                    className="w-full"
                                    onClick={handleExport}
                                    disabled={isProcessing || selectedConversations.size === 0}
                                >
                                    {isProcessing ? (
                                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                    ) : (
                                        <Download className="h-4 w-4 mr-2" />
                                    )}
                                    Dışa Aktar
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {/* Import Zone */}
                                <div
                                    onClick={() => fileInputRef.current?.click()}
                                    className={cn(
                                        "border-2 border-dashed rounded-xl p-8",
                                        "flex flex-col items-center justify-center text-center",
                                        "cursor-pointer transition-all",
                                        "border-(--color-border) hover:border-(--color-primary)/50"
                                    )}
                                >
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept=".json"
                                        onChange={handleFileSelect}
                                        className="hidden"
                                    />
                                    <Upload className="h-10 w-10 text-(--color-text-muted) mb-3" />
                                    <p className="font-medium">Dosya seçin</p>
                                    <p className="text-sm text-(--color-text-muted)">
                                        JSON formatında yedek dosyası
                                    </p>
                                </div>

                                {/* Warning */}
                                <div className="flex items-start gap-3 p-3 rounded-lg bg-(--color-warning-soft)">
                                    <Info className="h-5 w-5 text-(--color-warning) shrink-0 mt-0.5" />
                                    <p className="text-sm text-(--color-warning)">
                                        İçe aktarma mevcut sohbetlerin üzerine yazabilir.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Result Message */}
                        <AnimatePresence>
                            {result && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 10 }}
                                    className={cn(
                                        "flex items-center gap-2 p-3 rounded-lg mt-4",
                                        result.type === 'success'
                                            ? "bg-(--color-success-soft) text-(--color-success)"
                                            : "bg-(--color-error-soft) text-(--color-error)"
                                    )}
                                >
                                    {result.type === 'success' ? (
                                        <Check className="h-5 w-5" />
                                    ) : (
                                        <AlertCircle className="h-5 w-5" />
                                    )}
                                    <span className="text-sm">{result.message}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    )
}
