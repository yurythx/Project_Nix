"""Serviço de qualidade para mangás.

Este módulo implementa a melhoria 6 (sistema de qualidade)
com detecção de duplicatas, análise de qualidade e moderação automática.
"""

import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Q
from PIL import Image, ImageStat, ImageFilter
import numpy as np
from datetime import datetime, timedelta

from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..exceptions import MangaException

logger = logging.getLogger(__name__)

class ImageQualityAnalyzer:
    """Analisador de qualidade de imagens."""
    
    # Thresholds para análise de qualidade
    MIN_RESOLUTION_SCORE = 0.6  # Resolução mínima aceitável
    MIN_SHARPNESS_SCORE = 0.4   # Nitidez mínima aceitável
    MIN_CONTRAST_SCORE = 0.3    # Contraste mínimo aceitável
    MAX_NOISE_SCORE = 0.7       # Ruído máximo aceitável
    
    def analyze_image_quality(self, image_file: UploadedFile) -> Dict[str, Any]:
        """Analisa a qualidade de uma imagem."""
        try:
            with Image.open(image_file) as img:
                # Converte para RGB se necessário
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                analysis = {
                    'filename': image_file.name,
                    'size': image_file.size,
                    'dimensions': img.size,
                    'format': img.format,
                    'mode': img.mode,
                    'quality_scores': {},
                    'overall_score': 0.0,
                    'quality_level': 'unknown',
                    'issues': [],
                    'recommendations': []
                }
                
                # Análise de resolução
                resolution_score = self._analyze_resolution(img)
                analysis['quality_scores']['resolution'] = resolution_score
                
                # Análise de nitidez
                sharpness_score = self._analyze_sharpness(img)
                analysis['quality_scores']['sharpness'] = sharpness_score
                
                # Análise de contraste
                contrast_score = self._analyze_contrast(img)
                analysis['quality_scores']['contrast'] = contrast_score
                
                # Análise de ruído
                noise_score = self._analyze_noise(img)
                analysis['quality_scores']['noise'] = noise_score
                
                # Análise de aspect ratio
                aspect_ratio_score = self._analyze_aspect_ratio(img)
                analysis['quality_scores']['aspect_ratio'] = aspect_ratio_score
                
                # Calcula score geral
                overall_score = self._calculate_overall_score(analysis['quality_scores'])
                analysis['overall_score'] = overall_score
                
                # Determina nível de qualidade
                analysis['quality_level'] = self._determine_quality_level(overall_score)
                
                # Identifica problemas e recomendações
                analysis['issues'] = self._identify_issues(analysis['quality_scores'])
                analysis['recommendations'] = self._generate_recommendations(analysis)
                
                return analysis
                
        except Exception as e:
            logger.error(f"Erro na análise de qualidade de {image_file.name}: {e}")
            return {
                'filename': image_file.name,
                'error': str(e),
                'quality_level': 'error'
            }
    
    def _analyze_resolution(self, img: Image.Image) -> float:
        """Analisa a resolução da imagem."""
        width, height = img.size
        total_pixels = width * height
        
        # Considera resoluções típicas de mangá
        # 1200x1800 = 2.16M pixels (boa qualidade)
        # 800x1200 = 0.96M pixels (qualidade mínima)
        if total_pixels >= 2_160_000:  # >= 1200x1800
            return 1.0
        elif total_pixels >= 1_440_000:  # >= 1000x1440
            return 0.8
        elif total_pixels >= 960_000:   # >= 800x1200
            return 0.6
        elif total_pixels >= 480_000:   # >= 600x800
            return 0.4
        else:
            return 0.2
    
    def _analyze_sharpness(self, img: Image.Image) -> float:
        """Analisa a nitidez da imagem usando filtro Laplaciano."""
        try:
            # Converte para escala de cinza para análise
            gray = img.convert('L')
            
            # Redimensiona se muito grande para performance
            if gray.size[0] > 1000 or gray.size[1] > 1000:
                gray.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
            
            # Aplica filtro Laplaciano para detectar bordas
            laplacian = gray.filter(ImageFilter.Kernel((3, 3), 
                [-1, -1, -1, -1, 8, -1, -1, -1, -1], 1, 0))
            
            # Calcula variância (maior variância = mais nitidez)
            stat = ImageStat.Stat(laplacian)
            variance = stat.var[0]
            
            # Normaliza o score (valores típicos: 0-1000)
            sharpness_score = min(variance / 500.0, 1.0)
            return sharpness_score
            
        except Exception as e:
            logger.warning(f"Erro na análise de nitidez: {e}")
            return 0.5  # Score neutro em caso de erro
    
    def _analyze_contrast(self, img: Image.Image) -> float:
        """Analisa o contraste da imagem."""
        try:
            # Converte para escala de cinza
            gray = img.convert('L')
            
            # Redimensiona se muito grande
            if gray.size[0] > 1000 or gray.size[1] > 1000:
                gray.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
            
            # Calcula estatísticas
            stat = ImageStat.Stat(gray)
            
            # Contraste baseado no desvio padrão
            # Maior desvio padrão = maior contraste
            std_dev = stat.stddev[0]
            
            # Normaliza (valores típicos: 0-128)
            contrast_score = min(std_dev / 64.0, 1.0)
            return contrast_score
            
        except Exception as e:
            logger.warning(f"Erro na análise de contraste: {e}")
            return 0.5
    
    def _analyze_noise(self, img: Image.Image) -> float:
        """Analisa o nível de ruído da imagem."""
        try:
            # Converte para escala de cinza
            gray = img.convert('L')
            
            # Redimensiona se muito grande
            if gray.size[0] > 500 or gray.size[1] > 500:
                gray.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            # Aplica filtro de suavização
            smooth = gray.filter(ImageFilter.GaussianBlur(radius=1))
            
            # Calcula diferença (ruído)
            diff = Image.new('L', gray.size)
            for i in range(gray.size[0]):
                for j in range(gray.size[1]):
                    if i < gray.size[0] and j < gray.size[1]:
                        try:
                            orig_pixel = gray.getpixel((i, j))
                            smooth_pixel = smooth.getpixel((i, j))
                            diff_value = abs(orig_pixel - smooth_pixel)
                            diff.putpixel((i, j), diff_value)
                        except IndexError:
                            continue
            
            # Calcula média do ruído
            stat = ImageStat.Stat(diff)
            noise_level = stat.mean[0]
            
            # Inverte o score (menos ruído = melhor)
            noise_score = max(0, 1.0 - (noise_level / 25.0))
            return noise_score
            
        except Exception as e:
            logger.warning(f"Erro na análise de ruído: {e}")
            return 0.5
    
    def _analyze_aspect_ratio(self, img: Image.Image) -> float:
        """Analisa se o aspect ratio é adequado para mangá."""
        width, height = img.size
        aspect_ratio = height / width
        
        # Aspect ratios típicos de mangá: 1.4 - 1.6
        ideal_ratio = 1.5
        tolerance = 0.3
        
        diff = abs(aspect_ratio - ideal_ratio)
        if diff <= tolerance:
            return 1.0 - (diff / tolerance) * 0.3  # Score entre 0.7 e 1.0
        else:
            return max(0.3, 0.7 - (diff - tolerance) * 0.5)  # Score decrescente
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calcula o score geral ponderado."""
        weights = {
            'resolution': 0.25,
            'sharpness': 0.25,
            'contrast': 0.20,
            'noise': 0.20,
            'aspect_ratio': 0.10
        }
        
        weighted_sum = sum(scores.get(key, 0) * weight for key, weight in weights.items())
        return round(weighted_sum, 3)
    
    def _determine_quality_level(self, overall_score: float) -> str:
        """Determina o nível de qualidade baseado no score."""
        if overall_score >= 0.8:
            return 'excellent'
        elif overall_score >= 0.65:
            return 'good'
        elif overall_score >= 0.5:
            return 'acceptable'
        elif overall_score >= 0.35:
            return 'poor'
        else:
            return 'very_poor'
    
    def _identify_issues(self, scores: Dict[str, float]) -> List[str]:
        """Identifica problemas específicos na imagem."""
        issues = []
        
        if scores.get('resolution', 0) < self.MIN_RESOLUTION_SCORE:
            issues.append('Resolução muito baixa')
        
        if scores.get('sharpness', 0) < self.MIN_SHARPNESS_SCORE:
            issues.append('Imagem desfocada ou borrada')
        
        if scores.get('contrast', 0) < self.MIN_CONTRAST_SCORE:
            issues.append('Contraste muito baixo')
        
        if scores.get('noise', 0) < (1.0 - self.MAX_NOISE_SCORE):
            issues.append('Muito ruído na imagem')
        
        if scores.get('aspect_ratio', 0) < 0.5:
            issues.append('Proporções inadequadas para mangá')
        
        return issues
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Gera recomendações para melhorar a qualidade."""
        recommendations = []
        scores = analysis['quality_scores']
        
        if scores.get('resolution', 0) < 0.6:
            recommendations.append('Use imagens com resolução mínima de 800x1200 pixels')
        
        if scores.get('sharpness', 0) < 0.4:
            recommendations.append('Verifique se a imagem não está desfocada')
        
        if scores.get('contrast', 0) < 0.3:
            recommendations.append('Ajuste o contraste da imagem')
        
        if scores.get('noise', 0) < 0.3:
            recommendations.append('Reduza o ruído da imagem')
        
        if analysis['quality_level'] in ['poor', 'very_poor']:
            recommendations.append('Considere usar uma versão de melhor qualidade desta imagem')
        
        return recommendations

