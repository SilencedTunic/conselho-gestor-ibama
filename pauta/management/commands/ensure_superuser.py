import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Garante que existe um superusuário com as credenciais definidas em "
        "DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD. Idempotente: se o usuário já existir, "
        "apenas atualiza senha e permissões. Não faz nada se as variáveis não estiverem "
        "definidas (ex: ambiente local de desenvolvimento)."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not (username and email and password):
            self.stdout.write("DJANGO_SUPERUSER_* não definidas, pulando.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email}
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        acao = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Superusuário '{username}' {acao}."))
