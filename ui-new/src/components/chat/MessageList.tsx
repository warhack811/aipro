/**
 * MessageList Component
 * 
 * Renders list of messages with animations and reply support.
 * Basitleştirilmiş versiyon - mesajlar olduğu gibi gösterilir.
 */

import { motion } from 'framer-motion'
import type { Message } from '@/types'
import { MessageBubble } from './MessageBubble'

interface MessageListProps {
    messages: Message[]
    onReply?: (message: Message) => void
}

export function MessageList({ messages, onReply }: MessageListProps) {
    return (
        <div className="px-4 md:px-8 py-6 space-y-6">
            {messages.map((message, index) => (
                <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                        duration: 0.3,
                        delay: index === messages.length - 1 ? 0 : 0,
                        ease: [0.16, 1, 0.3, 1]
                    }}
                >
                    <MessageBubble
                        message={message}
                        onReply={onReply}
                    />
                </motion.div>
            ))}
        </div>
    )
}
