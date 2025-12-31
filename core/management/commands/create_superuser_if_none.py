import os
import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

class Command(BaseCommand):
    help = 'Create a superuser if none exists'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Checking for existing superuser...')
            self.stdout.flush()

            User = get_user_model()

            # Check if any superuser exists
            superuser_count = User.objects.filter(is_superuser=True).count()
            self.stdout.write(f'Found {superuser_count} superuser(s)')
            self.stdout.flush()

            if superuser_count > 0:
                self.stdout.write(self.style.SUCCESS('Superuser already exists, skipping creation'))
                self.stdout.flush()
                return

            # Get credentials from environment variables or use defaults
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

            self.stdout.write(f'Creating superuser "{username}"...')
            self.stdout.flush()

            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )

            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully!'))
            self.stdout.write(self.style.WARNING('Default credentials - Please change password after first login!'))
            self.stdout.flush()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))
            self.stdout.flush()
            # Don't exit with error - we want the server to start even if superuser creation fails
            import traceback
            traceback.print_exc()
            self.stdout.write(self.style.WARNING('Continuing without superuser...'))
