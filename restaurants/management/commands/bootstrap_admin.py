import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the first Django staff account from private deployment variables."

    def handle(self, *args, **options):
        username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "").strip()
        password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
        email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip()
        if not username and not password:
            self.stdout.write("No bootstrap staff credentials configured; skipping.")
            return
        if not username or not password:
            raise CommandError("Set both BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD.")

        user_model = get_user_model()
        existing = user_model.objects.filter(username=username).first()
        if existing:
            if existing.is_staff and existing.is_superuser:
                self.stdout.write(f"Staff account '{username}' already exists; skipping.")
                return
            raise CommandError(f"Username '{username}' already exists without staff access.")

        user_model.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Staff account '{username}' created."))