class DuplicateDetector:
    """Detector de imagens duplicadas."""
    
    def __init__(self):
        self.cache_timeout = 3600 * 24  # 24 horas
    
    def calculate_image_hash(self, image_file: UploadedFile) -> str:
        """Calcula hash perceptual da imagem."""
        try:
            with Image.open(image_file) as img:
                # Redimensiona para 8x8 para hash perceptual simples
                img = img.convert('L').resize((8, 8), Image.Resampling.LANCZOS)
                
                # Calcula média dos pixels
                pixels = list(img.getdata())
                avg = sum(pixels) / len(pixels)
                
                # Cria hash binário
                hash_bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
                
                # Converte para hexadecimal
                hash_hex = hex(int(hash_bits, 2))[2:]
                return hash_hex.zfill(16)  # Preenche com zeros à esquerda
                
        except Exception as e:
            logger.error(f"Erro ao calcular hash de {image_file.name}: {e}")
            # Fallback para hash MD5 do arquivo
            return self._calculate_file_hash(image_file)
    
    def _calculate_file_hash(self, file: UploadedFile) -> str:
        """Calcula hash MD5 do arquivo."""
        hash_md5 = hashlib.md5()
        for chunk in file.chunks():
            hash_md5.update(chunk)
        file.seek(0)
        return hash_md5.hexdigest()
    
    def find_duplicates_in_database(self, image_hash: str, manga_id: int = None) -> List[Dict[str, Any]]:
        """Procura duplicatas no banco de dados."""
        # Por enquanto, implementação simplificada
        # Em uma implementação completa, armazenaria hashes no banco
        cache_key = f"image_hash:{image_hash}"
        existing = cache.get(cache_key)
        
        if existing:
            return [{
                'page_id': existing['page_id'],
                'chapter_id': existing['chapter_id'],
                'manga_id': existing['manga_id'],
                'similarity': 1.0
            }]
        
        return []
    
    def store_image_hash(self, image_hash: str, page_id: int, chapter_id: int, manga_id: int):
        """Armazena hash da imagem no cache."""
        cache_key = f"image_hash:{image_hash}"
        cache.set(cache_key, {
            'page_id': page_id,
            'chapter_id': chapter_id,
            'manga_id': manga_id,
            'stored_at': datetime.now().isoformat()
        }, timeout=self.cache_timeout)
    
    def find_similar_images(self, image_hash: str, threshold: float = 0.9) -> List[Dict[str, Any]]:
        """Encontra imagens similares baseado em hash perceptual."""
        # Implementação simplificada - em produção usaria algoritmos mais sofisticados
        similar_images = []
        
        # Busca por hashes similares (diferença de poucos bits)
        for i in range(1, 4):  # Permite diferença de 1-3 bits
            similar_hashes = self._generate_similar_hashes(image_hash, i)
            for similar_hash in similar_hashes:
                duplicates = self.find_duplicates_in_database(similar_hash)
                for duplicate in duplicates:
                    duplicate['similarity'] = 1.0 - (i * 0.1)  # Reduz similaridade por bit diferente
                    if duplicate['similarity'] >= threshold:
                        similar_images.append(duplicate)
        
        return similar_images
    
    def _generate_similar_hashes(self, original_hash: str, bit_diff: int) -> List[str]:
        """Gera hashes com diferença de poucos bits."""
        # Implementação simplificada - retorna lista vazia
        # Em produção, geraria todas as combinações possíveis
        return []

