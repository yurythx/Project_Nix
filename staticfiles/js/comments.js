/**
 * Sistema de Comentários - JavaScript
 * Gerencia interações em tempo real, WebSockets e AJAX
 */

class CommentsSystem {
    constructor(options = {}) {
        this.options = {
            contentType: options.contentType || null,
            objectId: options.objectId || null,
            apiUrl: options.apiUrl || '/api/comments/',
            csrfToken: options.csrfToken || this.getCsrfToken(),
            websocketUrl: options.websocketUrl || this.getWebSocketUrl(),
            enableRealTime: options.enableRealTime !== false,
            autoRefresh: options.autoRefresh !== false,
            refreshInterval: options.refreshInterval || 30000, // 30 segundos
            maxRetries: options.maxRetries || 3,
            ...options
        };
        
        this.websocket = null;
        this.retryCount = 0;
        this.isConnected = false;
        this.pendingActions = [];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupWebSocket();
        this.setupAutoRefresh();
        this.setupNotifications();
    }
    
    // ==================== EVENT BINDING ====================
    
    bindEvents() {
        // Formulário principal de comentário
        const mainForm = document.getElementById('comment-form');
        if (mainForm) {
            mainForm.addEventListener('submit', (e) => this.handleCommentSubmit(e));
        }
        
        // Formulários de resposta
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('reply-form')) {
                this.handleReplySubmit(e);
            }
        });
        
        // Formulários de edição
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('edit-form')) {
                this.handleEditSubmit(e);
            }
        });
        
        // Botões de reação
        document.addEventListener('click', (e) => {
            if (e.target.closest('.reaction-btn')) {
                this.handleReaction(e);
            }
        });
        
        // Botões de resposta
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('reply-btn')) {
                this.toggleReplyForm(e);
            }
        });
        
        // Botões de edição
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('edit-btn')) {
                this.toggleEditForm(e);
            }
        });
        
        // Botões de exclusão
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-btn')) {
                this.handleDelete(e);
            }
        });
        
        // Botões de denúncia
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('report-btn')) {
                this.handleReport(e);
            }
        });
        
        // Botões de fixar/desfixar
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('pin-btn')) {
                this.handlePin(e);
            }
        });
        
        // Carregar mais comentários
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('load-more-btn')) {
                this.loadMoreComments(e);
            }
        });
        
        // Carregar respostas
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('load-replies-btn')) {
                this.loadReplies(e);
            }
        });
    }
    
    // ==================== WEBSOCKET ====================
    
    setupWebSocket() {
        if (!this.options.enableRealTime || !this.options.websocketUrl) {
            return;
        }
        
        try {
            this.websocket = new WebSocket(this.options.websocketUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket conectado');
                this.isConnected = true;
                this.retryCount = 0;
                this.processPendingActions();
                this.joinCommentGroup();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket desconectado');
                this.isConnected = false;
                this.reconnectWebSocket();
            };
            
            this.websocket.onerror = (error) => {
                console.error('Erro no WebSocket:', error);
                this.isConnected = false;
            };
            
        } catch (error) {
            console.error('Erro ao conectar WebSocket:', error);
        }
    }
    
    reconnectWebSocket() {
        if (this.retryCount >= this.options.maxRetries) {
            console.log('Máximo de tentativas de reconexão atingido');
            return;
        }
        
        this.retryCount++;
        const delay = Math.pow(2, this.retryCount) * 1000; // Backoff exponencial
        
        setTimeout(() => {
            console.log(`Tentativa de reconexão ${this.retryCount}/${this.options.maxRetries}`);
            this.setupWebSocket();
        }, delay);
    }
    
    joinCommentGroup() {
        if (!this.isConnected || !this.options.contentType || !this.options.objectId) {
            return;
        }
        
        this.sendWebSocketMessage({
            action: 'join_group',
            content_type: this.options.contentType,
            object_id: this.options.objectId
        });
    }
    
    sendWebSocketMessage(data) {
        if (this.isConnected && this.websocket) {
            this.websocket.send(JSON.stringify(data));
        } else {
            this.pendingActions.push(data);
        }
    }
    
    processPendingActions() {
        while (this.pendingActions.length > 0) {
            const action = this.pendingActions.shift();
            this.sendWebSocketMessage(action);
        }
    }
    
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'comment_update':
                    this.handleCommentUpdate(data.data);
                    break;
                case 'reaction_update':
                    this.handleReactionUpdate(data.data);
                    break;
                case 'thread_update':
                    this.handleThreadUpdate(data.data);
                    break;
                case 'notification':
                    this.handleNotification(data.data);
                    break;
                case 'moderation_update':
                    this.handleModerationUpdate(data.data);
                    break;
                default:
                    console.log('Tipo de mensagem WebSocket desconhecido:', data.type);
            }
        } catch (error) {
            console.error('Erro ao processar mensagem WebSocket:', error);
        }
    }
    
    // ==================== COMMENT HANDLERS ====================
    
    async handleCommentSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const formData = new FormData(form);
        
        this.setLoading(submitBtn, true);
        
        try {
            const response = await this.makeRequest(form.action, {
                method: 'POST',
                body: formData
            });
            
            if (response.success) {
                this.showMessage('success', response.message || 'Comentário enviado com sucesso!');
                form.reset();
                
                if (response.comment_html) {
                    this.addCommentToDOM(response.comment_html);
                }
                
                this.updateCommentCount(1);
            } else {
                this.handleFormErrors(form, response.errors);
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao enviar comentário. Tente novamente.');
            console.error('Erro ao enviar comentário:', error);
        } finally {
            this.setLoading(submitBtn, false);
        }
    }
    
    async handleReplySubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const commentId = form.dataset.commentId;
        const submitBtn = form.querySelector('button[type="submit"]');
        const formData = new FormData(form);
        
        this.setLoading(submitBtn, true);
        
        try {
            const response = await this.makeRequest(form.action, {
                method: 'POST',
                body: formData
            });
            
            if (response.success) {
                this.showMessage('success', response.message || 'Resposta enviada com sucesso!');
                form.reset();
                this.hideReplyForm(commentId);
                
                if (response.reply_html) {
                    this.addReplyToDOM(commentId, response.reply_html);
                }
                
                this.updateReplyCount(commentId, 1);
            } else {
                this.handleFormErrors(form, response.errors);
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao enviar resposta. Tente novamente.');
            console.error('Erro ao enviar resposta:', error);
        } finally {
            this.setLoading(submitBtn, false);
        }
    }
    
    async handleEditSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const commentId = form.dataset.commentId;
        const submitBtn = form.querySelector('button[type="submit"]');
        const formData = new FormData(form);
        
        this.setLoading(submitBtn, true);
        
        try {
            const response = await this.makeRequest(form.action, {
                method: 'POST',
                body: formData
            });
            
            if (response.success) {
                this.showMessage('success', response.message || 'Comentário editado com sucesso!');
                this.hideEditForm(commentId);
                
                if (response.comment_html) {
                    this.updateCommentInDOM(commentId, response.comment_html);
                }
            } else {
                this.handleFormErrors(form, response.errors);
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao editar comentário. Tente novamente.');
            console.error('Erro ao editar comentário:', error);
        } finally {
            this.setLoading(submitBtn, false);
        }
    }
    
    // ==================== REACTION HANDLERS ====================
    
    async handleReaction(e) {
        e.preventDefault();
        
        const btn = e.target.closest('.reaction-btn');
        const commentId = btn.dataset.commentId;
        const action = btn.dataset.action;
        
        if (btn.disabled) return;
        
        btn.disabled = true;
        
        try {
            const response = await this.makeRequest(`${this.options.apiUrl}${commentId}/reaction/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.options.csrfToken
                },
                body: JSON.stringify({ action })
            });
            
            if (response.success) {
                this.updateReactionUI(commentId, action, response.data);
            } else {
                this.showMessage('error', response.message || 'Erro ao processar reação.');
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao processar reação. Tente novamente.');
            console.error('Erro na reação:', error);
        } finally {
            btn.disabled = false;
        }
    }
    
    updateReactionUI(commentId, action, data) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const likeBtn = commentElement.querySelector('.like-btn');
        const dislikeBtn = commentElement.querySelector('.dislike-btn');
        
        // Atualiza contadores
        if (likeBtn) {
            const likeCount = likeBtn.querySelector('.reaction-count');
            if (likeCount) likeCount.textContent = data.likes_count || 0;
        }
        
        if (dislikeBtn) {
            const dislikeCount = dislikeBtn.querySelector('.reaction-count');
            if (dislikeCount) dislikeCount.textContent = data.dislikes_count || 0;
        }
        
        // Atualiza estado ativo
        likeBtn?.classList.toggle('active', data.user_reaction === 'like');
        dislikeBtn?.classList.toggle('active', data.user_reaction === 'dislike');
    }
    
    // ==================== UI HELPERS ====================
    
    toggleReplyForm(e) {
        e.preventDefault();
        
        const btn = e.target;
        const commentId = btn.dataset.commentId;
        const replyContainer = document.getElementById(`reply-form-${commentId}`);
        
        if (replyContainer) {
            const isVisible = replyContainer.style.display !== 'none';
            replyContainer.style.display = isVisible ? 'none' : 'block';
            btn.textContent = isVisible ? '💬 Responder' : '❌ Cancelar';
            
            if (!isVisible) {
                const textarea = replyContainer.querySelector('textarea');
                if (textarea) textarea.focus();
            }
        }
    }
    
    hideReplyForm(commentId) {
        const replyContainer = document.getElementById(`reply-form-${commentId}`);
        const replyBtn = document.querySelector(`[data-comment-id="${commentId}"].reply-btn`);
        
        if (replyContainer) {
            replyContainer.style.display = 'none';
        }
        
        if (replyBtn) {
            replyBtn.textContent = '💬 Responder';
        }
    }
    
    toggleEditForm(e) {
        e.preventDefault();
        
        const btn = e.target;
        const commentId = btn.dataset.commentId;
        const editContainer = document.getElementById(`edit-form-${commentId}`);
        const commentText = document.getElementById(`comment-text-${commentId}`);
        
        if (editContainer && commentText) {
            const isVisible = editContainer.style.display !== 'none';
            editContainer.style.display = isVisible ? 'none' : 'block';
            commentText.style.display = isVisible ? 'block' : 'none';
            btn.textContent = isVisible ? '✏️ Editar' : '❌ Cancelar';
            
            if (!isVisible) {
                const textarea = editContainer.querySelector('textarea');
                if (textarea) textarea.focus();
            }
        }
    }
    
    hideEditForm(commentId) {
        const editContainer = document.getElementById(`edit-form-${commentId}`);
        const commentText = document.getElementById(`comment-text-${commentId}`);
        const editBtn = document.querySelector(`[data-comment-id="${commentId}"].edit-btn`);
        
        if (editContainer) {
            editContainer.style.display = 'none';
        }
        
        if (commentText) {
            commentText.style.display = 'block';
        }
        
        if (editBtn) {
            editBtn.textContent = '✏️ Editar';
        }
    }
    
    async handleDelete(e) {
        e.preventDefault();
        
        const btn = e.target;
        const commentId = btn.dataset.commentId;
        
        if (!confirm('Tem certeza que deseja excluir este comentário?')) {
            return;
        }
        
        btn.disabled = true;
        
        try {
            const response = await this.makeRequest(`${this.options.apiUrl}${commentId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.options.csrfToken
                }
            });
            
            if (response.success) {
                this.removeCommentFromDOM(commentId);
                this.showMessage('success', response.message || 'Comentário excluído com sucesso!');
                this.updateCommentCount(-1);
            } else {
                this.showMessage('error', response.message || 'Erro ao excluir comentário.');
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao excluir comentário. Tente novamente.');
            console.error('Erro ao excluir comentário:', error);
        } finally {
            btn.disabled = false;
        }
    }
    
    async handleReport(e) {
        e.preventDefault();
        
        const btn = e.target;
        const commentId = btn.dataset.commentId;
        const reason = prompt('Motivo da denúncia:');
        
        if (!reason || reason.trim() === '') {
            return;
        }
        
        btn.disabled = true;
        
        try {
            const response = await this.makeRequest(`${this.options.apiUrl}${commentId}/report/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.options.csrfToken
                },
                body: JSON.stringify({ reason: reason.trim() })
            });
            
            if (response.success) {
                this.showMessage('success', response.message || 'Comentário denunciado com sucesso!');
                btn.style.display = 'none';
            } else {
                this.showMessage('error', response.message || 'Erro ao denunciar comentário.');
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao denunciar comentário. Tente novamente.');
            console.error('Erro ao denunciar comentário:', error);
        } finally {
            btn.disabled = false;
        }
    }
    
    async handlePin(e) {
        e.preventDefault();
        
        const btn = e.target;
        const commentId = btn.dataset.commentId;
        const isPinned = btn.classList.contains('pinned');
        
        btn.disabled = true;
        
        try {
            const response = await this.makeRequest(`${this.options.apiUrl}${commentId}/pin/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.options.csrfToken
                }
            });
            
            if (response.success) {
                btn.classList.toggle('pinned', !isPinned);
                btn.textContent = isPinned ? '📌 Fixar' : '📌 Desfixar';
                this.showMessage('success', response.message || `Comentário ${isPinned ? 'desfixado' : 'fixado'} com sucesso!`);
                
                // Atualiza indicador visual
                const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
                const pinnedIndicator = commentElement?.querySelector('.pinned-indicator');
                if (pinnedIndicator) {
                    pinnedIndicator.style.display = isPinned ? 'none' : 'inline';
                }
            } else {
                this.showMessage('error', response.message || 'Erro ao fixar/desfixar comentário.');
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao fixar/desfixar comentário. Tente novamente.');
            console.error('Erro ao fixar/desfixar comentário:', error);
        } finally {
            btn.disabled = false;
        }
    }
    
    // ==================== DOM MANIPULATION ====================
    
    addCommentToDOM(commentHtml) {
        const commentsList = document.getElementById('comments-list');
        if (!commentsList) return;
        
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = commentHtml;
        const newComment = tempDiv.firstElementChild;
        
        if (newComment) {
            commentsList.insertBefore(newComment, commentsList.firstChild);
            this.animateElement(newComment, 'fadeIn');
        }
    }
    
    addReplyToDOM(parentCommentId, replyHtml) {
        const repliesContainer = document.getElementById(`replies-${parentCommentId}`);
        if (!repliesContainer) return;
        
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = replyHtml;
        const newReply = tempDiv.firstElementChild;
        
        if (newReply) {
            repliesContainer.appendChild(newReply);
            this.animateElement(newReply, 'fadeIn');
        }
    }
    
    updateCommentInDOM(commentId, commentHtml) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = commentHtml;
        const updatedComment = tempDiv.firstElementChild;
        
        if (updatedComment) {
            commentElement.parentNode.replaceChild(updatedComment, commentElement);
            this.animateElement(updatedComment, 'pulse');
        }
    }
    
    removeCommentFromDOM(commentId) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (commentElement) {
            this.animateElement(commentElement, 'fadeOut', () => {
                commentElement.remove();
            });
        }
    }
    
    updateCommentCount(delta) {
        const countElement = document.querySelector('.comment-count');
        if (countElement) {
            const currentCount = parseInt(countElement.textContent) || 0;
            countElement.textContent = Math.max(0, currentCount + delta);
        }
    }
    
    updateReplyCount(commentId, delta) {
        const replyCountElement = document.querySelector(`[data-comment-id="${commentId}"] .reply-count`);
        if (replyCountElement) {
            const currentCount = parseInt(replyCountElement.textContent) || 0;
            replyCountElement.textContent = Math.max(0, currentCount + delta);
        }
    }
    
    // ==================== WEBSOCKET EVENT HANDLERS ====================
    
    handleCommentUpdate(data) {
        switch (data.action) {
            case 'created':
                if (data.comment && data.user && data.user.id !== this.getCurrentUserId()) {
                    this.addCommentToDOM(data.comment_html);
                    this.showNotification('Novo comentário adicionado!');
                }
                break;
            case 'updated':
                if (data.comment) {
                    this.updateCommentInDOM(data.comment.uuid, data.comment_html);
                }
                break;
            case 'deleted':
                if (data.comment) {
                    this.removeCommentFromDOM(data.comment.uuid);
                }
                break;
        }
    }
    
    handleReactionUpdate(data) {
        if (data.comment_uuid && data.reaction_data) {
            this.updateReactionUI(data.comment_uuid, null, data.reaction_data);
        }
    }
    
    handleThreadUpdate(data) {
        if (data.action === 'reply_added' && data.affected_comment) {
            const parentId = data.root_comment_id;
            this.updateReplyCount(parentId, 1);
            
            if (data.affected_comment_html) {
                this.addReplyToDOM(parentId, data.affected_comment_html);
            }
        }
    }
    
    handleNotification(data) {
        this.showNotification(data.title, data.message, data.type);
    }
    
    handleModerationUpdate(data) {
        if (data.comment_uuid) {
            const commentElement = document.querySelector(`[data-comment-id="${data.comment_uuid}"]`);
            if (commentElement) {
                // Atualiza status de moderação
                const statusBadge = commentElement.querySelector('.status-badge');
                if (statusBadge) {
                    statusBadge.textContent = data.status;
                    statusBadge.className = `status-badge status-${data.status}`;
                }
            }
        }
    }
    
    // ==================== UTILITIES ====================
    
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.options.csrfToken,
                ...options.headers
            }
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    setLoading(element, isLoading) {
        if (!element) return;
        
        if (isLoading) {
            element.disabled = true;
            element.dataset.originalText = element.textContent;
            element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
        } else {
            element.disabled = false;
            element.textContent = element.dataset.originalText || 'Enviar';
        }
    }
    
    showMessage(type, message) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.comments-container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove após 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    showNotification(title, message = '', type = 'info') {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/favicon.ico'
            });
        } else {
            this.showMessage(type, `${title}${message ? ': ' + message : ''}`);
        }
    }
    
    handleFormErrors(form, errors) {
        // Remove erros anteriores
        form.querySelectorAll('.field-error').forEach(el => el.remove());
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        
        if (errors) {
            Object.entries(errors).forEach(([field, fieldErrors]) => {
                const fieldElement = form.querySelector(`[name="${field}"]`);
                if (fieldElement) {
                    fieldElement.classList.add('is-invalid');
                    
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'field-error text-danger small';
                    errorDiv.textContent = Array.isArray(fieldErrors) ? fieldErrors[0] : fieldErrors;
                    
                    fieldElement.parentNode.appendChild(errorDiv);
                }
            });
        }
    }
    
    animateElement(element, animation, callback) {
        element.classList.add(`animate-${animation}`);
        
        element.addEventListener('animationend', function handler() {
            element.removeEventListener('animationend', handler);
            element.classList.remove(`animate-${animation}`);
            if (callback) callback();
        });
    }
    
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     document.querySelector('meta[name=csrf-token]')?.content ||
                     this.getCookie('csrftoken');
        return token;
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/comments/`;
    }
    
    getCurrentUserId() {
        // Implementar conforme sua autenticação
        const userElement = document.querySelector('[data-user-id]');
        return userElement ? parseInt(userElement.dataset.userId) : null;
    }
    
    setupAutoRefresh() {
        if (!this.options.autoRefresh) return;
        
        setInterval(() => {
            if (!this.isConnected) {
                this.refreshComments();
            }
        }, this.options.refreshInterval);
    }
    
    setupNotifications() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    async refreshComments() {
        try {
            const response = await this.makeRequest(window.location.href, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.comments_html) {
                const commentsList = document.getElementById('comments-list');
                if (commentsList) {
                    commentsList.innerHTML = response.comments_html;
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar comentários:', error);
        }
    }
    
    async loadMoreComments(e) {
        e.preventDefault();
        
        const btn = e.target;
        const page = btn.dataset.page;
        
        this.setLoading(btn, true);
        
        try {
            const response = await this.makeRequest(`${this.options.apiUrl}?page=${page}`);
            
            if (response.success && response.comments_html) {
                const commentsList = document.getElementById('comments-list');
                if (commentsList) {
                    commentsList.insertAdjacentHTML('beforeend', response.comments_html);
                }
                
                if (response.has_next) {
                    btn.dataset.page = parseInt(page) + 1;
                } else {
                    btn.style.display = 'none';
                }
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao carregar mais comentários.');
            console.error('Erro ao carregar mais comentários:', error);
        } finally {
            this.setLoading(btn, false);
        }
    }
    
    async loadReplies(e) {
        e.preventDefault();
        
        const btn = e.target;
        const commentId = btn.dataset.commentId;
        
        this.setLoading(btn, true);
        
        try {
            const response = await this.makeRequest(`${this.options.apiUrl}${commentId}/replies/`);
            
            if (response.success && response.replies_html) {
                const repliesContainer = document.getElementById(`replies-${commentId}`);
                if (repliesContainer) {
                    repliesContainer.innerHTML = response.replies_html;
                }
                
                btn.style.display = 'none';
            }
        } catch (error) {
            this.showMessage('error', 'Erro ao carregar respostas.');
            console.error('Erro ao carregar respostas:', error);
        } finally {
            this.setLoading(btn, false);
        }
    }
    
    // ==================== PUBLIC API ====================
    
    destroy() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        // Remove event listeners se necessário
        // Implementar conforme necessidade
    }
    
    reconnect() {
        this.retryCount = 0;
        this.setupWebSocket();
    }
    
    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
    }
}

// Exporta para uso global
window.CommentsSystem = CommentsSystem;

// Auto-inicialização se houver configuração na página
document.addEventListener('DOMContentLoaded', function() {
    const configElement = document.getElementById('comments-config');
    if (configElement) {
        try {
            const config = JSON.parse(configElement.textContent);
            window.commentsSystem = new CommentsSystem(config);
        } catch (error) {
            console.error('Erro ao inicializar sistema de comentários:', error);
        }
    }
});