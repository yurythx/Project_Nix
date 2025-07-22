import random
from django.core.exceptions import ObjectDoesNotExist
from apps.accounts.models.verification import VerificationCode
from apps.accounts.interfaces.repositories import IVerificationRepository

class DjangoVerificationRepository(IVerificationRepository):
    """Implementação concreta do repositório de códigos de verificação"""
    
    def create_verification_code(self, user, code_type: str) -> str:
        """
        Cria um novo código de verificação
        :return: O código de 6 dígitos gerado
        """
        # Remove códigos existentes do mesmo tipo
        VerificationCode.objects.filter(
            user=user, 
            code_type=code_type
        ).delete()
        
        # Gera código de 6 dígitos
        code = str(random.randint(100000, 999999))
        
        # Cria e salva o novo código
        VerificationCode.objects.create(
            user=user,
            code=code,
            code_type=code_type
        )
        
        return code
    
    def verify_code(self, user, code: str, code_type: str) -> bool:
        """
        Verifica se o código é válido
        :return: True se válido, False se inválido ou expirado
        """
        try:
            verification = VerificationCode.objects.get(
                user=user,
                code=code,
                code_type=code_type
            )
            
            if verification.is_expired():
                verification.delete()
                return False
                
            return True
        except VerificationCode.DoesNotExist:
            return False
    
    def delete_code(self, user, code_type: str) -> None:
        """Remove todos os códigos de um tipo específico para o usuário"""
        VerificationCode.objects.filter(
            user=user, 
            code_type=code_type
        ).delete()