/**
 * FileUpload Component
 * 
 * Premium drag & drop file upload with:
 * - Drag & drop zone
 * - File preview
 * - Progress indicator
 * - Multiple file support
 */

import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Upload, X, FileText, File as FileIcon,
    CheckCircle, AlertCircle, Loader2, Paperclip
} from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { documentApi } from '@/api'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface UploadedFile {
    id: string
    file: File
    status: 'pending' | 'uploading' | 'success' | 'error'
    progress: number
    error?: string
    chunks?: number
}

interface FileUploadProps {
    onUploadComplete?: (file: UploadedFile) => void
    onClose?: () => void
    maxFiles?: number
    acceptedTypes?: string[]
    conversationId?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export function FileUpload({
    onUploadComplete,
    onClose,
    maxFiles = 5,
    acceptedTypes = ['.pdf', '.txt'],
    conversationId
}: FileUploadProps) {
    const [files, setFiles] = useState<UploadedFile[]>([])
    const [isDragOver, setIsDragOver] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Upload mutation
    const uploadMutation = useMutation({
        mutationFn: async (file: File) => {
            return documentApi.uploadDocument(file)
        },
        onSuccess: (_data, variables) => {
            setFiles(prev => prev.map(f =>
                f.file === variables
                    ? { ...f, status: 'success' as const, progress: 100 }
                    : f
            ))
        },
        onError: (error, variables) => {
            setFiles(prev => prev.map(f =>
                f.file === variables
                    ? { ...f, status: 'error' as const, error: (error as Error).message }
                    : f
            ))
        }
    })

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)

