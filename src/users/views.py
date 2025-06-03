from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
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
                
                messages.success(request, f'¡Registro exitoso! Bienvenido Dr. {first_name} {last_name}. Ya puedes iniciar sesión.')
                return redirect('veterinary_login')
                
            except Exception as e:
                messages.error(request, f'Error al crear el usuario: {str(e)}')
    
    return render(request, 'users/veterinary_register.html')

def veterinary_dashboard(request):
    """Placeholder dashboard view"""
    if not request.user.is_authenticated:
        return redirect('veterinary_login')
    
    try:
        veterinarian = Veterinarian.objects.get(user=request.user)
        return render(request, 'users/dashboard.html', {'veterinarian': veterinarian})
    except Veterinarian.DoesNotExist:
        messages.error(request, 'Acceso denegado.')
        return redirect('veterinary_login')
