/**
 * Enhanced Upload System for Manga Chapters
 * 
 * Implementa a melhoria 5 (interface de upload aprimorada) com:
 * - Drag & drop avançado
 * - Preview de imagens
 * - Validação instantânea
 * - Upload resumível
 * - Sessões de upload
 */

class EnhancedUploadSystem {
    constructor(options = {}) {
        this.options = {
            dropZoneSelector: '#enhanced-drop-zone',
            fileInputSelector: '#enhanced-file-input',
            previewContainerSelector: '#file-preview-container',
            progressContainerSelector: '#upload-progress-container',
            sessionInfoSelector: '#session-info',
            maxFileSize: 20 * 1024 * 1024, // 20MB
            maxSessionSize: 200 * 1024 * 1024, // 200MB
            maxFiles: 500,
            allowedTypes: ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
            allowedExtensions: ['.jpg', '.jpeg', '.png', '.webp', '.gif'],
            chunkSize: 1024 * 1024, // 1MB chunks for resumable upload
            ...options
        };
        
        this.files = new Map(); // Map<fileId, FileInfo>
        this.uploadSession = null;
        this.currentUploads = new Map(); // Map<fileId, UploadInfo>
        this.totalSize = 0;
        this.validationResults = null;
        
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
        this.createUploadSession();
    }
    
    setupElements() {
        this.dropZone = document.querySelector(this.options.dropZoneSelector);
        this.fileInput = document.querySelector(this.options.fileInputSelector);
        this.previewContainer = document.querySelector(this.options.previewContainerSelector);
        this.progressContainer = document.querySelector(this.options.progressContainerSelector);
        this.sessionInfo = document.querySelector(this.options.sessionInfoSelector);
        
        if (!this.dropZone || !this.fileInput) {
            console.error('Required elements not found');
            return;
        }
        
        // Cria elementos se não existirem
        if (!this.previewContainer) {
            this.previewContainer = this.createPreviewContainer();
        }
        
        if (!this.progressContainer) {
            this.progressContainer = this.createProgressContainer();
        }
        
        if (!this.sessionInfo) {
            this.sessionInfo = this.createSessionInfo();
        }
    }
    
    createPreviewContainer() {
        const container = document.createElement('div');
        container.id = 'file-preview-container';
        container.className = 'file-preview-container';
        container.innerHTML = `
            <h5><i class="fas fa-images me-2"></i>Arquivos Selecionados</h5>
            <div class="preview-grid" id="preview-grid"></div>
            <div class="preview-summary" id="preview-summary"></div>
        `;
        this.dropZone.parentNode.insertBefore(container, this.dropZone.nextSibling);
        return container;
    }
    
    createProgressContainer() {
        const container = document.createElement('div');
        container.id = 'upload-progress-container';
        container.className = 'upload-progress-container';
        container.style.display = 'none';
        container.innerHTML = `
            <h5><i class="fas fa-cloud-upload-alt me-2"></i>Progresso do Upload</h5>
            <div class="overall-progress mb-3">
                <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         id="overall-progress-bar" style="width: 0%">0%</div>
                </div>
                <div class="progress-info mt-2">
                    <span id="progress-text">Preparando upload...</span>
                    <span id="progress-details" class="float-end">0 MB / 0 MB</span>
                </div>
            </div>
            <div class="file-progress-list" id="file-progress-list"></div>
        `;
        this.previewContainer.parentNode.insertBefore(container, this.previewContainer.nextSibling);
        return container;
    }
    
    createSessionInfo() {
        const container = document.createElement('div');
        container.id = 'session-info';
        container.className = 'session-info alert alert-info';
        container.innerHTML = `
            <h6><i class="fas fa-info-circle me-2"></i>Informações da Sessão</h6>
            <div class="row">
                <div class="col-md-3">
                    <strong>Arquivos:</strong> <span id="session-files">0</span>
                </div>
                <div class="col-md-3">
                    <strong>Tamanho:</strong> <span id="session-size">0 MB</span>
                </div>
                <div class="col-md-3">
                    <strong>Válidos:</strong> <span id="session-valid">0</span>
                </div>
                <div class="col-md-3">
                    <strong>Status:</strong> <span id="session-status">Preparando</span>
                </div>
            </div>
        `;
        this.dropZone.parentNode.insertBefore(container, this.dropZone);
        return container;
    }
    
