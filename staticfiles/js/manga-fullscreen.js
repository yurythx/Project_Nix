// manga-fullscreen.js - Visualizador em tela cheia para leitura de mangás

class MangaFullscreenViewer {
    constructor(options) {
        // Configurações padrão
        this.defaults = {
            containerId: 'fullscreen-container',
            readerId: 'fullscreen-reader',
            controlsClass: 'fullscreen-controls',
            pageClass: 'fullscreen-page',
            activePageClass: 'active',
            pageIndicatorId: 'fs-page-indicator',
            prevButtonId: 'fs-prev-page',
            nextButtonId: 'fs-next-page',
            closeButtonId: 'fs-close',
            toggleButtonId: 'fullscreen-toggle',
            totalPages: 0,
            startPage: 0,
            hideControlsDelay: 3000, // 3 segundos
            swipeThreshold: 50 // pixels
        };

        // Mescla as opções fornecidas com as padrão
        this.settings = { ...this.defaults, ...options };

        // Elementos do DOM
        this.elements = {};
        this.currentPage = this.settings.startPage;
        this.hideControlsTimeout = null;

        // Inicializa o visualizador
        this.init();
    }

    // Inicializa o visualizador
    init() {
        this.cacheElements();
        this.bindEvents();
        this.updatePage(this.currentPage);
    }

    // Armazena referências aos elementos do DOM
    cacheElements() {
        const { 
            containerId, 
            readerId, 
            pageClass,
            pageIndicatorId,
            prevButtonId,
            nextButtonId,
            closeButtonId,
            toggleButtonId,
            controlsClass
        } = this.settings;

        this.elements = {
            container: document.getElementById(containerId),
            reader: document.getElementById(readerId),
            pages: document.querySelectorAll(`.${pageClass}`),
            pageIndicator: document.getElementById(pageIndicatorId),
            prevButton: document.getElementById(prevButtonId),
            nextButton: document.getElementById(nextButtonId),
            closeButton: document.getElementById(closeButtonId),
            toggleButton: document.getElementById(toggleButtonId),
            controls: document.querySelector(`.${controlsClass}`)
        };
    }

