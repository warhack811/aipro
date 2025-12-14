/**
 * Button Component
 * 
 * Premium, accessible button with multiple variants
 * Built with CVA for type-safe variants
 */

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
    // Base styles
    `inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl
   text-sm font-medium transition-all duration-200
   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--color-primary) focus-visible:ring-offset-2
   disabled:pointer-events-none disabled:opacity-50
   active:scale-[0.98]`,
    {
        variants: {
            variant: {
                // Primary - Gradient brand button
                primary: `bg-(--gradient-brand) text-white
                  shadow-md hover:shadow-lg
                  hover:brightness-110
                  ring-offset-2 ring-offset-(--color-bg)`,

                // Secondary - Solid primary
                secondary: `bg-(--color-primary) text-(--color-msg-user-text)
                    hover:bg-(--color-primary-hover)
                    shadow-md`,

                // Outline - Bordered
                outline: `border border-(--color-border) bg-transparent
                  hover:bg-(--color-bg-surface-hover)
                  hover:border-(--color-primary)`,

                // Ghost - Minimal
                ghost: `bg-transparent hover:bg-(--color-bg-surface-hover)`,

                // Soft - Subtle background
                soft: `bg-(--color-primary-soft) text-(--color-primary)
               hover:bg-(--color-primary-softer)`,

                // Destructive
                destructive: `bg-(--color-error-soft) text-(--color-error)
                      hover:bg-(--color-error) hover:text-white`,

                // Link style
                link: `underline-offset-4 hover:underline text-(--color-primary)`,
            },
            size: {
                sm: 'h-8 px-3 text-xs rounded-lg',
                md: 'h-10 px-4 text-sm',
                lg: 'h-12 px-6 text-base rounded-2xl',
                xl: 'h-14 px-8 text-lg rounded-2xl',
                icon: 'h-10 w-10 p-0',
                'icon-sm': 'h-8 w-8 p-0 rounded-lg',
                'icon-lg': 'h-12 w-12 p-0',
            },
        },
        defaultVariants: {
            variant: 'primary',
            size: 'md',
        },
    }
)

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
    isLoading?: boolean
    leftIcon?: React.ReactNode
    rightIcon?: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            className,
            variant,
            size,
            isLoading,
            leftIcon,
            rightIcon,
            disabled,
            children,
            ...props
        },
        ref
    ) => {
        return (
            <button
                className={cn(buttonVariants({ variant, size, className }))}
                ref={ref}
                disabled={disabled || isLoading}
                {...props}
            >
                {isLoading ? (
                    <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                ) : leftIcon ? (
                    <span className="shrink-0">{leftIcon}</span>
                ) : null}

                {children}

                {rightIcon && !isLoading && (
                    <span className="shrink-0">{rightIcon}</span>
                )}
            </button>
        )
    }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