    setupEventListeners() {
        // Drag and drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.highlight(), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => this.unhighlight(), false);
        });
        
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        
        // File input change
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Window events
        window.addEventListener('beforeunload', (e) => this.handleBeforeUnload(e));
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    highlight() {
        this.dropZone.classList.add('dragover');
    }
    
    unhighlight() {
        this.dropZone.classList.remove('dragover');
    }
    
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.processFiles(Array.from(files));
    }
    
    handleFileSelect(e) {
        const files = e.target.files;
        this.processFiles(Array.from(files));
    }
    
    async processFiles(fileList) {
        const newFiles = [];
        
        for (const file of fileList) {
            const fileId = this.generateFileId(file);
            
            // Verifica se já existe
            if (this.files.has(fileId)) {
                this.showNotification(`Arquivo ${file.name} já foi adicionado`, 'warning');
                continue;
            }
            
            const fileInfo = {
                id: fileId,
                file: file,
                name: file.name,
                size: file.size,
                type: file.type,
                status: 'pending',
                preview: null,
                validation: null,
                uploadProgress: 0,
                chunks: [],
                uploadedChunks: 0
            };
            
            this.files.set(fileId, fileInfo);
            newFiles.push(fileInfo);
        }
        
        if (newFiles.length > 0) {
            await this.validateFiles(newFiles);
            this.updatePreview();
            this.updateSessionInfo();
        }
    }
    
    generateFileId(file) {
        return `${file.name}_${file.size}_${file.lastModified}`;
    }
    
    async validateFiles(fileInfos) {
        for (const fileInfo of fileInfos) {
            try {
                const validation = await this.validateSingleFile(fileInfo);
                fileInfo.validation = validation;
                fileInfo.status = validation.valid ? 'valid' : 'invalid';
                
                if (validation.valid && this.isImageFile(fileInfo.file)) {
                    fileInfo.preview = await this.generatePreview(fileInfo.file);
                }
            } catch (error) {
                console.error(`Erro na validação de ${fileInfo.name}:`, error);
                fileInfo.validation = {
                    valid: false,
                    errors: [`Erro na validação: ${error.message}`]
                };
                fileInfo.status = 'error';
            }
        }
        
        // Atualiza validação geral
        await this.updateValidationResults();
    }
    
    async validateSingleFile(fileInfo) {
        const validation = {
            valid: true,
            errors: [],
            warnings: [],
            quality: null
        };
        
        // Validação de tamanho
        if (fileInfo.size > this.options.maxFileSize) {
            validation.valid = false;
            validation.errors.push(`Arquivo muito grande (${this.formatFileSize(fileInfo.size)}). Máximo: ${this.formatFileSize(this.options.maxFileSize)}`);
        }
        
        // Validação de tipo
        if (!this.isAllowedType(fileInfo.file)) {
            validation.valid = false;
            validation.errors.push(`Tipo de arquivo não permitido: ${fileInfo.type}`);
        }
        
        // Validação de extensão
        if (!this.isAllowedExtension(fileInfo.name)) {
            validation.valid = false;
            validation.errors.push(`Extensão não permitida`);
        }
        
        // Validação de imagem (se for imagem)
        if (validation.valid && this.isImageFile(fileInfo.file)) {
            try {
                const imageValidation = await this.validateImage(fileInfo.file);
                validation.quality = imageValidation.quality;
                
                if (imageValidation.errors.length > 0) {
                    validation.valid = false;
                    validation.errors.push(...imageValidation.errors);
                }
                
                if (imageValidation.warnings.length > 0) {
                    validation.warnings.push(...imageValidation.warnings);
                }
            } catch (error) {
                validation.warnings.push(`Não foi possível analisar a qualidade da imagem`);
            }
        }
        
        return validation;
    }
    
    async validateImage(file) {
        return new Promise((resolve) => {
            const img = new Image();
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            img.onload = () => {
                const validation = {
                    errors: [],
                    warnings: [],
                    quality: {
                        width: img.width,
                        height: img.height,
                        aspectRatio: img.height / img.width,
                        resolution: img.width * img.height
                    }
                };
                
                // Validação de dimensões mínimas
                if (img.width < 800 || img.height < 1200) {
                    validation.errors.push(`Dimensões muito pequenas (${img.width}x${img.height}). Mínimo: 800x1200`);
                }
                
                // Validação de dimensões máximas
                if (img.width > 10000 || img.height > 10000) {
                    validation.errors.push(`Dimensões muito grandes (${img.width}x${img.height}). Máximo: 10000x10000`);
                }
                
                // Validação de aspect ratio
                const aspectRatio = img.height / img.width;
                if (aspectRatio < 1.2 || aspectRatio > 1.8) {
                    validation.warnings.push(`Proporção incomum (${aspectRatio.toFixed(2)}). Recomendado: 1.4-1.6`);
                }
                
                // Análise de qualidade básica
                canvas.width = Math.min(img.width, 500);
                canvas.height = Math.min(img.height, 500);
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                try {
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    validation.quality.brightness = this.calculateBrightness(imageData);
                    validation.quality.contrast = this.calculateContrast(imageData);
                } catch (error) {
                    console.warn('Erro na análise de qualidade:', error);
                }
                
                resolve(validation);
            };
            
            img.onerror = () => {
                resolve({
                    errors: ['Arquivo de imagem corrompido ou inválido'],
                    warnings: [],
                    quality: null
                });
            };
            
            img.src = URL.createObjectURL(file);
        });
    }
    
    calculateBrightness(imageData) {
        const data = imageData.data;
        let sum = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            sum += (r + g + b) / 3;
        }
        
        return sum / (data.length / 4);
    }
    
    calculateContrast(imageData) {
        const data = imageData.data;
        const brightness = this.calculateBrightness(imageData);
        let variance = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const pixelBrightness = (r + g + b) / 3;
            variance += Math.pow(pixelBrightness - brightness, 2);
        }
        
        return Math.sqrt(variance / (data.length / 4));
    }
    
    async generatePreview(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => resolve(null);
            reader.readAsDataURL(file);
        });
    }
    
    isImageFile(file) {
        return file.type.startsWith('image/');
    }
    
    isAllowedType(file) {
        return this.options.allowedTypes.includes(file.type);
    }
    
    isAllowedExtension(filename) {
        const ext = '.' + filename.split('.').pop().toLowerCase();
        return this.options.allowedExtensions.includes(ext);
    }
    
    updatePreview() {
        const previewGrid = this.previewContainer.querySelector('#preview-grid');
        const previewSummary = this.previewContainer.querySelector('#preview-summary');
        
        if (!previewGrid) return;
        
        previewGrid.innerHTML = '';
        
        this.files.forEach((fileInfo) => {
            const previewItem = this.createPreviewItem(fileInfo);
            previewGrid.appendChild(previewItem);
        });
        
        // Atualiza resumo
        const totalFiles = this.files.size;
        const validFiles = Array.from(this.files.values()).filter(f => f.status === 'valid').length;
        const totalSize = Array.from(this.files.values()).reduce((sum, f) => sum + f.size, 0);
        
        if (previewSummary) {
            previewSummary.innerHTML = `
                <div class="row text-center">
                    <div class="col-md-3">
                        <strong>Total:</strong> ${totalFiles} arquivos
                    </div>
                    <div class="col-md-3">
                        <strong>Válidos:</strong> ${validFiles} arquivos
                    </div>
                    <div class="col-md-3">
                        <strong>Tamanho:</strong> ${this.formatFileSize(totalSize)}
                    </div>
                    <div class="col-md-3">
                        <strong>Status:</strong> 
                        <span class="badge ${validFiles === totalFiles ? 'bg-success' : 'bg-warning'}">
                            ${validFiles === totalFiles ? 'Pronto' : 'Verificar'}
                        </span>
                    </div>
                </div>
            `;
        }
        
        this.previewContainer.style.display = totalFiles > 0 ? 'block' : 'none';
    }
    
    createPreviewItem(fileInfo) {
        const item = document.createElement('div');
        item.className = 'preview-item';
        item.dataset.fileId = fileInfo.id;
        
        const statusClass = {
            'valid': 'success',
            'invalid': 'danger',
            'error': 'danger',
            'pending': 'secondary'
        }[fileInfo.status] || 'secondary';
        
        const statusIcon = {
            'valid': 'check-circle',
            'invalid': 'exclamation-triangle',
            'error': 'times-circle',
            'pending': 'clock'
        }[fileInfo.status] || 'clock';
        
        let previewContent = '';
        if (fileInfo.preview) {
            previewContent = `<img src="${fileInfo.preview}" alt="Preview" class="preview-image">`;
        } else {
            previewContent = `<div class="preview-placeholder"><i class="fas fa-file-image"></i></div>`;
        }
        
        let validationInfo = '';
        if (fileInfo.validation) {
            if (fileInfo.validation.errors.length > 0) {
                validationInfo += `<div class="validation-errors">${fileInfo.validation.errors.map(e => `<small class="text-danger">• ${e}</small>`).join('<br>')}</div>`;
            }
            if (fileInfo.validation.warnings.length > 0) {
                validationInfo += `<div class="validation-warnings">${fileInfo.validation.warnings.map(w => `<small class="text-warning">• ${w}</small>`).join('<br>')}</div>`;
            }
            if (fileInfo.validation.quality) {
                const q = fileInfo.validation.quality;
                validationInfo += `<div class="quality-info"><small class="text-muted">${q.width}x${q.height} • ${this.formatFileSize(fileInfo.size)}</small></div>`;
            }
        }
        
        item.innerHTML = `
            <div class="preview-content">
                ${previewContent}
                <div class="preview-overlay">
                    <button type="button" class="btn btn-sm btn-danger remove-file" 
                            onclick="enhancedUpload.removeFile('${fileInfo.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="preview-info">
                <div class="file-name" title="${fileInfo.name}">${this.truncateFilename(fileInfo.name)}</div>
                <div class="file-status">
                    <span class="badge bg-${statusClass}">
                        <i class="fas fa-${statusIcon} me-1"></i>${fileInfo.status}
                    </span>
                </div>
                ${validationInfo}
            </div>
        `;
        
        return item;
    }
    
    truncateFilename(filename, maxLength = 20) {
        if (filename.length <= maxLength) return filename;
        const ext = filename.split('.').pop();
        const name = filename.substring(0, filename.lastIndexOf('.'));
        const truncated = name.substring(0, maxLength - ext.length - 4) + '...';
        return `${truncated}.${ext}`;
    }
    
    removeFile(fileId) {
        if (this.files.has(fileId)) {
            this.files.delete(fileId);
            this.updatePreview();
            this.updateSessionInfo();
            this.updateValidationResults();
        }
    }
    
    async updateValidationResults() {
        const files = Array.from(this.files.values());
        const validFiles = files.filter(f => f.status === 'valid');
        const invalidFiles = files.filter(f => f.status === 'invalid' || f.status === 'error');
        
        this.validationResults = {
            totalFiles: files.length,
            validFiles: validFiles.length,
            invalidFiles: invalidFiles.length,
            totalSize: files.reduce((sum, f) => sum + f.size, 0),
            canUpload: validFiles.length > 0 && invalidFiles.length === 0
        };
        
        // Dispara evento personalizado
        const event = new CustomEvent('validationUpdated', {
            detail: this.validationResults
        });
        document.dispatchEvent(event);
    }
    
    updateSessionInfo() {
        if (!this.sessionInfo) return;
        
        const files = Array.from(this.files.values());
        const validFiles = files.filter(f => f.status === 'valid');
        const totalSize = files.reduce((sum, f) => sum + f.size, 0);
        
        const sessionFiles = this.sessionInfo.querySelector('#session-files');
        const sessionSize = this.sessionInfo.querySelector('#session-size');
        const sessionValid = this.sessionInfo.querySelector('#session-valid');
        const sessionStatus = this.sessionInfo.querySelector('#session-status');
        
        if (sessionFiles) sessionFiles.textContent = files.length;
        if (sessionSize) sessionSize.textContent = this.formatFileSize(totalSize);
        if (sessionValid) sessionValid.textContent = validFiles.length;
        
        if (sessionStatus) {
            let status = 'Preparando';
            if (files.length === 0) {
                status = 'Aguardando arquivos';
            } else if (validFiles.length === files.length && files.length > 0) {
                status = 'Pronto para upload';
            } else if (validFiles.length > 0) {
                status = 'Verificar arquivos';
            } else {
                status = 'Arquivos inválidos';
            }
            sessionStatus.textContent = status;
        }
    }
    
    async createUploadSession() {
        try {
            const response = await fetch('/api/manga/upload/session/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    manga_id: this.options.mangaId,
                    volume_id: this.options.volumeId
                })
            });
            
            if (response.ok) {
                this.uploadSession = await response.json();
                console.log('Sessão de upload criada:', this.uploadSession.session_id);
            } else {
                console.error('Erro ao criar sessão de upload');
            }
        } catch (error) {
            console.error('Erro ao criar sessão de upload:', error);
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showNotification(message, type = 'info') {
        // Implementação simples de notificação
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    handleBeforeUnload(e) {
        if (this.files.size > 0) {
            e.preventDefault();
            e.returnValue = 'Você tem arquivos selecionados. Tem certeza que deseja sair?';
        }
    }
    
    // Métodos públicos para integração
    getValidFiles() {
        return Array.from(this.files.values()).filter(f => f.status === 'valid');
    }
    
    getSessionId() {
        return this.uploadSession?.session_id;
    }
    
    canStartUpload() {
        return this.validationResults?.canUpload || false;
    }
    
    clear() {
        this.files.clear();
        this.updatePreview();
        this.updateSessionInfo();
        this.updateValidationResults();
    }
}

// Instância global
let enhancedUpload = null;

// Inicialização automática quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.querySelector('#enhanced-drop-zone');
    if (dropZone) {
        enhancedUpload = new EnhancedUploadSystem({
            mangaId: window.mangaId,
            volumeId: window.volumeId
        });
        
        // Torna disponível globalmente
        window.enhancedUpload = enhancedUpload;
    }
});