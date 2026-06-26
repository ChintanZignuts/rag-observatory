import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class Command(BaseCommand):
    help = 'Create a default API user and generate token.'

    def handle(self, *args, **options):
        username = os.getenv('DASHBOARD_USERNAME', 'admin')
        password = os.getenv('DASHBOARD_PASSWORD', 'admin123')
        email = 'admin@example.com'

        self.stdout.write(f"Checking if user '{username}' exists...")
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}' with password '{password}'."))
        else:
            self.stdout.write(f"User '{username}' already exists.")

        # Generate or get token
        token, _ = Token.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(f"User '{username}' token: {token.key}"))
