from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.veterinary_login, name='veterinary_login'),
    path('veterinary/login/', views.veterinary_login, name='veterinary_login'),
    path('register/', views.veterinary_register, name='veterinary_register'),
    path('veterinary/register/', views.veterinary_register, name='veterinary_register'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('dashboard/', views.veterinary_dashboard, name='veterinary_dashboard'),
    path('veterinary/dashboard/', views.veterinary_dashboard, name='veterinary_dashboard'),
] 