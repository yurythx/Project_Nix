from apps.audiobooks.repositories.audiobook_repository import AudiobookRepository

class AudiobookService:
    def __init__(self, repository=None):
        self.repository = repository or AudiobookRepository()

    def list_audiobooks(self):
        return self.repository.get_all()

    def get_audiobook(self, audiobook_id):
        return self.repository.get_by_id(audiobook_id)

    def create_audiobook(self, data):
        return self.repository.create(data)

    def update_audiobook(self, audiobook_id, data):
        return self.repository.update(audiobook_id, data)

    def delete_audiobook(self, audiobook_id):
        return self.repository.delete(audiobook_id) 