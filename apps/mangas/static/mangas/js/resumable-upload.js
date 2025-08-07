/**
 * Resumable Upload System
 * 
 * Implementa upload resumível com chunks para arquivos grandes,
 * parte da melhoria 5 (interface de upload aprimorada).
 */

class ResumableUpload {
    constructor(options = {}) {
        this.options = {
            chunkSize: 1024 * 1024, // 1MB chunks
            maxRetries: 3,
            retryDelay: 1000, // 1 segundo
            uploadUrl: '/api/upload/chunk/',
            sessionUrl: '/api/upload/session/',
            ...options
        };
        
        this.uploads = new Map(); // Map<fileId, UploadInfo>
        this.activeUploads = 0;
        this.maxConcurrentUploads = 3;
        
        this.eventListeners = {
            progress: [],
            complete: [],
            error: [],
            start: [],
            pause: [],
            resume: []
        };
    }
    
    /**
     * Adiciona um arquivo para upload resumível
     */
    addFile(file, metadata = {}) {
        const fileId = this.generateFileId(file);
        
        const uploadInfo = {
            id: fileId,
            file: file,
            metadata: metadata,
            status: 'pending', // pending, uploading, paused, completed, error
            progress: 0,
            uploadedBytes: 0,
            totalBytes: file.size,
            chunks: this.calculateChunks(file),
            uploadedChunks: new Set(),
            currentChunk: 0,
            retries: 0,
            error: null,
            startTime: null,
            endTime: null,
            sessionId: null,
            uploadId: null
        };
        
        this.uploads.set(fileId, uploadInfo);
        return fileId;
    }
    
    /**
     * Inicia o upload de um arquivo
     */
    async startUpload(fileId) {
        const uploadInfo = this.uploads.get(fileId);
        if (!uploadInfo) {
            throw new Error('Arquivo não encontrado');
        }
        
        if (uploadInfo.status === 'uploading') {
            return; // Já está fazendo upload
        }
        
        try {
            uploadInfo.status = 'uploading';
            uploadInfo.startTime = new Date();
            uploadInfo.error = null;
            
            this.emit('start', { fileId, uploadInfo });
            
            // Cria sessão de upload se necessário
            if (!uploadInfo.sessionId) {
                await this.createUploadSession(uploadInfo);
            }
            
            // Verifica chunks já enviados
            await this.checkUploadedChunks(uploadInfo);
            
            // Inicia upload dos chunks
            await this.uploadChunks(uploadInfo);
            
            // Finaliza upload
            await this.finalizeUpload(uploadInfo);
            
            uploadInfo.status = 'completed';
            uploadInfo.endTime = new Date();
            uploadInfo.progress = 100;
            
            this.emit('complete', { fileId, uploadInfo });
            
        } catch (error) {
            uploadInfo.status = 'error';
            uploadInfo.error = error.message;
            
            this.emit('error', { fileId, uploadInfo, error });
            throw error;
        }
    }
    
    /**
     * Pausa o upload de um arquivo
     */
    pauseUpload(fileId) {
        const uploadInfo = this.uploads.get(fileId);
        if (!uploadInfo || uploadInfo.status !== 'uploading') {
            return false;
        }
        
        uploadInfo.status = 'paused';
        this.emit('pause', { fileId, uploadInfo });
        return true;
    }
    
    /**
     * Resume o upload de um arquivo
     */
    async resumeUpload(fileId) {
        const uploadInfo = this.uploads.get(fileId);
        if (!uploadInfo || uploadInfo.status !== 'paused') {
            return false;
        }
        
        this.emit('resume', { fileId, uploadInfo });
        await this.startUpload(fileId);
        return true;
    }
    
    /**
     * Cancela o upload de um arquivo
     */
    async cancelUpload(fileId) {
        const uploadInfo = this.uploads.get(fileId);
        if (!uploadInfo) {
            return false;
        }
        
        // Cancela sessão no servidor se existir
        if (uploadInfo.sessionId) {
            try {
                await this.cancelUploadSession(uploadInfo.sessionId);
            } catch (error) {
                console.warn('Erro ao cancelar sessão:', error);
            }
        }
        
        this.uploads.delete(fileId);
        return true;
    }
    
