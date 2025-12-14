/**
 * ImageCompletedCard Component
 * 
 * Tamamlanmış görsel kartı.
 * Chat içinde bot mesajı olarak görünür.
 * 
 * Özellikler:
 * - Resim önizlemesi (tıklanabilir - lightbox açar)
 * - Prompt gösterimi
 * - Aksiyon butonları: Yeniden oluştur, İndir, Kopyala, Büyüt
 */

import { useState, useCallback, memo, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    RefreshCw,
    Download,
    Copy,
    ZoomIn,
    Check,
    ExternalLink,
    Sparkles
} from 'lucide-react'

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface ImageCompletedCardProps {
    imageUrl: string
    prompt: string
    onRegenerate?: (prompt: string) => void
    onOpenLightbox?: (imageUrl: string) => void
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export const ImageCompletedCard = memo(function ImageCompletedCard({
    imageUrl,
    prompt,
    onRegenerate,
    onOpenLightbox,
}: ImageCompletedCardProps) {
    const [isHovered, setIsHovered] = useState(false)
    const [isLoaded, setIsLoaded] = useState(false)
    const [copySuccess, setCopySuccess] = useState(false)
    const [isRegenerating, setIsRegenerating] = useState(false)
    const imageRef = useRef<HTMLImageElement>(null)

    // Truncate prompt for display
    const displayPrompt = prompt.length > 80
        ? prompt.slice(0, 80) + '...'
        : prompt

    // Handle image download
    const handleDownload = useCallback(async () => {
        try {
            const response = await fetch(imageUrl)
            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `mami-ai-${Date.now()}.png`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            window.URL.revokeObjectURL(url)
        } catch (error) {
            console.error('Download failed:', error)
        }
    }, [imageUrl])

    // Handle copy to clipboard
    const handleCopy = useCallback(async () => {
        try {
            const response = await fetch(imageUrl)
            const blob = await response.blob()
            await navigator.clipboard.write([
                new ClipboardItem({ [blob.type]: blob })
            ])
            setCopySuccess(true)
            setTimeout(() => setCopySuccess(false), 2000)
        } catch (error) {
            // Fallback: copy URL
            try {
                await navigator.clipboard.writeText(imageUrl)
                setCopySuccess(true)
                setTimeout(() => setCopySuccess(false), 2000)
            } catch (e) {
                console.error('Copy failed:', e)
            }
        }
    }, [imageUrl])

    // Handle regenerate
    const handleRegenerate = useCallback(async () => {
        if (isRegenerating || !onRegenerate) return
        setIsRegenerating(true)
        try {
            await onRegenerate(prompt)
        } finally {
            setTimeout(() => setIsRegenerating(false), 1000)
        }
    }, [prompt, onRegenerate, isRegenerating])

    // Handle lightbox
    const handleLightbox = useCallback(() => {
        if (onOpenLightbox) {
            onOpenLightbox(imageUrl)
        } else {
            // Fallback: open in new tab
            window.open(imageUrl, '_blank')
        }
    }, [imageUrl, onOpenLightbox])

    return (
        <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
            className="image-completed-card"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Card Container */}
            <div className={`
                relative overflow-hidden rounded-2xl
                bg-linear-to-br from-(--color-surface) to-(--color-surface-hover)
                border border-(--color-border)
                transition-all duration-300
                ${isHovered ? 'border-(--color-primary)/40 shadow-xl shadow-(--color-primary)/5' : ''}
            `}>
                {/* Success Sparkle (on load) */}
                <AnimatePresence>
                    {!isLoaded && (
                        <motion.div
                            className="absolute inset-0 flex items-center justify-center bg-(--color-surface) z-10"
                            exit={{ opacity: 0 }}
                        >
                            <Sparkles className="w-8 h-8 text-(--color-primary) animate-pulse" />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Image Container */}
                <div
                    className="relative cursor-pointer group"
                    onClick={handleLightbox}
                >
                    {/* Image */}
                    <motion.img
                        ref={imageRef}
                        src={imageUrl}
                        alt={prompt}
                        onLoad={() => setIsLoaded(true)}
                        initial={{ opacity: 0, scale: 1.02 }}
                        animate={{ opacity: isLoaded ? 1 : 0, scale: 1 }}
                        transition={{ duration: 0.4 }}
                        className="w-full rounded-t-2xl object-cover"
                        style={{ maxHeight: '400px' }}
                    />

                    {/* Hover Overlay */}
                    <motion.div
                        className="absolute inset-0 bg-transparent group-hover:bg-(--color-bg)/30 transition-colors duration-200 flex items-center justify-center"
                    >
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: isHovered ? 1 : 0, scale: isHovered ? 1 : 0.8 }}
                            transition={{ duration: 0.2 }}
                            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm text-white"
                        >
                            <ZoomIn className="w-4 h-4" />
                            <span className="text-sm font-medium">Büyüt</span>
                        </motion.div>
                    </motion.div>
                </div>

                {/* Content */}
                <div className="p-4 space-y-3">
                    {/* Prompt */}
                    <p className="text-sm text-(--color-text) leading-relaxed">
                        <Sparkles className="inline w-3.5 h-3.5 mr-1.5 text-(--color-primary)" />
                        {displayPrompt}
                    </p>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                        {/* Regenerate */}
                        {onRegenerate && (
                            <ActionButton
                                icon={RefreshCw}
                                label="Yeniden"
                                onClick={handleRegenerate}
                                isLoading={isRegenerating}
                                variant="primary"
                            />
                        )}

                        {/* Download */}
                        <ActionButton
                            icon={Download}
                            label="İndir"
                            onClick={handleDownload}
                        />

                        {/* Copy */}
                        <ActionButton
                            icon={copySuccess ? Check : Copy}
                            label={copySuccess ? 'Kopyalandı' : 'Kopyala'}
                            onClick={handleCopy}
                            isSuccess={copySuccess}
                        />

                        {/* Open in new tab */}
                        <ActionButton
                            icon={ExternalLink}
                            label="Aç"
                            onClick={() => window.open(imageUrl, '_blank')}
                        />
                    </div>
                </div>
            </div>
        </motion.div>
    )
})

// ═══════════════════════════════════════════════════════════════════════════
// ACTION BUTTON
// ═══════════════════════════════════════════════════════════════════════════

interface ActionButtonProps {
    icon: React.ComponentType<{ className?: string }>
    label: string
    onClick: () => void
    isLoading?: boolean
    isSuccess?: boolean
    variant?: 'default' | 'primary'
}

const ActionButton = memo(function ActionButton({
    icon: Icon,
    label,
    onClick,
    isLoading,
    isSuccess,
    variant = 'default',
}: ActionButtonProps) {
    return (
        <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            disabled={isLoading}
            className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                text-xs font-medium transition-all duration-200
                ${variant === 'primary'
                    ? 'bg-(--color-primary)/20 text-(--color-primary) hover:bg-(--color-primary)/30'
                    : 'bg-(--color-surface-hover) text-(--color-text-muted) hover:text-(--color-text) hover:bg-(--color-border)'
                }
                ${isSuccess ? 'bg-green-500/20 text-green-400' : ''}
                ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
        >
            <Icon className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{label}</span>
        </motion.button>
    )
})

export default ImageCompletedCard
