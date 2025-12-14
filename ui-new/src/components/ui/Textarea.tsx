/**
 * Textarea Component
 * 
 * Auto-resizing textarea for chat input
 */

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps
    extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    autoResize?: boolean
    maxHeight?: number
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, autoResize = true, maxHeight = 200, onChange, ...props }, ref) => {
        const textareaRef = React.useRef<HTMLTextAreaElement | null>(null)

        // Combine refs
        React.useImperativeHandle(ref, () => textareaRef.current!)

        const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
            if (autoResize && textareaRef.current) {
                textareaRef.current.style.height = 'auto'
                const newHeight = Math.min(textareaRef.current.scrollHeight, maxHeight)
                textareaRef.current.style.height = `${newHeight}px`
            }
            onChange?.(e)
        }

        // Reset height when value is cleared
        React.useEffect(() => {
            if (autoResize && textareaRef.current && !props.value) {
                textareaRef.current.style.height = 'auto'
            }
        }, [props.value, autoResize])

        return (
            <textarea
                className={cn(
                    `flex w-full rounded-xl border border-(--color-border) 
            bg-(--color-bg-input) px-4 py-3 text-sm
            placeholder:text-(--color-text-muted)
            transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-(--color-primary) focus:ring-offset-0
            focus:border-(--color-primary)
            disabled:cursor-not-allowed disabled:opacity-50
            resize-none scrollbar-thin`,
            "flex items-center",  
            "px-0 py-2", 
                    className
                )}
                ref={textareaRef}
                onChange={handleChange}
                {...props}
            />
        )
    }
)
Textarea.displayName = 'Textarea'

export { Textarea }