class QualityModerationService:
    """Serviço de moderação automática baseado em qualidade."""
    
    def __init__(self):
        self.quality_analyzer = ImageQualityAnalyzer()
        self.duplicate_detector = DuplicateDetector()
        
        # Thresholds para moderação automática
        self.auto_reject_threshold = 0.3
        self.manual_review_threshold = 0.5
        self.auto_approve_threshold = 0.7
    
    def moderate_upload(self, files: List[UploadedFile], manga_id: int) -> Dict[str, Any]:
        """Modera um upload baseado em qualidade e duplicatas."""
        moderation_result = {
            'auto_approved': [],
            'manual_review': [],
            'auto_rejected': [],
            'duplicates_found': [],
            'quality_issues': [],
            'overall_status': 'pending'
        }
        
        for file in files:
            file_result = self._moderate_single_file(file, manga_id)
            
            if file_result['action'] == 'auto_approve':
                moderation_result['auto_approved'].append(file_result)
            elif file_result['action'] == 'manual_review':
                moderation_result['manual_review'].append(file_result)
            elif file_result['action'] == 'auto_reject':
                moderation_result['auto_rejected'].append(file_result)
            
            if file_result.get('duplicates'):
                moderation_result['duplicates_found'].extend(file_result['duplicates'])
            
            if file_result.get('quality_issues'):
                moderation_result['quality_issues'].extend(file_result['quality_issues'])
        
        # Determina status geral
        if moderation_result['auto_rejected']:
            moderation_result['overall_status'] = 'rejected'
        elif moderation_result['manual_review']:
            moderation_result['overall_status'] = 'manual_review'
        else:
            moderation_result['overall_status'] = 'approved'
        
        return moderation_result
    
    def _moderate_single_file(self, file: UploadedFile, manga_id: int) -> Dict[str, Any]:
        """Modera um único arquivo."""
        result = {
            'filename': file.name,
            'action': 'manual_review',
            'quality_analysis': None,
            'duplicates': [],
            'quality_issues': [],
            'reasons': []
        }
        
        try:
            # Análise de qualidade
            quality_analysis = self.quality_analyzer.analyze_image_quality(file)
            result['quality_analysis'] = quality_analysis
            
            overall_score = quality_analysis.get('overall_score', 0)
            
            # Detecção de duplicatas
            image_hash = self.duplicate_detector.calculate_image_hash(file)
            duplicates = self.duplicate_detector.find_duplicates_in_database(image_hash, manga_id)
            result['duplicates'] = duplicates
            
            # Decisão de moderação
            if duplicates:
                result['action'] = 'auto_reject'
                result['reasons'].append('Imagem duplicada encontrada')
            elif overall_score < self.auto_reject_threshold:
                result['action'] = 'auto_reject'
                result['reasons'].append(f'Qualidade muito baixa (score: {overall_score})')
                result['quality_issues'] = quality_analysis.get('issues', [])
            elif overall_score >= self.auto_approve_threshold:
                result['action'] = 'auto_approve'
                result['reasons'].append(f'Qualidade excelente (score: {overall_score})')
            else:
                result['action'] = 'manual_review'
                result['reasons'].append(f'Qualidade moderada (score: {overall_score}) - revisão manual necessária')
                if quality_analysis.get('issues'):
                    result['quality_issues'] = quality_analysis['issues']
            
        except Exception as e:
            logger.error(f"Erro na moderação de {file.name}: {e}")
            result['action'] = 'manual_review'
            result['reasons'].append(f'Erro na análise: {str(e)}')
        
        return result
    
    def get_moderation_stats(self, manga_id: int = None) -> Dict[str, Any]:
        """Retorna estatísticas de moderação."""
        # Implementação simplificada - em produção consultaria banco de dados
        return {
            'total_files_moderated': 0,
            'auto_approved': 0,
            'manual_review': 0,
            'auto_rejected': 0,
            'duplicates_found': 0,
            'avg_quality_score': 0.0
        }