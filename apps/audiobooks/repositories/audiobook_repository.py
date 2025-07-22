from apps.audiobooks.interfaces.audiobook_repository import AudiobookRepositoryInterface

class AudiobookRepository(AudiobookRepositoryInterface):
    def get_all(self):
        # Implementação real
        pass

    def get_by_id(self, audiobook_id):
        pass

    def create(self, data):
        pass

    def update(self, audiobook_id, data):
        pass

    def delete(self, audiobook_id):
        pass 