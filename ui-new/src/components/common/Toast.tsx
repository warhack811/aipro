/**
 * Toast Notification System
 * 
 * Premium toast notifications with animations
 */

import { useState, useEffect, useCallback, createContext, useContext } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn, generateId } from '@/lib/utils'
import type { Toast } from '@/types'

// ─────────────────────────────────────────────────────────────────────────────
// Toast Context
// ─────────────────────────────────────────────────────────────────────────────

interface ToastContextType {
    toasts: Toast[]
    addToast: (toast: Omit<Toast, 'id'>) => string
    removeToast: (id: string) => void
    success: (title: string, message?: string) => void
    error: (title: string, message?: string) => void
    warning: (title: string, message?: string) => void
    info: (title: string, message?: string) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

export function useToast() {
    const context = useContext(ToastContext)
    if (!context) {
        throw new Error('useToast must be used within ToastProvider')
    }
    return context
}

// ─────────────────────────────────────────────────────────────────────────────
// Toast Provider
// ─────────────────────────────────────────────────────────────────────────────

interface ToastProviderProps {
    children: React.ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
    const [toasts, setToasts] = useState<Toast[]>([])

    const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
        const id = generateId('toast')
        const newToast: Toast = { ...toast, id }

        setToasts(prev => [...prev, newToast])

        // Auto-remove after duration
        const duration = toast.duration ?? 5000
        if (duration > 0) {
            setTimeout(() => {
                removeToast(id)
            }, duration)
        }

        return id
    }, [])

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    const success = useCallback((title: string, message?: string) => {
        addToast({ type: 'success', title, message })
    }, [addToast])

    const error = useCallback((title: string, message?: string) => {
        addToast({ type: 'error', title, message, duration: 8000 })
    }, [addToast])

    const warning = useCallback((title: string, message?: string) => {
        addToast({ type: 'warning', title, message })
    }, [addToast])

    const info = useCallback((title: string, message?: string) => {
        addToast({ type: 'info', title, message })
    }, [addToast])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Toast Container & Item
// ─────────────────────────────────────────────────────────────────────────────

interface ToastContainerProps {
    toasts: Toast[]
    onRemove: (id: string) => void
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
    return (
        <div
            className={cn(
                "fixed bottom-4 right-4 z-(--z-toast)",
                "flex flex-col gap-2 max-w-md w-full pointer-events-none"
            )}
        >
            <AnimatePresence mode="popLayout">
                {toasts.map(toast => (
                    <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
                ))}
            </AnimatePresence>
        </div>
    )
}

interface ToastItemProps {
    toast: Toast
    onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
    const [progress, setProgress] = useState(100)
    const duration = toast.duration ?? 5000

    useEffect(() => {
        if (duration <= 0) return

        const interval = setInterval(() => {
            setProgress(prev => {
                const newProgress = prev - (100 / (duration / 100))
                return newProgress <= 0 ? 0 : newProgress
            })
        }, 100)

        return () => clearInterval(interval)
    }, [duration])

    const icons = {
        success: <CheckCircle className="h-5 w-5" />,
        error: <AlertCircle className="h-5 w-5" />,
        warning: <AlertTriangle className="h-5 w-5" />,
        info: <Info className="h-5 w-5" />,
    }

    const colors = {
        success: 'text-(--color-success) bg-(--color-success-soft)',
        error: 'text-(--color-error) bg-(--color-error-soft)',
        warning: 'text-(--color-warning) bg-(--color-warning-soft)',
        info: 'text-(--color-info) bg-(--color-info-soft)',
    }

    const progressColors = {
        success: 'bg-(--color-success)',
        error: 'bg-(--color-error)',
        warning: 'bg-(--color-warning)',
        info: 'bg-(--color-info)',
    }

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.9 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={cn(
                "relative overflow-hidden pointer-events-auto",
                "bg-(--color-bg-surface) border border-(--color-border)",
                "rounded-xl shadow-lg"
            )}
        >
            <div className="flex items-start gap-3 p-4">
                {/* Icon */}
                <div className={cn("p-1.5 rounded-lg shrink-0", colors[toast.type])}>
                    {icons[toast.type]}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm">{toast.title}</p>
                    {toast.message && (
                        <p className="text-sm text-(--color-text-muted) mt-0.5">
                            {toast.message}
                        </p>
                    )}
                </div>

                {/* Close Button */}
                <button
                    onClick={() => onRemove(toast.id)}
                    className="p-1 rounded-lg hover:bg-(--color-bg-surface-hover) text-(--color-text-muted) transition-colors"
                >
                    <X className="h-4 w-4" />
                </button>
            </div>

            {/* Progress bar */}
            {duration > 0 && (
                <div className="h-1 bg-(--color-border)">
                    <motion.div
                        className={cn("h-full", progressColors[toast.type])}
                        initial={{ width: '100%' }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.1 }}
                    />
                </div>
            )}
        </motion.div>
    )
}
