#!/usr/bin/env python
"""
Simple test data creation script for AdLab Laboratory System.
This script creates basic test data for the most important models.
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Veterinarian, Address
from protocols.models import Protocol, WorkOrder

User = get_user_model()

def create_simple_test_data():
    """Create basic test data for the laboratory system."""
    
    print("🚀 Creating simple test data for AdLab Laboratory System...")
    
    # ==============================================
    # 1. CREATE USERS
    # ==============================================
    print("📝 Creating users...")
    
    # Lab staff users
    lab_tech1, created = User.objects.get_or_create(
        username='lab_tech1',
        defaults={
            'email': 'lab_tech1@adlab.local',
            'first_name': 'María',
            'last_name': 'González',
            'role': User.Role.PERSONAL_LAB,
            'is_active': True,
            'email_verified': True,
            'failed_login_attempts': 0,
        }
    )
    if created:
        lab_tech1.set_password('lab123')
        lab_tech1.save()
        print(f"  ✅ Created lab technician: {lab_tech1.email}")
    
    # Veterinarian users
    vet1, created = User.objects.get_or_create(
        username='vet1',
        defaults={
            'email': 'dr.garcia@veterinaria.com',
            'first_name': 'Dr. Roberto',
            'last_name': 'García',
            'role': User.Role.VETERINARIO,
            'is_active': True,
            'email_verified': True,
            'failed_login_attempts': 0,
        }
    )
    if created:
        vet1.set_password('vet123')
        vet1.save()
        print(f"  ✅ Created veterinarian: {vet1.email}")
    
    vet2, created = User.objects.get_or_create(
        username='vet2',
        defaults={
            'email': 'dra.lopez@clinica.com',
            'first_name': 'Dra. Patricia',
            'last_name': 'López',
            'role': User.Role.VETERINARIO,
            'is_active': True,
            'email_verified': True,
            'failed_login_attempts': 0,
        }
    )
    if created:
        vet2.set_password('vet123')
        vet2.save()
        print(f"  ✅ Created veterinarian: {vet2.email}")
    
    # ==============================================
    # 2. CREATE VETERINARIAN PROFILES
    # ==============================================
    print("👨‍⚕️ Creating veterinarian profiles...")
    
    admin_user = User.objects.get(username='admin')
    
    vet_profile1, created = Veterinarian.objects.get_or_create(
        user=vet1,
        defaults={
            'first_name': 'Dr. Roberto',
            'last_name': 'García',
            'license_number': 'MP-12345',
            'phone': '+54 11 1234-5678',
            'email': 'dr.garcia@veterinaria.com',
            'is_verified': True,
            'verified_by': admin_user,
            'verified_at': timezone.now(),
        }
    )
    if created:
        print(f"  ✅ Created veterinarian profile: {vet_profile1}")
    
    vet_profile2, created = Veterinarian.objects.get_or_create(
        user=vet2,
        defaults={
            'first_name': 'Dra. Patricia',
            'last_name': 'López',
            'license_number': 'MP-23456',
            'phone': '+54 11 2345-6789',
            'email': 'dra.lopez@clinica.com',
            'is_verified': True,
            'verified_by': admin_user,
            'verified_at': timezone.now(),
        }
    )
    if created:
        print(f"  ✅ Created veterinarian profile: {vet_profile2}")
    
    # ==============================================
    # 3. CREATE ADDRESSES
    # ==============================================
    print("🏠 Creating addresses...")
    
    address1, created = Address.objects.get_or_create(
        veterinarian=vet_profile1,
        defaults={
            'province': 'Buenos Aires',
            'locality': 'CABA',
            'street': 'Av. Corrientes',
            'number': '1234',
            'postal_code': '1043',
            'floor': '2',
            'apartment': 'A',
            'notes': 'Consultorio principal',
        }
    )
    if created:
        print(f"  ✅ Created address for {vet_profile1}")
    
    address2, created = Address.objects.get_or_create(
        veterinarian=vet_profile2,
        defaults={
            'province': 'Buenos Aires',
            'locality': 'La Plata',
            'street': 'Calle 7',
            'number': '567',
            'postal_code': '1900',
            'notes': 'Clínica veterinaria',
        }
    )
    if created:
        print(f"  ✅ Created address for {vet_profile2}")
    
    # ==============================================
    # 4. CREATE WORK ORDERS
    # ==============================================
    print("📋 Creating work orders...")
    
    work_order1, created = WorkOrder.objects.get_or_create(
        order_number='WO-2024-001'
    )
    if created:
        print(f"  ✅ Created work order: {work_order1.order_number}")
    
    work_order2, created = WorkOrder.objects.get_or_create(
        order_number='WO-2024-002'
    )
    if created:
        print(f"  ✅ Created work order: {work_order2.order_number}")
    
    # ==============================================
    # 5. CREATE PROTOCOLS
    # ==============================================
    print("📄 Creating protocols...")
    
    protocol1, created = Protocol.objects.get_or_create(
        protocol_number='CT 24/001',
        defaults={
            'temporary_code': 'TMP-CT-20241201-001',
            'analysis_type': Protocol.AnalysisType.CYTOLOGY,
            'veterinarian': vet_profile1,
            'work_order': work_order2,
            'species': 'Canino',
            'breed': 'Labrador',
            'sex': Protocol.Sex.MALE,
            'age': '3 años',
            'animal_identification': 'Max',
            'owner_last_name': 'García',
            'owner_first_name': 'Juan',
            'presumptive_diagnosis': 'Masa abdominal',
            'clinical_history': 'Paciente con masa palpable en abdomen, sin otros síntomas',
            'academic_interest': False,
            'submission_date': date(2024, 12, 1),
            'status': Protocol.Status.RECEIVED,
            'discrepancies': '',
            'reception_notes': '',
            'sample_condition': 'good',
        }
    )
    if created:
        print(f"  ✅ Created protocol: {protocol1.protocol_number}")
    
    protocol2, created = Protocol.objects.get_or_create(
        protocol_number='HP 24/001',
        defaults={
            'temporary_code': 'TMP-HP-20241201-002',
            'analysis_type': Protocol.AnalysisType.HISTOPATHOLOGY,
            'veterinarian': vet_profile2,
            'work_order': work_order1,
            'species': 'Felino',
            'breed': 'Persa',
            'sex': Protocol.Sex.FEMALE,
            'age': '5 años',
            'animal_identification': 'Luna',
            'owner_last_name': 'López',
            'owner_first_name': 'María',
            'presumptive_diagnosis': 'Tumor mamario',
            'clinical_history': 'Masa en glándula mamaria, cirugía de extirpación',
            'academic_interest': False,
            'submission_date': date(2024, 12, 1),
            'status': Protocol.Status.PROCESSING,
            'discrepancies': '',
            'reception_notes': '',
            'sample_condition': 'good',
        }
    )
    if created:
        print(f"  ✅ Created protocol: {protocol2.protocol_number}")
    
    protocol3, created = Protocol.objects.get_or_create(
        protocol_number='CT 24/002',
        defaults={
            'temporary_code': 'TMP-CT-20241202-003',
            'analysis_type': Protocol.AnalysisType.CYTOLOGY,
            'veterinarian': vet_profile1,
            'work_order': work_order2,
            'species': 'Canino',
            'breed': 'Mestizo',
            'sex': Protocol.Sex.MALE,
            'age': '7 años',
            'animal_identification': 'Rex',
            'owner_last_name': 'Torres',
            'owner_first_name': 'Carlos',
            'presumptive_diagnosis': 'Linfadenopatía',
            'clinical_history': 'Aumento de tamaño de ganglios linfáticos',
            'academic_interest': False,
            'submission_date': date(2024, 12, 2),
            'status': Protocol.Status.SUBMITTED,
            'discrepancies': '',
            'reception_notes': '',
            'sample_condition': 'good',
        }
    )
    if created:
        print(f"  ✅ Created protocol: {protocol3.protocol_number}")
    
    print("\n🎉 Simple test data creation completed successfully!")
    print("\n📊 Summary of created data:")
    print(f"  👥 Users: {User.objects.count()}")
    print(f"  👨‍⚕️ Veterinarians: {Veterinarian.objects.count()}")
    print(f"  🏠 Addresses: {Address.objects.count()}")
    print(f"  📋 Work Orders: {WorkOrder.objects.count()}")
    print(f"  📄 Protocols: {Protocol.objects.count()}")
    
    print("\n🔑 Test User Credentials:")
    print("  Admin: admin / admin123")
    print("  Lab Tech 1: lab_tech1@adlab.local / lab123")
    print("  Veterinarian 1: dr.garcia@veterinaria.com / vet123")
    print("  Veterinarian 2: dra.lopez@clinica.com / vet123")
    
    print("\n📋 Created Protocols:")
    for protocol in Protocol.objects.all():
        print(f"  - {protocol.protocol_number}: {protocol.analysis_type} - {protocol.species} ({protocol.status})")

if __name__ == '__main__':
    create_simple_test_data()
