/**
 * MultiModalInput Component
 * 
 * Combined image + text input for chat:
 * - Image preview with remove
 * - Drag & drop images
 * - Paste from clipboard
 * - Multiple images
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Image as ImageIcon, X, Plus, Camera, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface ImageAttachment {
    id: string
    file: File
    preview: string
    uploading?: boolean
}

interface MultiModalInputProps {
    images: ImageAttachment[]
    onImagesChange: (images: ImageAttachment[]) => void
    maxImages?: number
    disabled?: boolean
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export function MultiModalInput({
    images,
    onImagesChange,
    maxImages = 4,
    disabled = false
}: MultiModalInputProps) {
    const [isDragOver, setIsDragOver] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Handle paste from clipboard
    useEffect(() => {
        const handlePaste = (e: ClipboardEvent) => {
            if (disabled || images.length >= maxImages) return

            const items = e.clipboardData?.items
            if (!items) return

            for (const item of items) {
                if (item.type.startsWith('image/')) {
                    const file = item.getAsFile()
                    if (file) {
                        addImage(file)
                    }
                }
            }
        }

        document.addEventListener('paste', handlePaste)
        return () => document.removeEventListener('paste', handlePaste)
    }, [images.length, maxImages, disabled])

    const addImage = useCallback((file: File) => {
        if (images.length >= maxImages) return

        const preview = URL.createObjectURL(file)
        const newImage: ImageAttachment = {
            id: `img-${Date.now()}-${Math.random()}`,
            file,
            preview
        }

        onImagesChange([...images, newImage])
    }, [images, maxImages, onImagesChange])

    const removeImage = useCallback((id: string) => {
        const image = images.find(img => img.id === id)
        if (image) {
            URL.revokeObjectURL(image.preview)
        }
        onImagesChange(images.filter(img => img.id !== id))
    }, [images, onImagesChange])

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        if (!disabled) setIsDragOver(true)
    }, [disabled])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)

        if (disabled) return

        const files = Array.from(e.dataTransfer.files)
            .filter(file => file.type.startsWith('image/'))
            .slice(0, maxImages - images.length)

        files.forEach(addImage)
    }, [disabled, images.length, maxImages, addImage])

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files) return

        const files = Array.from(e.target.files)
            .filter(file => file.type.startsWith('image/'))
            .slice(0, maxImages - images.length)

        files.forEach(addImage)

        // Reset input
        e.target.value = ''
    }, [images.length, maxImages, addImage])

    if (images.length === 0) {
        return null // Don't show anything if no images
    }

    return (
        <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
                "flex flex-wrap gap-2 p-2 rounded-xl mb-2",
                "bg-(--color-bg) border border-(--color-border)",
                isDragOver && "border-(--color-primary) bg-(--color-primary-soft)"
            )}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileSelect}
                className="hidden"
            />

            {/* Image Previews */}
            <AnimatePresence>
                {images.map(image => (
                    <motion.div
                        key={image.id}
                        layout
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="relative group"
                    >
                        <img
                            src={image.preview}
                            alt="Upload preview"
                            className="h-16 w-16 object-cover rounded-lg"
                        />

                        {/* Loading overlay */}
                        {image.uploading && (
                            <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
                                <Loader2 className="h-5 w-5 text-white animate-spin" />
                            </div>
                        )}

                        {/* Remove button */}
                        <button
                            onClick={() => removeImage(image.id)}
                            className={cn(
                                "absolute -top-1.5 -right-1.5 p-1 rounded-full",
                                "bg-(--color-error) text-white",
                                "opacity-0 group-hover:opacity-100 transition-opacity",
                                "hover:bg-(--color-error)/80"
                            )}
                        >
                            <X className="h-3 w-3" />
                        </button>
                    </motion.div>
                ))}
            </AnimatePresence>

            {/* Add more button */}
            {images.length < maxImages && !disabled && (
                <button
                    onClick={() => fileInputRef.current?.click()}
                    className={cn(
                        "h-16 w-16 rounded-lg border-2 border-dashed",
                        "border-(--color-border) hover:border-(--color-primary)",
                        "flex items-center justify-center text-(--color-text-muted)",
                        "hover:text-(--color-primary) transition-colors"
                    )}
                >
                    <Plus className="h-5 w-5" />
                </button>
            )}
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// ADD IMAGE BUTTON (for input area)
// ─────────────────────────────────────────────────────────────────────────────

interface AddImageButtonProps {
    onClick: () => void
    hasImages?: boolean
    disabled?: boolean
}

export function AddImageButton({ onClick, hasImages, disabled }: AddImageButtonProps) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                "p-2 rounded-lg transition-colors",
                disabled && "opacity-50 cursor-not-allowed",
                hasImages
                    ? "bg-(--color-secondary-soft) text-(--color-secondary)"
                    : "text-(--color-text-muted) hover:bg-(--color-bg-surface) hover:text-(--color-text)"
            )}
            title="Görsel ekle"
        >
            <ImageIcon className="h-5 w-5" />
        </button>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// USE MULTI MODAL HOOK
// ─────────────────────────────────────────────────────────────────────────────

export function useMultiModal() {
    const [images, setImages] = useState<ImageAttachment[]>([])
    const fileInputRef = useRef<HTMLInputElement>(null)

    const addImage = useCallback((file: File) => {
        const preview = URL.createObjectURL(file)
        const newImage: ImageAttachment = {
            id: `img-${Date.now()}-${Math.random()}`,
            file,
            preview
        }
        setImages(prev => [...prev, newImage])
    }, [])

    const removeImage = useCallback((id: string) => {
        setImages(prev => {
            const image = prev.find(img => img.id === id)
            if (image) {
                URL.revokeObjectURL(image.preview)
            }
            return prev.filter(img => img.id !== id)
        })
    }, [])

    const clearImages = useCallback(() => {
        images.forEach(img => URL.revokeObjectURL(img.preview))
        setImages([])
    }, [images])

    const openFilePicker = useCallback(() => {
        fileInputRef.current?.click()
    }, [])

    const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files) return

        Array.from(e.target.files)
            .filter(file => file.type.startsWith('image/'))
            .slice(0, 4 - images.length)
            .forEach(addImage)

        e.target.value = ''
    }, [images.length, addImage])

    return {
        images,
        setImages,
        addImage,
        removeImage,
        clearImages,
        openFilePicker,
        handleFileChange,
        fileInputRef,
        hasImages: images.length > 0
    }
}
