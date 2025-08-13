/**
 * Performance Optimization Module
 * Handles resource loading, caching, and performance monitoring
 */

class PerformanceOptimizer {
    constructor() {
        this.metrics = {
            loadTime: 0,
            domContentLoaded: 0,
            firstPaint: 0,
            firstContentfulPaint: 0,
            largestContentfulPaint: 0
        };
        this.init();
    }

    init() {
        this.measurePerformance();
        this.optimizeResources();
        this.preloadCriticalResources();
        this.setupIntersectionObserver();
    }

    // Measure performance metrics
    measurePerformance() {
        // Wait for page to load
        window.addEventListener('load', () => {
            this.collectMetrics();
        });

        // Measure DOM content loaded
        document.addEventListener('DOMContentLoaded', () => {
            this.metrics.domContentLoaded = performance.now();
        });
    }

    // Collect performance metrics
    collectMetrics() {
        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');

        this.metrics.loadTime = navigation.loadEventEnd - navigation.loadEventStart;

        paint.forEach(entry => {
            if (entry.name === 'first-paint') {
                this.metrics.firstPaint = entry.startTime;
            } else if (entry.name === 'first-contentful-paint') {
                this.metrics.firstContentfulPaint = entry.startTime;
            }
        });

        // Largest Contentful Paint
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.largestContentfulPaint = lastEntry.startTime;
            });
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
        }

        // Log metrics in development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('Performance Metrics:', this.metrics);
        }
    }

    // Optimize resource loading
    optimizeResources() {
        // Preload critical fonts
        this.preloadFont('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

        // Optimize images
        this.optimizeImages();

        // Defer non-critical CSS
        this.deferNonCriticalCSS();

        // Optimize third-party scripts
        this.optimizeThirdPartyScripts();
    }

    // Preload critical fonts
    preloadFont(fontUrl) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'style';
        link.href = fontUrl;
        link.onload = () => {
            link.rel = 'stylesheet';
        };
        document.head.appendChild(link);
    }

    // Optimize images
    optimizeImages() {
        // Add loading="lazy" to images below the fold
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach((img, index) => {
            // First 3 images load eagerly, rest lazy
            if (index > 2) {
                img.loading = 'lazy';
            }
        });

        // Implement progressive image loading
        this.setupProgressiveImageLoading();
    }

    // Setup progressive image loading
    setupProgressiveImageLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadProgressiveImage(entry.target);
                        imageObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px 0px'
            });

            images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for older browsers
            images.forEach(img => this.loadProgressiveImage(img));
        }
    }

    // Load progressive image
    loadProgressiveImage(img) {
        const lowQualitySrc = img.dataset.lowQuality;
        const highQualitySrc = img.dataset.src;

        if (lowQualitySrc) {
            // Load low quality first
            img.src = lowQualitySrc;
            img.classList.add('loading');

            // Then load high quality
            const highQualityImg = new Image();
            highQualityImg.onload = () => {
                img.src = highQualitySrc;
                img.classList.remove('loading');
                img.classList.add('loaded');
            };
            highQualityImg.src = highQualitySrc;
        } else {
            img.src = highQualitySrc;
            img.classList.add('loaded');
        }
    }

    // Defer non-critical CSS
    deferNonCriticalCSS() {
        const nonCriticalCSS = [
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
        ];

        nonCriticalCSS.forEach(href => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.media = 'print';
            link.onload = () => {
                link.media = 'all';
            };
            document.head.appendChild(link);
        });
    }

    // Optimize third-party scripts
    optimizeThirdPartyScripts() {
        // Delay loading of non-critical scripts
        setTimeout(() => {
            this.loadNonCriticalScripts();
        }, 3000);
    }

    // Load non-critical scripts
    loadNonCriticalScripts() {
        // Analytics scripts
        if (window.gtag) {
            // Google Analytics is already loaded
        }

        // Social media widgets
        this.loadSocialWidgets();
    }

    // Load social media widgets
    loadSocialWidgets() {
        // Only load if social elements are present
        if (document.querySelector('.social-widget')) {
            // Load social scripts here
        }
    }



    // Preload critical resources
    preloadCriticalResources() {
        const criticalResources = [
            { href: '/static/css/main.css', as: 'style' },
            { href: '/static/js/main.js', as: 'script' }
        ];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = resource.as;
            link.href = resource.href;
            document.head.appendChild(link);
        });
    }

    // Setup intersection observer for animations
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            const animationObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate');
                        animationObserver.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1
            });

            // Observe elements with animation classes
            document.querySelectorAll('.animate-on-scroll').forEach(el => {
                animationObserver.observe(el);
            });
        }
    }

    // Resource hints
    addResourceHints() {
        const hints = [
            { rel: 'dns-prefetch', href: '//fonts.googleapis.com' },
            { rel: 'dns-prefetch', href: '//fonts.gstatic.com' },
            { rel: 'dns-prefetch', href: '//cdnjs.cloudflare.com' },
            { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
            { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true }
        ];

        hints.forEach(hint => {
            const link = document.createElement('link');
            link.rel = hint.rel;
            link.href = hint.href;
            if (hint.crossorigin) link.crossOrigin = hint.crossorigin;
            document.head.appendChild(link);
        });
    }

    // Critical resource loading
    loadCriticalResources() {
        return new Promise((resolve) => {
            const criticalResources = [
                '/static/css/main.css',
                '/static/js/theme-toggle.js'
            ];

            let loadedCount = 0;
            const totalResources = criticalResources.length;

            criticalResources.forEach(resource => {
                if (resource.endsWith('.css')) {
                    const link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = resource;
                    link.onload = () => {
                        loadedCount++;
                        if (loadedCount === totalResources) resolve();
                    };
                    document.head.appendChild(link);
                } else if (resource.endsWith('.js')) {
                    const script = document.createElement('script');
                    script.src = resource;
                    script.onload = () => {
                        loadedCount++;
                        if (loadedCount === totalResources) resolve();
                    };
                    document.head.appendChild(script);
                }
            });
        });
    }

    // Get performance metrics
    getMetrics() {
        return this.metrics;
    }

    // Send metrics to analytics
    sendMetrics() {
        if (window.gtag) {
            gtag('event', 'timing_complete', {
                name: 'load',
                value: Math.round(this.metrics.loadTime)
            });

            gtag('event', 'timing_complete', {
                name: 'first_contentful_paint',
                value: Math.round(this.metrics.firstContentfulPaint)
            });
        }
    }
}

// Initialize performance optimizer
document.addEventListener('DOMContentLoaded', () => {
    window.performanceOptimizer = new PerformanceOptimizer();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}
