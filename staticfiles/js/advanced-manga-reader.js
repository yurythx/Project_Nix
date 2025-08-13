/**
 * Leitor de Mangá Avançado
 * Funcionalidades inspiradas nos melhores sites de leitura de mangá
 */

class AdvancedMangaReader {
    constructor(options = {}) {
        this.options = {
            container: '#manga-reader',
            fullscreenContainer: '#fullscreen-container',
            controlsContainer: '#reader-controls',
            pageContainer: '#pages-container',
            ...options
        };
        
        this.currentPage = 1;
        this.totalPages = 0;
        this.isFullscreen = false;
        this.readingMode = 'vertical'; // vertical, horizontal, webtoon
        this.zoomLevel = 1;
        this.autoScroll = false;
        this.autoScrollSpeed = 1;
        this.readingProgress = {};
        this.sessionStartTime = Date.now();
        
        this.init();
    }
    
    init() {
        this.container = document.querySelector(this.options.container);
        this.fullscreenContainer = document.querySelector(this.options.fullscreenContainer);
        this.controlsContainer = document.querySelector(this.options.controlsContainer);
        this.pageContainer = document.querySelector(this.options.pageContainer);
        
        if (!this.container) {
            console.error('Container do leitor não encontrado');
            return;
        }
        
        this.setupEventListeners();
        this.setupControls();
        this.loadReadingProgress();
        this.startProgressTracking();
    }
    
    setupEventListeners() {
        // Navegação por teclado
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        
        // Navegação por mouse
        this.container.addEventListener('click', (e) => this.handleClick(e));
        
        // Gestos de toque
        this.setupTouchGestures();
        
        // Scroll automático
        this.setupAutoScroll();
        
        // Zoom com scroll
        this.setupZoom();
        
        // Detectar quando o usuário está lendo
        this.setupReadingDetection();
    }
    
    setupControls() {
        if (!this.controlsContainer) return;
        
        this.controlsContainer.innerHTML = `
            <div class="reader-controls-bar">
                <div class="controls-left">
                    <button class="btn btn-sm btn-outline-light" id="prev-page" title="Página Anterior (←)">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="page-indicator" id="page-indicator">1 / 1</span>
                    <button class="btn btn-sm btn-outline-light" id="next-page" title="Próxima Página (→)">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                
                <div class="controls-center">
                    <div class="reading-mode-selector">
                        <button class="btn btn-sm btn-outline-light" id="mode-vertical" title="Modo Vertical">
                            <i class="fas fa-arrows-alt-v"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light" id="mode-horizontal" title="Modo Horizontal">
                            <i class="fas fa-arrows-alt-h"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light" id="mode-webtoon" title="Modo Webtoon">
                            <i class="fas fa-stream"></i>
                        </button>
                    </div>
                    
                    <div class="zoom-controls">
                        <button class="btn btn-sm btn-outline-light" id="zoom-out" title="Diminuir Zoom (-)">
                            <i class="fas fa-search-minus"></i>
                        </button>
                        <span class="zoom-level" id="zoom-level">100%</span>
                        <button class="btn btn-sm btn-outline-light" id="zoom-in" title="Aumentar Zoom (+)">
                            <i class="fas fa-search-plus"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light" id="zoom-fit" title="Ajustar à Tela">
                            <i class="fas fa-expand-arrows-alt"></i>
                        </button>
                    </div>
                </div>
                
                <div class="controls-right">
                    <button class="btn btn-sm btn-outline-light" id="auto-scroll" title="Scroll Automático">
                        <i class="fas fa-scroll"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-light" id="fullscreen-toggle" title="Tela Cheia (F)">
                        <i class="fas fa-expand"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-light" id="close-reader" title="Fechar (ESC)">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="reading-progress"></div>
            </div>
        `;
        
        // Adicionar event listeners aos controles
        this.bindControlEvents();
    }
    
    bindControlEvents() {
        // Navegação
        document.getElementById('prev-page')?.addEventListener('click', () => this.previousPage());
        document.getElementById('next-page')?.addEventListener('click', () => this.nextPage());
        
        // Modos de leitura
        document.getElementById('mode-vertical')?.addEventListener('click', () => this.setReadingMode('vertical'));
        document.getElementById('mode-horizontal')?.addEventListener('click', () => this.setReadingMode('horizontal'));
        document.getElementById('mode-webtoon')?.addEventListener('click', () => this.setReadingMode('webtoon'));
        
        // Zoom
        document.getElementById('zoom-in')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('zoom-out')?.addEventListener('click', () => this.zoomOut());
        document.getElementById('zoom-fit')?.addEventListener('click', () => this.zoomFit());
        
        // Outros controles
        document.getElementById('auto-scroll')?.addEventListener('click', () => this.toggleAutoScroll());
        document.getElementById('fullscreen-toggle')?.addEventListener('click', () => this.toggleFullscreen());
        document.getElementById('close-reader')?.addEventListener('click', () => this.closeReader());
    }
    
