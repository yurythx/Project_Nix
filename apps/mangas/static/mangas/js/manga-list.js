/**
 * Manga List Page Functionality
 * Handles interactive elements on the manga list page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle manga card clicks (except on buttons and links)
    document.querySelectorAll('.manga-card').forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't navigate if clicking on a button, link, or other interactive element
            if (e.target.tagName === 'A' || 
                e.target.tagName === 'BUTTON' || 
                e.target.closest('a') || 
                e.target.closest('button')) {
                return;
            }
            
            // Find the first link in the card and navigate to it
            const link = this.querySelector('a[href]');
            if (link) {
                window.location.href = link.href;
            }
        });
    });

    // Handle search form submission with loading state
    const searchForm = document.querySelector('form[action="#"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="q"]');
            if (searchInput && searchInput.value.trim() === '') {
                e.preventDefault();
                return false;
            }
            // Add loading state
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Buscando...';
                submitButton.disabled = true;
            }
        });
    }
});
