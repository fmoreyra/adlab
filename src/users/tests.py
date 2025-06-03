from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from .models import Veterinarian, Address


class VeterinaryUserTestCase(TestCase):
    def setUp(self):
        """Set up test client and sample data"""
        self.client = Client()
        self.registration_url = reverse('veterinary_register')
        self.login_url = reverse('veterinary_login')
        self.dashboard_url = reverse('veterinary_dashboard')
        
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
        # Register and login user
        self.client.post(self.registration_url, self.vet_data)
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
