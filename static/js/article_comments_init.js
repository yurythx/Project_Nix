import { initializeTOC, initializeCommentForm, initializeReplyForms, initializeLazyLoadReplies, initializeLoadMoreComments } from './article_comments.js';

document.addEventListener('DOMContentLoaded', function() {
    initializeTOC();
    initializeCommentForm();
    initializeReplyForms();
    initializeLazyLoadReplies();
    initializeLoadMoreComments();
}); 