/**
 * Sistema de Comentários para Capítulos de Mangá
 */

class MangaComments {
    constructor(options = {}) {
        this.options = {
            chapterId: null,
            apiUrl: '/mangas/api/comments/',
            ...options
        };
        
        this.currentPage = 1;
        this.currentFilter = 'all';
        this.currentSort = 'newest';
        this.comments = [];
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadComments();
        this.setupCharacterCount();
    }
    
    bindEvents() {
        // Formulário de comentário
        const commentForm = document.getElementById('comment-form');
        if (commentForm) {
            commentForm.addEventListener('submit', (e) => this.handleCommentSubmit(e));
        }
        
        // Contador de caracteres
        const commentContent = document.getElementById('comment-content');
        if (commentContent) {
            commentContent.addEventListener('input', (e) => this.updateCharacterCount(e));
        }
        
        // Filtros
        document.querySelectorAll('input[name="comment-filter"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleFilterChange(e));
        });
        
        // Ordenação
        document.querySelectorAll('[data-sort]').forEach(link => {
            link.addEventListener('click', (e) => this.handleSortChange(e));
        });
        
        // Botões de ação
        document.getElementById('refresh-comments')?.addEventListener('click', () => this.loadComments());
        document.getElementById('toggle-comments')?.addEventListener('click', () => this.toggleComments());
        
        // Modal de edição
        document.getElementById('save-edit-comment')?.addEventListener('click', () => this.saveEditComment());
        
