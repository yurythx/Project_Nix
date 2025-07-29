"""
Serializers para API REST do app mangas
Implementa serialização completa com otimizações de performance
"""

from rest_framework import serializers
from django.contrib.auth.models import User

from .models.manga import Manga
from .models.volume import Volume
from .models.capitulo import Capitulo
from .models.pagina import Pagina


class UserSerializer(serializers.ModelSerializer):
    """Serializer básico para usuário"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class PaginaSerializer(serializers.ModelSerializer):
    """Serializer para páginas"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Pagina
        fields = [
            'id', 'number', 'image', 'image_url', 'alt_text',
            'created_at', 'updated_at'
        ]
    
    def get_image_url(self, obj):
        """Retorna URL completa da imagem"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class CapituloListSerializer(serializers.ModelSerializer):
    """Serializer para lista de capítulos"""
    
    pages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Capitulo
        fields = [
            'id', 'number', 'title', 'slug', 'description',
            'is_published', 'view_count', 'pages_count',
            'created_at', 'updated_at'
        ]
    
    def get_pages_count(self, obj):
        """Retorna número de páginas do capítulo"""
        return obj.paginas.count()


class CapituloDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para capítulos"""
    
    pages = PaginaSerializer(source='paginas', many=True, read_only=True)
    volume_info = serializers.SerializerMethodField()
    navigation = serializers.SerializerMethodField()
    
    class Meta:
        model = Capitulo
        fields = [
            'id', 'number', 'title', 'slug', 'description',
            'is_published', 'view_count', 'pages', 'volume_info',
            'navigation', 'created_at', 'updated_at'
        ]
    
    def get_volume_info(self, obj):
        """Retorna informações do volume"""
        return {
            'id': obj.volume.id,
            'number': obj.volume.number,
            'title': obj.volume.title,
        }
    
    def get_navigation(self, obj):
        """Retorna informações de navegação"""
        # Aqui seria implementada a lógica de navegação
        # Por simplicidade, retorna estrutura básica
        return {
            'previous_chapter': None,
            'next_chapter': None,
        }


class VolumeSerializer(serializers.ModelSerializer):
    """Serializer para volumes"""
    
    chapters = CapituloListSerializer(source='capitulos', many=True, read_only=True)
    chapters_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Volume
        fields = [
            'id', 'number', 'title', 'description', 'cover_image',
            'chapters', 'chapters_count', 'created_at', 'updated_at'
        ]
    
    def get_chapters_count(self, obj):
        """Retorna número de capítulos do volume"""
        return obj.capitulos.filter(is_published=True).count()


class MangaListSerializer(serializers.ModelSerializer):
    """Serializer para lista de mangás"""
    
    created_by = UserSerializer(read_only=True)
    total_chapters = serializers.SerializerMethodField()
    total_volumes = serializers.SerializerMethodField()
    latest_chapter = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Manga
        fields = [
            'id', 'title', 'slug', 'description', 'author',
            'cover_image', 'cover_image_url', 'status', 'is_published',
            'is_featured', 'view_count', 'created_by', 'total_chapters',
            'total_volumes', 'latest_chapter', 'created_at', 'updated_at'
        ]
    
    def get_total_chapters(self, obj):
        """Retorna total de capítulos publicados"""
        return Capitulo.objects.filter(
            volume__manga=obj,
            is_published=True
        ).count()
    
    def get_total_volumes(self, obj):
        """Retorna total de volumes"""
        return obj.volumes.count()
    
    def get_latest_chapter(self, obj):
        """Retorna informações do último capítulo"""
        latest = Capitulo.objects.filter(
            volume__manga=obj,
            is_published=True
        ).order_by('-volume__number', '-number').first()
        
        if latest:
            return {
                'id': latest.id,
                'number': latest.number,
                'title': latest.title,
                'slug': latest.slug,
                'volume_number': latest.volume.number,
            }
        return None
    
    def get_cover_image_url(self, obj):
        """Retorna URL completa da capa"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class MangaDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para mangás"""
    
    created_by = UserSerializer(read_only=True)
    volumes = VolumeSerializer(many=True, read_only=True)
    statistics = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Manga
        fields = [
            'id', 'title', 'slug', 'description', 'author',
            'cover_image', 'cover_image_url', 'status', 'is_published',
            'is_featured', 'view_count', 'created_by', 'volumes',
            'statistics', 'created_at', 'updated_at'
        ]
    
    def get_statistics(self, obj):
        """Retorna estatísticas do mangá"""
        total_chapters = Capitulo.objects.filter(
            volume__manga=obj,
            is_published=True
        ).count()
        
        total_pages = Pagina.objects.filter(
            capitulo__volume__manga=obj,
            capitulo__is_published=True
        ).count()
        
        return {
            'total_volumes': obj.volumes.count(),
            'total_chapters': total_chapters,
            'total_pages': total_pages,
            'view_count': obj.view_count,
        }
    
    def get_cover_image_url(self, obj):
        """Retorna URL completa da capa"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class MangaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de mangás"""
    
    class Meta:
        model = Manga
        fields = [
            'title', 'description', 'author', 'cover_image',
            'status', 'is_published', 'is_featured'
        ]
    
    def validate_title(self, value):
        """Valida título do mangá"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Título deve ter pelo menos 2 caracteres"
            )
        return value.strip()
    
    def create(self, validated_data):
        """Cria novo mangá"""
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)


class CapituloCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de capítulos"""
    
    class Meta:
        model = Capitulo
        fields = [
            'number', 'title', 'description', 'is_published'
        ]
    
    def validate_number(self, value):
        """Valida número do capítulo"""
        if value < 1:
            raise serializers.ValidationError(
                "Número do capítulo deve ser positivo"
            )
        return value
    
    def validate_title(self, value):
        """Valida título do capítulo"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Título deve ter pelo menos 2 caracteres"
            )
        return value.strip()


class PaginaCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de páginas"""
    
    class Meta:
        model = Pagina
        fields = ['number', 'image', 'alt_text']
    
    def validate_number(self, value):
        """Valida número da página"""
        if value < 1:
            raise serializers.ValidationError(
                "Número da página deve ser positivo"
            )
        return value
    
    def validate_image(self, value):
        """Valida imagem da página"""
        if not value:
            raise serializers.ValidationError(
                "Imagem é obrigatória"
            )
        
        # Validação de tamanho (10MB max)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "Imagem muito grande. Máximo 10MB"
            )
        
        return value
