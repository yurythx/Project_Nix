/**
 * Inicializa o visualizador de EPUB
 * @param {string} bookUrl - URL do arquivo EPUB
 * @param {string} bookId - ID do livro para salvar o progresso
 * @param {boolean} isAuthenticated - Se o usuário está autenticado
 * @param {boolean} fullscreen - Se deve iniciar em tela cheia
 */
function initEpubViewer(bookUrl, bookId, isAuthenticated, fullscreen = false) {
    // Verificar se o Epub.js está disponível
    if (typeof ePub === 'undefined') {
        console.error('ePub.js não foi carregado corretamente');
        return;
    }

    // Elemento onde o leitor será renderizado
    const viewer = document.getElementById('epub-reader');
    if (!viewer) {
        console.error('Elemento #epub-reader não encontrado');
        return;
    }

    // Limpar o conteúdo atual
    viewer.innerHTML = '';

    // Criar elementos do leitor
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.overflow = 'hidden';
    container.style.position = 'relative';

    // Área de visualização
    const area = document.createElement('div');
    area.style.flex = '1';
    area.style.overflow = 'auto';
    area.style.position = 'relative';
    area.style.backgroundColor = '#f5f5f5';
    area.style.padding = '20px';
    area.style.boxSizing = 'border-box';
    
    // Configurações de fonte
    const settings = {
        fontSize: 100, // Tamanho da fonte em porcentagem
        theme: 'light', // Tema claro por padrão
        lineHeight: 1.6, // Altura da linha
        fontFamily: 'Arial, sans-serif' // Fonte
    };

    // Carregar configurações salvas
    const savedSettings = localStorage.getItem('epubViewerSettings');
    if (savedSettings) {
        Object.assign(settings, JSON.parse(savedSettings));
    }

    // Aplicar configurações
    function applySettings() {
        const isMobile = window.innerWidth <= 768;
        
        // Ajustar tamanho da fonte baseado no dispositivo
        const baseFontSize = isMobile ? 14 : 16;
        const calculatedFontSize = (settings.fontSize / 100) * baseFontSize;
        
        // Aplicar estilos ao conteúdo
        area.style.fontSize = `${calculatedFontSize}px`;
        area.style.lineHeight = settings.lineHeight;
        area.style.fontFamily = settings.fontFamily;
        area.style.color = settings.theme === 'dark' ? '#f5f5f5' : '#333';
        area.style.backgroundColor = settings.theme === 'dark' ? '#333' : '#f5f5f5';
        area.style.padding = isMobile ? '10px' : '20px';
        area.style.maxWidth = isMobile ? '100%' : '800px';
        area.style.margin = '0 auto';
        
        // Ajustar imagens e outros elementos
        const contentElements = area.querySelectorAll('img, iframe, video');
        contentElements.forEach(el => {
            el.style.maxWidth = '100%';
            el.style.height = 'auto';
            el.style.display = 'block';
            el.style.margin = '0 auto';
        });
        
        // Ajustar tabelas para rolagem horizontal em dispositivos móveis
        const tables = area.querySelectorAll('table');
        tables.forEach(table => {
            const wrapper = document.createElement('div');
            wrapper.style.overflowX = 'auto';
            wrapper.style.width = '100%';
            wrapper.style.margin = '1em 0';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
            
            table.style.width = '100%';
            table.style.tableLayout = 'fixed';
            table.style.borderCollapse = 'collapse';
        });
        
        // Salvar configurações
        localStorage.setItem('epubViewerSettings', JSON.stringify(settings));
    }

    // Aplicar configurações iniciais
    applySettings();

    // Carregar o livro
    const book = ePub(bookUrl);
    let rendition;
    
    // Configurar navegação por toque
    let touchStartX = 0;
    let touchEndX = 0;
    
    const handleTouchStart = (e) => {
        touchStartX = e.changedTouches[0].screenX;
    };
    
    const handleTouchEnd = (e) => {
        if (!rendition) return;
        
        touchEndX = e.changedTouches[0].screenX;
        const deltaX = touchEndX - touchStartX;
        
        // Navegar com deslize de 50px ou mais
        if (Math.abs(deltaX) > 50) {
            if (deltaX > 0) {
                rendition.prev();
            } else {
                rendition.next();
            }
        }
    };
    
    // Adicionar event listeners para navegação por toque
    area.addEventListener('touchstart', handleTouchStart, { passive: true });
    area.addEventListener('touchend', handleTouchEnd, { passive: true });
    
    // Quando o livro for aberto
    book.opened.then(() => {
        // Obter o progresso salvo (se houver)
        let savedLocation = null;
        if (isAuthenticated) {
            // Aqui você pode adicionar lógica para buscar o progresso do servidor
            // Por enquanto, usamos o localStorage
            savedLocation = localStorage.getItem(`bookProgress_${bookId}`);
        }

        // Configurar opções de renderização com base no tamanho da tela
        const isMobile = window.innerWidth <= 768;
        
        // Inicializar a renderização
        rendition = book.renderTo(area, {
            width: '100%',
            height: '100%',
            spread: isMobile ? 'none' : 'auto', // Páginas espelhadas apenas em telas grandes
            manager: 'continuous', // Modo contínuo
            flow: 'paginated',
            snap: true,
            overflow: 'hidden'
        });
        
        // Ajustar o zoom inicial baseado no tamanho da tela
        rendition.themes.register('responsive', {
            'body': {
                'margin': '0',
                'padding': '0',
                'background-color': settings.theme === 'dark' ? '#333' : '#f5f5f5',
                'color': settings.theme === 'dark' ? '#f5f5f5' : '#333',
                'font-family': settings.fontFamily,
                'line-height': settings.lineHeight,
                'font-size': '100%',
                'text-align': 'justify',
                'hyphens': 'auto',
                'overflow-x': 'hidden',
                'word-wrap': 'break-word',
                'max-width': '100%',
                'box-sizing': 'border-box'
            }
        });
        
        rendition.themes.select('responsive');
        
        // Ajustar o zoom quando a janela for redimensionada
        const handleResize = () => {
            if (!rendition) return;
            const newWidth = window.innerWidth;
            const newHeight = window.innerHeight;
            
            // Ajustar o zoom baseado no tamanho da tela
            let zoomLevel = 1;
            
            if (newWidth < 576) { // Mobile pequeno
                zoomLevel = 0.8;
            } else if (newWidth < 768) { // Mobile grande
                zoomLevel = 0.9;
            } else if (newWidth < 992) { // Tablet
                zoomLevel = 1;
            } else { // Desktop
                zoomLevel = 1.1;
            }
            
            rendition.themes.fontSize(`${settings.fontSize}%`);
            rendition.resize(newWidth, newHeight).then(() => {
                rendition.zoom(zoomLevel);
            });
        };
        
        // Adicionar listener para redimensionamento
        window.addEventListener('resize', handleResize);
        
        // Configurar o tamanho inicial
        handleResize();

        // Exibir o conteúdo
        return rendition.display(savedLocation || undefined);
    }).then(() => {
        console.log('Livro carregado com sucesso');
        
        // Salvar o progresso periodicamente
        if (isAuthenticated) {
            setInterval(() => {
                if (rendition) {
                    const location = rendition.currentLocation();
                    if (location && location.start) {
                        // Aqui você pode adicionar lógica para salvar no servidor
                        localStorage.setItem(`bookProgress_${bookId}`, JSON.stringify(location.start));
                    }
                }
            }, 5000); // Salvar a cada 5 segundos
        }
        
        // Configurar atalhos de teclado
        document.addEventListener('keydown', handleKeyDown);
    }).catch(error => {
        console.error('Erro ao carregar o livro:', error);
        area.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <i class="fas fa-exclamation-triangle fa-3x" style="color: #dc3545; margin-bottom: 1rem;"></i>
                <h3>Erro ao carregar o livro</h3>
                <p>${error.message || 'Não foi possível carregar o arquivo EPUB'}</p>
                <a href="${bookUrl}" class="btn btn-primary mt-3" download>
                    <i class="fas fa-download"></i> Baixar arquivo
                </a>
            </div>
        `;
    });

    // Função para lidar com teclas de atalho
    function handleKeyDown(event) {
        if (!rendition) return;
        
        switch (event.key) {
            case 'ArrowRight':
            case 'ArrowDown':
            case ' ':
                rendition.next();
                event.preventDefault();
                break;
                
            case 'ArrowLeft':
            case 'ArrowUp':
                rendition.prev();
                event.preventDefault();
                break;
                
            case 'Home':
                rendition.display(book.locations.first());
                event.preventDefault();
                break;
                
            case 'End':
                rendition.display(book.locations.last());
                event.preventDefault();
                break;
        }
    }

    // Adicionar controles de navegação
    const controls = document.createElement('div');
    controls.style.position = 'fixed';
    controls.style.bottom = '20px';
    controls.style.right = '20px';
    controls.style.zIndex = '1000';
    controls.style.display = 'flex';
    controls.style.gap = '10px';
    controls.style.padding = '10px';
    controls.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    controls.style.borderRadius = '50px';
    controls.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';

    // Botão de voltar
    const prevBtn = createControlButton('fa-chevron-left', 'Página anterior (←)', () => {
        if (rendition) rendition.prev();
    });
    
    // Botão de próximo
    const nextBtn = createControlButton('fa-chevron-right', 'Próxima página (→)', () => {
        if (rendition) rendition.next();
    });
    
    // Botão de aumentar fonte
    const increaseFontBtn = createControlButton('fa-search-plus', 'Aumentar fonte (Ctrl + +)', () => {
        settings.fontSize = Math.min(settings.fontSize + 10, 200);
        applySettings();
    });
    
    // Botão de diminuir fonte
    const decreaseFontBtn = createControlButton('fa-search-minus', 'Diminuir fonte (Ctrl + -)', () => {
        settings.fontSize = Math.max(settings.fontSize - 10, 50);
        applySettings();
    });
    
    // Botão de alternar tema
    const themeBtn = createControlButton('fa-moon', 'Alternar tema claro/escuro (T)', () => {
        settings.theme = settings.theme === 'dark' ? 'light' : 'dark';
        applySettings();
        
        // Atualizar ícone
        const icon = themeBtn.querySelector('i');
        if (settings.theme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            themeBtn.title = 'Alternar para tema claro (T)';
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            themeBtn.title = 'Alternar para tema escuro (T)';
        }
    });
    
    // Adicionar botões aos controles
    controls.appendChild(prevBtn);
    controls.appendChild(nextBtn);
    controls.appendChild(document.createElement('span')).style.width = '10px';
    controls.appendChild(increaseFontBtn);
    controls.appendChild(decreaseFontBtn);
    controls.appendChild(themeBtn);
    
    // Adicionar elementos ao container
    container.appendChild(area);
    viewer.appendChild(container);
    document.body.appendChild(controls);
    
    // Configurar atalhos de teclado adicionais
    document.addEventListener('keydown', (e) => {
        // Ctrl + + para aumentar a fonte
        if ((e.ctrlKey || e.metaKey) && e.key === '+') {
            e.preventDefault();
            settings.fontSize = Math.min(settings.fontSize + 10, 200);
            applySettings();
        }
        
        // Ctrl + - para diminuir a fonte
        if ((e.ctrlKey || e.metaKey) && e.key === '-') {
            e.preventDefault();
            settings.fontSize = Math.max(settings.fontSize - 10, 50);
            applySettings();
        }
        
        // T para alternar tema
        if (e.key.toLowerCase() === 't') {
            e.preventDefault();
            themeBtn.click();
        }
    });
}

/**
 * Cria um botão de controle para o leitor
 * @param {string} iconClass - Classe do ícone FontAwesome
 * @param {string} title - Texto de dica
 * @param {Function} onClick - Função de callback
 * @returns {HTMLElement} - Elemento do botão
 */
function createControlButton(iconClass, title, onClick) {
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-light';
    btn.style.width = '40px';
    btn.style.height = '40px';
    btn.style.borderRadius = '50%';
    btn.style.display = 'flex';
    btn.style.alignItems = 'center';
    btn.style.justifyContent = 'center';
    btn.style.border = 'none';
    btn.style.cursor = 'pointer';
    btn.style.transition = 'all 0.2s';
    btn.title = title;
    
    const icon = document.createElement('i');
    icon.className = `fas ${iconClass}`;
    
    btn.appendChild(icon);
    btn.addEventListener('click', onClick);
    
    // Efeito de hover
    btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'scale(1.1)';
        btn.style.backgroundColor = '#fff';
    });
    
    btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'scale(1)';
        btn.style.backgroundColor = '';
    });
    
    return btn;
}

// Exportar a função para ser chamada pelo template
window.initEpubViewer = initEpubViewer;
