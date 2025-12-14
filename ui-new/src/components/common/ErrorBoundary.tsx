/**
 * Error Boundary Component
 * 
 * Premium error handling with graceful recovery
 */

import { Component, type ErrorInfo, type ReactNode } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// ERROR BOUNDARY CLASS COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

interface Props {
    children: ReactNode
    fallback?: ReactNode
    onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
    hasError: boolean
    error: Error | null
    errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props)
        this.state = { hasError: false, error: null, errorInfo: null }
    }

    static getDerivedStateFromError(error: Error): Partial<State> {
        return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        this.setState({ errorInfo })

        // Log to console in development
        console.error('ErrorBoundary caught an error:', error, errorInfo)

        // Call custom error handler if provided
        this.props.onError?.(error, errorInfo)

        // TODO: Report to error tracking service (Sentry, etc.)
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null })
    }

    handleReload = () => {
        window.location.reload()
    }

    handleGoHome = () => {
        window.location.href = '/'
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback
            }

            return (
                <ErrorFallback
                    error={this.state.error}
                    errorInfo={this.state.errorInfo}
                    onReset={this.handleReset}
                    onReload={this.handleReload}
                    onGoHome={this.handleGoHome}
                />
            )
        }

        return this.props.children
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// ERROR FALLBACK UI
// ─────────────────────────────────────────────────────────────────────────────

interface ErrorFallbackProps {
    error: Error | null
    errorInfo: ErrorInfo | null
    onReset: () => void
    onReload: () => void
    onGoHome: () => void
}

function ErrorFallback({
    error,
    errorInfo,
    onReset,
    onReload,
    onGoHome
}: ErrorFallbackProps) {
    const isDev = import.meta.env.DEV

    return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-(--color-bg)">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={cn(
                    "max-w-lg w-full p-8 rounded-3xl",
                    "bg-(--color-bg-surface) border border-(--color-border)",
                    "text-center"
                )}
            >
                {/* Error Icon */}
                <motion.div
                    initial={{ rotate: 0 }}
                    animate={{ rotate: [0, -10, 10, -10, 10, 0] }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-(--color-error-soft) flex items-center justify-center"
                >
                    <AlertTriangle className="h-10 w-10 text-(--color-error)" />
                </motion.div>

                {/* Title */}
                <h1 className="text-2xl font-display font-bold mb-2">
                    Bir Şeyler Ters Gitti
                </h1>

                <p className="text-(--color-text-muted) mb-6">
                    Beklenmeyen bir hata oluştu. Endişelenmeyin, verileriniz güvende.
                </p>

                {/* Error Details (Dev only) */}
                {isDev && error && (
                    <details className="mb-6 text-left">
                        <summary className="cursor-pointer text-sm text-(--color-text-muted) hover:text-(--color-text)">
                            <Bug className="inline h-4 w-4 mr-1" />
                            Teknik Detaylar (Geliştirici)
                        </summary>
                        <div className="mt-2 p-3 rounded-lg bg-(--color-bg) border border-(--color-error)/30 overflow-auto">
                            <p className="text-(--color-error) font-mono text-sm mb-2">
                                {error.name}: {error.message}
                            </p>
                            {errorInfo && (
                                <pre className="text-xs text-(--color-text-muted) whitespace-pre-wrap">
                                    {errorInfo.componentStack}
                                </pre>
                            )}
                        </div>
                    </details>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Button
                        variant="primary"
                        onClick={onReset}
                        leftIcon={<RefreshCw className="h-4 w-4" />}
                    >
                        Tekrar Dene
                    </Button>

                    <Button
                        variant="outline"
                        onClick={onReload}
                    >
                        Sayfayı Yenile
                    </Button>

                    <Button
                        variant="ghost"
                        onClick={onGoHome}
                        leftIcon={<Home className="h-4 w-4" />}
                    >
                        Ana Sayfa
                    </Button>
                </div>

                {/* Support Link */}
                <p className="mt-6 text-xs text-(--color-text-muted)">
                    Sorun devam ederse{' '}
                    <a href="mailto:support@example.com" className="underline hover:text-(--color-primary)">
                        destek ekibiyle iletişime geçin
                    </a>
                </p>
            </motion.div>
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT-LEVEL ERROR BOUNDARY
// ─────────────────────────────────────────────────────────────────────────────

interface InlineErrorProps {
    message?: string
    onRetry?: () => void
}

export function InlineError({ message = 'Bir hata oluştu', onRetry }: InlineErrorProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "p-4 rounded-xl",
                "bg-(--color-error-soft) border border-(--color-error)/30",
                "flex items-center gap-3"
            )}
        >
            <AlertTriangle className="h-5 w-5 text-(--color-error) shrink-0" />
            <span className="text-sm text-(--color-error)">{message}</span>
            {onRetry && (
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onRetry}
                    className="ml-auto"
                >
                    Tekrar Dene
                </Button>
            )}
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// SUSPENSE FALLBACK
// ─────────────────────────────────────────────────────────────────────────────

export function SuspenseFallback() {
    return (
        <div className="flex items-center justify-center min-h-[200px]">
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-8 h-8 rounded-full border-2 border-(--color-primary) border-t-transparent"
            />
        </div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// FULL PAGE LOADER
// ─────────────────────────────────────────────────────────────────────────────

export function FullPageLoader() {
    return (
        <div className="fixed inset-0 z-(--z-max) bg-(--color-bg) flex items-center justify-center">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center"
            >
                {/* Animated Logo */}
                <motion.div
                    animate={{
                        scale: [1, 1.1, 1],
                        rotate: [0, 5, -5, 0]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-(--gradient-brand) flex items-center justify-center shadow-2xl"
                >
                    <span className="text-3xl">✨</span>
                </motion.div>

                <p className="text-(--color-text-muted)">Yükleniyor...</p>
            </motion.div>
        </div>
    )
}
