# Pacote de mixins do app audiobooks
from .permission_mixins import (
    VideoAudioOwnerOrStaffMixin,
    VideoAudioCreatorRequiredMixin,
    VideoAudioReadOnlyMixin,
    VideoProgressOwnerOrStaffMixin,
    VideoFavoriteOwnerOrStaffMixin
)

__all__ = [
    'VideoAudioOwnerOrStaffMixin',
    'VideoAudioCreatorRequiredMixin', 
    'VideoAudioReadOnlyMixin',
    'VideoProgressOwnerOrStaffMixin',
    'VideoFavoriteOwnerOrStaffMixin'
]