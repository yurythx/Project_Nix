/**
 * Image Optimization and Lazy Loading System
 * Provides WebP support detection, lazy loading, and responsive images
 */

class ImageOptimizer {
    constructor() {
        this.supportsWebP = false;
        this.observer = null;
        this.init();
    }

    async init() {
        await this.detectWebPSupport();
        this.setupLazyLoading();
        this.optimizeExistingImages();
        this.addWebPClass();
    }

    // Detect WebP support
    async detectWebPSupport() {
        return new Promise((resolve) => {
            const webP = new Image();
            webP.onload = webP.onerror = () => {
                this.supportsWebP = (webP.height === 2);
                resolve(this.supportsWebP);
            };
            webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
        });
    }

    // Add WebP class to document
    addWebPClass() {
        document.documentElement.classList.add(this.supportsWebP ? 'webp' : 'no-webp');
    }

    // Setup Intersection Observer for lazy loading
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            // Observe all lazy images
            document.querySelectorAll('img[data-src]').forEach(img => {
                this.observer.observe(img);
            });
        } else {
            // Fallback for browsers without IntersectionObserver
            document.querySelectorAll('img[data-src]').forEach(img => {
                this.loadImage(img);
            });
        }
    }

    // Load individual image
    loadImage(img) {
        // Show placeholder while loading
        img.classList.add('img-placeholder');

        const imageUrl = this.getOptimalImageUrl(img);
        
        // Create new image to preload
        const imageLoader = new Image();
        
        imageLoader.onload = () => {
            img.src = imageUrl;
            img.classList.remove('img-lazy', 'img-placeholder');
            img.classList.add('loaded');
            
            // Remove data-src to prevent reloading
            img.removeAttribute('data-src');
            
            // Trigger custom event
            img.dispatchEvent(new CustomEvent('imageLoaded', {
                detail: { url: imageUrl, webp: this.supportsWebP }
            }));
        };

        imageLoader.onerror = () => {
            // Fallback to original src if WebP fails
            if (img.dataset.fallback) {
                img.src = img.dataset.fallback;
            } else {
                img.src = img.dataset.src;
            }
            img.classList.remove('img-lazy', 'img-placeholder');
            img.classList.add('loaded', 'error');
        };

        imageLoader.src = imageUrl;
    }

    // Get optimal image URL based on device and format support
    getOptimalImageUrl(img) {
        const dataSrc = img.dataset.src;
        const webpSrc = img.dataset.webp;
        
        // Use WebP if supported and available
        if (this.supportsWebP && webpSrc) {
            return webpSrc;
        }
        
        // Add responsive sizing parameters if needed
        return this.addResponsiveParams(dataSrc, img);
    }

    // Add responsive parameters to image URL
    addResponsiveParams(url, img) {
        if (!url) return '';
        
        // Get container width for responsive sizing
        const containerWidth = img.parentElement.offsetWidth;
        const devicePixelRatio = window.devicePixelRatio || 1;
        const targetWidth = Math.ceil(containerWidth * devicePixelRatio);
        
        // If URL already has parameters, append with &, otherwise use ?
        const separator = url.includes('?') ? '&' : '?';
        
        // Add width parameter for dynamic resizing (if your backend supports it)
        return `${url}${separator}w=${targetWidth}&q=85&f=auto`;
    }

    // Optimize existing images
    optimizeExistingImages() {
        document.querySelectorAll('img:not([data-src])').forEach(img => {
            if (!img.src) return;
            
            // Add responsive attributes
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            
            // Add optimization classes
            img.classList.add('img-optimized');
            
            // Add error handling
            img.onerror = () => {
                img.classList.add('error');
                console.warn('Failed to load image:', img.src);
            };
        });
    }

    // Create responsive image element
    createResponsiveImage(src, alt, options = {}) {
        const {
            webpSrc = null,
            fallbackSrc = null,
            lazy = true,
            aspectRatio = null,
            className = '',
            sizes = '100vw'
        } = options;

        const container = document.createElement('div');
        container.className = `img-container ${aspectRatio ? `img-container-${aspectRatio}` : ''} ${className}`;

        const img = document.createElement('img');
        img.alt = alt;
        img.className = 'img-optimized';
        
        if (lazy) {
            img.className += ' img-lazy';
            img.dataset.src = src;
            if (webpSrc) img.dataset.webp = webpSrc;
            if (fallbackSrc) img.dataset.fallback = fallbackSrc;
            
            // Add placeholder
            img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PC9zdmc+';
            
            // Observe for lazy loading
            if (this.observer) {
                this.observer.observe(img);
            }
        } else {
            img.src = this.supportsWebP && webpSrc ? webpSrc : src;
        }

        container.appendChild(img);
        return container;
    }

    // Preload critical images
    preloadImages(urls) {
        urls.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = url;
            document.head.appendChild(link);
        });
    }

    // Convert image to WebP (client-side conversion for uploaded images)
    async convertToWebP(file, quality = 0.85) {
        return new Promise((resolve, reject) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();

            img.onload = () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);

                canvas.toBlob(resolve, 'image/webp', quality);
            };

            img.onerror = reject;
            img.src = URL.createObjectURL(file);
        });
    }

    // Get image dimensions without loading
    async getImageDimensions(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve({ width: img.width, height: img.height });
            img.onerror = reject;
            img.src = url;
        });
    }

    // Cleanup
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// Initialize image optimizer
document.addEventListener('DOMContentLoaded', () => {
    window.imageOptimizer = new ImageOptimizer();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageOptimizer;
}