    // Configura os eventos
    bindEvents() {
        const { elements } = this;

        // Navegação por botões
        if (elements.prevButton) {
            elements.prevButton.addEventListener('click', () => this.prevPage());
        }
        
        if (elements.nextButton) {
            elements.nextButton.addEventListener('click', () => this.nextPage());
        }

        // Fechar tela cheia
        if (elements.closeButton) {
            elements.closeButton.addEventListener('click', () => this.close());
        }

        // Abrir tela cheia
        if (elements.toggleButton) {
            elements.toggleButton.addEventListener('click', () => this.open());
        }

        // Teclado
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));

        // Toque/arrastar
        if (elements.reader) {
            let touchStartX = 0;
            
            elements.reader.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
                this.showControls();
            }, { passive: true });

            elements.reader.addEventListener('touchend', (e) => {
                const touchEndX = e.changedTouches[0].screenX;
                const diff = touchStartX - touchEndX;
                
                if (Math.abs(diff) > this.settings.swipeThreshold) {
                    if (diff > 0) {
                        this.nextPage();
                    } else {
                        this.prevPage();
                    }
                }
            }, { passive: true });
        }

        // Controles de mouse
        if (elements.container) {
            // Mostrar/ocultar controles ao mover o mouse
            elements.container.addEventListener('mousemove', () => {
                this.showControls();
            });

            // Navegação por clique na página
            elements.container.addEventListener('click', (e) => {
                if (e.target === elements.container || e.target === elements.reader) {
                    const rect = elements.container.getBoundingClientRect();
                    const clickX = e.clientX - rect.left;
                    const third = rect.width / 3;
                    
                    if (clickX < third) {
                        this.prevPage();
                    } else if (clickX > third * 2) {
                        this.nextPage();
                    } else {
                        this.toggleControls();
                    }
                }
            });
        }
    }

    // Atualiza a página atual
    updatePage(index) {
        const { elements, settings } = this;
        
        // Verifica se o índice é válido
        if (index < 0 || index >= settings.totalPages) {
            return;
        }

        // Atualiza a página atual
        this.currentPage = index;

        // Atualiza a exibição das páginas
        elements.pages.forEach((page, i) => {
            if (i === index) {
                page.classList.add(settings.activePageClass);
                // Rola para a página ativa
                page.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                page.classList.remove(settings.activePageClass);
            }
        });

        // Atualiza o indicador de página
        if (elements.pageIndicator) {
            elements.pageIndicator.textContent = `${index + 1} / ${settings.totalPages}`;
        }

        // Atualiza o estado dos botões de navegação
        if (elements.prevButton) {
            elements.prevButton.disabled = index === 0;
        }
        
        if (elements.nextButton) {
            elements.nextButton.disabled = index === settings.totalPages - 1;
        }

        // Mostra os controles
        this.showControls();
    }

    // Navega para a página anterior
    prevPage() {
        if (this.currentPage > 0) {
            this.updatePage(this.currentPage - 1);
        }
    }

    // Navega para a próxima página
    nextPage() {
        if (this.currentPage < this.settings.totalPages - 1) {
            this.updatePage(this.currentPage + 1);
        }
    }

    // Abre o visualizador em tela cheia
    open() {
        const { elements } = this;
        
        if (!elements.container) return;

        // Ativa o container de tela cheia
        elements.container.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // Sincroniza com a página atual do visualizador normal, se disponível
        if (window.mangaViewer && typeof window.mangaViewer.getCurrentPage === 'function') {
            const currentPage = window.mangaViewer.getCurrentPage();
            if (currentPage !== null && currentPage >= 0) {
                this.updatePage(currentPage);
            } else {
                this.updatePage(0);
            }
        } else {
            this.updatePage(0);
        }

        // Mostra os controles
        this.showControls();
    }

    // Fecha o visualizador em tela cheia
    close() {
        const { elements } = this;
        
        if (!elements.container) return;

        // Desativa o container de tela cheia
        elements.container.style.display = 'none';
        document.body.style.overflow = '';

        // Limpa o timeout de ocultar controles
        if (this.hideControlsTimeout) {
            clearTimeout(this.hideControlsTimeout);
            this.hideControlsTimeout = null;
        }
    }

    // Mostra os controles
    showControls() {
        const { elements } = this;
        
        if (!elements.controls) return;

        // Mostra os controles
        elements.controls.style.display = 'flex';

        // Configura para esconder após um tempo
        if (this.hideControlsTimeout) {
            clearTimeout(this.hideControlsTimeout);
        }

        this.hideControlsTimeout = setTimeout(() => {
            if (elements.controls) {
                elements.controls.style.display = 'none';
            }
        }, this.settings.hideControlsDelay);
    }

    // Alterna a visibilidade dos controles
    toggleControls() {
        const { elements } = this;
        
        if (!elements.controls) return;

        if (elements.controls.style.display === 'flex') {
            elements.controls.style.display = 'none';
        } else {
            this.showControls();
        }
    }

    // Manipula eventos de teclado
    handleKeyDown(e) {
        // Só processa se o visualizador estiver aberto
        if (!this.elements.container || this.elements.container.style.display !== 'block') {
            return;
        }

        switch (e.key) {
            case 'Escape':
                this.close();
                break;
            case 'ArrowLeft':
                this.prevPage();
                e.preventDefault();
                break;
            case 'ArrowRight':
            case ' ':
                this.nextPage();
                e.preventDefault();
                break;
            case 'ArrowUp':
            case 'PageUp':
                this.prevPage();
                e.preventDefault();
                break;
            case 'ArrowDown':
            case 'PageDown':
            case 'Enter':
                this.nextPage();
                e.preventDefault();
                break;
            case 'Home':
                this.updatePage(0);
                e.preventDefault();
                break;
            case 'End':
                this.updatePage(this.settings.totalPages - 1);
                e.preventDefault();
                break;
        }
    }
}

// Exporta a classe para uso global
window.MangaFullscreenViewer = MangaFullscreenViewer;
