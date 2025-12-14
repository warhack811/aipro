/**
 * CodeBlock Component
 * 
 * Styled code block with syntax highlighting, copy button, and language badge
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Copy, Check } from 'lucide-react'
import { highlightCode, getLanguageDisplayName, copyCode } from '@/lib/codeHighlighter'
import { cn } from '@/lib/utils'

interface CodeBlockProps {
    code: string
    language?: string
    className?: string
}

export function CodeBlock({ code, language = 'plaintext', className }: CodeBlockProps) {
    const [copied, setCopied] = useState(false)

    const highlightedCode = highlightCode(code, language)
    const displayLang = getLanguageDisplayName(language)

    const handleCopy = async () => {
        const success = await copyCode(code)
        if (success) {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    return (
        <div className={cn(
            "relative group rounded-xl overflow-hidden",
            "bg-[#1e1e2e] border border-[#313244]",
            "my-3",
            className
        )}>
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#181825] border-b border-[#313244]">
                <span className="text-xs font-medium text-[#cdd6f4]">
                    {displayLang}
                </span>

                <motion.button
                    onClick={handleCopy}
                    className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs",
                        "transition-all duration-200",
                        copied
                            ? "bg-green-500/20 text-green-400"
                            : "bg-[#313244] text-[#a6adc8] hover:bg-[#45475a] hover:text-[#cdd6f4]"
                    )}
                    whileTap={{ scale: 0.95 }}
                >
                    {copied ? (
                        <>
                            <Check className="h-3.5 w-3.5" />
                            <span>Kopyalandı</span>
                        </>
                    ) : (
                        <>
                            <Copy className="h-3.5 w-3.5" />
                            <span>Kopyala</span>
                        </>
                    )}
                </motion.button>
            </div>

            {/* Code */}
            <div className="overflow-x-auto">
                <pre className="p-4 text-sm leading-relaxed">
                    <code
                        className={`language-${language}`}
                        dangerouslySetInnerHTML={{ __html: highlightedCode }}
                    />
                </pre>
            </div>
        </div>
    )
}
