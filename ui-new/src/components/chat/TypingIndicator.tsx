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
            "flex items-center gap-4 px-4 md:px-8 py-4",
            className
        )}>
            {/* Avatar - Slightly larger glow */}
            <div className="w-9 h-9 rounded-xl bg-(--gradient-brand) flex items-center justify-center flex-shrink-0 shadow-lg shadow-(--color-primary)/10">
                <span className="text-base">✨</span>
            </div>

            {/* Typing bubble - Premium Look */}
            <div className="flex items-center gap-3 px-5 py-3.5 rounded-2xl rounded-tl-sm bg-(--color-bg-surface) border border-(--color-border) shadow-xs">
                {/* Dots Animation - Smoother */}
                <div className="flex gap-1.5 pt-1">
                    {[0, 1, 2].map((i) => (
                        <motion.span
                            key={i}
                            className="w-2 h-2 rounded-full bg-(--color-primary)"
                            animate={{
                                y: ["0%", "-50%", "0%"],
                                opacity: [0.5, 1, 0.5],
                                scale: [0.9, 1.1, 0.9]
                            }}
                            transition={{
                                duration: 0.8,
                                repeat: Infinity,
                                delay: i * 0.15,
                                ease: "easeInOut"
                            }}
                        />
                    ))}
                </div>

                <span className="text-sm font-medium text-(--color-text-secondary) tracking-wide">
                    {branding.displayName} düşünüyor...
                </span>
            </div>
        </div>
    )
}
