import os
import imghdr
import zipfile
import rarfile
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible
from PIL import Image
import logging

from apps.mangas.constants.file_limits import (
    MAX_UPLOAD_SIZE,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIME_TYPES,
    ALLOWED_ARCHIVE_EXTENSIONS,
    ALLOWED_ARCHIVE_MIME_TYPES,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    MAX_IMAGE_WIDTH,
    MAX_IMAGE_HEIGHT,
    ERROR_MESSAGES
)

logger = logging.getLogger(__name__)

@deconstructible
class BaseFileValidator:
    def __init__(self, max_size=None, allowed_extensions=None, allowed_mimetypes=None, message=None):
        self.max_size = max_size or MAX_UPLOAD_SIZE
        self.allowed_extensions = allowed_extensions or []
        self.allowed_mimetypes = allowed_mimetypes or []
        self.message = message

    def __call__(self, value):
        if self.max_size and value.size > self.max_size:
            raise ValidationError(
                self.message or ERROR_MESSAGES['file_too_large'].format(filesizeformat(self.max_size))
            )

        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        if self.allowed_extensions and ext not in self.allowed_extensions:
            raise ValidationError(
                self.message or ERROR_MESSAGES['invalid_file_type'].format(', '.join(self.allowed_extensions))
            )

        if self.allowed_mimetypes and value.content_type not in self.allowed_mimetypes:
            raise ValidationError(
                self.message or ERROR_MESSAGES['invalid_file_type'].format(', '.join(self.allowed_mimetypes))
            )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.max_size == other.max_size and
            self.allowed_extensions == other.allowed_extensions and
            self.allowed_mimetypes == other.allowed_mimetypes and
            self.message == other.message
        )

@deconstructible
class ImageFileValidator(BaseFileValidator):
    def __init__(self, min_width=None, min_height=None, max_width=None, max_height=None, **kwargs):
        super().__init__(
            allowed_extensions=kwargs.pop('allowed_extensions', ALLOWED_IMAGE_EXTENSIONS),
            allowed_mimetypes=kwargs.pop('allowed_mimetypes', ALLOWED_IMAGE_MIME_TYPES),
            **kwargs
        )
        self.min_width = min_width or MIN_IMAGE_WIDTH
        self.min_height = min_height or MIN_IMAGE_HEIGHT
        self.max_width = max_width or MAX_IMAGE_WIDTH
        self.max_height = max_height or MAX_IMAGE_HEIGHT

    def __call__(self, value):
        super().__call__(value)

        try:
            with Image.open(value) as img:
                width, height = img.size

                if width < self.min_width or height < self.min_height:
                    raise ValidationError(
                        ERROR_MESSAGES['image_dimensions_too_small'].format(self.min_width, self.min_height)
                    )
                if width > self.max_width or height > self.max_height:
                    raise ValidationError(
                        ERROR_MESSAGES['image_dimensions_too_large'].format(self.max_width, self.max_height)
                    )

                # Basic check for image integrity
                img.verify()

        except (IOError, SyntaxError, Image.DecompressionBombError) as e:
            logger.error(f"Image validation error for {value.name}: {e}")
            raise ValidationError("O arquivo não é uma imagem válida ou está corrompido.")
        except Exception as e:
            logger.error(f"Unexpected image validation error for {value.name}: {e}")
            raise ValidationError("Ocorreu um erro inesperado ao validar a imagem.")

    def __eq__(self, other):
        return (
            super().__eq__(other) and
            isinstance(other, self.__class__) and
            self.min_width == other.min_width and
            self.min_height == other.min_height and
            self.max_width == other.max_width and
            self.max_height == other.max_height
        )

@deconstructible
class ArchiveFileValidator(BaseFileValidator):
    def __init__(self, **kwargs):
        super().__init__(
            allowed_extensions=kwargs.pop('allowed_extensions', ALLOWED_ARCHIVE_EXTENSIONS),
            allowed_mimetypes=kwargs.pop('allowed_mimetypes', ALLOWED_ARCHIVE_MIME_TYPES),
            **kwargs
        )

    def __call__(self, value):
        super().__call__(value)

        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        try:
            if ext == 'zip' or ext == 'cbz':
                with zipfile.ZipFile(value) as zf:
                    # Check if there's at least one file and it's not a directory
                    if not any(not f.endswith('/') for f in zf.namelist()):
                        raise ValidationError(ERROR_MESSAGES['invalid_archive_content'])
            elif ext == 'rar' or ext == 'cbr':
                with rarfile.RarFile(value) as rf:
                    # Check if there's at least one file and it's not a directory
                    if not any(not f.endswith('/') for f in rf.namelist()):
                        raise ValidationError(ERROR_MESSAGES['invalid_archive_content'])
            elif ext == 'pdf':
                # For PDF, a simple read attempt might suffice for basic validation
                value.read(1024) # Try reading first 1KB
                value.seek(0) # Reset pointer
            else:
                # This case should ideally be caught by allowed_extensions, but as a fallback
                raise ValidationError(ERROR_MESSAGES['invalid_file_type'].format(', '.join(self.allowed_extensions)))

        except (zipfile.BadZipFile, rarfile.BadRarFile, EOFError, TypeError) as e:
            logger.error(f"Archive validation error for {value.name}: {e}")
            raise ValidationError("O arquivo compactado está corrompido ou não é válido.")
        except Exception as e:
            logger.error(f"Unexpected archive validation error for {value.name}: {e}")
            raise ValidationError("Ocorreu um erro inesperado ao validar o arquivo compactado.")

@deconstructible
class ContentValidator:
    def __init__(self, model, field_name, message=None):
        self.model = model
        self.field_name = field_name
        self.message = message

    def __call__(self, value, instance=None):
        # Check for uniqueness, excluding the current instance if it's an update
        query = {self.field_name: value}
        if instance and instance.pk:
            if self.model.objects.filter(**query).exclude(pk=instance.pk).exists():
                raise ValidationError(
                    self.message or ERROR_MESSAGES['number_not_unique'].format(self.model._meta.verbose_name)
                )
        else:
            if self.model.objects.filter(**query).exists():
                raise ValidationError(
                    self.message or ERROR_MESSAGES['number_not_unique'].format(self.model._meta.verbose_name)
                )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.model == other.model and
            self.field_name == other.field_name and
            self.message == other.message
        )