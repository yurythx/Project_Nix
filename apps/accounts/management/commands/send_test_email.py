from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Envia um e-mail de teste para o endereço especificado.'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, required=True, help='Endereço de e-mail de destino')

    def handle(self, *args, **options):
        to_email = options['to']
        subject = 'Teste de envio de e-mail (Fireflies)'
        message = 'Este é um e-mail de teste enviado pelo comando de management do Fireflies.'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not from_email:
            self.stderr.write('ERRO: DEFAULT_FROM_EMAIL não está configurado nas settings.')
            return
        try:
            send_mail(subject, message, from_email, [to_email], fail_silently=False)
            self.stdout.write(f'SUCESSO: E-mail de teste enviado para {to_email} com sucesso!')
        except Exception as e:
            self.stderr.write(f'ERRO ao enviar e-mail: {e}') 