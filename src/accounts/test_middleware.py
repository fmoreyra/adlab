"""
Tests for VeterinarianProfileRequiredMiddleware.
"""

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.middleware import VeterinarianProfileRequiredMiddleware
from accounts.models import Address, Veterinarian

User = get_user_model()


class VeterinarianProfileRequiredMiddlewareTest(TestCase):
    """Test cases for VeterinarianProfileRequiredMiddleware."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.middleware = VeterinarianProfileRequiredMiddleware(lambda r: None)

        # Create test users
        self.vet_user = User.objects.create_user(
            username="vet@example.com",
            email="vet@example.com",
            password="testpass123",
            first_name="Test",
            last_name="Vet",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        self.staff_user = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="testpass123",
            first_name="Test",
            last_name="Staff",
            role=User.Role.PERSONAL_LAB,
        )

        self.admin_user = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="testpass123",
            first_name="Test",
            last_name="Admin",
            role=User.Role.ADMIN,
        )

        # Create complete veterinarian profile
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="Test",
            last_name="Vet",
            license_number="MP-12345",
            phone="+54 11 1234-5678",
            email="vet@example.com",
        )

        # Create address for complete profile
        self.address = Address.objects.create(
            veterinarian=self.veterinarian,
            province="Buenos Aires",
            locality="CABA",
            street="Av. Corrientes",
            number="1234",
        )

    def test_middleware_allows_non_authenticated_users(self):
        """Test that middleware allows non-authenticated users."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()  # Anonymous user

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # No redirect

    def test_middleware_allows_non_veterinarians(self):
        """Test that middleware allows non-veterinarian users."""
        request = self.factory.get("/")
        request.user = self.staff_user

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # No redirect

    def test_middleware_allows_veterinarians_with_complete_profile(self):
        """Test that middleware allows veterinarians with complete profiles."""
        request = self.factory.get("/")
        request.user = self.vet_user

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # No redirect

    def test_middleware_redirects_veterinarians_without_profile(self):
        """Test that middleware redirects veterinarians without profiles."""
        # Create veterinarian without profile
        vet_no_profile = User.objects.create_user(
            username="vet_noprofile@example.com",
            email="vet_noprofile@example.com",
            password="testpass123",
            first_name="Test",
            last_name="VetNoProfile",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        request = self.factory.get("/")
        request.user = vet_no_profile

        response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:complete_profile"))

    def test_middleware_redirects_veterinarians_with_incomplete_profile(self):
        """Test that middleware redirects veterinarians with incomplete profiles."""
        # Create veterinarian with incomplete profile
        vet_incomplete = User.objects.create_user(
            username="vet_incomplete@example.com",
            email="vet_incomplete@example.com",
            password="testpass123",
            first_name="Test",
            last_name="VetIncomplete",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        # Create incomplete profile (missing required fields)
        Veterinarian.objects.create(
            user=vet_incomplete,
            first_name="Test",
            last_name="",  # Missing last name
            license_number="",  # Missing license
            phone="",  # Missing phone
            email="",  # Missing email
        )

        request = self.factory.get("/")
        request.user = vet_incomplete

        response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:complete_profile"))

    def test_middleware_allows_whitelisted_urls(self):
        """Test that middleware allows access to whitelisted URLs."""
        vet_no_profile = User.objects.create_user(
            username="vet_noprofile@example.com",
            email="vet_noprofile@example.com",
            password="testpass123",
            first_name="Test",
            last_name="VetNoProfile",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        # Test complete profile URL
        request = self.factory.get("/accounts/veterinarian/complete-profile/")
        request.user = vet_no_profile

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # No redirect

        # Test logout URL
        request = self.factory.get("/accounts/logout/")
        request.user = vet_no_profile

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # No redirect

        # Test admin URL
        request = self.factory.get("/admin/")
        request.user = vet_no_profile

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # No redirect

        # Test static files
        request = self.factory.get("/static/css/app.css")
        request.user = vet_no_profile

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # No redirect

    def test_middleware_redirects_non_whitelisted_urls(self):
        """Test that middleware redirects non-whitelisted URLs for incomplete profiles."""
        vet_no_profile = User.objects.create_user(
            username="vet_noprofile@example.com",
            email="vet_noprofile@example.com",
            password="testpass123",
            first_name="Test",
            last_name="VetNoProfile",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        # Test dashboard URL
        request = self.factory.get("/dashboard/")
        request.user = vet_no_profile

        response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:complete_profile"))

        # Test protocols URL
        request = self.factory.get("/protocols/")
        request.user = vet_no_profile

        response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:complete_profile"))

    def test_has_complete_profile_method(self):
        """Test the _has_complete_profile method."""
        # Test complete profile
        self.assertTrue(self.middleware._has_complete_profile(self.vet_user))

        # Test user without profile
        vet_no_profile = User.objects.create_user(
            username="vet_noprofile@example.com",
            email="vet_noprofile@example.com",
            password="testpass123",
            first_name="Test",
            last_name="VetNoProfile",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.assertFalse(self.middleware._has_complete_profile(vet_no_profile))

        # Test user with incomplete profile
        vet_incomplete = User.objects.create_user(
            username="vet_incomplete@example.com",
            email="vet_incomplete@example.com",
            password="testpass123",
            first_name="Test",
            last_name="VetIncomplete",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        Veterinarian.objects.create(
            user=vet_incomplete,
            first_name="Test",
            last_name="",  # Missing last name
            license_number="MP-67890",  # Different license number
            phone="+54 11 1234-5678",
            email="vet_incomplete@example.com",
        )
        self.assertFalse(self.middleware._has_complete_profile(vet_incomplete))

    def test_is_whitelisted_url_method(self):
        """Test the _is_whitelisted_url method."""
        # Test whitelisted URLs
        self.assertTrue(
            self.middleware._is_whitelisted_url(
                "/accounts/veterinarian/complete-profile/"
            )
        )
        self.assertTrue(
            self.middleware._is_whitelisted_url("/accounts/logout/")
        )
        self.assertTrue(self.middleware._is_whitelisted_url("/admin/"))
        self.assertTrue(
            self.middleware._is_whitelisted_url("/static/css/app.css")
        )
        self.assertTrue(
            self.middleware._is_whitelisted_url("/media/uploads/file.jpg")
        )

        # Test non-whitelisted URLs
        self.assertFalse(self.middleware._is_whitelisted_url("/dashboard/"))
        self.assertFalse(self.middleware._is_whitelisted_url("/protocols/"))
        self.assertFalse(
            self.middleware._is_whitelisted_url("/accounts/profile/")
        )
