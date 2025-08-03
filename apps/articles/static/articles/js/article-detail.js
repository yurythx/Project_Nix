/**
 * JavaScript específico para detalhes de artigos
 * Separado seguindo princípios de organização
 */

class ArticleDetailManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupReadingProgress();
        this.setupSocialSharing();
        // Sistema de comentários gerenciado por apps.comments
        this.setupPrintFunction();
        this.setupFontSizeControls();
    }

    /**
     * Configura barra de progresso de leitura
     */
    setupReadingProgress() {
        const progressBar = document.createElement('div');
        progressBar.className = 'reading-progress';
        progressBar.innerHTML = '<div class="reading-progress-bar"></div>';
        document.body.appendChild(progressBar);

        const progressBarFill = progressBar.querySelector('.reading-progress-bar');
        
        window.addEventListener('scroll', () => {
            const article = document.querySelector('.article-content');
            if (!article) return;

            const articleTop = article.offsetTop;
            const articleHeight = article.offsetHeight;
            const windowHeight = window.innerHeight;
            const scrollTop = window.pageYOffset;

            const progress = Math.min(
                Math.max((scrollTop - articleTop + windowHeight) / articleHeight, 0),
                1
            );

            progressBarFill.style.width = `${progress * 100}%`;
        });
    }

    /**
     * Configura botões de compartilhamento social
     */
    setupSocialSharing() {
        const shareButtons = document.querySelectorAll('[data-share]');
        
        shareButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const platform = button.dataset.share;
                const url = encodeURIComponent(window.location.href);
                const title = encodeURIComponent(document.title);
                
                let shareUrl = '';
                
                switch (platform) {
                    case 'twitter':
                        shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                        break;
                    case 'facebook':
                        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                        break;
                    case 'linkedin':
                        shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
                        break;
                    case 'whatsapp':
                        shareUrl = `https://wa.me/?text=${title} ${url}`;
                        break;
                }
                
                if (shareUrl) {
                    window.open(shareUrl, '_blank', 'width=600,height=400');
                }
            });
        });

        // Botão de copiar link
        const copyLinkButton = document.querySelector('[data-copy-link]');
        if (copyLinkButton) {
            copyLinkButton.addEventListener('click', async (e) => {
                e.preventDefault();
                try {
                    await navigator.clipboard.writeText(window.location.href);
                    this.showToast('Link copiado para a área de transferência!');
                } catch (err) {
                    console.error('Erro ao copiar link:', err);
                }
            });
        }
    }

    // Sistema de comentários migrado para apps.comments
    // Use article_comments.js para funcionalidades de comentários

    /**
     * Configura função de impressão
     */
    setupPrintFunction() {
        const printButton = document.querySelector('[data-print]');
        if (printButton) {
            printButton.addEventListener('click', (e) => {
                e.preventDefault();
                window.print();
            });
        }
    }

    /**
     * Configura controles de tamanho da fonte
     */
    setupFontSizeControls() {
        const increaseFontButton = document.querySelector('[data-font-increase]');
        const decreaseFontButton = document.querySelector('[data-font-decrease]');
        const resetFontButton = document.querySelector('[data-font-reset]');
        
        let currentFontSize = 1; // em rem
        
        if (increaseFontButton) {
            increaseFontButton.addEventListener('click', (e) => {
                e.preventDefault();
                currentFontSize = Math.min(currentFontSize + 0.1, 1.5);
                this.updateFontSize(currentFontSize);
            });
        }
        
        if (decreaseFontButton) {
            decreaseFontButton.addEventListener('click', (e) => {
                e.preventDefault();
                currentFontSize = Math.max(currentFontSize - 0.1, 0.8);
                this.updateFontSize(currentFontSize);
            });
        }
        
        if (resetFontButton) {
            resetFontButton.addEventListener('click', (e) => {
                e.preventDefault();
                currentFontSize = 1;
                this.updateFontSize(currentFontSize);
            });
        }
    }

    /**
     * Atualiza tamanho da fonte do artigo
     */
    updateFontSize(size) {
        const articleContent = document.querySelector('.article-content');
        if (articleContent) {
            articleContent.style.fontSize = `${size}rem`;
            localStorage.setItem('article-font-size', size);
        }
    }

    // Método showReplyForm removido - funcionalidade migrada para apps.comments

    /**
     * Mostra toast de notificação
     */
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Anima entrada
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove após 3 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Inicializa quando DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new ArticleDetailManager();
    
    // Restaura tamanho da fonte salvo
    const savedFontSize = localStorage.getItem('article-font-size');
    if (savedFontSize) {
        const articleContent = document.querySelector('.article-content');
        if (articleContent) {
            articleContent.style.fontSize = `${savedFontSize}rem`;
        }
    }
});

// CSS para elementos criados dinamicamente
const articleDetailStyleElement = document.createElement('style');
articleDetailStyleElement.textContent = `
    .reading-progress {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background-color: rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }
    
    .reading-progress-bar {
        height: 100%;
        background-color: #007bff;
        transition: width 0.1s ease;
    }
    
    .toast-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1050;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    }
    
    .toast-notification.show {
        transform: translateX(0);
    }
    
    .toast-success {
        background-color: #28a745;
    }
    
    .toast-error {
        background-color: #dc3545;
    }
    
    .reply-form {
        border-left: 3px solid #007bff;
        padding-left: 1rem;
        background-color: #f8f9fa;
        border-radius: 0 8px 8px 0;
        padding: 1rem;
    }
`;
document.head.appendChild(articleDetailStyleElement);
