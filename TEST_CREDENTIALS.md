# Test Credentials - AdLab Laboratory System

**Date**: October 12, 2025  
**Password Reset**: Completed ✅  
**Common Password**: `Password123!`

---

## 🔐 User Credentials by Role

### 1. VETERINARIO (Veterinary Clients)

| Email                        | Username                     | Name               | Status | Email Verified | Password      |
|------------------------------|------------------------------|--------------------|--------|----------------|---------------|
| fmoreyra@gmail.com           | fmoreyra@gmail.com           | Facundo Moreyra    | Active | ✅ Yes         | Password123!  |
| dr.torres@hospital.com       | vet3                         | Dr. Miguel Torres  | Active | ✅ Yes         | Password123!  |
| dra.lopez@clinica.com        | vet2                         | Dra. Patricia López| Active | ✅ Yes         | Password123!  |
| dr.garcia@veterinaria.com    | vet1                         | Dr. Roberto García | Active | ✅ Yes         | Password123!  |
| admin@adlab.local            | admin                        | -                  | Active | ❌ No          | Password123!  |

**Dashboard**: `/dashboard/veterinarian/`

**Features Available**:
- Submit new protocols (cytology/histopathology)
- View protocol list and status
- Download reports
- Manage profile
- View work orders

---

### 2. PERSONAL_LAB (Laboratory Staff)

| Email                  | Username    | Name              | Status | Email Verified | Password      |
|------------------------|-------------|-------------------|--------|----------------|---------------|
| lab_tech1@adlab.local  | lab_tech1   | María González    | Active | ✅ Yes         | Password123!  |
| lab_tech2@adlab.local  | lab_tech2   | Carlos Rodríguez  | Active | ✅ Yes         | Password123!  |

**Dashboard**: `/dashboard/lab-staff/`

**Features Available**:
- Sample reception and confirmation
- Processing management
- Register cassettes and slides
- Create work orders
- Generate labels
- Search protocols

---

### 3. HISTOPATOLOGO (Histopathologists)

| Email                   | Username     | Name             | Status | Email Verified | Password      |
|-------------------------|--------------|------------------|--------|----------------|---------------|
| histopath1@adlab.local  | histopath1   | Dr. Ana Martínez | Active | ✅ Yes         | Password123!  |

**Dashboard**: `/dashboard/histopathologist/`

**Features Available**:
- View pending reports
- Create and edit reports
- Generate PDF reports
- Sign reports digitally
- View report history
- Access productivity statistics

---

### 4. ADMIN (Administrators)

| Email | Username | Name | Status | Email Verified | Password |
|-------|----------|------|--------|----------------|----------|
| -     | -        | -    | -      | -              | -        |

**Note**: No dedicated admin role users found. Users with superuser status can access admin features.

**Dashboard**: `/dashboard/admin/`

**Features Available**:
- Access Django admin panel
- Manage all users
- View system analytics
- Monitor system health
- Configure system settings
- Access security logs

---

## 🌐 Access URLs

**Application URL**: http://localhost:8000

### Dashboard URLs
- **Main Dashboard**: http://localhost:8000/dashboard/ (auto-redirects by role)
- **Veterinarian**: http://localhost:8000/dashboard/veterinarian/
- **Lab Staff**: http://localhost:8000/dashboard/lab-staff/
- **Histopathologist**: http://localhost:8000/dashboard/histopathologist/
- **Admin**: http://localhost:8000/dashboard/admin/

### Other Important URLs
- **Login**: http://localhost:8000/accounts/login/
- **Register**: http://localhost:8000/accounts/register/
- **Django Admin**: http://localhost:8000/admin/
- **Landing Page**: http://localhost:8000/

---

## 🧪 Testing the Dashboards

### Test Each Role:

1. **Veterinarian Dashboard Test**:
   ```
   Email: fmoreyra@gmail.com
   Password: Password123!
   
   Expected: Purple-themed dashboard with protocols and reports
   ```

2. **Lab Staff Dashboard Test**:
   ```
   Email: lab_tech1@adlab.local
   Password: Password123!
   
   Expected: Blue-themed dashboard with processing queue
   ```

3. **Histopathologist Dashboard Test**:
   ```
   Email: histopath1@adlab.local
   Password: Password123!
   
   Expected: Indigo-themed dashboard with pending reports
   ```

4. **Admin Dashboard Test**:
   ```
   Note: Use a superuser account for admin dashboard
   
   Expected: Gray-themed dashboard with system health
   ```

---

## 📊 User Statistics

- **Total Users**: 8
- **Veterinarians**: 5 (including 1 without email verification)
- **Lab Staff**: 2
- **Histopathologists**: 1
- **Admins**: 0 (dedicated role)

---

## 🔒 Security Notes

1. **Password Reset**: All passwords have been reset to `Password123!`
2. **Change Passwords**: Users should change passwords after first login (in production)
3. **Email Verification**: Most users have verified emails except `admin@adlab.local`
4. **Active Status**: All users are currently active

---

## 🚀 Quick Start Guide

### To test a dashboard:

1. Open browser to http://localhost:8000
2. Click "Ingresar" (Login)
3. Use any credentials from the tables above
4. You'll be automatically redirected to your role-specific dashboard
5. Explore the features and statistics

### To switch between roles:

1. Logout from current session
2. Login with credentials from a different role
3. Dashboard will automatically adjust to the new role

---

## 📝 Notes

- **Common Password**: All users share `Password123!` for testing purposes
- **Email Format**: Internal users use `@adlab.local` domain
- **Role-Based Routing**: The system automatically routes users to the correct dashboard
- **Permission Checking**: Each dashboard checks user permissions before displaying content

---

## ✅ Dashboard Features Implemented

### All Dashboards Include:
- ✅ Welcome section with role-specific greeting
- ✅ Quick action cards for common tasks
- ✅ Real-time statistics widgets
- ✅ Recent activity/queue displays
- ✅ Feature discovery grids
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Professional gradients and icons
- ✅ Role-based access control

---

**Last Updated**: October 12, 2025  
**System**: AdLab Laboratory Management System  
**Step**: 15 - User Dashboards & Feature Discovery  
**Status**: ✅ Complete and Ready for Testing

