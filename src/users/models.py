from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Address(models.Model):
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    number = models.CharField(max_length=10)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.street} {self.number}, {self.city}, {self.province}"

class Veterinarian(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='veterinarian_profile')
    phone = models.CharField(max_length=20, unique=True)
    license_number = models.CharField(max_length=50, unique=True)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, related_name='veterinarian', null=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text='Designates whether this veterinarian has been approved by an admin.')

    def __str__(self):
        status = "✓" if self.is_approved else "⏳"
        return f"{status} {self.user.first_name} {self.user.last_name} (Veterinarian)"
    
    @property
    def first_name(self):
        return self.user.first_name
    
    @property
    def last_name(self):
        return self.user.last_name
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def username(self):
        return self.user.username

class Histopathologist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='histopathologist_profile')
    license_number = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=100)
    signature = models.FileField(upload_to='signatures/', blank=True)
    can_issue_reports = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} (Histopathologist)"
    
    @property
    def first_name(self):
        return self.user.first_name
    
    @property
    def last_name(self):
        return self.user.last_name
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def username(self):
        return self.user.username
