/**
 * Project Nix - Main JavaScript File
 * Custom functionality for the Project Nix CMS
 */

document.addEventListener('DOMContentLoaded', function() {

    // Initialize all components
    initializeTooltips();
    initializePopovers();
    initializeAlerts();
    initializeSearch();
    initializeUnifiedNavigation();
    initializeImageErrorHandling();
    initializeScrollEffects();

    console.log('🌟 Project Nix CMS initialized successfully!');
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Auto-dismiss alerts after 5 seconds
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Enhanced search functionality
 */
function initializeSearch() {
    const searchForms = document.querySelectorAll('form[action*="search"], form[action*="busca"]');
    
    searchForms.forEach(function(form) {
        const input = form.querySelector('input[type="search"], input[name="q"]');
        
        if (input) {
            // Add search suggestions (placeholder for future implementation)
            input.addEventListener('input', function() {
                // TODO: Implement search suggestions
            });
            
            // Add keyboard shortcuts
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    input.blur();
                }
            });
        }
    });
    
    // Global search shortcut (Ctrl/Cmd + K)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="q"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}

/**
 * Enhanced navigation
 */
function initializeNavigation() {
    // Active link highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
    });
    
    // Mobile menu drawer behavior
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Fechar menu ao clicar no overlay
        navbarCollapse.addEventListener('click', function(e) {
            if (e.target === navbarCollapse) {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse) {
                    bsCollapse.hide();
                }
            }
        });
        
        // ESC para fechar menu
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && navbarCollapse.classList.contains('show')) {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse) {
                    bsCollapse.hide();
                }
            }
        });
        
        // Bloquear scroll quando menu está aberto
        navbarCollapse.addEventListener('shown.bs.collapse', function() {
            document.body.style.overflow = 'hidden';
        });
        
        navbarCollapse.addEventListener('hidden.bs.collapse', function() {
            document.body.style.overflow = '';
        });
    }
}

/**
 * Image error handling
 */
function initializeImageErrorHandling() {
    // Handle image loading errors
    document.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            const img = e.target;
            console.warn('Image failed to load:', img.src);

            // Hide broken images
            img.style.display = 'none';

            // Optionally show a placeholder
            const container = img.closest('.img-container');
            if (container && !container.querySelector('.img-placeholder')) {
                const placeholder = document.createElement('div');
                placeholder.className = 'img-placeholder d-flex align-items-center justify-content-center bg-light text-muted';
                placeholder.style.cssText = 'width: 100%; height: 100%; min-height: 200px;';
                placeholder.innerHTML = '<i class="fas fa-image fa-2x"></i>';
                container.appendChild(placeholder);
            }
        }
    }, true);

    // Check for images that might already be broken
    const images = document.querySelectorAll('img');
    images.forEach(function(img) {
        if (img.complete && img.naturalWidth === 0) {
            img.style.display = 'none';
        }
    });
}

/**
 * Scroll effects
 */
function initializeScrollEffects() {
    let ticking = false;
    
    function updateScrollEffects() {
        const scrollTop = window.pageYOffset;
        
        // Navbar background on scroll
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (scrollTop > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
        
        // Fade in elements
        const fadeElements = document.querySelectorAll('.fade-in-on-scroll');
        fadeElements.forEach(function(element) {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('fade-in');
            }
        });
        
        ticking = false;
    }
    
    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(updateScrollEffects);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestTick);
}

/**
 * Utility functions
 */
const ProjectNix = {
    
    /**
     * Show loading state
     */
    showLoading: function(element) {
        if (element) {
            element.classList.add('loading');
            element.setAttribute('disabled', 'disabled');
        }
    },
    
    /**
     * Hide loading state
     */
    hideLoading: function(element) {
        if (element) {
            element.classList.remove('loading');
            element.removeAttribute('disabled');
        }
    },
    
    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info', duration = 5000) {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.warn('Toast container not found');
            return;
        }

        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas fa-info-circle me-2 text-${type}"></i>
                    <strong class="me-auto">Project Nix</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();

        // Auto remove from DOM after hiding
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    },
    
    /**
     * Smooth scroll to element
     */
    scrollTo: function(element, offset = 0) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
            const offsetPosition = elementPosition - offset;
            
            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    },
    
    /**
     * Copy text to clipboard
     */
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                ProjectNix.showToast('Texto copiado para a área de transferência!', 'success');
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
                ProjectNix.showToast('Erro ao copiar texto', 'danger');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                ProjectNix.showToast('Texto copiado para a área de transferência!', 'success');
            } catch (err) {
                console.error('Fallback: Oops, unable to copy', err);
                ProjectNix.showToast('Erro ao copiar texto', 'danger');
            }
            document.body.removeChild(textArea);
        }
    }
};

// Make Project Nix utilities globally available
window.ProjectNix = ProjectNix;
// Backward compatibility
window.FireFlies = ProjectNix;

