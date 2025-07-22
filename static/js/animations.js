/**
 * Animation Controller
 * Handles scroll animations, page transitions, and micro-interactions
 */

class AnimationController {
    constructor() {
        this.scrollObserver = null;
        this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.init();
    }

    init() {
        this.setupScrollAnimations();
        this.setupPageTransitions();
        this.setupMicroInteractions();
        this.setupStaggeredAnimations();
        this.bindEvents();
    }

    // Setup scroll-triggered animations
    setupScrollAnimations() {
        if (this.reducedMotion) return;

        if ('IntersectionObserver' in window) {
            this.scrollObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');
                        this.scrollObserver.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            // Observe all scroll reveal elements
            document.querySelectorAll('.scroll-reveal').forEach(el => {
                this.scrollObserver.observe(el);
            });
        } else {
            // Fallback for browsers without IntersectionObserver
            document.querySelectorAll('.scroll-reveal').forEach(el => {
                el.classList.add('revealed');
            });
        }
    }

    // Setup page transition animations
    setupPageTransitions() {
        if (this.reducedMotion) return;

        // Add page enter animation to main content
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.classList.add('page-enter');
        }

        // Handle link clicks for smooth transitions
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.isInternalLink(link)) {
                this.handlePageTransition(e, link);
            }
        });
    }

    // Check if link is internal
    isInternalLink(link) {
        const href = link.getAttribute('href');
        return href && 
               !href.startsWith('http') && 
               !href.startsWith('mailto:') && 
               !href.startsWith('tel:') &&
               !href.startsWith('#') &&
               !link.hasAttribute('download') &&
               !link.getAttribute('target');
    }

    // Handle page transition
    handlePageTransition(e, link) {
        if (this.reducedMotion) return;

        e.preventDefault();
        
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.classList.add('page-exit');
            
            setTimeout(() => {
                window.location.href = link.href;
            }, 300);
        } else {
            window.location.href = link.href;
        }
    }

    // Setup micro-interactions
    setupMicroInteractions() {
        if (this.reducedMotion) return;

        // Button ripple effect
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn') || e.target.closest('.btn')) {
                this.createRipple(e);
            }
        });

        // Form focus animations
        document.querySelectorAll('.form-control, .form-select').forEach(input => {
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });

            input.addEventListener('blur', () => {
                input.parentElement.classList.remove('focused');
            });
        });

        // Card hover effects
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                if (!this.reducedMotion) {
                    card.classList.add('hover-lift');
                }
            });

            card.addEventListener('mouseleave', () => {
                card.classList.remove('hover-lift');
            });
        });
    }

    // Create ripple effect for buttons
    createRipple(e) {
        const button = e.target.classList.contains('btn') ? e.target : e.target.closest('.btn');
        if (!button) return;

        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;

        button.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    // Setup staggered animations
    setupStaggeredAnimations() {
        if (this.reducedMotion) return;

        document.querySelectorAll('.stagger-container').forEach(container => {
            const items = container.children;
            Array.from(items).forEach((item, index) => {
                item.style.animationDelay = `${index * 0.1}s`;
                item.classList.add('fade-in-up');
            });
        });
    }

    // Bind additional events
    bindEvents() {
        // Handle reduced motion preference changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.reducedMotion = e.matches;
            if (this.reducedMotion) {
                this.disableAnimations();
            } else {
                this.enableAnimations();
            }
        });

        // Handle theme changes for animations
        window.addEventListener('themeChanged', (e) => {
            this.updateAnimationsForTheme(e.detail.theme);
        });

        // Handle window resize for responsive animations
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
    }

    // Disable animations for reduced motion
    disableAnimations() {
        document.documentElement.style.setProperty('--transition', 'none');
        document.querySelectorAll('.scroll-reveal').forEach(el => {
            el.classList.add('revealed');
        });
    }

    // Enable animations
    enableAnimations() {
        document.documentElement.style.removeProperty('--transition');
    }

    // Update animations for theme
    updateAnimationsForTheme(theme) {
        // Adjust animation colors based on theme
        const root = document.documentElement;
        if (theme === 'dark') {
            root.style.setProperty('--glow-color', 'rgba(68, 183, 139, 0.6)');
        } else {
            root.style.setProperty('--glow-color', 'rgba(12, 75, 51, 0.6)');
        }
    }

    // Handle window resize
    handleResize() {
        // Recalculate animations if needed
        if (this.scrollObserver) {
            // Re-observe elements that might have changed position
            document.querySelectorAll('.scroll-reveal:not(.revealed)').forEach(el => {
                this.scrollObserver.unobserve(el);
                this.scrollObserver.observe(el);
            });
        }
    }

    // Public methods for manual animation control
    animateElement(element, animationClass, duration = null) {
        if (this.reducedMotion) return Promise.resolve();

        return new Promise((resolve) => {
            element.classList.add(animationClass);
            
            const handleAnimationEnd = () => {
                element.removeEventListener('animationend', handleAnimationEnd);
                resolve();
            };

            element.addEventListener('animationend', handleAnimationEnd);

            if (duration) {
                setTimeout(() => {
                    element.removeEventListener('animationend', handleAnimationEnd);
                    resolve();
                }, duration);
            }
        });
    }

    // Animate a sequence of elements
    async animateSequence(elements, animationClass, delay = 100) {
        if (this.reducedMotion) return;

        for (let i = 0; i < elements.length; i++) {
            this.animateElement(elements[i], animationClass);
            if (i < elements.length - 1) {
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    // Show loading animation
    showLoading(element, text = 'Carregando') {
        const loader = document.createElement('div');
        loader.className = 'loading-container';
        loader.innerHTML = `
            <div class="loading-spinner"></div>
            <span class="loading-text">${text}<span class="loading-dots"></span></span>
        `;
        
        element.appendChild(loader);
        return loader;
    }

    // Hide loading animation
    hideLoading(loader) {
        if (loader && loader.parentNode) {
            loader.classList.add('fade-out');
            setTimeout(() => {
                loader.remove();
            }, 300);
        }
    }

    // Cleanup
    destroy() {
        if (this.scrollObserver) {
            this.scrollObserver.disconnect();
        }
    }
}

// Add ripple animation CSS
const rippleCSS = `
@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}
`;

// Inject ripple CSS
const style = document.createElement('style');
style.textContent = rippleCSS;
document.head.appendChild(style);

// Initialize animation controller
document.addEventListener('DOMContentLoaded', () => {
    window.animationController = new AnimationController();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnimationController;
}
