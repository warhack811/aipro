/**
 * Input Component
 * 
 * Premium text input with variants
 */

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps
    extends React.InputHTMLAttributes<HTMLInputElement> {
    error?: string
    leftIcon?: React.ReactNode
    rightIcon?: React.ReactNode
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, error, leftIcon, rightIcon, ...props }, ref) => {
        return (
            <div className="relative w-full">
                {leftIcon && (
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 text-(--color-text-muted)">
                        {leftIcon}
                    </div>
                )}

                <input
                    type={type}
                    className={cn(
                        `flex h-10 w-full rounded-xl border bg-(--color-bg-input)
             px-4 py-2 text-sm
             placeholder:text-(--color-text-muted)
             transition-all duration-200
             focus:outline-none focus:ring-2 focus:ring-(--color-primary) focus:ring-offset-0
             focus:border-(--color-primary)
             disabled:cursor-not-allowed disabled:opacity-50`,
                        leftIcon && 'pl-10',
                        rightIcon && 'pr-10',
                        error
                            ? 'border-(--color-error) focus:ring-(--color-error)'
                            : 'border-(--color-border)',
                        className
                    )}
                    ref={ref}
                    {...props}
                />

                {rightIcon && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-(--color-text-muted)">
                        {rightIcon}
                    </div>
                )}

                {error && (
                    <p className="mt-1.5 text-xs text-(--color-error)">{error}</p>
                )}
            </div>
        )
    }
)
Input.displayName = 'Input'

export { Input }
