/**
 * Image Generation UI Component
 * 
 * Shows image generation progress and gallery
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Image, X, Download, Trash2, ZoomIn, Loader2,
    AlertCircle, CheckCircle, ExternalLink
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { imageApi } from '@/api'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { ImageJob } from '@/types'

interface ImageGalleryProps {
    isOpen: boolean
    onClose: () => void
}

export function ImageGallery({ isOpen, onClose }: ImageGalleryProps) {
    const [selectedImage, setSelectedImage] = useState<string | null>(null)

    // Fetch gallery images
    const { data, isLoading } = useQuery({
        queryKey: ['gallery'],
        queryFn: imageApi.getGallery,
        enabled: isOpen,
    })

    const images = data?.images || []

    if (!isOpen) return null

    return (
        <>
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="fixed inset-0 bg-black/70 backdrop-blur-sm z-(--z-modal-backdrop)"
            />

            {/* Modal */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={cn(
                    "fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
                    "w-full max-w-4xl max-h-[85vh]",
                    "bg-(--color-bg-surface) border border-(--color-border)",
                    "rounded-2xl shadow-2xl overflow-hidden",
                    "z-(--z-modal) flex flex-col"
                )}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-(--color-border)">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-linear-to-br from-pink-500 to-rose-500">
                            <Image className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-lg font-display font-semibold">Görsel Galeri</h2>
                            <p className="text-sm text-(--color-text-muted)">
                                {images.length} görsel
                            </p>
                        </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                {/* Gallery Grid */}
                <div className="flex-1 overflow-y-auto p-6">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-(--color-primary)" />
                        </div>
                    ) : images.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-(--color-text-muted)">
                            <Image className="h-16 w-16 mb-4 opacity-30" />
                            <p>Henüz görsel oluşturulmamış</p>
                            <p className="text-sm mt-1">"/görsel" komutu ile görsel oluşturabilirsiniz</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {images.map((img, index) => (
                                <motion.div
                                    key={img.image_url || index}
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="group relative aspect-square rounded-xl overflow-hidden cursor-pointer"
                                    onClick={() => setSelectedImage(img.image_url)}
                                >
                                    <img
                                        src={img.image_url}
                                        alt={img.prompt || `Generated ${index + 1}`}
                                        className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                                    />

                                    {/* Overlay */}
                                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex flex-col items-center justify-center p-2">
                                        <ZoomIn className="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                                        {img.prompt && (
                                            <p className="text-white text-xs mt-2 opacity-0 group-hover:opacity-100 line-clamp-2 text-center">
                                                {img.prompt}
                                            </p>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>
            </motion.div>

            {/* Lightbox */}
            <AnimatePresence>
                {selectedImage && (
                    <ImageLightbox
                        src={selectedImage}
                        onClose={() => setSelectedImage(null)}
                    />
                )}
            </AnimatePresence>
        </>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

interface ImageLightboxProps {
    src: string
    onClose: () => void
}

function ImageLightbox({ src, onClose }: ImageLightboxProps) {
    const handleDownload = async () => {
        const response = await fetch(src)
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `generated-${Date.now()}.png`
        a.click()
        window.URL.revokeObjectURL(url)
    }

    return (
        <>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="fixed inset-0 bg-black/90 z-(--z-max)"
            />

            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="fixed inset-4 md:inset-12 z-(--z-max) flex flex-col items-center justify-center"
            >
                <img
                    src={src}
                    alt="Full size"
                    className="max-w-full max-h-[calc(100%-60px)] object-contain rounded-lg shadow-2xl"
                />

                {/* Controls */}
                <div className="flex gap-2 mt-4">
                    <Button
                        variant="secondary"
                        onClick={handleDownload}
                        leftIcon={<Download className="h-4 w-4" />}
                    >
                        İndir
                    </Button>
                    <Button
                        variant="ghost"
                        onClick={onClose}
                    >
                        Kapat
                    </Button>
                </div>
            </motion.div>
        </>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

interface ImageProgressCardProps {
    job: ImageJob
}

export function ImageProgressCard({ job }: ImageProgressCardProps) {
    const getStatusIcon = () => {
        switch (job.status) {
            case 'queued':
                return <Loader2 className="h-4 w-4 animate-spin" />
            case 'processing':
                return <Loader2 className="h-4 w-4 animate-spin" />
            case 'complete':
                return <CheckCircle className="h-4 w-4 text-(--color-success)" />
            case 'error':
                return <AlertCircle className="h-4 w-4 text-(--color-error)" />
        }
    }

    const getStatusText = () => {
        switch (job.status) {
            case 'queued':
                return job.queuePosition ? `Sırada: ${job.queuePosition}` : 'Sırada bekliyor...'
            case 'processing':
                return `İşleniyor... ${Math.round(job.progress)}%`
            case 'complete':
                return 'Tamamlandı'
            case 'error':
                return 'Hata oluştu'
        }
    }

    return (
        <div className="bg-(--color-bg-surface) border border-(--color-border) rounded-2xl overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-(--color-border) flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-linear-to-br from-pink-500 to-rose-500">
                        <Image className="h-4 w-4 text-white" />
                    </div>
                    <span className="font-medium text-sm">Görsel Oluşturuluyor</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-(--color-text-muted)">
                    {getStatusIcon()}
                    <span>{getStatusText()}</span>
                </div>
            </div>

            {/* Preview Area */}
            <div className="p-4">
                <div className="relative h-48 rounded-xl overflow-hidden bg-(--color-bg) flex items-center justify-center">
                    {job.status === 'complete' && job.imageUrl ? (
                        <img
                            src={job.imageUrl}
                            alt="Generated"
                            className="w-full h-full object-cover animate-fade-in"
                        />
                    ) : job.status === 'error' ? (
                        <div className="text-center text-(--color-error)">
                            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                            <p className="text-sm">{job.error || 'Görsel oluşturulamadı'}</p>
                        </div>
                    ) : (
                        <>
                            {/* Animated placeholder */}
                            <div className="absolute inset-0 bg-linear-to-br from-pink-500/10 to-purple-500/10 animate-pulse" />

                            {/* Progress circle */}
                            <div className="relative">
                                <svg className="w-20 h-20 transform -rotate-90">
                                    <circle
                                        cx="40"
                                        cy="40"
                                        r="36"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                        fill="none"
                                        className="text-(--color-border)"
                                    />
                                    <circle
                                        cx="40"
                                        cy="40"
                                        r="36"
                                        stroke="url(#gradient)"
                                        strokeWidth="4"
                                        fill="none"
                                        strokeDasharray={`${2 * Math.PI * 36}`}
                                        strokeDashoffset={`${2 * Math.PI * 36 * (1 - job.progress / 100)}`}
                                        strokeLinecap="round"
                                        className="transition-all duration-300"
                                    />
                                    <defs>
                                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" stopColor="#ec4899" />
                                            <stop offset="100%" stopColor="#8b5cf6" />
                                        </linearGradient>
                                    </defs>
                                </svg>
                                <span className="absolute inset-0 flex items-center justify-center text-lg font-bold">
                                    {Math.round(job.progress)}%
                                </span>
                            </div>
                        </>
                    )}
                </div>

                {/* Prompt */}
                <p className="text-xs text-(--color-text-muted) mt-3 truncate">
                    {job.prompt}
                </p>
            </div>
        </div>
    )
}
