from apps.articles.models.comment import Comment

class CommentRepository:
    def create(self, **kwargs):
        return Comment.objects.create(**kwargs)

    def get_by_id(self, comment_id):
        return Comment.objects.get(id=comment_id)

    def filter(self, **kwargs):
        return Comment.objects.filter(**kwargs)

    def update(self, comment, **kwargs):
        for key, value in kwargs.items():
            setattr(comment, key, value)
        comment.save()
        return comment 