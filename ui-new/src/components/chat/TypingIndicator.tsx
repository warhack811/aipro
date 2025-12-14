/**
 * TypingIndicator Component
 * 
 * Animated "AI is typing..." indicator with bouncing dots
 */

import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useBranding } from '@/stores'

interface TypingIndicatorProps {
    className?: string
}

export function TypingIndicator({ className }: TypingIndicatorProps) {
    const branding = useBranding()

    return (
        <div className={cn(
            "flex items-start gap-3 px-4 md:px-8 py-2",
            className
        )}>
            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-(--gradient-brand) flex items-center justify-center flex-shrink-0">
                <span className="text-sm">✨</span>
            </div>

            {/* Typing bubble */}
            <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-(--color-bg-surface)">
                <span className="text-sm text-(--color-text-muted)">
                    {branding.displayName} yazıyor
                </span>

                {/* Bouncing dots */}
                <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                        <motion.span
                            key={i}
                            className="w-1.5 h-1.5 rounded-full bg-(--color-primary)"
                            animate={{
                                y: [0, -4, 0],
                                opacity: [0.4, 1, 0.4]
                            }}
                            transition={{
                                duration: 0.6,
                                repeat: Infinity,
                                delay: i * 0.15,
                                ease: "easeInOut"
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    )
}
