from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Seed initial users"

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username="joy").exists():
            User.objects.create_user(
                username="joy",
                email="joy@example.com",
                password="mypassword"
            )
            self.stdout.write(self.style.SUCCESS("User 'joy' created"))
        else:
            self.stdout.write(self.style.WARNING("User 'joy' already exists"))