// Back to Top Button
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var mybutton = document.getElementById("btn-back-to-top");
        if (!mybutton) return;
        window.onscroll = function () {
            if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
                mybutton.style.display = "block";
            } else {
                mybutton.style.display = "none";
            }
        };
        mybutton.addEventListener("click", function() {
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
        });
    });
})();

// ===== MOBILE NAVIGATION ENHANCEMENTS =====

// Melhorar a experiência do menu mobile
document.addEventListener('DOMContentLoaded', function() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const closeButton = document.querySelector('.navbar-close-x');
    const body = document.body;

    // Prevenir scroll do body quando menu está aberto
    function toggleBodyScroll(disable) {
        if (disable) {
            body.style.overflow = 'hidden';
            body.style.paddingRight = '0px'; // Compensar scrollbar
        } else {
            body.style.overflow = '';
            body.style.paddingRight = '';
        }
    }

    // Fechar menu ao clicar em links de navegação (não dropdowns)
    const mobileNavLinks = navbarCollapse?.querySelectorAll('.nav-link:not(.dropdown-toggle)');
    if (mobileNavLinks) {
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Não fechar se for dropdown ou botão
                if (link.classList.contains('dropdown-toggle') || 
                    link.closest('.dropdown-menu') || 
                    link.tagName === 'BUTTON') {
                    return;
                }
                
                if (window.innerWidth <= 991.98) {
                    setTimeout(() => {
                        navbarCollapse.classList.remove('show');
                        toggleBodyScroll(false);
                    }, 300); // Delay para permitir transição
                }
            });
        });
    }

    // Fechar menu ao clicar no botão X
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            navbarCollapse.classList.remove('show');
            toggleBodyScroll(false);
        });
    }

    // Fechar menu ao clicar fora (overlay)
    if (navbarCollapse) {
        navbarCollapse.addEventListener('click', function(e) {
            if (e.target === navbarCollapse) {
                navbarCollapse.classList.remove('show');
                toggleBodyScroll(false);
            }
        });
    }

    // Abrir menu
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            toggleBodyScroll(true);
        });
    }

    // Fechar menu ao redimensionar para desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth > 991.98) {
            navbarCollapse.classList.remove('show');
            toggleBodyScroll(false);
        }
    });

    // Adicionar animação de entrada para itens do menu
    function animateMenuItems() {
        const menuItems = navbarCollapse?.querySelectorAll('.nav-item');
        if (menuItems) {
            menuItems.forEach((item, index) => {
                item.style.opacity = '0';
                item.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    item.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    item.style.opacity = '1';
                    item.style.transform = 'translateX(0)';
                }, 100 + (index * 50));
            });
        }
    }

    // Observar quando o menu abre
    if (navbarCollapse) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (navbarCollapse.classList.contains('show')) {
                        animateMenuItems();
                    }
                }
            });
        });

        observer.observe(navbarCollapse, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
});

/**
 * Initialize Mobile Menu with slide animation
 */
function initializeMobileMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const navbarCloseX = document.querySelector('.navbar-close-x');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    if (!navbarToggler || !navbarCollapse) return;

    // Function to close menu
    function closeMenu() {
        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
        if (bsCollapse) {
            bsCollapse.hide();
        } else {
            navbarCollapse.classList.remove('show');
        }
    }

    // Function to open menu
    function openMenu() {
        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse) ||
                          new bootstrap.Collapse(navbarCollapse, { toggle: false });
        bsCollapse.show();
    }

    // Close menu when clicking X button
    if (navbarCloseX) {
        navbarCloseX.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeMenu();
        });
    }

    // Close menu when clicking on nav links (mobile)
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                setTimeout(() => closeMenu(), 150);
            }
        });
    });

    // Close menu when clicking outside (overlay)
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 &&
            navbarCollapse.classList.contains('show') &&
            !navbarCollapse.contains(e.target) &&
            !navbarToggler.contains(e.target)) {
            closeMenu();
        }
    });

    // Handle escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && navbarCollapse.classList.contains('show')) {
            closeMenu();
        }
    });

    // Prevent body scroll when menu is open
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                if (navbarCollapse.classList.contains('show')) {
                    document.body.style.overflow = 'hidden';
                } else {
                    document.body.style.overflow = '';
                }
            }
        });
    });

    observer.observe(navbarCollapse, {
        attributes: true,
        attributeFilter: ['class']
    });

    // Improve touch handling for mobile
    let touchStartX = 0;
    let touchStartY = 0;

    navbarCollapse.addEventListener('touchstart', function(e) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    });

    navbarCollapse.addEventListener('touchmove', function(e) {
        if (!navbarCollapse.classList.contains('show')) return;

        const touchX = e.touches[0].clientX;
        const touchY = e.touches[0].clientY;
        const deltaX = touchX - touchStartX;
        const deltaY = touchY - touchStartY;

        // Swipe left to close menu
        if (deltaX < -50 && Math.abs(deltaY) < 100) {
            closeMenu();
        }
    });

    console.log('📱 Mobile menu initialized with slide animation');
}
