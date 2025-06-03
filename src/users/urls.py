from django.urls import path
from . import views

urlpatterns = [
    path('veterinary/login/', views.veterinary_login, name='veterinary_login'),
    path('veterinary/register/', views.veterinary_register, name='veterinary_register'),
    path('veterinary/dashboard/', views.veterinary_dashboard, name='veterinary_dashboard'),
] 