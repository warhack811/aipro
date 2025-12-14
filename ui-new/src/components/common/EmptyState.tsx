/**
 * Empty State Components
 * 
 * Beautiful empty states for various scenarios
 */

import { motion } from 'framer-motion'
import {
    MessageSquare,
    Search,
    FolderOpen,
    Image,
    Brain,
    Wifi,
    WifiOff,
    Plus,
    RefreshCw
} from 'lucide-react'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface EmptyStateProps {
    icon?: React.ReactNode
    title: string
    description?: string
    action?: {
        label: string
        onClick: () => void
        icon?: React.ReactNode
    }
    secondaryAction?: {
        label: string
        onClick: () => void
    }
    className?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// BASE EMPTY STATE
// ─────────────────────────────────────────────────────────────────────────────

export function EmptyState({
    icon,
    title,
    description,
    action,
    secondaryAction,
    className
}: EmptyStateProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "flex flex-col items-center justify-center py-16 px-6 text-center",
                className
            )}
        >
            {icon && (
                <motion.div
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1, type: "spring" }}
                    className="w-20 h-20 rounded-2xl bg-(--color-bg-surface) border border-(--color-border) flex items-center justify-center mb-6"
                >
                    <div className="text-(--color-text-muted)">
                        {icon}
                    </div>
                </motion.div>
            )}

            <h3 className="text-lg font-display font-semibold mb-2">
                {title}
            </h3>

            {description && (
                <p className="text-sm text-(--color-text-muted) max-w-sm mb-6">
                    {description}
                </p>
            )}

            {action && (
                <div className="flex gap-3">
                    <Button
                        variant="primary"
                        onClick={action.onClick}
                        leftIcon={action.icon}
                    >
                        {action.label}
                    </Button>

                    {secondaryAction && (
                        <Button
                            variant="outline"
                            onClick={secondaryAction.onClick}
                        >
                            {secondaryAction.label}
                        </Button>
                    )}
                </div>
            )}
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// PRESET EMPTY STATES
// ─────────────────────────────────────────────────────────────────────────────

export function NoConversations({ onNewChat }: { onNewChat: () => void }) {
    return (
        <EmptyState
            icon={<MessageSquare className="h-10 w-10" />}
            title="Henüz sohbet yok"
            description="Yeni bir sohbet başlatarak AI asistanınızla konuşmaya başlayın."
            action={{
                label: "Yeni Sohbet",
                onClick: onNewChat,
                icon: <Plus className="h-4 w-4" />
            }}
        />
    )
}

export function NoSearchResults({ query, onClear }: { query: string; onClear: () => void }) {
    return (
        <EmptyState
            icon={<Search className="h-10 w-10" />}
            title="Sonuç bulunamadı"
            description={`"${query}" için sonuç bulunamadı. Farklı kelimeler deneyin.`}
            action={{
                label: "Aramayı Temizle",
                onClick: onClear,
                icon: <RefreshCw className="h-4 w-4" />
            }}
        />
    )
}

export function NoMemories({ onAdd }: { onAdd: () => void }) {
    return (
        <EmptyState
            icon={<Brain className="h-10 w-10" />}
            title="Henüz anı yok"
            description="AI asistanınızın hatırlamasını istediğiniz bilgileri ekleyin."
            action={{
                label: "Anı Ekle",
                onClick: onAdd,
                icon: <Plus className="h-4 w-4" />
            }}
        />
    )
}

export function NoImages({ onGenerate }: { onGenerate: () => void }) {
    return (
        <EmptyState
            icon={<Image className="h-10 w-10" />}
            title="Galeri boş"
            description="Henüz oluşturulmuş görsel yok. Sohbet içinde görsel oluşturabilirsiniz."
            action={{
                label: "Görsel Oluştur",
                onClick: onGenerate,
                icon: <Plus className="h-4 w-4" />
            }}
        />
    )
}

export function NoFiles() {
    return (
        <EmptyState
            icon={<FolderOpen className="h-10 w-10" />}
            title="Dosya yok"
            description="Henüz yüklenmiş dosya bulunmuyor."
        />
    )
}

export function Offline({ onRetry }: { onRetry: () => void }) {
    return (
        <EmptyState
            icon={<WifiOff className="h-10 w-10" />}
            title="Bağlantı kesildi"
            description="İnternet bağlantınızı kontrol edin ve tekrar deneyin."
            action={{
                label: "Tekrar Dene",
                onClick: onRetry,
                icon: <RefreshCw className="h-4 w-4" />
            }}
        />
    )
}

export function ConnectionError({ onRetry }: { onRetry: () => void }) {
    return (
        <EmptyState
            icon={<Wifi className="h-10 w-10" />}
            title="Sunucuya bağlanılamıyor"
            description="Sunucu ile bağlantı kurulamadı. Lütfen daha sonra tekrar deneyin."
            action={{
                label: "Tekrar Dene",
                onClick: onRetry,
                icon: <RefreshCw className="h-4 w-4" />
            }}
        />
    )
}
