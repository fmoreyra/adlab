import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Veterinarian, Address

# Create your views here.

@csrf_protect
def veterinary_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has a veterinarian profile
            try:
                veterinarian = Veterinarian.objects.get(user=user)
                if not veterinarian.is_approved:
                    messages.error(request, 'Tu cuenta está pendiente de aprobación por un administrador. Por favor, espera a que tu cuenta sea activada.')
                    return render(request, 'users/veterinary_login.html')
                login(request, user)
                messages.success(request, f'Bienvenido, Dr. {veterinarian.first_name} {veterinarian.last_name}')
                return redirect('veterinary_dashboard')
            except Veterinarian.DoesNotExist:
                messages.error(request, 'Acceso denegado. Solo veterinarios pueden ingresar.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'users/veterinary_login.html')

@csrf_protect
def veterinary_register(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        license_number = request.POST.get('license_number')
        
        # Address fields
        province = request.POST.get('province')
        city = request.POST.get('city')
        street = request.POST.get('street')
        number = request.POST.get('number')
        postal_code = request.POST.get('postal_code')
        
        # Validation
        errors = []
        
        if not all([username, password, password_confirm, first_name, last_name, email, phone, license_number]):
            errors.append('Todos los campos son obligatorios.')
        
        if password != password_confirm:
            errors.append('Las contraseñas no coinciden.')
        
        if len(password) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres.')
        
        # Validate phone number (only numbers, spaces, hyphens, plus signs, and parentheses)
        if phone:  # Only validate if phone is provided
            phone_pattern = r'^[\d\s\-\+\(\)]+$'
            if not re.match(phone_pattern, phone):
                errors.append('El número de teléfono solo puede contener números, espacios, guiones, paréntesis y el signo +.')
        
        if User.objects.filter(username=username).exists():
            errors.append('El nombre de usuario ya existe.')
        
        if User.objects.filter(email=email).exists():
            errors.append('El email ya está registrado.')
        
        if Veterinarian.objects.filter(license_number=license_number).exists():
            errors.append('El número de matrícula ya está registrado.')
        
        if Veterinarian.objects.filter(phone=phone).exists():
            errors.append('El número de teléfono ya está registrado.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Create address if provided
                address = None
                if any([province, city, street, number, postal_code]):
                    address = Address.objects.create(
                        province=province or '',
                        city=city or '',
                        street=street or '',
                        number=number or '',
                        postal_code=postal_code or ''
                    )
                
                # Create Django User
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                
                # Create veterinarian profile
                veterinarian = Veterinarian.objects.create(
                    user=user,
                    phone=phone,
                    license_number=license_number,
                    address=address
                )
                
                messages.success(request, f'¡Registro exitoso! Dr. {first_name} {last_name}, tu cuenta ha sido creada y está pendiente de aprobación por un administrador. Te notificaremos cuando esté activada.')
                return redirect('veterinary_login')
                
            except Exception as e:
                messages.error(request, f'Error al crear el usuario: {str(e)}')
    
    return render(request, 'users/veterinary_register.html')

@login_required
@csrf_protect
def complete_profile(request):
    """Complete veterinarian profile for users who registered via social login"""
    user = request.user
    
    # Check if user already has a veterinarian profile
    try:
        veterinarian = Veterinarian.objects.get(user=user)
        if veterinarian.is_approved:
            return redirect('veterinary_dashboard')
        else:
            # Profile exists but not approved, show pending approval
            return render(request, 'users/pending_approval.html')
    except Veterinarian.DoesNotExist:
        pass  # User needs to complete profile
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        license_number = request.POST.get('license_number')
        
        # Address fields
        province = request.POST.get('province')
        city = request.POST.get('city')
        street = request.POST.get('street')
        number = request.POST.get('number')
        postal_code = request.POST.get('postal_code')
        
        # Validation
        errors = []
        
        if not all([phone, license_number]):
            errors.append('El teléfono y número de matrícula son obligatorios.')
        
        # Validate phone number
        if phone:
            phone_pattern = r'^[\d\s\-\+\(\)]+$'
            if not re.match(phone_pattern, phone):
                errors.append('El número de teléfono solo puede contener números, espacios, guiones, paréntesis y el signo +.')
        
        if Veterinarian.objects.filter(license_number=license_number).exists():
            errors.append('El número de matrícula ya está registrado.')
        
        if Veterinarian.objects.filter(phone=phone).exists():
            errors.append('El número de teléfono ya está registrado.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Create address if provided
                address = None
                if any([province, city, street, number, postal_code]):
                    address = Address.objects.create(
                        province=province or '',
                        city=city or '',
                        street=street or '',
                        number=number or '',
                        postal_code=postal_code or ''
                    )
                
                # Create veterinarian profile
                veterinarian = Veterinarian.objects.create(
                    user=user,
                    phone=phone,
                    license_number=license_number,
                    address=address
                )
                
                messages.success(request, f'¡Perfil completado! Dr. {user.first_name} {user.last_name}, tu cuenta está pendiente de aprobación por un administrador.')
                return render(request, 'users/pending_approval.html')
                
            except Exception as e:
                messages.error(request, f'Error al completar el perfil: {str(e)}')
    
    return render(request, 'users/complete_profile.html', {'user': user})

def veterinary_dashboard(request):
    """Placeholder dashboard view"""
    if not request.user.is_authenticated:
        return redirect('veterinary_login')
    
    try:
        veterinarian = Veterinarian.objects.get(user=request.user)
        if not veterinarian.is_approved:
            messages.error(request, 'Tu cuenta no ha sido aprobada aún. Contacta al administrador.')
            return redirect('veterinary_login')
        return render(request, 'users/dashboard.html', {'veterinarian': veterinarian})
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Acceso denegado.')
        return redirect('veterinary_login')
