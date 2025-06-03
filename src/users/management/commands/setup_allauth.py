from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up django-allauth with Google OAuth'

    def handle(self, *args, **options):
        # Update or create the Site
        site, created = Site.objects.get_or_create(
            id=settings.SITE_ID,
            defaults={
                'domain': 'localhost:8000',
                'name': 'FCV Veterinary Lab'
            }
        )
        
        if not created:
            site.domain = 'localhost:8000'
            site.name = 'FCV Veterinary Lab'
            site.save()
            
        self.stdout.write(
            self.style.SUCCESS(f'Site updated: {site.domain}')
        )
        
        # Create Google OAuth application (if not exists)
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': 'your-google-client-id-here',
                'secret': 'your-google-client-secret-here',
            }
        )
        
        if created:
            google_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS('Google OAuth app created')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Google OAuth app already exists')
            )
            
        self.stdout.write(
            self.style.SUCCESS('Django-allauth setup complete!')
        )
        self.stdout.write(
            self.style.WARNING('Remember to update the Google OAuth credentials in the Django admin!')
        ) 