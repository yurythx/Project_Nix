/**
 * Script para gerenciar o upload de múltiplos arquivos e pastas
 * Inclui suporte para arrastar e soltar arquivos
 */

document.addEventListener('DOMContentLoaded', function() {
    // Encontra todos os widgets de upload de arquivo múltiplo
    const fileInputs = document.querySelectorAll('.multiple-file-input input[type="file"]');
    
    // Aplica o gerenciamento de eventos para cada input
    fileInputs.forEach(input => {
        const container = input.closest('.multiple-file-input');
        const fileList = container.querySelector('.file-list') || createFileList(container);
        
        // Atualiza a interface quando arquivos são selecionados
        input.addEventListener('change', function(e) {
            updateFileList(this, fileList);
        });
        
        // Suporte para arrastar e soltar
        const dropArea = container.querySelector('.file-upload-area');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        dropArea.addEventListener('drop', handleDrop, false);
        
        // Adiciona evento de clique para remover arquivos
        fileList.addEventListener('click', function(e) {
            const removeBtn = e.target.closest('.remove-file');
            if (removeBtn) {
                e.preventDefault();
                const fileItem = removeBtn.closest('.file-item');
                const fileName = fileItem.dataset.filename;
                removeFileFromInput(input, fileName);
                fileItem.remove();
                
                // Se não houver mais arquivos, esconde a lista
                if (fileList.children.length === 0) {
                    fileList.style.display = 'none';
                }
            }
        });
    });
    
    /**
     * Cria um elemento para exibir a lista de arquivos
     */
    function createFileList(container) {
        const fileList = document.createElement('div');
        fileList.className = 'file-list';
        fileList.style.display = 'none';
        container.appendChild(fileList);
        return fileList;
    }
    
    /**
     * Atualiza a lista de arquivos exibida
     */
    function updateFileList(input, fileListElement) {
        // Limpa a lista atual
        fileListElement.innerHTML = '';
        
        // Se não houver arquivos, esconde a lista
        if (!input.files || input.files.length === 0) {
            fileListElement.style.display = 'none';
            return;
        }
        
        // Adiciona cada arquivo à lista
        Array.from(input.files).forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.dataset.filename = file.name;
            
            fileItem.innerHTML = `
                <span class="file-name">${escapeHtml(file.name)}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
                <button type="button" class="remove-file" aria-label="Remover arquivo">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            fileListElement.appendChild(fileItem);
        });
        
        // Mostra a lista
        fileListElement.style.display = 'block';
    }
    
    /**
     * Remove um arquivo do input file
     */
    function removeFileFromInput(input, fileName) {
        const files = Array.from(input.files);
        const filteredFiles = files.filter(file => file.name !== fileName);
        
        // Cria um novo DataTransfer para armazenar os arquivos restantes
        const dataTransfer = new DataTransfer();
        filteredFiles.forEach(file => dataTransfer.items.add(file));
        
        // Atualiza os arquivos no input
        input.files = dataTransfer.files;
    }
    
    /**
     * Funções auxiliares para arrastar e soltar
     */
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        this.classList.add('dragover');
    }
    
    function unhighlight() {
        this.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        // Atualiza o input com os arquivos arrastados
        const input = this.closest('.multiple-file-input').querySelector('input[type="file"]');
        input.files = files;
        
        // Dispara o evento change para atualizar a interface
        const event = new Event('change');
        input.dispatchEvent(event);
    }
    
    /**
     * Formata o tamanho do arquivo para exibição amigável
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * Escapa HTML para evitar XSS
     */
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
