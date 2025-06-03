from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from allauth.socialaccount.models import SocialApp, SocialAccount
from allauth.account.models import EmailAddress
from django.contrib.sites.models import Site
from .models import Veterinarian, Address


class VeterinaryUserTestCase(TestCase):
    def setUp(self):
        """Set up test client and sample data"""
        self.client = Client()
        self.registration_url = reverse('veterinary_register')
        self.login_url = reverse('veterinary_login')
        self.dashboard_url = reverse('veterinary_dashboard')
        self.complete_profile_url = reverse('complete_profile')
        
        # Sample veterinary user data
        self.vet_data = {
            'username': 'drsmith',
            'password': 'secure123',
            'password_confirm': 'secure123',
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'dr.smith@example.com',
            'phone': '+1234567890',
            'license_number': 'VET12345',
            'province': 'Buenos Aires',
            'city': 'La Plata',
            'street': 'Calle Falsa',
            'number': '123',
            'postal_code': '1900'
        }

    def test_registration_success(self):
        """Test successful veterinary user registration"""
        response = self.client.post(self.registration_url, self.vet_data)
        
        # Should redirect to login
        self.assertRedirects(response, self.login_url)
        
        # Check that user was created
        self.assertTrue(User.objects.filter(username='drsmith').exists())
        
        # Check that veterinarian profile was created
        self.assertTrue(Veterinarian.objects.filter(license_number='VET12345').exists())
        
        # Check that address was created
        self.assertTrue(Address.objects.filter(city='La Plata').exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Registro exitoso' in str(message) for message in messages))

    def test_registration_duplicate_username(self):
        """Test registration fails with duplicate username"""
        # Create first user
        self.client.post(self.registration_url, self.vet_data)
        
        # Try to create second user with same username
        duplicate_data = self.vet_data.copy()
        duplicate_data.update({
            'email': 'different@example.com',
            'phone': '+0987654321',
            'license_number': 'VET54321'
        })
        
        response = self.client.post(self.registration_url, duplicate_data)
        
        # Should not redirect (stays on registration page)
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('nombre de usuario ya existe' in str(message) for message in messages))
        
        # Should only have one user
        self.assertEqual(User.objects.count(), 1)

    def test_registration_duplicate_email(self):
        """Test registration fails with duplicate email"""
        # Create first user
        self.client.post(self.registration_url, self.vet_data)
        
        # Try to create second user with same email
        duplicate_data = self.vet_data.copy()
        duplicate_data.update({
            'username': 'different_user',
            'phone': '+0987654321',
            'license_number': 'VET54321'
        })
        
        response = self.client.post(self.registration_url, duplicate_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('email ya está registrado' in str(message) for message in messages))

    def test_registration_duplicate_license_number(self):
        """Test registration fails with duplicate license number"""
        # Create first user
        self.client.post(self.registration_url, self.vet_data)
        
        # Try to create second user with same license number
        duplicate_data = self.vet_data.copy()
        duplicate_data.update({
            'username': 'different_user',
            'email': 'different@example.com',
            'phone': '+0987654321'
        })
        
        response = self.client.post(self.registration_url, duplicate_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('matrícula ya está registrado' in str(message) for message in messages))

    def test_registration_duplicate_phone(self):
        """Test registration fails with duplicate phone number"""
        # Create first user
        self.client.post(self.registration_url, self.vet_data)
        
        # Try to create second user with same phone
        duplicate_data = self.vet_data.copy()
        duplicate_data.update({
            'username': 'different_user',
            'email': 'different@example.com',
            'license_number': 'VET54321'
        })
        
        response = self.client.post(self.registration_url, duplicate_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('teléfono ya está registrado' in str(message) for message in messages))

    def test_registration_password_mismatch(self):
        """Test registration fails when passwords don't match"""
        invalid_data = self.vet_data.copy()
        invalid_data['password_confirm'] = 'different_password'
        
        response = self.client.post(self.registration_url, invalid_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('contraseñas no coinciden' in str(message) for message in messages))
        
        # Should not create user
        self.assertEqual(User.objects.count(), 0)

    def test_registration_short_password(self):
        """Test registration fails with short password"""
        invalid_data = self.vet_data.copy()
        invalid_data['password'] = '123'
        invalid_data['password_confirm'] = '123'
        
        response = self.client.post(self.registration_url, invalid_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('al menos 6 caracteres' in str(message) for message in messages))

    def test_registration_missing_fields(self):
        """Test registration fails with missing required fields"""
        incomplete_data = {
            'username': 'drsmith',
            'password': 'secure123',
            # Missing other required fields
        }
        
        response = self.client.post(self.registration_url, incomplete_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('campos son obligatorios' in str(message) for message in messages))

    def test_login_success(self):
        """Test successful login and redirect to dashboard"""
        # First register a user
        self.client.post(self.registration_url, self.vet_data)
        
        # Approve the user
        vet = Veterinarian.objects.get(license_number='VET12345')
        vet.is_approved = True
        vet.save()
        
        # Then try to log in
        login_data = {
            'username': 'drsmith',
            'password': 'secure123'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        # Should redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Bienvenido, Dr. John Smith' in str(message) for message in messages))

    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        # Register a user first
        self.client.post(self.registration_url, self.vet_data)
        
        # Try to log in with wrong password
        login_data = {
            'username': 'drsmith',
            'password': 'wrong_password'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        # Should not redirect (stays on login page)
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Usuario o contraseña incorrectos' in str(message) for message in messages))

    def test_login_non_veterinary_user(self):
        """Test login fails for non-veterinary users"""
        # Create a regular user without veterinary profile
        User.objects.create_user(
            username='regularuser',
            password='password123',
            email='regular@example.com'
        )
        
        login_data = {
            'username': 'regularuser',
            'password': 'password123'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Solo veterinarios pueden ingresar' in str(message) for message in messages))

    def test_dashboard_access_authenticated(self):
        """Test dashboard access for authenticated veterinary user"""
        # Register and approve user
        self.client.post(self.registration_url, self.vet_data)
        vet = Veterinarian.objects.get(license_number='VET12345')
        vet.is_approved = True
        vet.save()
        
        # Login user
        self.client.post(self.login_url, {
            'username': 'drsmith',
            'password': 'secure123'
        })
        
        # Access dashboard
        response = self.client.get(self.dashboard_url)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        
        # Should contain user information
        self.assertContains(response, 'John Smith')
        self.assertContains(response, 'dr.smith@example.com')
        self.assertContains(response, 'VET12345')

    def test_dashboard_access_unauthenticated(self):
        """Test dashboard redirects unauthenticated users to login"""
        response = self.client.get(self.dashboard_url)
        
        # Should redirect to login
        self.assertRedirects(response, self.login_url)

    def test_dashboard_access_non_veterinary_user(self):
        """Test dashboard access denied for non-veterinary authenticated users"""
        # Create and login regular user
        user = User.objects.create_user(
            username='regularuser',
            password='password123',
            email='regular@example.com'
        )
        self.client.force_login(user)
        
        # Try to access dashboard
        response = self.client.get(self.dashboard_url)
        
        # Should redirect to login
        self.assertRedirects(response, self.login_url)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Acceso denegado' in str(message) for message in messages))

    def test_registration_without_address(self):
        """Test registration works without address information"""
        data_without_address = {
            'username': 'drjones',
            'password': 'secure123',
            'password_confirm': 'secure123',
            'first_name': 'Jane',
            'last_name': 'Jones',
            'email': 'dr.jones@example.com',
            'phone': '+9876543210',
            'license_number': 'VET98765'
        }
        
        response = self.client.post(self.registration_url, data_without_address)
        
        # Should redirect to login
        self.assertRedirects(response, self.login_url)
        
        # Check that user was created
        self.assertTrue(User.objects.filter(username='drjones').exists())
        
        # Check that veterinarian profile was created without address
        vet = Veterinarian.objects.get(license_number='VET98765')
        self.assertIsNone(vet.address)

    def test_login_get_request(self):
        """Test GET request to login page"""
        response = self.client.get(self.login_url)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        
        # Should contain login form
        self.assertContains(response, 'Log in')
        self.assertContains(response, 'Usuario:')
        self.assertContains(response, 'Contraseña:')

    def test_registration_get_request(self):
        """Test GET request to registration page"""
        response = self.client.get(self.registration_url)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        
        # Should contain registration form
        self.assertContains(response, 'Registrarse')
        self.assertContains(response, 'Usuario:')
        self.assertContains(response, 'Nro. Matrícula:')

    def test_registration_invalid_phone_number(self):
        """Test registration fails with invalid phone number containing letters"""
        invalid_data = self.vet_data.copy()
        invalid_data['phone'] = '+123abc456'
        
        response = self.client.post(self.registration_url, invalid_data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('solo puede contener números' in str(message) for message in messages))

    def test_registration_valid_phone_formats(self):
        """Test registration accepts valid phone number formats"""
        valid_phones = [
            '+1234567890',
            '123-456-7890',
            '(123) 456-7890',
            '123 456 7890',
            '+54 9 11 1234-5678',
            '1234567890'
        ]
        
        for i, phone in enumerate(valid_phones):
            valid_data = self.vet_data.copy()
            valid_data.update({
                'username': f'drtest{i}',
                'email': f'test{i}@example.com',
                'license_number': f'VET{i}2345',
                'phone': phone
            })
            
            response = self.client.post(self.registration_url, valid_data)
            
            # Should redirect to login (successful registration)
            self.assertRedirects(response, self.login_url)
            
            # Check that user was created
            self.assertTrue(User.objects.filter(username=f'drtest{i}').exists())

    def test_registration_invalid_phone_special_chars(self):
        """Test registration fails with phone number containing invalid special characters"""
        invalid_phones = [
            '+123#456',
            '123*456*7890',
            '123@456.com',
            'abc-def-ghij',
            '123.456.7890',  # dots not allowed
            '123_456_7890'   # underscores not allowed
        ]
        
        for phone in invalid_phones:
            invalid_data = self.vet_data.copy()
            invalid_data['phone'] = phone
            
            response = self.client.post(self.registration_url, invalid_data)
            
            # Should not redirect (stays on registration page)
            self.assertEqual(response.status_code, 200)
            
            # Check error message appears
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any('solo puede contener números' in str(message) for message in messages))

    def test_registration_creates_unapproved_user(self):
        """Test that new registrations create unapproved users by default"""
        response = self.client.post(self.registration_url, self.vet_data)
        
        # Should redirect to login
        self.assertRedirects(response, self.login_url)
        
        # Check that veterinarian was created as unapproved
        vet = Veterinarian.objects.get(license_number='VET12345')
        self.assertFalse(vet.is_approved)
        
        # Check success message mentions approval
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('pendiente de aprobación' in str(message) for message in messages))

    def test_login_unapproved_user(self):
        """Test that unapproved users cannot log in"""
        # Register a user (will be unapproved by default)
        self.client.post(self.registration_url, self.vet_data)
        
        # Try to log in
        login_data = {
            'username': 'drsmith',
            'password': 'secure123'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        # Should not redirect (stays on login page)
        self.assertEqual(response.status_code, 200)
        
        # Check error message about pending approval
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('pendiente de aprobación' in str(message) for message in messages))

    def test_login_approved_user(self):
        """Test that approved users can log in successfully"""
        # Register a user
        self.client.post(self.registration_url, self.vet_data)
        
        # Approve the user
        vet = Veterinarian.objects.get(license_number='VET12345')
        vet.is_approved = True
        vet.save()
        
        # Try to log in
        login_data = {
            'username': 'drsmith',
            'password': 'secure123'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        # Should redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Bienvenido, Dr. John Smith' in str(message) for message in messages))

    def test_dashboard_access_unapproved_user(self):
        """Test dashboard access denied for unapproved users"""
        # Register a user
        self.client.post(self.registration_url, self.vet_data)
        
        # Force login the user (bypassing our login check)
        user = User.objects.get(username='drsmith')
        self.client.force_login(user)
        
        # Try to access dashboard
        response = self.client.get(self.dashboard_url)
        
        # Should redirect to login
        self.assertRedirects(response, self.login_url)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('no ha sido aprobada' in str(message) for message in messages))

    def test_dashboard_access_approved_user(self):
        """Test dashboard access works for approved users"""
        # Register and approve a user
        self.client.post(self.registration_url, self.vet_data)
        vet = Veterinarian.objects.get(license_number='VET12345')
        vet.is_approved = True
        vet.save()
        
        # Login the user
        self.client.post(self.login_url, {
            'username': 'drsmith',
            'password': 'secure123'
        })
        
        # Access dashboard
        response = self.client.get(self.dashboard_url)
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        
        # Should contain user information
        self.assertContains(response, 'John Smith')
        self.assertContains(response, 'dr.smith@example.com')

    def test_veterinarian_str_method_shows_approval_status(self):
        """Test that the __str__ method shows approval status with icons"""
        # Create unapproved veterinarian
        self.client.post(self.registration_url, self.vet_data)
        vet = Veterinarian.objects.get(license_number='VET12345')
        
        # Check unapproved status
        self.assertIn('⏳', str(vet))
        self.assertIn('John Smith', str(vet))
        
        # Approve and check approved status
        vet.is_approved = True
        vet.save()
        self.assertIn('✓', str(vet))
        self.assertIn('John Smith', str(vet))

    def test_admin_approval_workflow(self):
        """Test that approval field works correctly in the model"""
        # Create veterinarian
        user = User.objects.create_user(
            username='testvet',
            password='testpass',
            first_name='Test',
            last_name='Vet',
            email='test@vet.com'
        )
        
        vet = Veterinarian.objects.create(
            user=user,
            phone='+1234567890',
            license_number='TEST123'
        )
        
        # Should be unapproved by default
        self.assertFalse(vet.is_approved)
        
        # Approve
        vet.is_approved = True
        vet.save()
        
        # Verify approval
        vet.refresh_from_db()
        self.assertTrue(vet.is_approved)


class CompleteProfileTestCase(TestCase):
    """Test cases for the complete_profile view for Google OAuth users"""
    
    def setUp(self):
        self.client = Client()
        self.complete_profile_url = reverse('complete_profile')
        self.login_url = reverse('veterinary_login')
        self.dashboard_url = reverse('veterinary_dashboard')
        
        # Create a social user (Google OAuth)
        self.social_user = User.objects.create_user(
            username='googlesocialuser',
            email='google.user@gmail.com',
            first_name='Google',
            last_name='User'
        )
        
        # Create an EmailAddress for the social user
        EmailAddress.objects.create(
            user=self.social_user,
            email='google.user@gmail.com',
            verified=True,
            primary=True
        )
    
    def test_complete_profile_get_unauthenticated(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(self.complete_profile_url)
        self.assertRedirects(response, '/accounts/login/?next=/users/complete-profile/')
    
    def test_complete_profile_get_authenticated_no_profile(self):
        """Test GET request for authenticated user without veterinarian profile"""
        self.client.force_login(self.social_user)
        response = self.client.get(self.complete_profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Google User')
        self.assertContains(response, 'google.user@gmail.com')
        self.assertContains(response, 'Completar Perfil')
    
    def test_complete_profile_post_success(self):
        """Test successful profile completion"""
        self.client.force_login(self.social_user)
        
        profile_data = {
            'phone': '+54911234567',
            'license_number': 'GOOGLE123',
            'province': 'Buenos Aires',
            'city': 'CABA',
            'street': 'Av. Corrientes',
            'number': '1234',
            'postal_code': '1001'
        }
        
        response = self.client.post(self.complete_profile_url, profile_data)
        
        # Should show pending approval template
        self.assertEqual(response.status_code, 200)
        
        # Check that veterinarian profile was created
        vet = Veterinarian.objects.get(user=self.social_user)
        self.assertEqual(vet.phone, '+54911234567')
        self.assertEqual(vet.license_number, 'GOOGLE123')
        self.assertFalse(vet.is_approved)  # Should be unapproved by default
        
        # Check that address was created
        self.assertIsNotNone(vet.address)
        self.assertEqual(vet.address.city, 'CABA')
    
    def test_complete_profile_post_missing_required_fields(self):
        """Test profile completion fails with missing required fields"""
        self.client.force_login(self.social_user)
        
        incomplete_data = {
            'phone': '+54911234567',
            # Missing license_number
        }
        
        response = self.client.post(self.complete_profile_url, incomplete_data)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('teléfono y número de matrícula son obligatorios' in str(message) for message in messages))
        
        # Should not create veterinarian profile
        self.assertFalse(Veterinarian.objects.filter(user=self.social_user).exists())
    
    def test_complete_profile_post_duplicate_license(self):
        """Test profile completion fails with duplicate license number"""
        # Create existing veterinarian with license
        existing_user = User.objects.create_user(username='existing', email='existing@test.com')
        Veterinarian.objects.create(
            user=existing_user,
            phone='+5499999999',
            license_number='DUPLICATE123'
        )
        
        self.client.force_login(self.social_user)
        
        duplicate_data = {
            'phone': '+54911234567',
            'license_number': 'DUPLICATE123'
        }
        
        response = self.client.post(self.complete_profile_url, duplicate_data)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('matrícula ya está registrado' in str(message) for message in messages))
    
    def test_complete_profile_post_duplicate_phone(self):
        """Test profile completion fails with duplicate phone number"""
        # Create existing veterinarian with phone
        existing_user = User.objects.create_user(username='existing', email='existing@test.com')
        Veterinarian.objects.create(
            user=existing_user,
            phone='+54911234567',
            license_number='EXISTING123'
        )
        
        self.client.force_login(self.social_user)
        
        duplicate_data = {
            'phone': '+54911234567',
            'license_number': 'GOOGLE123'
        }
        
        response = self.client.post(self.complete_profile_url, duplicate_data)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('teléfono ya está registrado' in str(message) for message in messages))
    
    def test_complete_profile_post_invalid_phone(self):
        """Test profile completion fails with invalid phone format"""
        self.client.force_login(self.social_user)
        
        invalid_data = {
            'phone': 'invalid_phone_123@',
            'license_number': 'GOOGLE123'
        }
        
        response = self.client.post(self.complete_profile_url, invalid_data)
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('solo puede contener números' in str(message) for message in messages))
    
    def test_complete_profile_already_has_approved_profile(self):
        """Test user with approved profile is redirected to dashboard"""
        # Create approved veterinarian profile
        vet = Veterinarian.objects.create(
            user=self.social_user,
            phone='+54911111111',
            license_number='APPROVED123',
            is_approved=True
        )
        
        self.client.force_login(self.social_user)
        response = self.client.get(self.complete_profile_url)
        
        self.assertRedirects(response, self.dashboard_url)
    
    def test_complete_profile_already_has_unapproved_profile(self):
        """Test user with unapproved profile sees pending approval"""
        # Create unapproved veterinarian profile
        vet = Veterinarian.objects.create(
            user=self.social_user,
            phone='+54911111111',
            license_number='PENDING123',
            is_approved=False
        )
        
        self.client.force_login(self.social_user)
        response = self.client.get(self.complete_profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cuenta Pendiente de Aprobación')
    
    def test_complete_profile_without_address(self):
        """Test profile completion works without address information"""
        self.client.force_login(self.social_user)
        
        minimal_data = {
            'phone': '+54911234567',
            'license_number': 'MINIMAL123'
        }
        
        response = self.client.post(self.complete_profile_url, minimal_data)
        
        # Should show pending approval template
        self.assertEqual(response.status_code, 200)
        
        # Check that veterinarian profile was created without address
        vet = Veterinarian.objects.get(user=self.social_user)
        self.assertEqual(vet.phone, '+54911234567')
        self.assertEqual(vet.license_number, 'MINIMAL123')
        self.assertIsNone(vet.address)
