/**
 * Memory Manager Component
 * 
 * CRUD interface for user memories
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Brain, Plus, Edit2, Trash2, X, Lightbulb, Search,
    Loader2, AlertCircle, Check
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { memoryApi } from '@/api'
import { Button, Input, Textarea } from '@/components/ui'
import { cn, formatDate } from '@/lib/utils'
import type { Memory } from '@/types'

interface MemoryManagerProps {
    isOpen: boolean
    onClose: () => void
}

export function MemoryManager({ isOpen, onClose }: MemoryManagerProps) {
    const queryClient = useQueryClient()
    const [searchQuery, setSearchQuery] = useState('')
    const [isAdding, setIsAdding] = useState(false)
    const [editingId, setEditingId] = useState<string | null>(null)
    const [newMemoryText, setNewMemoryText] = useState('')
    const [newMemoryImportance, setNewMemoryImportance] = useState(0.5)

    // Fetch memories
    const { data: memories = [], isLoading, error } = useQuery({
        queryKey: ['memories'],
        queryFn: memoryApi.getMemories,
        enabled: isOpen,
    })

    // Create mutation
    const createMutation = useMutation({
        mutationFn: (data: { text: string; importance: number }) =>
            memoryApi.createMemory(data.text, data.importance),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['memories'] })
            setNewMemoryText('')
            setNewMemoryImportance(0.5)
            setIsAdding(false)
        },
    })

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: memoryApi.deleteMemory,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['memories'] })
        },
    })

    // Filter memories
    const filteredMemories = memories.filter((m: Memory) =>
        m.text.toLowerCase().includes(searchQuery.toLowerCase())
    )

    // Sort by importance
    const sortedMemories = [...filteredMemories].sort((a: Memory, b: Memory) =>
        b.importance - a.importance
    )

    const handleCreate = () => {
        if (!newMemoryText.trim()) return
        createMutation.mutate({
            text: newMemoryText.trim(),
            importance: newMemoryImportance
        })
    }

    if (!isOpen) return null

    return (
        <>
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-(--z-modal-backdrop)"
            />

            {/* Modal */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                className={cn(
                    "fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
                    "w-full max-w-2xl max-h-[85vh]",
                    "bg-(--color-bg-surface) border border-(--color-border)",
                    "rounded-2xl shadow-2xl overflow-hidden",
                    "z-(--z-modal) flex flex-col"
                )}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-(--color-border)">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-(--gradient-brand)">
                            <Brain className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-lg font-display font-semibold">Hafıza Yönetimi</h2>
                            <p className="text-sm text-(--color-text-muted)">
                                AI'ın hatırlamasını istediğiniz bilgiler
                            </p>
                        </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                {/* Search & Add */}
                <div className="px-6 py-4 border-b border-(--color-border) space-y-3">
                    <div className="flex gap-2">
                        <Input
                            placeholder="Hafızalarda ara..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            leftIcon={<Search className="h-4 w-4" />}
                            className="flex-1"
                        />
                        <Button
                            variant="primary"
                            onClick={() => setIsAdding(true)}
                            leftIcon={<Plus className="h-4 w-4" />}
                        >
                            Ekle
                        </Button>
                    </div>

                    {/* Add New Memory Form */}
                    <AnimatePresence>
                        {isAdding && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="p-4 rounded-xl bg-(--color-bg) border border-(--color-border)"
                            >
                                <Textarea
                                    placeholder="Örn: Benim adım Ahmet ve yazılım mühendisiyim..."
                                    value={newMemoryText}
                                    onChange={(e) => setNewMemoryText(e.target.value)}
                                    rows={3}
                                    className="mb-3"
                                />

                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <label className="text-sm text-(--color-text-muted)">
                                            Önem:
                                        </label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="1"
                                            step="0.1"
                                            value={newMemoryImportance}
                                            onChange={(e) => setNewMemoryImportance(parseFloat(e.target.value))}
                                            className="w-24 accent-(--color-primary)"
                                        />
                                        <span className="text-sm font-medium">
                                            {Math.round(newMemoryImportance * 100)}%
                                        </span>
                                    </div>

                                    <div className="flex gap-2">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => {
                                                setIsAdding(false)
                                                setNewMemoryText('')
                                            }}
                                        >
                                            İptal
                                        </Button>
                                        <Button
                                            variant="primary"
                                            size="sm"
                                            onClick={handleCreate}
                                            isLoading={createMutation.isPending}
                                            disabled={!newMemoryText.trim()}
                                        >
                                            Kaydet
                                        </Button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Memory List */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-(--color-primary)" />
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center py-12 text-(--color-error)">
                            <AlertCircle className="h-8 w-8 mb-2" />
                            <p>Hafızalar yüklenemedi</p>
                        </div>
                    ) : sortedMemories.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-(--color-text-muted)">
                            <Brain className="h-12 w-12 mb-3 opacity-50" />
                            <p className="text-center">
                                {searchQuery
                                    ? 'Arama sonucu bulunamadı'
                                    : 'Henüz hafıza eklenmemiş'}
                            </p>
                            <p className="text-sm text-center mt-1">
                                AI'ın sizin hakkınızda hatırlamasını istediğiniz bilgileri ekleyin
                            </p>
                        </div>
                    ) : (
                        sortedMemories.map((memory: Memory) => (
                            <MemoryCard
                                key={memory.id}
                                memory={memory}
                                isEditing={editingId === memory.id}
                                onEdit={() => setEditingId(memory.id)}
                                onCancelEdit={() => setEditingId(null)}
                                onDelete={() => deleteMutation.mutate(memory.id)}
                                isDeleting={deleteMutation.isPending}
                            />
                        ))
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-3 border-t border-(--color-border) bg-(--color-bg)">
                    <p className="text-xs text-(--color-text-muted) text-center">
                        {memories.length} hafıza kayıtlı
                    </p>
                </div>
            </motion.div>
        </>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

interface MemoryCardProps {
    memory: Memory
    isEditing: boolean
    onEdit: () => void
    onCancelEdit: () => void
    onDelete: () => void
    isDeleting: boolean
}

function MemoryCard({
    memory,
    isEditing,
    onEdit,
    onCancelEdit,
    onDelete,
    isDeleting
}: MemoryCardProps) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "group p-4 rounded-xl border transition-all",
                "bg-(--color-bg) border-(--color-border)",
                "hover:border-(--color-primary)/30"
            )}
        >
            <div className="flex items-start gap-3">
                {/* Importance indicator */}
                <div className={cn(
                    "p-2 rounded-lg shrink-0",
                    memory.importance > 0.7
                        ? "bg-(--color-primary-soft) text-(--color-primary)"
                        : memory.importance > 0.4
                            ? "bg-(--color-accent-soft) text-(--color-accent)"
                            : "bg-(--color-bg-surface) text-(--color-text-muted)"
                )}>
                    <Lightbulb className="h-4 w-4" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm leading-relaxed">{memory.text}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-(--color-text-muted)">
                        <span>{formatDate(memory.createdAt)}</span>
                        <span>•</span>
                        <span>Önem: {Math.round(memory.importance * 100)}%</span>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={onEdit}
                    >
                        <Edit2 className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={onDelete}
                        disabled={isDeleting}
                        className="hover:bg-(--color-error-soft) hover:text-(--color-error)"
                    >
                        {isDeleting ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                        )}
                    </Button>
                </div>
            </div>
        </motion.div>
    )
}
