from apps.articles.repositories.comment_repository import CommentRepository
from apps.articles.models.article import Article
from apps.articles.models.comment import Comment

class CommentService:
    def __init__(self, comment_repository=None):
        self.comment_repository = comment_repository or CommentRepository()

    def add_comment(self, article: Article, user, name, email, content, website=None, ip_address=None, user_agent=None):
        # Validações de negócio
        if not content or len(content) < 10:
            raise ValueError("Comentário deve ter pelo menos 10 caracteres")
        if not name:
            raise ValueError("Nome é obrigatório")
        if not email:
            raise ValueError("Email é obrigatório")
        # Outras validações podem ser adicionadas aqui
        comment = self.comment_repository.create(
            article=article,
            user=user if user and user.is_authenticated else None,
            name=name,
            email=email,
            content=content,
            website=website,
            ip_address=ip_address,
            user_agent=user_agent,
            is_approved=True  # ou lógica de aprovação
        )
        return comment

    def add_reply(self, article: Article, parent_comment: Comment, user, name, email, content, ip_address=None, user_agent=None):
        if not content or len(content) < 10:
            raise ValueError("Resposta deve ter pelo menos 10 caracteres")
        if not name:
            raise ValueError("Nome é obrigatório")
        if not email:
            raise ValueError("Email é obrigatório")
        reply = self.comment_repository.create(
            article=article,
            parent=parent_comment,
            user=user if user and user.is_authenticated else None,
            name=name,
            email=email,
            content=content,
            ip_address=ip_address,
            user_agent=user_agent,
            is_approved=True
        )
        return reply

    def moderate_comment(self, comment_id, is_approved, is_spam):
        comment = self.comment_repository.get_by_id(comment_id)
        comment.is_approved = is_approved
        comment.is_spam = is_spam
        comment.save()
        return comment 