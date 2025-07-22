/**
 * Project Nix Theme Toggle System
 * Supports Light, Dark, and Auto themes
 */

class NixThemeToggle {
    constructor() {
        this.themes = ['light', 'dark'];
        this.currentTheme = this.getStoredTheme() || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.bindEvents();
        this.updateToggleState();
    }

    bindEvents() {
        // Bind click events to existing theme toggle buttons
        const themeButtons = document.querySelectorAll('.theme-option');
        themeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const theme = button.getAttribute('data-theme');
                this.setTheme(theme);
            });
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('theme-option')) {
                this.handleKeyboardNavigation(e);
            }
        });
    }

    handleKeyboardNavigation(e) {
        const options = Array.from(document.querySelectorAll('.theme-option'));
        const currentIndex = options.indexOf(e.target);
        let newIndex;

        switch (e.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                newIndex = currentIndex > 0 ? currentIndex - 1 : options.length - 1;
                options[newIndex].focus();
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                newIndex = currentIndex < options.length - 1 ? currentIndex + 1 : 0;
                options[newIndex].focus();
                break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                e.target.click();
                break;
        }
    }

    setTheme(theme) {
        if (!this.themes.includes(theme)) return;
        
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.storeTheme(theme);
        this.updateToggleState();
        this.announceThemeChange(theme);
    }

    applyTheme(theme) {
        const html = document.documentElement;

        // Remove existing theme classes
        html.removeAttribute('data-theme');

        // Apply the selected theme directly
        html.setAttribute('data-theme', theme);

        // Update meta theme-color
        this.updateMetaThemeColor(theme);

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme, appliedTheme: theme }
        }));
    }

    updateMetaThemeColor(theme) {
        let themeColor = '#ffffff'; // Project Nix light theme

        if (theme === 'dark') {
            themeColor = '#0f172a'; // Project Nix dark theme
        }

        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        metaThemeColor.content = themeColor;

        // Also update viewport-fit for iOS
        let viewportMeta = document.querySelector('meta[name="viewport"]');
        if (viewportMeta && !viewportMeta.content.includes('viewport-fit')) {
            viewportMeta.content += ', viewport-fit=cover';
        }
    }

    updateToggleState() {
        const options = document.querySelectorAll('.theme-option');
        options.forEach(option => {
            const isActive = option.getAttribute('data-theme') === this.currentTheme;
            option.classList.toggle('active', isActive);
            option.setAttribute('aria-checked', isActive);
            option.setAttribute('tabindex', isActive ? '0' : '-1');
        });
    }

    announceThemeChange(theme) {
        const messages = {
            light: 'Tema claro ativado',
            dark: 'Tema escuro ativado'
        };

        // Create announcement for screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = messages[theme];

        document.body.appendChild(announcement);

        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    getStoredTheme() {
        try {
            // Try new key first, fallback to old key for compatibility
            return localStorage.getItem('nix-theme') || localStorage.getItem('django-theme');
        } catch (e) {
            return null;
        }
    }

    storeTheme(theme) {
        try {
            localStorage.setItem('nix-theme', theme);
        } catch (e) {
            // Silently fail if localStorage is not available
        }
    }

    // Public API
    getCurrentTheme() {
        return this.currentTheme;
    }

    getAppliedTheme() {
        return document.documentElement.getAttribute('data-theme');
    }
}

// Initialize theme toggle when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.nixTheme = new NixThemeToggle();
    // Backward compatibility
    window.djangoTheme = window.nixTheme;
});

// Apply theme immediately to prevent flash
(function() {
    const storedTheme = localStorage.getItem('nix-theme') || localStorage.getItem('django-theme') || 'light';
    const html = document.documentElement;

    // Apply the stored theme directly (only light or dark)
    html.setAttribute('data-theme', storedTheme);
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NixThemeToggle;
}
