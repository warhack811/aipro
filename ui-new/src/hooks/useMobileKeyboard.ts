/**
 * Mobile Keyboard Support Hook
 * 
 * visualViewport API kullanarak mobil klavye yüksekliğini algılar
 * ve CSS variable olarak ayarlar. iOS ve Android destekler.
 */

import { useEffect, useState } from 'react'

interface KeyboardState {
    isVisible: boolean
    height: number
}

/**
 * Mobil klavye durumunu takip eden hook
 */
export function useMobileKeyboard(): KeyboardState {
    const [state, setState] = useState<KeyboardState>({
        isVisible: false,
        height: 0,
    })

    useEffect(() => {
        // Server-side rendering check
        if (typeof window === 'undefined') return

        const viewport = window.visualViewport
        if (!viewport) return

        let initialHeight = window.innerHeight

        const handleResize = () => {
            const currentHeight = viewport.height
            const keyboardHeight = Math.max(0, initialHeight - currentHeight)

            // Klavye görünür kabul edilmesi için minimum yükseklik
            const isVisible = keyboardHeight > 100

            setState({ isVisible, height: keyboardHeight })

            // CSS variable güncelle
            document.documentElement.style.setProperty(
                '--keyboard-height',
                `${keyboardHeight}px`
            )

            // Body class toggle
            if (isVisible) {
                document.body.classList.add('keyboard-visible')
            } else {
                document.body.classList.remove('keyboard-visible')
            }
        }

        // Orientation change'de initial height güncelle
        const handleOrientationChange = () => {
            setTimeout(() => {
                initialHeight = window.innerHeight
            }, 100)
        }

        viewport.addEventListener('resize', handleResize)
        window.addEventListener('orientationchange', handleOrientationChange)

        return () => {
            viewport.removeEventListener('resize', handleResize)
            window.removeEventListener('orientationchange', handleOrientationChange)
            document.body.classList.remove('keyboard-visible')
        }
    }, [])

    return state
}

/**
 * Input focus olduğunda scroll yapan utility
 */
export function scrollInputIntoView(element: HTMLElement | null, delay: number = 100): void {
    if (!element) return

    setTimeout(() => {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
        })
    }, delay)
}