        const droppedFiles = Array.from(e.dataTransfer.files)
        addFiles(droppedFiles)
    }, [])

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            addFiles(Array.from(e.target.files))
        }
    }, [])

    const addFiles = useCallback((newFiles: File[]) => {
        const validFiles = newFiles.filter(file => {
            const ext = '.' + file.name.split('.').pop()?.toLowerCase()
            return acceptedTypes.includes(ext)
        }).slice(0, maxFiles - files.length)

        const uploadFiles: UploadedFile[] = validFiles.map(file => ({
            id: `file-${Date.now()}-${Math.random()}`,
            file,
            status: 'pending' as const,
            progress: 0
        }))

        setFiles(prev => [...prev, ...uploadFiles])

        // Start uploading
        uploadFiles.forEach(uf => {
            setFiles(prev => prev.map(f =>
                f.id === uf.id ? { ...f, status: 'uploading' as const } : f
            ))
            uploadMutation.mutate(uf.file)
        })
    }, [files.length, maxFiles, acceptedTypes, uploadMutation])

    const removeFile = useCallback((id: string) => {
        setFiles(prev => prev.filter(f => f.id !== id))
    }, [])

    const successCount = files.filter(f => f.status === 'success').length
    const errorCount = files.filter(f => f.status === 'error').length
    const uploadingCount = files.filter(f => f.status === 'uploading').length

    return (
        <div className="space-y-4">
            {/* Drop Zone */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                    "relative border-2 border-dashed rounded-2xl p-8",
                    "flex flex-col items-center justify-center text-center",
                    "cursor-pointer transition-all duration-200",
                    isDragOver
                        ? "border-(--color-primary) bg-(--color-primary-soft)"
                        : "border-(--color-border) hover:border-(--color-primary)/50 hover:bg-(--color-bg-surface)"
                )}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept={acceptedTypes.join(',')}
                    onChange={handleFileSelect}
                    className="hidden"
                />

                <motion.div
                    animate={{ scale: isDragOver ? 1.1 : 1 }}
                    className="w-16 h-16 rounded-2xl bg-(--color-bg-surface) border border-(--color-border) flex items-center justify-center mb-4"
                >
                    <Upload className={cn(
                        "h-8 w-8 transition-colors",
                        isDragOver ? "text-(--color-primary)" : "text-(--color-text-muted)"
                    )} />
                </motion.div>

                <h3 className="font-medium mb-1">
                    {isDragOver ? "Dosyaları bırakın" : "Dosya yükleyin"}
                </h3>
                <p className="text-sm text-(--color-text-muted)">
                    Sürükleyin veya tıklayarak seçin
                </p>
                <p className="text-xs text-(--color-text-muted) mt-2">
                    {acceptedTypes.join(', ')} desteklenir • Maks. {maxFiles} dosya
                </p>
            </div>

            {/* File List */}
            <AnimatePresence>
                {files.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-2"
                    >
                        {files.map(file => (
                            <FileItem
                                key={file.id}
                                file={file}
                                onRemove={() => removeFile(file.id)}
                            />
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Summary */}
            {files.length > 0 && (
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4">
                        {successCount > 0 && (
                            <span className="text-(--color-success) flex items-center gap-1">
                                <CheckCircle className="h-4 w-4" />
                                {successCount} başarılı
                            </span>
                        )}
                        {errorCount > 0 && (
                            <span className="text-(--color-error) flex items-center gap-1">
                                <AlertCircle className="h-4 w-4" />
                                {errorCount} hatalı
                            </span>
                        )}
                        {uploadingCount > 0 && (
                            <span className="text-(--color-text-muted) flex items-center gap-1">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                {uploadingCount} yükleniyor
                            </span>
                        )}
                    </div>

                    {onClose && (
                        <Button variant="primary" size="sm" onClick={onClose}>
                            Tamam
                        </Button>
                    )}
                </div>
            )}
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// FILE ITEM
// ─────────────────────────────────────────────────────────────────────────────

interface FileItemProps {
    file: UploadedFile
    onRemove: () => void
}

function FileItem({ file, onRemove }: FileItemProps) {
    const ext = file.file.name.split('.').pop()?.toLowerCase()
    const Icon = ext === 'pdf' ? FileText : FileIcon

    const formatSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    return (
        <motion.div
            layout
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            className={cn(
                "flex items-center gap-3 p-3 rounded-xl",
                "bg-(--color-bg-surface) border",
                file.status === 'error'
                    ? "border-(--color-error)/30"
                    : file.status === 'success'
                        ? "border-(--color-success)/30"
                        : "border-(--color-border)"
            )}
        >
            {/* Icon */}
            <div className={cn(
                "p-2 rounded-lg",
                file.status === 'error'
                    ? "bg-(--color-error-soft)"
                    : file.status === 'success'
                        ? "bg-(--color-success-soft)"
                        : "bg-(--color-bg)"
            )}>
                <Icon className={cn(
                    "h-5 w-5",
                    file.status === 'error'
                        ? "text-(--color-error)"
                        : file.status === 'success'
                            ? "text-(--color-success)"
                            : "text-(--color-text-muted)"
                )} />
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{file.file.name}</span>
                    <span className="text-xs text-(--color-text-muted)">
                        {formatSize(file.file.size)}
                    </span>
                </div>

                {file.status === 'uploading' && (
                    <div className="mt-1.5 h-1 rounded-full bg-(--color-bg) overflow-hidden">
                        <motion.div
                            className="h-full bg-(--color-primary)"
                            initial={{ width: 0 }}
                            animate={{ width: '100%' }}
                            transition={{ duration: 2, ease: 'easeInOut' }}
                        />
                    </div>
                )}

                {file.status === 'error' && file.error && (
                    <p className="text-xs text-(--color-error) mt-0.5">{file.error}</p>
                )}

                {file.status === 'success' && (
                    <p className="text-xs text-(--color-success) mt-0.5">
                        Yüklendi ve işlendi
                    </p>
                )}
            </div>

            {/* Status Icon / Remove */}
            {file.status === 'uploading' ? (
                <Loader2 className="h-5 w-5 text-(--color-primary) animate-spin" />
            ) : file.status === 'success' ? (
                <CheckCircle className="h-5 w-5 text-(--color-success)" />
            ) : (
                <button
                    onClick={onRemove}
                    className="p-1 rounded hover:bg-(--color-error-soft) text-(--color-text-muted) hover:text-(--color-error)"
                >
                    <X className="h-4 w-4" />
                </button>
            )}
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPACT UPLOAD BUTTON (for input area)
// ─────────────────────────────────────────────────────────────────────────────

interface CompactUploadButtonProps {
    onClick: () => void
    hasFiles?: boolean
}

export function CompactUploadButton({ onClick, hasFiles }: CompactUploadButtonProps) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "p-2 rounded-lg transition-colors",
                hasFiles
                    ? "bg-(--color-primary-soft) text-(--color-primary)"
                    : "text-(--color-text-muted) hover:bg-(--color-bg-surface) hover:text-(--color-text)"
            )}
            title="Dosya yükle"
        >
            <Paperclip className="h-5 w-5" />
        </button>
    )
}
