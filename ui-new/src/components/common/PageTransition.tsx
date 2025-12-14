/**
 * Page Transition Component
 * 
 * Smooth page transitions with Framer Motion
 */

import { motion, type HTMLMotionProps } from 'framer-motion'
import type { ReactNode } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// ANIMATION VARIANTS
// ─────────────────────────────────────────────────────────────────────────────

const animations = {
    fade: {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
    },
    fadeUp: {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: -20 },
    },
    fadeDown: {
        initial: { opacity: 0, y: -20 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: 20 },
    },
    slideLeft: {
        initial: { opacity: 0, x: 50 },
        animate: { opacity: 1, x: 0 },
        exit: { opacity: 0, x: -50 },
    },
    slideRight: {
        initial: { opacity: 0, x: -50 },
        animate: { opacity: 1, x: 0 },
        exit: { opacity: 0, x: 50 },
    },
    scale: {
        initial: { opacity: 0, scale: 0.95 },
        animate: { opacity: 1, scale: 1 },
        exit: { opacity: 0, scale: 1.05 },
    },
    scaleUp: {
        initial: { opacity: 0, scale: 0.9 },
        animate: { opacity: 1, scale: 1 },
        exit: { opacity: 0, scale: 0.9 },
    },
}

type AnimationType = keyof typeof animations

// ─────────────────────────────────────────────────────────────────────────────
// PAGE TRANSITION
// ─────────────────────────────────────────────────────────────────────────────

interface PageTransitionProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
    children: ReactNode
    animation?: AnimationType
    duration?: number
    delay?: number
}

export function PageTransition({
    children,
    animation = 'fadeUp',
    duration = 0.3,
    delay = 0,
    ...props
}: PageTransitionProps) {
    const variants = animations[animation]

    return (
        <motion.div
            initial="initial"
            animate="animate"
            exit="exit"
            variants={variants}
            transition={{
                duration,
                delay,
                ease: [0.16, 1, 0.3, 1], // ease-out-expo
            }}
            {...props}
        >
            {children}
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// STAGGER CHILDREN
// ─────────────────────────────────────────────────────────────────────────────

interface StaggerContainerProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
    children: ReactNode
    staggerDelay?: number
}

export function StaggerContainer({
    children,
    staggerDelay = 0.1,
    ...props
}: StaggerContainerProps) {
    return (
        <motion.div
            initial="hidden"
            animate="visible"
            variants={{
                hidden: {},
                visible: {
                    transition: {
                        staggerChildren: staggerDelay,
                    },
                },
            }}
            {...props}
        >
            {children}
        </motion.div>
    )
}

interface StaggerItemProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
    children: ReactNode
}

export function StaggerItem({ children, ...props }: StaggerItemProps) {
    return (
        <motion.div
            variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 },
            }}
            transition={{
                duration: 0.3,
                ease: [0.16, 1, 0.3, 1],
            }}
            {...props}
        >
            {children}
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// FADE IN VIEW
// ─────────────────────────────────────────────────────────────────────────────

interface FadeInViewProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
    children: ReactNode
    direction?: 'up' | 'down' | 'left' | 'right'
    distance?: number
    delay?: number
    once?: boolean
}

export function FadeInView({
    children,
    direction = 'up',
    distance = 20,
    delay = 0,
    once = true,
    ...props
}: FadeInViewProps) {
    const directionOffset = {
        up: { y: distance },
        down: { y: -distance },
        left: { x: distance },
        right: { x: -distance },
    }

    return (
        <motion.div
            initial={{ opacity: 0, ...directionOffset[direction] }}
            whileInView={{ opacity: 1, x: 0, y: 0 }}
            viewport={{ once }}
            transition={{
                duration: 0.5,
                delay,
                ease: [0.16, 1, 0.3, 1],
            }}
            {...props}
        >
            {children}
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// HOVER SCALE
// ─────────────────────────────────────────────────────────────────────────────

interface HoverScaleProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
    children: ReactNode
    scale?: number
}

export function HoverScale({ children, scale = 1.02, ...props }: HoverScaleProps) {
    return (
        <motion.div
            whileHover={{ scale }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.2 }}
            {...props}
        >
            {children}
        </motion.div>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// PULSE
// ─────────────────────────────────────────────────────────────────────────────

interface PulseProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
    children: ReactNode
    pulseScale?: number
}

export function Pulse({ children, pulseScale = 1.05, ...props }: PulseProps) {
    return (
        <motion.div
            animate={{
                scale: [1, pulseScale, 1],
            }}
            transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
            }}
            {...props}
        >
            {children}
        </motion.div>
    )
}
