// static/js/manga-viewer.js
window.initMangaViewer = function(opts) {
    var total = opts.total || 1;
    var current = 0;
    var pages = document.querySelectorAll('.manga-page');
    var prevBtn = document.getElementById('prev-page');
    var nextBtn = document.getElementById('next-page');
    var indicator = document.getElementById('page-indicator');
    function showPage(idx) {
        pages.forEach(function(page, i) {
            page.style.display = (i === idx) ? 'block' : 'none';
        });
        indicator.textContent = (idx+1) + ' / ' + total;
        prevBtn.disabled = idx === 0;
        nextBtn.disabled = idx === total-1;
        current = idx;
    }
    prevBtn && prevBtn.addEventListener('click', function() {
        if (current > 0) showPage(current-1);
    });
    nextBtn && nextBtn.addEventListener('click', function() {
        if (current < total-1) showPage(current+1);
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') prevBtn && prevBtn.click();
        if (e.key === 'ArrowRight') nextBtn && nextBtn.click();
    });
    // Touch/swipe
    var startX = null;
    var reader = document.getElementById('manga-reader');
    if (reader) {
        reader.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
        });
        reader.addEventListener('touchend', function(e) {
            if (startX === null) return;
            var dx = e.changedTouches[0].clientX - startX;
            if (dx > 50) prevBtn && prevBtn.click();
            if (dx < -50) nextBtn && nextBtn.click();
            startX = null;
        });
    }
    showPage(0);
}; 