    handleKeyPress(e) {
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.previousPage();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextPage();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.scrollUp();
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.scrollDown();
                break;
            case ' ':
                e.preventDefault();
                this.nextPage();
                break;
            case 'f':
            case 'F':
                e.preventDefault();
                this.toggleFullscreen();
                break;
            case 'Escape':
                if (this.isFullscreen) {
                    this.toggleFullscreen();
                }
                break;
            case '+':
            case '=':
                e.preventDefault();
                this.zoomIn();
                break;
            case '-':
                e.preventDefault();
                this.zoomOut();
                break;
            case '0':
                e.preventDefault();
                this.zoomFit();
                break;
            case 'a':
            case 'A':
                e.preventDefault();
                this.toggleAutoScroll();
                break;
        }
    }
    
    setupTouchGestures() {
        let startX = 0;
        let startY = 0;
        let startTime = 0;
        
        this.container.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            startTime = Date.now();
        });
        
        this.container.addEventListener('touchend', (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const endTime = Date.now();
            const duration = endTime - startTime;
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // Swipe horizontal
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    this.previousPage();
                } else {
                    this.nextPage();
                }
            }
            
            // Tap para próxima página
            if (Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10 && duration < 300) {
                const centerX = this.container.offsetWidth / 2;
                if (endX > centerX) {
                    this.nextPage();
                } else {
                    this.previousPage();
                }
            }
        });
    }
    
    setupAutoScroll() {
        this.autoScrollInterval = null;
        
        this.toggleAutoScroll = () => {
            this.autoScroll = !this.autoScroll;
            
            if (this.autoScroll) {
                this.startAutoScroll();
                document.getElementById('auto-scroll')?.classList.add('active');
            } else {
                this.stopAutoScroll();
                document.getElementById('auto-scroll')?.classList.remove('active');
            }
        };
    }
    
    startAutoScroll() {
        this.autoScrollInterval = setInterval(() => {
            if (this.readingMode === 'vertical') {
                window.scrollBy(0, this.autoScrollSpeed);
            } else {
                this.nextPage();
            }
        }, 100);
    }
    
    stopAutoScroll() {
        if (this.autoScrollInterval) {
            clearInterval(this.autoScrollInterval);
            this.autoScrollInterval = null;
        }
    }
    
    setupZoom() {
        this.container.addEventListener('wheel', (e) => {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                if (e.deltaY < 0) {
                    this.zoomIn();
                } else {
                    this.zoomOut();
                }
            }
        });
    }
    
    setupReadingDetection() {
        // Detectar quando o usuário está ativamente lendo
        let lastActivity = Date.now();
        const activityThreshold = 30000; // 30 segundos
        
        const updateActivity = () => {
            lastActivity = Date.now();
        };
        
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, updateActivity);
        });
        
        // Verificar se o usuário está lendo
        setInterval(() => {
            const timeSinceActivity = Date.now() - lastActivity;
            if (timeSinceActivity < activityThreshold) {
                this.updateReadingProgress();
            }
        }, 5000);
    }
    
    setReadingMode(mode) {
        this.readingMode = mode;
        this.container.className = `manga-reader mode-${mode}`;
        
        // Atualizar botões ativos
        document.querySelectorAll('.reading-mode-selector button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`mode-${mode}`)?.classList.add('active');
        
        // Aplicar estilos específicos do modo
        this.applyReadingModeStyles(mode);
        
        // Salvar preferência
        localStorage.setItem('manga-reading-mode', mode);
    }
    
    applyReadingModeStyles(mode) {
        const styles = {
            vertical: {
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '10px'
            },
            horizontal: {
                display: 'flex',
                flexDirection: 'row',
                overflowX: 'auto',
                gap: '10px'
            },
            webtoon: {
                display: 'block',
                width: '100%',
                maxWidth: '800px',
                margin: '0 auto'
            }
        };
        
        Object.assign(this.pageContainer.style, styles[mode]);
    }
    
    zoomIn() {
        this.zoomLevel = Math.min(this.zoomLevel * 1.2, 3);
        this.applyZoom();
    }
    
    zoomOut() {
        this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.3);
        this.applyZoom();
    }
    
    zoomFit() {
        this.zoomLevel = 1;
        this.applyZoom();
    }
    
    applyZoom() {
        const pages = this.pageContainer.querySelectorAll('.manga-page img');
        pages.forEach(img => {
            img.style.transform = `scale(${this.zoomLevel})`;
        });
        
        document.getElementById('zoom-level').textContent = `${Math.round(this.zoomLevel * 100)}%`;
    }
    
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.showPage(this.currentPage);
        }
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.showPage(this.currentPage);
        } else {
            // Capítulo concluído
            this.markChapterAsCompleted();
        }
    }
    
    showPage(pageNumber) {
        this.currentPage = pageNumber;
        this.updatePageIndicator();
        this.updateProgressBar();
        this.saveReadingProgress();
        
        // Scroll para a página atual
        const currentPageElement = this.pageContainer.querySelector(`[data-page="${pageNumber}"]`);
        if (currentPageElement) {
            currentPageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    updatePageIndicator() {
        const indicator = document.getElementById('page-indicator');
        if (indicator) {
            indicator.textContent = `${this.currentPage} / ${this.totalPages}`;
        }
    }
    
    updateProgressBar() {
        const progress = document.getElementById('reading-progress');
        if (progress) {
            const percentage = (this.currentPage / this.totalPages) * 100;
            progress.style.width = `${percentage}%`;
        }
    }
    
    toggleFullscreen() {
        if (!this.isFullscreen) {
            this.enterFullscreen();
        } else {
            this.exitFullscreen();
        }
    }
    
    enterFullscreen() {
        this.fullscreenContainer.style.display = 'block';
        document.body.style.overflow = 'hidden';
        this.isFullscreen = true;
        
        document.getElementById('fullscreen-toggle').innerHTML = '<i class="fas fa-compress"></i>';
        
        // Focar no container
        this.fullscreenContainer.focus();
    }
    
    exitFullscreen() {
        this.fullscreenContainer.style.display = 'none';
        document.body.style.overflow = '';
        this.isFullscreen = false;
        
        document.getElementById('fullscreen-toggle').innerHTML = '<i class="fas fa-expand"></i>';
    }
    
    loadReadingProgress() {
        const savedProgress = localStorage.getItem(`manga-progress-${this.options.mangaSlug}-${this.options.chapterSlug}`);
        if (savedProgress) {
            this.readingProgress = JSON.parse(savedProgress);
            this.currentPage = this.readingProgress.currentPage || 1;
        }
    }
    
    saveReadingProgress() {
        this.readingProgress = {
            currentPage: this.currentPage,
            totalPages: this.totalPages,
            timestamp: Date.now(),
            readingTime: Date.now() - this.sessionStartTime
        };
        
        localStorage.setItem(
            `manga-progress-${this.options.mangaSlug}-${this.options.chapterSlug}`,
            JSON.stringify(this.readingProgress)
        );
        
        // Enviar progresso para o servidor
        this.sendProgressToServer();
    }
    
    sendProgressToServer() {
        if (!this.options.userIsAuthenticated) return;
        
        fetch('/mangas/progress/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                manga_slug: this.options.mangaSlug,
                chapter_slug: this.options.chapterSlug,
                current_page: this.currentPage,
                total_pages: this.totalPages,
                reading_time: this.readingProgress.readingTime
            })
        }).catch(error => {
            console.error('Erro ao salvar progresso:', error);
        });
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }
    
    markChapterAsCompleted() {
        if (this.options.userIsAuthenticated) {
            fetch('/mangas/progress/complete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    manga_slug: this.options.mangaSlug,
                    chapter_slug: this.options.chapterSlug
                })
            });
        }
        
        // Mostrar notificação de conclusão
        this.showCompletionNotification();
    }
    
    showCompletionNotification() {
        const notification = document.createElement('div');
        notification.className = 'completion-notification';
        notification.innerHTML = `
            <div class="completion-content">
                <h3>Capítulo Concluído!</h3>
                <p>Você terminou de ler este capítulo.</p>
                <div class="completion-actions">
                    <button class="btn btn-primary" onclick="location.reload()">Ler Novamente</button>
                    <button class="btn btn-secondary" onclick="window.history.back()">Voltar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    closeReader() {
        this.saveReadingProgress();
        this.exitFullscreen();
        
        // Fechar o leitor
        if (this.options.onClose) {
            this.options.onClose();
        }
    }
    
    startProgressTracking() {
        this.sessionStartTime = Date.now();
    }
    
    updateReadingProgress() {
        // Atualizar tempo de leitura
        const readingTime = Date.now() - this.sessionStartTime;
        this.readingProgress.readingTime = readingTime;
    }
}

// Inicializar o leitor quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    if (window.mangaReaderOptions) {
        window.mangaReader = new AdvancedMangaReader(window.mangaReaderOptions);
    }
}); 