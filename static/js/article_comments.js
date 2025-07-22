// static/js/article_comments.js

function getCookie(name) {
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
const csrftoken = getCookie('csrftoken');

function showLoading(btn) {
    if (btn) {
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...';
        btn.disabled = true;
    }
}
function hideLoading(btn) {
    if (btn && btn.dataset.originalText) {
        btn.innerHTML = btn.dataset.originalText;
        btn.disabled = false;
    }
}
function animateFadeIn(element) {
    if (element) {
        element.classList.add('fade-in');
        setTimeout(() => element.classList.remove('fade-in'), 1000);
    }
}
function initializeTOC() {
    const headings = document.querySelectorAll('.article-content h1, .article-content h2, .article-content h3, .article-content h4');
    const tocContainer = document.getElementById('table-django-of-contents');
    if (!tocContainer) return;
    if (headings.length > 0) {
        let tocHTML = '<ul class="list-unstyled">';
        headings.forEach(function(heading, index) {
            const id = 'heading-' + index;
            heading.id = id;
            const level = parseInt(heading.tagName.charAt(1));
            const indent = (level - 1) * 15;
            tocHTML += `
                <li style="margin-left: ${indent}px;" class="mb-1">
                    <a href="#${id}" class="text-decoration-none text-secondary">
                        ${heading.textContent}
                    </a>
                </li>
            `;
        });
        tocHTML += '</ul>';
        tocContainer.innerHTML = tocHTML;
        tocContainer.querySelectorAll('a').forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    } else {
        tocContainer.innerHTML = '<p class="text-secondary mb-0 text-body">Nenhum cabeçalho encontrado.</p>';
    }
}
function setAriaLive(feedbackId) {
    const feedback = document.getElementById(feedbackId);
    if (feedback) feedback.setAttribute('aria-live', 'polite');
}
function insertReplyHTML(commentId, html) {
    const repliesContainer = document.getElementById('replies-for-' + commentId);
    if (repliesContainer && html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const newReply = temp.firstElementChild;
        repliesContainer.appendChild(newReply);
        animateFadeIn(newReply);
    }
}
function initializeCommentForm() {
    const form = document.getElementById('comment-form');
    if (form) {
        form.onsubmit = null;
        setAriaLive('comment-feedback');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (form.classList.contains('submitting')) return;
            form.classList.add('submitting');
            const formData = new FormData(form);
            const feedback = document.getElementById('comment-feedback');
            const submitBtn = form.querySelector('button[type=submit]');
            showLoading(submitBtn);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (feedback) feedback.innerHTML = '';
                if (data.success) {
                    form.reset();
                    if (feedback) {
                        feedback.innerHTML = `<div class='alert alert-success fade-in-feedback'>${data.message || 'Comentário enviado com sucesso!'}</div>`;
                        animateFadeIn(feedback.firstElementChild);
                    }
                    if (data.is_approved && data.comment_html) {
                        const commentsList = document.getElementById('comments-list');
                        if (commentsList) {
                            const temp = document.createElement('div');
                            temp.innerHTML = data.comment_html;
                            const newComment = temp.firstElementChild;
                            commentsList.appendChild(newComment);
                            animateFadeIn(newComment);
                        }
                    }
                } else if (data.errors) {
                    let errorHtml = '<div class="alert alert-danger fade-in-feedback">';
                    for (const [field, errors] of Object.entries(data.errors)) {
                        errors.forEach(function(err) {
                            errorHtml += '<div><strong>' + field + ':</strong> ' + err.message + '</div>';
                        });
                    }
                    errorHtml += '</div>';
                    if (feedback) feedback.innerHTML = errorHtml;
                    const firstErrorField = form.querySelector('[name="' + Object.keys(data.errors)[0] + '"]');
                    if (firstErrorField) firstErrorField.focus();
                } else {
                    if (feedback) {
                        let msg = data.message;
                        if (typeof msg === 'object') msg = 'Erro ao enviar comentário.';
                        feedback.innerHTML = `<div class='alert alert-danger fade-in-feedback'>${msg || 'Erro ao enviar comentário.'}</div>`;
                    }
                }
            })
            .catch(() => {
                if (feedback) feedback.innerHTML = `<div class='alert alert-danger fade-in-feedback'>Erro de conexão ao enviar comentário.<\/div>`;
            })
            .finally(() => {
                hideLoading(submitBtn);
                form.classList.remove('submitting');
            });
        });
    }
}
function initializeReplyForms() {
    document.querySelectorAll('.reply-form').forEach(function(form) {
        form.onsubmit = null;
        const commentId = form.getAttribute('data-comment-id');
        setAriaLive('reply-feedback-' + commentId);
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (form.classList.contains('submitting')) return;
            form.classList.add('submitting');
            const feedback = document.getElementById('reply-feedback-' + commentId);
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type=submit]');
            showLoading(submitBtn);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                feedback.innerHTML = '';
                if (data.success) {
                    feedback.innerHTML = '<div class="alert alert-success" role="alert">' + data.message + '</div>';
                    animateFadeIn(feedback.firstElementChild);
                    form.reset();
                    if (data.is_approved && data.reply_html) {
                        insertReplyHTML(commentId, data.reply_html);
                    }
                } else if (data.errors) {
                    let errorHtml = '<div class="alert alert-danger" role="alert">';
                    for (const [field, errors] of Object.entries(data.errors)) {
                        errors.forEach(function(err) {
                            errorHtml += '<div><strong>' + field + ':</strong> ' + err.message + '</div>';
                        });
                    }
                    errorHtml += '</div>';
                    feedback.innerHTML = errorHtml;
                    const firstErrorField = form.querySelector('[name="' + Object.keys(data.errors)[0] + '"]');
                    if (firstErrorField) firstErrorField.focus();
                } else if (data.message) {
                    feedback.innerHTML = '<div class="alert alert-danger" role="alert">' + data.message + '</div>';
                }
            })
            .catch(() => {
                feedback.innerHTML = '<div class="alert alert-danger" role="alert">Erro ao enviar resposta. Tente novamente.</div>';
            })
            .finally(() => {
                hideLoading(submitBtn);
                form.classList.remove('submitting');
            });
        });
    });
}
// Lazy load de respostas (estrutura básica, backend deve fornecer endpoint e HTML)
function initializeLazyLoadReplies() {
    document.querySelectorAll('.btn-load-replies').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const commentId = btn.getAttribute('data-comment-id');
            btn.disabled = true;
            fetch(`/artigos/comentarios/${commentId}/replies/`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.text())
            .then(html => {
                insertReplyHTML(commentId, html);
                btn.style.display = 'none';
            })
            .catch(() => {
                btn.disabled = false;
            });
        });
    });
}
// Paginação/carregar mais comentários (estrutura básica)
function initializeLoadMoreComments() {
    const btn = document.getElementById('btn-load-more-comments');
    if (btn) {
        btn.addEventListener('click', function() {
            btn.disabled = true;
            const nextPage = btn.getAttribute('data-next-page');
            fetch(`/artigos/comentarios/?page=${nextPage}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.text())
            .then(html => {
                const commentsList = document.getElementById('comments-list');
                if (commentsList) {
                    const temp = document.createElement('div');
                    temp.innerHTML = html;
                    Array.from(temp.children).forEach(child => {
                        commentsList.appendChild(child);
                        animateFadeIn(child);
                    });
                }
                // Atualizar ou esconder botão conforme backend
            })
            .catch(() => {
                btn.disabled = false;
            });
        });
    }
}
document.addEventListener('DOMContentLoaded', function() {
    initializeTOC();
    initializeCommentForm();
    initializeReplyForms();
    initializeLazyLoadReplies();
    initializeLoadMoreComments();
});

export { initializeCommentForm, initializeReplyForms, initializeLazyLoadReplies, initializeLoadMoreComments, initializeTOC, showLoading, hideLoading, animateFadeIn, setAriaLive, insertReplyHTML, getCookie }; 