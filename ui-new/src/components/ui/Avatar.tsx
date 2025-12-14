/**
 * Avatar Component
 * 
 * User/bot avatars with fallback
 */

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
    src?: string
    alt?: string
    fallback?: React.ReactNode
    size?: 'sm' | 'md' | 'lg' | 'xl'
}

const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
    xl: 'h-16 w-16 text-lg',
}

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
    ({ className, src, alt, fallback, size = 'md', ...props }, ref) => {
        const [hasError, setHasError] = React.useState(false)

        return (
            <div
                ref={ref}
                className={cn(
                    `relative flex shrink-0 overflow-hidden rounded-full
           bg-(--color-bg-surface) shadow-sm`,
                    sizeClasses[size],
                    className
                )}
                {...props}
            >
                {src && !hasError ? (
                    <img
                        src={src}
                        alt={alt || 'Avatar'}
                        className="h-full w-full object-cover"
                        onError={() => setHasError(true)}
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-(--gradient-brand) text-(--color-msg-user-text) font-medium">
                        {fallback || '?'}
                    </div>
                )}
            </div>
        )
    }
)
Avatar.displayName = 'Avatar'

export { Avatar }
