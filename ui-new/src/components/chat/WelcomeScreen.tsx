/**
 * WelcomeScreen Component
 * 
 * Personalized welcome screen with quick actions
 */

import { motion } from 'framer-motion'
import { Pencil, Image, Search, Code, ArrowRight, Sparkles } from 'lucide-react'
import { useChatStore, useBranding, useUserStore } from '@/stores'
import { getGreeting } from '@/lib/utils'
import { cn } from '@/lib/utils'

export function WelcomeScreen() {
    const branding = useBranding()
    const user = useUserStore((state) => state.user)
    const setInputValue = useChatStore((state) => state.setInputValue)

    const greeting = getGreeting()
    const displayName = user?.displayName || user?.username || 'Kullanıcı'

    const handleSuggestion = (text: string) => {
        setInputValue(text)
        // Focus the input
        const input = document.querySelector('textarea')
        input?.focus()
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col items-center justify-center min-h-[70vh] text-center px-6 py-12"
        >
            {/* Animated Logo */}
            <motion.div
                className="relative w-28 h-28 mb-8"
                animate={{
                    scale: [1, 1.05, 1],
                    rotate: [0, 3, -3, 0]
                }}
                transition={{
                    duration: 6,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
            >
                {/* Glow effect */}
                <div className="absolute inset-0 bg-(--gradient-brand) rounded-3xl blur-2xl opacity-40 animate-pulse" />

                {/* Main logo */}
                <div className="relative w-full h-full bg-(--gradient-brand) rounded-3xl flex items-center justify-center shadow-2xl ring-4 ring-(--color-bg) ring-offset-2 ring-offset-(--color-bg-surface)">
                    <Sparkles className="h-12 w-12 text-white drop-shadow-lg" />
                </div>
            </motion.div>

            {/* Personalized Greeting */}
            <h1 className="text-4xl font-display font-bold mb-3">
                <span className="gradient-text">{greeting}</span>
                <span className="text-(--color-text)">, {displayName}!</span>
            </h1>

            <p className="text-(--color-text-secondary) text-lg max-w-md mb-10 leading-relaxed">
                Ben {branding.displayName}, kişisel asistanınız. Size nasıl yardımcı olabilirim?
            </p>

            {/* Quick Action Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-3xl w-full">
                <QuickActionCard
                    icon={<Pencil className="h-6 w-6" />}
                    title="Yazı Yaz"
                    description="Blog, e-posta, rapor..."
                    onClick={() => handleSuggestion("Bana profesyonel bir e-posta yaz: ")}
                    gradient="from-blue-500 to-cyan-500"
                />
                <QuickActionCard
                    icon={<Image className="h-6 w-6" />}
                    title="Görsel Oluştur"
                    description="AI ile resim üret"
                    onClick={() => handleSuggestion("Bana şöyle bir görsel oluştur: ")}
                    gradient="from-pink-500 to-rose-500"
                />
                <QuickActionCard
                    icon={<Search className="h-6 w-6" />}
                    title="Araştır"
                    description="Web'de bilgi bul"
                    onClick={() => handleSuggestion("İnternette araştır: ")}
                    gradient="from-green-500 to-emerald-500"
                />
                <QuickActionCard
                    icon={<Code className="h-6 w-6" />}
                    title="Kod Yaz"
                    description="Programlama yardımı"
                    onClick={() => handleSuggestion("Bana şunu kodla: ")}
                    gradient="from-violet-500 to-purple-500"
                />
            </div>

            {/* Example Prompts */}
            <div className="mt-12 w-full max-w-2xl">
                <p className="text-sm text-(--color-text-muted) mb-4">Örnek istekler:</p>
                <div className="flex flex-wrap justify-center gap-2">
                    {examplePrompts.map((prompt, i) => (
                        <button
                            key={i}
                            onClick={() => handleSuggestion(prompt)}
                            className={cn(
                                "px-4 py-2 rounded-full text-sm",
                                "bg-(--color-bg-surface) border border-(--color-border)",
                                "hover:border-(--color-primary) hover:bg-(--color-primary-softer)",
                                "transition-all duration-200"
                            )}
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            </div>
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

interface QuickActionCardProps {
    icon: React.ReactNode
    title: string
    description: string
    onClick: () => void
    gradient: string
}

function QuickActionCard({ icon, title, description, onClick, gradient }: QuickActionCardProps) {
    return (
        <motion.button
            whileHover={{ scale: 1.02, y: -4 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className={cn(
                "group relative overflow-hidden rounded-2xl p-5 text-left",
                "bg-(--color-bg-surface) border border-(--color-border)",
                "hover:border-(--color-border-hover) transition-all duration-300"
            )}
        >
            {/* Gradient Glow on Hover */}
            <div
                className={cn(
                    "absolute inset-0 opacity-0 group-hover:opacity-10",
                    `bg-linear-to-br ${gradient}`,
                    "blur-xl transition-opacity duration-300"
                )}
            />

            <div className="relative">
                <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center mb-3",
                    `bg-linear-to-br ${gradient}`,
                    "text-white shadow-lg"
                )}>
                    {icon}
                </div>
                <h3 className="font-semibold text-(--color-text) mb-1">{title}</h3>
                <p className="text-sm text-(--color-text-muted)">{description}</p>
            </div>

            {/* Arrow indicator */}
            <div className={cn(
                "absolute bottom-4 right-4",
                "opacity-0 group-hover:opacity-100",
                "transform translate-x-2 group-hover:translate-x-0",
                "transition-all duration-300"
            )}>
                <ArrowRight className="h-4 w-4 text-(--color-text-muted)" />
            </div>
        </motion.button>
    )
}

// ─────────────────────────────────────────────────────────────────────────────

const examplePrompts = [
    "Bana bir hikaye anlat",
    "Python ile web scraping nasıl yapılır?",
    "Bugün güncel haberleri özetle",
    "Türkiye'nin başkenti neresi?",
]
