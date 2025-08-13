// static/js/epub-viewer.js
window.initEpubViewer = function(epubUrl, bookSlug, userIsAuthenticated) {
    if (!window.ePub) {
        console.error('epub.js não carregado!');
        return;
    }
    var book = ePub(epubUrl);
    var rendition = book.renderTo("epub-reader", {
        width: "100%",
        height: 600,
        flow: "paginated",
        manager: "default",
        allowScriptedContent: true
    });

    // Função para buscar progresso do backend
    function fetchProgress(callback) {
        if (!userIsAuthenticated) {
            var key = 'epub-pos-' + epubUrl;
            callback(localStorage.getItem(key));
            return;
        }
        fetch(`/livros/${bookSlug}/progress/`, { credentials: 'same-origin' })
            .then(r => r.json())
            .then(data => callback(data.location || undefined))
            .catch(() => callback(undefined));
    }
    // Função para salvar progresso no backend
    function saveProgress(location) {
        if (!userIsAuthenticated) {
            var key = 'epub-pos-' + epubUrl;
            localStorage.setItem(key, location);
            return;
        }
        fetch(`/livros/${bookSlug}/progress/save/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: new URLSearchParams({ location })
        });
    }
    // Utilitário para CSRF
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

    // Restaurar posição
    fetchProgress(function(storedLoc) {
        rendition.display(storedLoc || undefined);
    });

    // Salvar posição ao navegar
    rendition.on('relocated', function(location) {
        saveProgress(location.start.cfi);
    });

    // Tema claro/escuro
    function setTheme(theme) {
        if (theme === 'dark') {
            rendition.themes.default({
                body: { background: '#23272f', color: '#f8f9fa' }
            });
        } else {
            rendition.themes.default({
                body: { background: '#fff', color: '#222' }
            });
        }
    }
    var theme = document.body.getAttribute('data-theme');
    setTheme(theme);
    var observer = new MutationObserver(function() {
        setTheme(document.body.getAttribute('data-theme'));
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });

    // Navegação básica
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowRight') rendition.next();
        if (e.key === 'ArrowLeft') rendition.prev();
    });
    // Touch para mobile
    var reader = document.getElementById('epub-reader');
    var startX = null;
    reader.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
    });
    reader.addEventListener('touchend', function(e) {
        if (startX === null) return;
        var dx = e.changedTouches[0].clientX - startX;
        if (dx > 50) rendition.prev();
        if (dx < -50) rendition.next();
        startX = null;
    });

    // Sumário (TOC)
    book.loaded.navigation.then(function(toc) {
        var tocList = toc.toc;
        if (!tocList || tocList.length === 0) return;
        // Cria container do TOC
        var tocContainer = document.createElement('div');
        tocContainer.id = 'epub-toc';
        tocContainer.style.cssText = 'margin-bottom: 1rem; overflow-x: auto; white-space: nowrap;';
        // Botão TOC mobile
        var tocToggle = document.createElement('button');
        tocToggle.textContent = 'Sumário';
        tocToggle.className = 'btn btn-outline-primary btn-sm mb-2 d-lg-none';
        tocToggle.onclick = function() {
            tocContainer.classList.toggle('show-toc');
        };
        reader.parentNode.insertBefore(tocToggle, reader);
        // Lista de capítulos
        var ul = document.createElement('ul');
        ul.className = 'nav nav-pills flex-nowrap mb-2';
        ul.style.cssText = 'overflow-x: auto;';
        tocList.forEach(function(item, idx) {
            var li = document.createElement('li');
            li.className = 'nav-item';
            var a = document.createElement('a');
            a.className = 'nav-link text-truncate';
            a.href = '#';
            a.textContent = item.label;
            a.title = item.label;
            a.onclick = function(e) {
                e.preventDefault();
                rendition.display(item.href);
                tocContainer.classList.remove('show-toc');
            };
            li.appendChild(a);
            ul.appendChild(li);
        });
        tocContainer.appendChild(ul);
        reader.parentNode.insertBefore(tocContainer, reader);
        // Estilo TOC
        var epubTocStyleElement = document.createElement('style');
epubTocStyleElement.textContent = `
            #epub-toc { background: #f8f9fa; border-radius: 0.5rem; padding: 0.5rem 0.5rem 0 0.5rem; }
            #epub-toc ul { margin-bottom: 0; }
            #epub-toc .nav-link { max-width: 180px; }
            #epub-toc.show-toc { display: block !important; }
            @media (max-width: 991px) {
                #epub-toc { display: none; }
                #epub-toc.show-toc { display: block; position: absolute; z-index: 10; background: #fff; width: 90vw; left: 5vw; top: 60px; box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
            }
        `;
        document.head.appendChild(epubTocStyleElement);
    });
};