        // Modal de reporte
        document.getElementById('submit-report')?.addEventListener('click', () => this.submitReport());
    }
    
    setupCharacterCount() {
        const editContent = document.getElementById('edit-comment-content');
        if (editContent) {
            editContent.addEventListener('input', (e) => this.updateEditCharacterCount(e));
        }
    }
    
    async loadComments(page = 1) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                chapter_id: this.options.chapterId,
                page: page,
                filter: this.currentFilter,
                sort: this.currentSort
            });
            
            const response = await fetch(`${this.options.apiUrl}?${params}`);
            const data = await response.json();
            
            if (response.ok) {
                this.renderComments(data);
                this.updateCommentCount(data.total_comments);
            } else {
                this.showError(data.error || 'Erro ao carregar comentários');
            }
        } catch (error) {
            console.error('Erro ao carregar comentários:', error);
            this.showError('Erro de conexão');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async handleCommentSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const content = formData.get('content').trim();
        const pageNumber = formData.get('page_number');
        
        if (!content) {
            this.showError('Por favor, escreva um comentário');
            return;
        }
        
        const submitBtn = form.querySelector('#submit-comment');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Enviando...';
        
        try {
            const response = await fetch(this.options.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    chapter_id: this.options.chapterId,
                    content: content,
                    page_number: pageNumber || null
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                form.reset();
                this.updateCharacterCount({ target: { value: '' } });
                this.loadComments(1); // Recarregar primeira página
                this.showSuccess('Comentário enviado com sucesso!');
            } else {
                this.showError(data.error || 'Erro ao enviar comentário');
            }
        } catch (error) {
            console.error('Erro ao enviar comentário:', error);
            this.showError('Erro de conexão');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
    
    async handleReaction(commentId, reactionType) {
        try {
            const response = await fetch(`${this.options.apiUrl}${commentId}/reaction/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ reaction_type: reactionType })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.updateReactionUI(commentId, reactionType, data.reaction_counts);
            } else {
                this.showError(data.error || 'Erro ao adicionar reação');
            }
        } catch (error) {
            console.error('Erro ao adicionar reação:', error);
            this.showError('Erro de conexão');
        }
    }
    
    async handleReply(commentId, content) {
        try {
            const response = await fetch(this.options.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    chapter_id: this.options.chapterId,
                    content: content,
                    parent_id: commentId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.loadComments(this.currentPage);
                this.showSuccess('Resposta enviada com sucesso!');
            } else {
                this.showError(data.error || 'Erro ao enviar resposta');
            }
        } catch (error) {
            console.error('Erro ao enviar resposta:', error);
            this.showError('Erro de conexão');
        }
    }
    
    async editComment(commentId, content) {
        try {
            const response = await fetch(`${this.options.apiUrl}${commentId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ content: content })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.loadComments(this.currentPage);
                this.showSuccess('Comentário editado com sucesso!');
                bootstrap.Modal.getInstance(document.getElementById('edit-comment-modal')).hide();
            } else {
                this.showError(data.error || 'Erro ao editar comentário');
            }
        } catch (error) {
            console.error('Erro ao editar comentário:', error);
            this.showError('Erro de conexão');
        }
    }
    
    async deleteComment(commentId) {
        if (!confirm('Tem certeza que deseja deletar este comentário?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.options.apiUrl}${commentId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                this.loadComments(this.currentPage);
                this.showSuccess('Comentário deletado com sucesso!');
            } else {
                const data = await response.json();
                this.showError(data.error || 'Erro ao deletar comentário');
            }
        } catch (error) {
            console.error('Erro ao deletar comentário:', error);
            this.showError('Erro de conexão');
        }
    }
    
    async reportComment(commentId, reason, description) {
        try {
            const response = await fetch(`${this.options.apiUrl}${commentId}/report/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    reason: reason,
                    description: description
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Comentário reportado com sucesso!');
                bootstrap.Modal.getInstance(document.getElementById('report-comment-modal')).hide();
            } else {
                this.showError(data.error || 'Erro ao reportar comentário');
            }
        } catch (error) {
            console.error('Erro ao reportar comentário:', error);
            this.showError('Erro de conexão');
        }
    }
    
    renderComments(data) {
        const container = document.getElementById('comments-content');
        const noComments = document.getElementById('no-comments');
        const pagination = document.getElementById('comments-pagination');
        
        if (!container) return;
        
        if (data.comments.length === 0) {
            container.style.display = 'none';
            noComments.style.display = 'block';
            pagination.style.display = 'none';
            return;
        }
        
        container.style.display = 'block';
        noComments.style.display = 'none';
        
        container.innerHTML = '';
        
        data.comments.forEach(comment => {
            const commentElement = this.createCommentElement(comment);
            container.appendChild(commentElement);
        });
        
        this.renderPagination(data);
    }
    
    createCommentElement(comment) {
        const template = document.getElementById('comment-template');
        const clone = template.content.cloneNode(true);
        
        const commentItem = clone.querySelector('.comment-item');
        commentItem.dataset.commentId = comment.id;
        
        // Avatar e informações do usuário
        const avatar = commentItem.querySelector('.comment-avatar');
        avatar.src = comment.user.avatar_url || '/static/images/default-avatar.png';
        avatar.alt = comment.user.username;
        
        commentItem.querySelector('.comment-username').textContent = comment.user.username;
        commentItem.querySelector('.comment-date').textContent = this.formatDate(comment.created_at);
        
        // Conteúdo
        commentItem.querySelector('.comment-text').textContent = comment.content;
        
        // Badges
        if (comment.page_number) {
            const pageBadge = commentItem.querySelector('.comment-page-badge');
            pageBadge.textContent = `Página ${comment.page_number}`;
            pageBadge.style.display = 'inline';
        }
        
        if (comment.is_edited) {
            commentItem.querySelector('.comment-edited-badge').style.display = 'inline';
        }
        
        // Reações
        this.updateReactionCounts(commentItem, comment.reaction_counts);
        
        // Ações baseadas em permissões
        if (!comment.can_edit) {
            commentItem.querySelector('.edit-comment').style.display = 'none';
        }
        if (!comment.can_delete) {
            commentItem.querySelector('.delete-comment').style.display = 'none';
        }
        if (!comment.can_report) {
            commentItem.querySelector('.report-comment').style.display = 'none';
        }
        
        // Event listeners
        this.bindCommentEvents(commentItem, comment);
        
        return commentItem;
    }
    
    bindCommentEvents(commentItem, comment) {
        // Reações
        commentItem.querySelectorAll('.reaction-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const reactionType = btn.dataset.reaction;
                this.handleReaction(comment.id, reactionType);
            });
        });
        
        // Editar
        commentItem.querySelector('.edit-comment')?.addEventListener('click', () => {
            this.openEditModal(comment);
        });
        
        // Deletar
        commentItem.querySelector('.delete-comment')?.addEventListener('click', () => {
            this.deleteComment(comment.id);
        });
        
        // Reportar
        commentItem.querySelector('.report-comment')?.addEventListener('click', () => {
            this.openReportModal(comment.id);
        });
        
        // Responder
        commentItem.querySelector('.reply-btn')?.addEventListener('click', () => {
            this.toggleReplyForm(commentItem);
        });
        
        // Formulário de resposta
        const replyForm = commentItem.querySelector('.reply-comment-form');
        if (replyForm) {
            replyForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const content = e.target.querySelector('textarea').value.trim();
                if (content) {
                    this.handleReply(comment.id, content);
                    this.toggleReplyForm(commentItem);
                }
            });
        }
    }
    
    openEditModal(comment) {
        document.getElementById('edit-comment-id').value = comment.id;
        document.getElementById('edit-comment-content').value = comment.content;
        this.updateEditCharacterCount({ target: { value: comment.content } });
        
        const modal = new bootstrap.Modal(document.getElementById('edit-comment-modal'));
        modal.show();
    }
    
    openReportModal(commentId) {
        document.getElementById('report-comment-id').value = commentId;
        document.getElementById('report-reason').value = '';
        document.getElementById('report-description').value = '';
        
        const modal = new bootstrap.Modal(document.getElementById('report-comment-modal'));
        modal.show();
    }
    
    toggleReplyForm(commentItem) {
        const replyForm = commentItem.querySelector('.reply-form');
        const isVisible = replyForm.style.display !== 'none';
        
        replyForm.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            replyForm.querySelector('textarea').focus();
        }
    }
    
    saveEditComment() {
        const commentId = document.getElementById('edit-comment-id').value;
        const content = document.getElementById('edit-comment-content').value.trim();
        
        if (!content) {
            this.showError('Por favor, escreva um comentário');
            return;
        }
        
        this.editComment(commentId, content);
    }
    
    submitReport() {
        const commentId = document.getElementById('report-comment-id').value;
        const reason = document.getElementById('report-reason').value;
        const description = document.getElementById('report-description').value.trim();
        
        if (!reason) {
            this.showError('Por favor, selecione um motivo');
            return;
        }
        
        this.reportComment(commentId, reason, description);
    }
    
    handleFilterChange(e) {
        this.currentFilter = e.target.value;
        this.loadComments(1);
    }
    
    handleSortChange(e) {
        e.preventDefault();
        this.currentSort = e.target.dataset.sort;
        this.loadComments(1);
    }
    
    toggleComments() {
        const container = document.getElementById('comments-container');
        const btn = document.getElementById('toggle-comments');
        const icon = btn.querySelector('i');
        
        if (container.style.display === 'none') {
            container.style.display = 'block';
            icon.className = 'fas fa-eye';
        } else {
            container.style.display = 'none';
            icon.className = 'fas fa-eye-slash';
        }
    }
    
    updateCharacterCount(e) {
        const count = e.target.value.length;
        document.getElementById('char-count').textContent = count;
    }
    
    updateEditCharacterCount(e) {
        const count = e.target.value.length;
        document.getElementById('edit-char-count').textContent = count;
    }
    
    updateReactionCounts(commentItem, counts) {
        Object.entries(counts).forEach(([type, count]) => {
            const btn = commentItem.querySelector(`[data-reaction="${type}"]`);
            if (btn) {
                btn.querySelector('.reaction-count').textContent = count;
            }
        });
    }
    
    updateReactionUI(commentId, reactionType, counts) {
        const commentItem = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (commentItem) {
            // Remover classe active de todos os botões
            commentItem.querySelectorAll('.reaction-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Adicionar classe active ao botão clicado
            const activeBtn = commentItem.querySelector(`[data-reaction="${reactionType}"]`);
            if (activeBtn) {
                activeBtn.classList.add('active');
            }
            
            // Atualizar contadores
            this.updateReactionCounts(commentItem, counts);
        }
    }
    
    renderPagination(data) {
        const pagination = document.getElementById('comments-pagination');
        const ul = pagination.querySelector('ul');
        
        if (data.total_pages <= 1) {
            pagination.style.display = 'none';
            return;
        }
        
        pagination.style.display = 'block';
        ul.innerHTML = '';
        
        // Botão anterior
        if (data.has_previous) {
            const li = document.createElement('li');
            li.className = 'page-item';
            li.innerHTML = `<a class="page-link" href="#" data-page="${data.previous_page_number}">Anterior</a>`;
            ul.appendChild(li);
        }
        
        // Páginas
        for (let i = 1; i <= data.total_pages; i++) {
            if (i === data.current_page || 
                i === 1 || 
                i === data.total_pages || 
                (i >= data.current_page - 2 && i <= data.current_page + 2)) {
                
                const li = document.createElement('li');
                li.className = `page-item ${i === data.current_page ? 'active' : ''}`;
                li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
                ul.appendChild(li);
            } else if (i === data.current_page - 3 || i === data.current_page + 3) {
                const li = document.createElement('li');
                li.className = 'page-item disabled';
                li.innerHTML = '<span class="page-link">...</span>';
                ul.appendChild(li);
            }
        }
        
        // Botão próximo
        if (data.has_next) {
            const li = document.createElement('li');
            li.className = 'page-item';
            li.innerHTML = `<a class="page-link" href="#" data-page="${data.next_page_number}">Próximo</a>`;
            ul.appendChild(li);
        }
        
        // Event listeners para paginação
        ul.querySelectorAll('.page-link[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                this.loadComments(page);
            });
        });
    }
    
    showLoading() {
        document.getElementById('comments-loading').style.display = 'block';
        document.getElementById('comments-content').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('comments-loading').style.display = 'none';
    }
    
    showError(message) {
        this.showNotification(message, 'danger');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    
    updateCommentCount(count) {
        const countElement = document.getElementById('comments-count');
        if (countElement) {
            countElement.textContent = count;
        }
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Agora mesmo';
        if (minutes < 60) return `${minutes} min atrás`;
        if (hours < 24) return `${hours}h atrás`;
        if (days < 7) return `${days} dias atrás`;
        
        return date.toLocaleDateString('pt-BR');
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    const chapterId = document.querySelector('#comment-form')?.dataset.chapterId;
    if (chapterId) {
        window.mangaComments = new MangaComments({
            chapterId: chapterId
        });
    }
}); 