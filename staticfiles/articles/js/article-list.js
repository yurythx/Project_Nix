/**
 * JavaScript específico para listagem de artigos
 * Separado seguindo princípios de organização
 */

class ArticleListManager {
    constructor() {
        this.currentPage = 1;
        this.isLoading = false;
        this.filters = {
            category: '',
            tag: '',
            search: '',
            sort: '-published_at'
        };
        this.init();
    }

    init() {
        this.setupSearch();
        this.setupFilters();
        this.setupInfiniteScroll();
        this.setupSorting();
        this.setupLazyLoading();
    }

    /**
     * Configura sistema de busca
     */
    setupSearch() {
        const searchForm = document.querySelector('#search-form');
        const searchInput = document.querySelector('#search-input');
        
        if (!searchForm || !searchInput) return;

        // Busca em tempo real com debounce
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filters.search = e.target.value.trim();
                this.resetAndSearch();
            }, 500);
        });

        // Busca ao submeter formulário
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.filters.search = searchInput.value.trim();
            this.resetAndSearch();
        });

        // Limpar busca
        const clearButton = document.querySelector('#clear-search');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                searchInput.value = '';
                this.filters.search = '';
                this.resetAndSearch();
            });
        }
    }

    /**
     * Configura filtros de categoria e tags
     */
    setupFilters() {
        // Filtros de categoria
        const categoryFilters = document.querySelectorAll('[data-category-filter]');
        categoryFilters.forEach(filter => {
            filter.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active de outros filtros
                categoryFilters.forEach(f => f.classList.remove('active'));
                
                // Adiciona active ao filtro clicado
                filter.classList.add('active');
                
                this.filters.category = filter.dataset.categoryFilter;
                this.resetAndSearch();
            });
        });

        // Filtros de tag
        const tagFilters = document.querySelectorAll('[data-tag-filter]');
        tagFilters.forEach(filter => {
            filter.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Toggle active para tags (permite múltiplas)
                filter.classList.toggle('active');
                
                // Coleta todas as tags ativas
                const activeTags = Array.from(document.querySelectorAll('[data-tag-filter].active'))
                    .map(tag => tag.dataset.tagFilter);
                
                this.filters.tag = activeTags.join(',');
                this.resetAndSearch();
            });
        });
    }

    /**
     * Configura scroll infinito
     */
    setupInfiniteScroll() {
        const loadMoreButton = document.querySelector('#load-more');
        
        if (loadMoreButton) {
            loadMoreButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadMoreArticles();
            });
        }

        // Auto-load ao chegar no final da página
        window.addEventListener('scroll', () => {
            if (this.isLoading) return;
            
            const scrollTop = window.pageYOffset;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            
            if (scrollTop + windowHeight >= documentHeight - 1000) {
                this.loadMoreArticles();
            }
        });
    }

    /**
     * Configura ordenação
     */
    setupSorting() {
        const sortSelect = document.querySelector('#sort-select');
        
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.filters.sort = e.target.value;
                this.resetAndSearch();
            });
        }

        // Botões de ordenação
        const sortButtons = document.querySelectorAll('[data-sort]');
        sortButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active de outros botões
                sortButtons.forEach(b => b.classList.remove('active'));
                
                // Adiciona active ao botão clicado
                button.classList.add('active');
                
                this.filters.sort = button.dataset.sort;
                this.resetAndSearch();
            });
        });
    }

    /**
     * Configura lazy loading para imagens
     */
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    /**
     * Reseta página e faz nova busca
     */
    resetAndSearch() {
        this.currentPage = 1;
        this.searchArticles(true);
    }

    /**
     * Carrega mais artigos
     */
    async loadMoreArticles() {
        if (this.isLoading) return;
        
        this.currentPage++;
        await this.searchArticles(false);
    }

    /**
     * Busca artigos com filtros
     */
    async searchArticles(replace = true) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(replace);
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                ...this.filters
            });
            
            const response = await fetch(`/artigos/search/?${params}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            if (!response.ok) {
                throw new Error('Erro na busca');
            }
            
            const data = await response.json();
            
            this.renderArticles(data.articles, replace);
            this.updatePagination(data.pagination);
            this.updateURL(params);
            
        } catch (error) {
            console.error('Erro ao buscar artigos:', error);
            this.showError('Erro ao carregar artigos. Tente novamente.');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    /**
     * Renderiza lista de artigos
     */
    renderArticles(articles, replace = true) {
        const container = document.querySelector('#articles-container');
        if (!container) return;
        
        if (replace) {
            container.innerHTML = '';
        }
        
        if (articles.length === 0 && replace) {
            this.showEmptyState();
            return;
        }
        
        articles.forEach(article => {
            const articleElement = this.createArticleElement(article);
            container.appendChild(articleElement);
        });
        
        // Reaplica lazy loading para novas imagens
        this.setupLazyLoading();
    }

    /**
     * Cria elemento HTML para artigo
     */
    createArticleElement(article) {
        const div = document.createElement('div');
        div.className = 'col-md-6 col-lg-4 mb-4';
        
        div.innerHTML = `
            <div class="card article-card h-100">
                <img data-src="${article.featured_image || '/static/images/default-article.jpg'}" 
                     class="card-img-top lazy" 
                     alt="${article.title}"
                     style="height: 200px; object-fit: cover;">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">
                        <a href="${article.url}" class="text-decoration-none text-dark">
                            ${article.title}
                        </a>
                    </h5>
                    <p class="card-text flex-grow-1">${article.excerpt}</p>
                    <div class="article-stats mt-auto">
                        <small class="text-muted">
                            <i class="fas fa-calendar"></i> ${article.published_at}
                        </small>
                        <small class="text-muted ms-3">
                            <i class="fas fa-eye"></i> ${article.views} visualizações
                        </small>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="badge bg-primary">${article.category}</span>
                        <small class="text-muted">${article.reading_time} min</small>
                    </div>
                </div>
            </div>
        `;
        
        return div;
    }

    /**
     * Atualiza paginação
     */
    updatePagination(pagination) {
        const loadMoreButton = document.querySelector('#load-more');
        
        if (loadMoreButton) {
            if (pagination.has_next) {
                loadMoreButton.style.display = 'block';
                loadMoreButton.textContent = `Carregar mais (${pagination.remaining} restantes)`;
            } else {
                loadMoreButton.style.display = 'none';
            }
        }
    }

    /**
     * Atualiza URL sem recarregar página
     */
    updateURL(params) {
        const url = new URL(window.location);
        
        // Remove parâmetros vazios
        Object.keys(this.filters).forEach(key => {
            if (this.filters[key]) {
                url.searchParams.set(key, this.filters[key]);
            } else {
                url.searchParams.delete(key);
            }
        });
        
        window.history.replaceState({}, '', url);
    }

    /**
     * Mostra estado de loading
     */
    showLoading(replace = true) {
        const container = document.querySelector('#articles-container');
        
        if (replace) {
            container.innerHTML = this.getLoadingHTML();
        } else {
            const loadingElement = document.createElement('div');
            loadingElement.innerHTML = this.getLoadingHTML();
            container.appendChild(loadingElement);
        }
    }

    /**
     * Esconde loading
     */
    hideLoading() {
        const loadingElements = document.querySelectorAll('.loading-skeleton');
        loadingElements.forEach(el => el.remove());
    }

    /**
     * HTML para estado de loading
     */
    getLoadingHTML() {
        return Array(6).fill().map(() => `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card">
                    <div class="loading-skeleton skeleton-card"></div>
                    <div class="card-body">
                        <div class="loading-skeleton skeleton-text"></div>
                        <div class="loading-skeleton skeleton-text medium"></div>
                        <div class="loading-skeleton skeleton-text short"></div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Mostra estado vazio
     */
    showEmptyState() {
        const container = document.querySelector('#articles-container');
        container.innerHTML = `
            <div class="col-12">
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>Nenhum artigo encontrado</h3>
                    <p>Tente ajustar os filtros ou termos de busca para encontrar o que procura.</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        Ver todos os artigos
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Mostra mensagem de erro
     */
    showError(message) {
        const container = document.querySelector('#articles-container');
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger text-center">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Ops!</strong> ${message}
                    <button class="btn btn-outline-danger btn-sm ms-2" onclick="location.reload()">
                        Tentar novamente
                    </button>
                </div>
            </div>
        `;
    }
}

// Inicializa quando DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new ArticleListManager();
});

// Utilitários globais
window.ArticleListUtils = {
    /**
     * Formata data para exibição
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    },

    /**
     * Trunca texto
     */
    truncateText(text, maxLength = 150) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength).trim() + '...';
    }
};
