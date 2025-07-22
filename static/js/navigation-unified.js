/**
 * Project Nix - Unified Navigation System
 * Optimized and clean navigation functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeUnifiedNavigation();
    console.log('🧭 Unified navigation system loaded');
});

/**
 * Initialize unified navigation functionality
 * Combines desktop and mobile navigation in one optimized function
 */
function initializeUnifiedNavigation() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const navbarCloseX = document.querySelector('.navbar-close-x');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    if (!navbarToggler || !navbarCollapse) {
        console.warn('Navigation elements not found');
        return;
    }

    // === UTILITY FUNCTIONS ===
    
    function toggleBodyScroll(disable) {
        if (disable) {
            document.body.style.overflow = 'hidden';
            document.body.style.paddingRight = getScrollbarWidth() + 'px';
        } else {
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
    }

    function getScrollbarWidth() {
        const outer = document.createElement('div');
        outer.style.visibility = 'hidden';
        outer.style.overflow = 'scroll';
        outer.style.msOverflowStyle = 'scrollbar';
        document.body.appendChild(outer);

        const inner = document.createElement('div');
        outer.appendChild(inner);

        const scrollbarWidth = (outer.offsetWidth - inner.offsetWidth);
        outer.parentNode.removeChild(outer);
        return scrollbarWidth;
    }

    function closeMenu() {
        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
        if (bsCollapse) {
            bsCollapse.hide();
        } else {
            navbarCollapse.classList.remove('show');
            toggleBodyScroll(false);
        }
    }

    function isMobile() {
        return window.innerWidth <= 991.98;
    }

    // === ACTIVE LINK HIGHLIGHTING ===
    function updateActiveLinks() {
        const currentPath = window.location.pathname;
        navLinks.forEach(function(link) {
            const href = link.getAttribute('href');
            if (href && currentPath.startsWith(href) && href !== '/') {
                link.classList.add('active');
            } else if (href === '/' && currentPath === '/') {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // Initialize active links
    updateActiveLinks();

    // === EVENT LISTENERS ===

    // Close button (X) functionality
    if (navbarCloseX) {
        navbarCloseX.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeMenu();
        });
    }

    // Auto-close on nav link click (mobile only)
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't close for dropdowns or buttons
            if (link.classList.contains('dropdown-toggle') || 
                link.closest('.dropdown-menu') || 
                link.tagName === 'BUTTON') {
                return;
            }
            
            if (isMobile()) {
                setTimeout(() => closeMenu(), 150);
            }
        });
    });

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && navbarCollapse.classList.contains('show')) {
            closeMenu();
        }
    });

    // Close on outside click (mobile only)
    document.addEventListener('click', function(e) {
        if (isMobile() && 
            navbarCollapse.classList.contains('show') &&
            !navbarCollapse.contains(e.target) &&
            !navbarToggler.contains(e.target)) {
            closeMenu();
        }
    });

    // === TOUCH GESTURES ===
    
    let touchStartX = 0;
    let touchStartY = 0;

    navbarCollapse.addEventListener('touchstart', function(e) {
        if (e.touches && e.touches.length > 0) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }
    }, { passive: true });

    navbarCollapse.addEventListener('touchmove', function(e) {
        if (!navbarCollapse.classList.contains('show') || !e.touches || e.touches.length === 0) return;

        const touchX = e.touches[0].clientX;
        const touchY = e.touches[0].clientY;
        const deltaX = touchX - touchStartX;
        const deltaY = touchY - touchStartY;

        // Swipe left to close menu
        if (deltaX < -50 && Math.abs(deltaY) < 100) {
            closeMenu();
        }
    }, { passive: true });

    // === MUTATION OBSERVER ===
    
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                const isOpen = navbarCollapse.classList.contains('show');
                toggleBodyScroll(isOpen);
                navbarToggler.setAttribute('aria-expanded', isOpen);
                
                // Update ARIA labels
                if (isOpen) {
                    navbarToggler.setAttribute('aria-label', 'Fechar menu de navegação');
                } else {
                    navbarToggler.setAttribute('aria-label', 'Abrir menu de navegação');
                }
            }
        });
    });

    observer.observe(navbarCollapse, {
        attributes: true,
        attributeFilter: ['class']
    });

    // === RESPONSIVE BEHAVIOR ===
    
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Close menu if switching to desktop
            if (!isMobile() && navbarCollapse.classList.contains('show')) {
                closeMenu();
            }
        }, 250);
    });

    // === ACCESSIBILITY ENHANCEMENTS ===
    
    // Focus management
    navbarToggler.addEventListener('click', function() {
        setTimeout(() => {
            if (navbarCollapse.classList.contains('show')) {
                // Focus first nav link when menu opens
                const firstNavLink = navbarCollapse.querySelector('.nav-link');
                if (firstNavLink) {
                    firstNavLink.focus();
                }
            }
        }, 350); // Wait for animation
    });

    // Trap focus within mobile menu
    if (isMobile()) {
        navbarCollapse.addEventListener('keydown', function(e) {
            if (e.key === 'Tab' && navbarCollapse.classList.contains('show')) {
                const focusableElements = navbarCollapse.querySelectorAll(
                    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
                );
                
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }

    console.log('🧭 Unified navigation initialized successfully');
}

// === GLOBAL UTILITIES ===

// Export for use in other scripts
window.NavigationUtils = {
    closeMenu: function() {
        const navbarCollapse = document.querySelector('.navbar-collapse');
        if (navbarCollapse && navbarCollapse.classList.contains('show')) {
            const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
            if (bsCollapse) {
                bsCollapse.hide();
            }
        }
    },
    
    isMobile: function() {
        return window.innerWidth <= 991.98;
    },
    
    updateActiveLinks: function() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        navLinks.forEach(function(link) {
            const href = link.getAttribute('href');
            if (href && currentPath.startsWith(href) && href !== '/') {
                link.classList.add('active');
            } else if (href === '/' && currentPath === '/') {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
};