    /**
     * Calcula os chunks de um arquivo
     */
    calculateChunks(file) {
        const chunks = [];
        const totalChunks = Math.ceil(file.size / this.options.chunkSize);
        
        for (let i = 0; i < totalChunks; i++) {
            const start = i * this.options.chunkSize;
            const end = Math.min(start + this.options.chunkSize, file.size);
            
            chunks.push({
                index: i,
                start: start,
                end: end,
                size: end - start,
                uploaded: false
            });
        }
        
        return chunks;
    }
    
    /**
     * Cria uma sessão de upload no servidor
     */
    async createUploadSession(uploadInfo) {
        const response = await fetch(this.options.sessionUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                filename: uploadInfo.file.name,
                filesize: uploadInfo.file.size,
                filetype: uploadInfo.file.type,
                chunks: uploadInfo.chunks.length,
                metadata: uploadInfo.metadata
            })
        });
        
        if (!response.ok) {
            throw new Error(`Erro ao criar sessão: ${response.status}`);
        }
        
        const data = await response.json();
        uploadInfo.sessionId = data.session_id;
        uploadInfo.uploadId = data.upload_id;
    }
    
    /**
     * Verifica quais chunks já foram enviados
     */
    async checkUploadedChunks(uploadInfo) {
        if (!uploadInfo.sessionId) return;
        
        try {
            const response = await fetch(
                `${this.options.sessionUrl}${uploadInfo.sessionId}/chunks/`,
                {
                    method: 'GET',
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    }
                }
            );
            
            if (response.ok) {
                const data = await response.json();
                const uploadedChunks = data.uploaded_chunks || [];
                
                uploadedChunks.forEach(chunkIndex => {
                    uploadInfo.uploadedChunks.add(chunkIndex);
                    uploadInfo.chunks[chunkIndex].uploaded = true;
                });
                
                // Atualiza progresso
                uploadInfo.uploadedBytes = uploadedChunks.length * this.options.chunkSize;
                uploadInfo.progress = (uploadInfo.uploadedBytes / uploadInfo.totalBytes) * 100;
            }
        } catch (error) {
            console.warn('Erro ao verificar chunks:', error);
        }
    }
    
    /**
     * Faz upload dos chunks
     */
    async uploadChunks(uploadInfo) {
        const pendingChunks = uploadInfo.chunks.filter(chunk => !chunk.uploaded);
        
        for (const chunk of pendingChunks) {
            // Verifica se foi pausado
            if (uploadInfo.status === 'paused') {
                break;
            }
            
            await this.uploadChunk(uploadInfo, chunk);
        }
    }
    
    /**
     * Faz upload de um chunk específico
     */
    async uploadChunk(uploadInfo, chunk) {
        const maxRetries = this.options.maxRetries;
        let retries = 0;
        
        while (retries <= maxRetries) {
            try {
                // Verifica se foi pausado
                if (uploadInfo.status === 'paused') {
                    return;
                }
                
                const chunkBlob = uploadInfo.file.slice(chunk.start, chunk.end);
                const formData = new FormData();
                
                formData.append('session_id', uploadInfo.sessionId);
                formData.append('upload_id', uploadInfo.uploadId);
                formData.append('chunk_index', chunk.index);
                formData.append('chunk_size', chunk.size);
                formData.append('chunk_data', chunkBlob);
                
                const response = await fetch(this.options.uploadUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: formData
                });
                
                if (response.ok) {
                    // Chunk enviado com sucesso
                    chunk.uploaded = true;
                    uploadInfo.uploadedChunks.add(chunk.index);
                    uploadInfo.uploadedBytes += chunk.size;
                    uploadInfo.progress = (uploadInfo.uploadedBytes / uploadInfo.totalBytes) * 100;
                    
                    this.emit('progress', { 
                        fileId: uploadInfo.id, 
                        uploadInfo,
                        chunkIndex: chunk.index,
                        progress: uploadInfo.progress
                    });
                    
                    break; // Sucesso, sai do loop de retry
                } else {
                    throw new Error(`Erro HTTP: ${response.status}`);
                }
                
            } catch (error) {
                retries++;
                
                if (retries > maxRetries) {
                    throw new Error(`Falha ao enviar chunk ${chunk.index} após ${maxRetries} tentativas: ${error.message}`);
                }
                
                // Aguarda antes de tentar novamente
                await this.delay(this.options.retryDelay * retries);
            }
        }
    }
    
    /**
     * Finaliza o upload no servidor
     */
    async finalizeUpload(uploadInfo) {
        const response = await fetch(
            `${this.options.sessionUrl}${uploadInfo.sessionId}/finalize/`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    upload_id: uploadInfo.uploadId,
                    total_chunks: uploadInfo.chunks.length
                })
            }
        );
        
        if (!response.ok) {
            throw new Error(`Erro ao finalizar upload: ${response.status}`);
        }
        
        const data = await response.json();
        uploadInfo.finalUrl = data.file_url;
        uploadInfo.fileId = data.file_id;
    }
    
    /**
     * Cancela uma sessão de upload no servidor
     */
    async cancelUploadSession(sessionId) {
        const response = await fetch(
            `${this.options.sessionUrl}${sessionId}/`,
            {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`Erro ao cancelar sessão: ${response.status}`);
        }
    }
    
    /**
     * Gera ID único para arquivo
     */
    generateFileId(file) {
        return `${file.name}_${file.size}_${file.lastModified}_${Date.now()}`;
    }
    
    /**
     * Obtém token CSRF
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Sistema de eventos
     */
    on(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
    }
    
    off(event, callback) {
        if (this.eventListeners[event]) {
            const index = this.eventListeners[event].indexOf(callback);
            if (index > -1) {
                this.eventListeners[event].splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Erro no listener de ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Métodos de utilidade
     */
    getUploadInfo(fileId) {
        return this.uploads.get(fileId);
    }
    
    getAllUploads() {
        return Array.from(this.uploads.values());
    }
    
    getUploadsByStatus(status) {
        return this.getAllUploads().filter(upload => upload.status === status);
    }
    
    getTotalProgress() {
        const uploads = this.getAllUploads();
        if (uploads.length === 0) return 0;
        
        const totalProgress = uploads.reduce((sum, upload) => sum + upload.progress, 0);
        return totalProgress / uploads.length;
    }
    
    getUploadSpeed(fileId) {
        const uploadInfo = this.uploads.get(fileId);
        if (!uploadInfo || !uploadInfo.startTime) return 0;
        
        const elapsed = (new Date() - uploadInfo.startTime) / 1000; // segundos
        if (elapsed === 0) return 0;
        
        return uploadInfo.uploadedBytes / elapsed; // bytes por segundo
    }
    
    getEstimatedTimeRemaining(fileId) {
        const uploadInfo = this.uploads.get(fileId);
        if (!uploadInfo) return 0;
        
        const speed = this.getUploadSpeed(fileId);
        if (speed === 0) return Infinity;
        
        const remainingBytes = uploadInfo.totalBytes - uploadInfo.uploadedBytes;
        return remainingBytes / speed; // segundos
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatTime(seconds) {
        if (!isFinite(seconds)) return '∞';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
}

// Integração com o Enhanced Upload System
if (typeof window !== 'undefined') {
    window.ResumableUpload = ResumableUpload;
    
    // Adiciona funcionalidade resumível ao Enhanced Upload
    document.addEventListener('DOMContentLoaded', function() {
        if (window.enhancedUpload) {
            // Cria instância de upload resumível
            const resumableUpload = new ResumableUpload({
                uploadUrl: '/api/upload/chunk/',
                sessionUrl: '/api/upload/session/'
            });
            
            // Integra com o sistema existente
            window.enhancedUpload.resumableUpload = resumableUpload;
            
            // Adiciona métodos de conveniência
            window.enhancedUpload.startResumableUpload = function(fileId) {
                return resumableUpload.startUpload(fileId);
            };
            
            window.enhancedUpload.pauseResumableUpload = function(fileId) {
                return resumableUpload.pauseUpload(fileId);
            };
            
            window.enhancedUpload.resumeResumableUpload = function(fileId) {
                return resumableUpload.resumeUpload(fileId);
            };
        }
    });
}

export default ResumableUpload;