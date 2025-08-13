// ===== DESIGN SYSTEM - BOOKS APP JAVASCRIPT =====

(function() {
    'use strict';
    
    // Configurações globais
    const CONFIG = {
        themes: ['light', 'dark', 'sepia'],
        fontSizes: ['small', 'medium', 'large'],
        storageKeys: {
            theme: 'books_theme',
            fontSize: 'books_font_size',
            favorites: 'books_favorites'
        },
        debounceDelay: 300,
        animationDuration: 300
    };
    
    // Utilitários
    const Utils = {
        // Debounce function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Throttle function
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            }
        },
        
        // Notificação simples
        notify(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type} animate-slide-down`;
            notification.textContent = message;
            
            // Estilos inline para notificação
            Object.assign(notification.style, {
                position: 'fixed',
                top: '20px',
                right: '20px',
                padding: '12px 20px',
                borderRadius: '8px',
                color: 'white',
                fontWeight: '500',
                zIndex: '9999',
                maxWidth: '300px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
            });
            
            // Cores por tipo
            const colors = {
                info: '#3b82f6',
                success: '#10b981',
                warning: '#f59e0b',
                error: '#ef4444'
            };
            notification.style.backgroundColor = colors[type] || colors.info;
            
            document.body.appendChild(notification);
            
            // Remove após 3 segundos
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
    };
    
    // Gerenciador de Temas
    const ThemeManager = {
        init() {
            this.loadTheme();
            this.bindEvents();
            this.createControls();
        },
        
        loadTheme() {
            const savedTheme = localStorage.getItem(CONFIG.storageKeys.theme) || 'light';
            this.setTheme(savedTheme);
        },
        
        setTheme(theme) {
            if (!CONFIG.themes.includes(theme)) return;
            
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem(CONFIG.storageKeys.theme, theme);
            
            // Atualiza botões ativos
            document.querySelectorAll('.theme-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.theme === theme);
            });
            
            // Atualiza ícone se existir
            const themeIcon = document.getElementById('theme-icon');
            if (themeIcon) {
                const icons = {
                    light: 'fas fa-sun',
                    dark: 'fas fa-moon',
                    sepia: 'fas fa-book'
                };
                themeIcon.className = icons[theme] || icons.light;
            }
        },
        
        createControls() {
            const container = document.querySelector('.theme-controls');
            if (!container) return;
            
            container.innerHTML = `
                <span class="control-label">Tema:</span>
                ${CONFIG.themes.map(theme => `
                    <button class="theme-btn" data-theme="${theme}" title="Tema ${theme}">
                        <i class="${this.getThemeIcon(theme)}"></i>
                        ${this.getThemeLabel(theme)}
                    </button>
                `).join('')}
            `;
        },
        
        getThemeIcon(theme) {
            const icons = {
                light: 'fas fa-sun',
                dark: 'fas fa-moon',
                sepia: 'fas fa-book'
            };
            return icons[theme] || 'fas fa-palette';
        },
        
        getThemeLabel(theme) {
            const labels = {
                light: 'Claro',
                dark: 'Escuro',
                sepia: 'Sépia'
            };
            return labels[theme] || theme;
        },
        
        bindEvents() {
            document.addEventListener('click', (e) => {
                if (e.target.closest('.theme-btn')) {
                    const theme = e.target.closest('.theme-btn').dataset.theme;
                    this.setTheme(theme);
                    Utils.notify(`Tema alterado para ${this.getThemeLabel(theme)}`, 'success');
                }
            });
        }
    };
    
    // Gerenciador de Fonte
    const FontManager = {
        init() {
            this.loadFontSize();
            this.bindEvents();
            this.createControls();
        },
        
        loadFontSize() {
            const savedSize = localStorage.getItem(CONFIG.storageKeys.fontSize) || 'medium';
            this.setFontSize(savedSize);
        },
        
        setFontSize(size) {
            if (!CONFIG.fontSizes.includes(size)) return;
            
            document.documentElement.setAttribute('data-font-size', size);
            localStorage.setItem(CONFIG.storageKeys.fontSize, size);
            
            // Aplica classes CSS baseadas no tamanho
            const multipliers = {
                small: 0.875,
                medium: 1,
                large: 1.125
            };
            
            document.documentElement.style.setProperty('--font-scale', multipliers[size]);
        },
        
        createControls() {
            const container = document.querySelector('.font-controls');
            if (!container) return;
            
            container.innerHTML = `
                <span class="control-label">Fonte:</span>
                <button class="font-btn" data-action="decrease" title="Diminuir fonte">
                    <i class="fas fa-minus"></i>
                </button>
                <span class="font-size-display">A</span>
                <button class="font-btn" data-action="increase" title="Aumentar fonte">
                    <i class="fas fa-plus"></i>
                </button>
            `;
        },
        
        bindEvents() {
            document.addEventListener('click', (e) => {
                const fontBtn = e.target.closest('.font-btn');
                if (!fontBtn) return;
                
                const action = fontBtn.dataset.action;
                const currentSize = localStorage.getItem(CONFIG.storageKeys.fontSize) || 'medium';
                const currentIndex = CONFIG.fontSizes.indexOf(currentSize);
                
                let newIndex = currentIndex;
                if (action === 'increase' && currentIndex < CONFIG.fontSizes.length - 1) {
                    newIndex++;
                } else if (action === 'decrease' && currentIndex > 0) {
                    newIndex--;
                }
                
                if (newIndex !== currentIndex) {
                    this.setFontSize(CONFIG.fontSizes[newIndex]);
                    Utils.notify(`Tamanho da fonte: ${CONFIG.fontSizes[newIndex]}`, 'info');
                }
            });
        }
    };
    
    // Sistema de Favoritos
    const FavoritesManager = {
        init() {
            this.loadFavorites();
            this.bindEvents();
        },
        
        loadFavorites() {
            this.favorites = JSON.parse(localStorage.getItem(CONFIG.storageKeys.favorites) || '[]');
            this.updateUI();
        },
        
        addFavorite(bookId) {
            if (!this.favorites.includes(bookId)) {
                this.favorites.push(bookId);
                this.saveFavorites();
                this.updateUI();
                Utils.notify('Livro adicionado aos favoritos', 'success');
            }
        },
        
        removeFavorite(bookId) {
            this.favorites = this.favorites.filter(id => id !== bookId);
            this.saveFavorites();
            this.updateUI();
            Utils.notify('Livro removido dos favoritos', 'info');
        },
        
        toggleFavorite(bookId) {
            if (this.favorites.includes(bookId)) {
                this.removeFavorite(bookId);
            } else {
                this.addFavorite(bookId);
            }
        },
        
        saveFavorites() {
            localStorage.setItem(CONFIG.storageKeys.favorites, JSON.stringify(this.favorites));
        },
        
        updateUI() {
            document.querySelectorAll('.favorite-btn').forEach(btn => {
                const bookId = btn.dataset.bookId;
                const isFavorite = this.favorites.includes(bookId);
                
                btn.classList.toggle('active', isFavorite);
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.className = isFavorite ? 'fas fa-heart' : 'far fa-heart';
                }
            });
        },
        
        bindEvents() {
            document.addEventListener('click', (e) => {
                const favoriteBtn = e.target.closest('.favorite-btn');
                if (favoriteBtn) {
                    e.preventDefault();
                    const bookId = favoriteBtn.dataset.bookId;
                    this.toggleFavorite(bookId);
                }
            });
        }
    };
    
    // Lazy Loading
    const LazyLoader = {
        init() {
            this.observer = new IntersectionObserver(this.handleIntersection.bind(this), {
                rootMargin: '50px'
            });
            
            this.observeElements();
        },
        
        observeElements() {
            document.querySelectorAll('[data-lazy]').forEach(el => {
                this.observer.observe(el);
            });
        },
        
        handleIntersection(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadElement(entry.target);
                    this.observer.unobserve(entry.target);
                }
            });
        },
        
        loadElement(element) {
            if (element.tagName === 'IMG') {
                const src = element.dataset.lazy;
                if (src) {
                    element.src = src;
                    element.classList.add('lazy-loaded');
                    element.removeAttribute('data-lazy');
                }
            } else {
                element.classList.add('lazy-loaded');
            }
        }
    };
    
    // Animações
    const AnimationManager = {
        init() {
            this.observeAnimations();
            this.bindHoverEffects();
        },
        
        observeAnimations() {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-fade-in');
                    }
                });
            }, { threshold: 0.1 });
            
            document.querySelectorAll('.book-card, .category-header, .book-form').forEach(el => {
                observer.observe(el);
            });
        },
        
        bindHoverEffects() {
            document.querySelectorAll('.btn, .book-card, .sidebar-link').forEach(el => {
                el.addEventListener('mouseenter', () => {
                    el.style.transform = 'translateY(-2px)';
                });
                
                el.addEventListener('mouseleave', () => {
                    el.style.transform = '';
                });
            });
        }
    };
    
    // Busca com Debounce
    const SearchManager = {
        init() {
            this.bindSearchEvents();
        },
        
        bindSearchEvents() {
            const searchInput = document.querySelector('#search-input, .search-input');
            if (!searchInput) return;
            
            const debouncedSearch = Utils.debounce(this.performSearch.bind(this), CONFIG.debounceDelay);
            
            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        },
        
        performSearch(query) {
            // Implementar lógica de busca aqui
            console.log('Searching for:', query);
            
            // Exemplo de filtro local
            const books = document.querySelectorAll('.book-card');
            books.forEach(book => {
                const title = book.querySelector('.book-title')?.textContent.toLowerCase() || '';
                const author = book.querySelector('.book-author')?.textContent.toLowerCase() || '';
                const searchTerm = query.toLowerCase();
                
                const matches = title.includes(searchTerm) || author.includes(searchTerm);
                book.style.display = matches ? '' : 'none';
            });
        }
    };
    
    // Atalhos de Teclado
    const KeyboardManager = {
        init() {
            this.bindKeyboardEvents();
        },
        
        bindKeyboardEvents() {
            document.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + K para focar na busca
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    const searchInput = document.querySelector('#search-input, .search-input');
                    if (searchInput) {
                        searchInput.focus();
                        Utils.notify('Campo de busca focado', 'info');
                    }
                }
                
                // Ctrl/Cmd + Shift + T para alternar tema
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                    e.preventDefault();
                    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
                    const currentIndex = CONFIG.themes.indexOf(currentTheme);
                    const nextIndex = (currentIndex + 1) % CONFIG.themes.length;
                    ThemeManager.setTheme(CONFIG.themes[nextIndex]);
                }
                
                // Ctrl/Cmd + Plus/Minus para fonte
                if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
                    e.preventDefault();
                    const currentSize = localStorage.getItem(CONFIG.storageKeys.fontSize) || 'medium';
                    const currentIndex = CONFIG.fontSizes.indexOf(currentSize);
                    if (currentIndex < CONFIG.fontSizes.length - 1) {
                        FontManager.setFontSize(CONFIG.fontSizes[currentIndex + 1]);
                    }
                }
                
                if ((e.ctrlKey || e.metaKey) && e.key === '-') {
                    e.preventDefault();
                    const currentSize = localStorage.getItem(CONFIG.storageKeys.fontSize) || 'medium';
                    const currentIndex = CONFIG.fontSizes.indexOf(currentSize);
                    if (currentIndex > 0) {
                        FontManager.setFontSize(CONFIG.fontSizes[currentIndex - 1]);
                    }
                }
            });
        }
    };
    
    // Acessibilidade
    const AccessibilityManager = {
        init() {
            this.enhanceKeyboardNavigation();
            this.addAriaLabels();
            this.setupLiveRegions();
        },
        
        enhanceKeyboardNavigation() {
            // Adiciona navegação por teclado para cards
            document.querySelectorAll('.book-card').forEach((card, index) => {
                card.setAttribute('tabindex', '0');
                card.setAttribute('role', 'article');
                
                card.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const link = card.querySelector('a');
                        if (link) link.click();
                    }
                });
            });
        },
        
        addAriaLabels() {
            // Adiciona labels para botões sem texto
            document.querySelectorAll('.theme-btn').forEach(btn => {
                if (!btn.getAttribute('aria-label')) {
                    const theme = btn.dataset.theme;
                    btn.setAttribute('aria-label', `Alterar para tema ${theme}`);
                }
            });
            
            document.querySelectorAll('.font-btn').forEach(btn => {
                if (!btn.getAttribute('aria-label')) {
                    const action = btn.dataset.action;
                    const label = action === 'increase' ? 'Aumentar fonte' : 'Diminuir fonte';
                    btn.setAttribute('aria-label', label);
                }
            });
        },
        
        setupLiveRegions() {
            // Cria região para anúncios de acessibilidade
            const liveRegion = document.createElement('div');
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            liveRegion.id = 'accessibility-announcements';
            document.body.appendChild(liveRegion);
        },
        
        announce(message) {
            const liveRegion = document.getElementById('accessibility-announcements');
            if (liveRegion) {
                liveRegion.textContent = message;
                setTimeout(() => {
                    liveRegion.textContent = '';
                }, 1000);
            }
        }
    };
    
    // Inicialização
    const BooksApp = {
        init() {
            // Aguarda o DOM estar pronto
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', this.start.bind(this));
            } else {
                this.start();
            }
        },
        
        start() {
            console.log('📚 Books Design System initialized');
            
            try {
                ThemeManager.init();
                FontManager.init();
                FavoritesManager.init();
                LazyLoader.init();
                AnimationManager.init();
                SearchManager.init();
                KeyboardManager.init();
                AccessibilityManager.init();
                
                // Adiciona classe para indicar que o JS foi carregado
                document.documentElement.classList.add('js-loaded');
                
                Utils.notify('Design System carregado com sucesso!', 'success');
            } catch (error) {
                console.error('Erro ao inicializar Books App:', error);
                Utils.notify('Erro ao carregar o sistema', 'error');
            }
        }
    };
    
    // Expõe funcionalidades globalmente se necessário
    window.BooksDesignSystem = {
        ThemeManager,
        FontManager,
        FavoritesManager,
        Utils,
        AccessibilityManager
    };
    
    // Inicializa a aplicação
    BooksApp.init();
    
})();