# Manual Testing Guide: Steps 05-08

This guide provides comprehensive test scenarios for manually verifying that features described in steps 05-08 are working correctly.

## 📋 Table of Contents

- [Step 05: Sample Processing & Tracking](#step-05-sample-processing--tracking)
- [Step 06: Report Generation & PDF Creation](#step-06-report-generation--pdf-creation)
- [Step 07: Work Order Management](#step-07-work-order-management)
- [Step 08: Email Notifications](#step-08-email-notifications)
- [Testing Checklist](#testing-checklist)
- [Database Verification](#database-verification)

---

## Step 05: Sample Processing & Tracking

### 🎯 Core Features to Test

#### 1. Cassette Registration
- **Location**: After sample reception, lab staff can register cassettes
- **Test Path**: Dashboard → Select received protocol → "Register Cassettes"
- **Expected Actions**:
  - [ ] Form displays with material description field
  - [ ] Color selection dropdown available
  - [ ] Processing stages dropdown (encasetado → fijacion → inclusion → etc.)
  - [ ] Save creates cassette with unique ID
  - [ ] Timestamp recorded automatically

#### 2. Slide Creation & Management
- **Location**: Cassette detail view
- **Test Path**: Click on cassette → "Add Slides"
- **Expected Actions**:
  - [ ] Can register multiple slides per cassette
  - [ ] Junction table `CassetteSlide` links slides to cassettes
  - [ ] One slide can be linked to multiple cassettes (real-world workflow)
  - [ ] Slide ID generated automatically

#### 3. Processing Stage Updates
- **Location**: Cassette detail view or processing dashboard
- **Test Path**: Select cassette → "Update Processing Stage"
- **Expected Actions**:
  - [ ] Dropdown with stages: encasetado, fijacion, inclusion, corte, tinción
  - [ ] Each update creates `ProcessingLog` entry
  - [ ] Timestamp and user who made change recorded
  - [ ] Cannot skip stages (must follow sequence)

#### 4. Processing Log History
- **Location**: Cassette detail page
- **Test Path**: Scroll to "Processing History"
- **Expected Actions**:
  - [ ] Complete timeline of all stage changes
  - [ ] Shows who changed, when, and what stage
  - [ ] Notes can be added for each change

### 🧪 Test Scenarios

#### Test 5.1: Complete Processing Workflow
1. **Setup**: Receive a histopathology protocol (needs to be in RECEIVED status)
2. **Action**: Register 2 cassettes
   - Material: "Masas mamarias"
   - Colors: "Rojo" and "Azul"
3. **Action**: Create 3 slides
   - Slide 1: "H&E 1"
   - Slide 2: "H&E 2" 
   - Slide 3: "PAS"
4. **Action**: Link slides to cassettes
   - Slide 1 → Cassette 1
   - Slide 2 → Both cassettes
   - Slide 3 → Cassette 2
5. **Action**: Update processing stages sequentially
   - Cassette 1: encasetado → fijacion → inclusion
   - Cassette 2: encasetado → fijacion
6. **Verify**: All processing logs created with timestamps

#### Test 5.2: Processing Validation
1. **Action**: Try to skip a processing stage
   - Attempt: fijacion → inclusion (without encasetado)
2. **Expected**: System prevents invalid transition
3. **Action**: Test concurrent updates
   - Two users updating same cassette
4. **Expected**: Database locking prevents corruption

---

## Step 06: Report Generation & PDF Creation

### 🎯 Core Features to Test

#### 1. Report Creation
- **Location**: Dashboard → Protocols → "Create Report" (for ready protocols)
- **Test Path**: Select processed protocol → Click "Create Report"
- **Expected Actions**:
  - [ ] Report form opens with protocol pre-selected
  - [ ] Form sections visible: Macroscopic, Microscopic, Diagnosis, Comments, Recommendations
  - [ ] Lab staff author dropdown shows only those with `can_create_reports=True`
  - [ ] Save creates report with DRAFT status

#### 2. Cassette Observations
- **Location**: Report editing page
- **Test Path**: Scroll to "Cassette Observations"
- **Expected Actions**:
  - [ ] Each cassette has observation field
  - [ ] Can add detailed microscopic findings per cassette
  - [ ] Observations saved to `CassetteObservation` model
  - [ ] Rich text formatting supported

#### 3. Report Images
- **Location**: Report editing page
- **Test Path**: "Add Image" button
- **Expected Actions**:
  - [ ] Can upload microscopy images (JPG/PNG)
  - [ ] Images stored in `ReportImage` model
  - [ ] Images appear in generated PDF
  - [ ] Multiple images per report supported
  - [ ] Image captions can be added

#### 4. Digital Signature Integration
- **Location**: Report editing page
- **Test Path**: Finalize report with signature
- **Expected Actions**:
  - [ ] If lab staff has signature image, it's included
  - [ ] Signature appears in generated PDF
  - [ ] Digital hash stored for integrity
  - [ ] Cannot finalize without signature if required

#### 5. PDF Generation
- **Location**: Report detail page
- **Test Path**: "Generate PDF" button
- **Expected Actions**:
  - [ ] PDF opens in browser/new tab
  - [ ] Includes all report sections
  - [ ] Professional formatting with lab header
  - [ ] QR code linking back to system
  - [ ] SHA-256 hash stored in database

### 🧪 Test Scenarios

#### Test 6.1: Complete Report Workflow
1. **Setup**: Select a fully processed protocol (all cassettes at final stage)
2. **Action**: Create report with all sections filled
   - Macroscopic: "Se recibe tejido mamario..."
   - Microscopic: "Se observa proliferación..."
   - Diagnosis: "Carcinoma mamario simple"
   - Recommendations: "Margen quirúrgico amplio..."
3. **Action**: Add observations for each cassette
   - Cassette 1: "Tejido bien fijado..."
   - Cassette 2: "Preservación celular adecuada..."
4. **Action**: Upload microscopy images
   - Image 1: H&E 40x
   - Image 2: H&E 100x
5. **Action**: Generate and download PDF
6. **Verify**: PDF content and format are correct

#### Test 6.2: Report Status Management
1. **Action**: Create report (verify status: DRAFT)
2. **Action**: Save as draft (verify still DRAFT)
3. **Action**: Finalize report (verify status: FINALIZED)
4. **Action**: Send report to veterinarian (verify status: SENT)
5. **Verify**: Status history logged with timestamps

#### Test 6.3: Permission Testing
1. **Action**: Login as lab staff without `can_create_reports`
2. **Action**: Try to access report creation
3. **Expected**: 404 or access denied
4. **Action**: Login as staff with permission
5. **Expected**: Access granted

---

## Step 07: Work Order Management

### 🎯 Core Features to Test

#### 1. Work Order Creation
- **Location**: Dashboard → "Work Orders" → "Create Work Order"
- **Test Path**: Select protocols → "Generate Work Order"
- **Expected Actions**:
  - [ ] Can select multiple protocols (related to same case)
  - [ ] Work order number generated: WO-YYYY-### (e.g., WO-2024-001)
  - [ ] Pricing automatically calculated from `PricingCatalog`
  - [ ] Date range selector for pricing periods

#### 2. Pricing Catalog Integration
- **Location**: Admin → Protocols → Pricing Catalog
- **Test Path**: View pricing rules
- **Expected Actions**:
  - [ ] Different prices for cytology vs histopathology
  - [ ] Date-based pricing (can have different prices over time)
  - [ ] Work order uses current active pricing
  - [ ] Can set special pricing per veterinarian

#### 3. Payment Tracking
- **Location**: Work Order detail view
- **Test Path**: Edit work order
- **Expected Actions**:
  - [ ] Fields visible: advance_payment, balance_due, payment_status
  - [ ] Can mark as paid/partial/unpaid
  - [ ] Payment history tracked
  - [ ] Automatic calculation of balance

#### 4. PDF Invoice Generation
- **Location**: Work Order detail page
- **Test Path**: "Generate Invoice PDF"
- **Expected Actions**:
  - [ ] Professional invoice with lab header
  - [ ] Lists all protocols with descriptions
  - [ ] Shows pricing breakdown
  - [ ] Payment status clearly displayed
  - [ ] QR code for tracking

### 🧪 Test Scenarios

#### Test 7.1: Single Protocol Work Order
1. **Setup**: Create and receive a protocol
2. **Action**: Generate work order for that protocol only
3. **Verify**: Pricing is correct
4. **Action**: Mark partial payment (50%)
5. **Action**: Generate invoice PDF
6. **Expected**: Invoice shows partial payment status

#### Test 7.2: Multiple Protocol Work Order
1. **Setup**: Create multiple protocols for same animal
   - Protocol 1: Citología, masa mamaria
   - Protocol 2: Histopatología, ganglio
2. **Action**: Generate single work order with all protocols
3. **Verify**: All protocols included
4. **Verify**: Combined pricing calculated
5. **Action**: Generate combined invoice

#### Test 7.3: Pricing Catalog Testing
1. **Setup**: Create different pricing rules
   - Cytology: $1500 (valid until 2024-12-31)
   - Cytology: $1700 (valid from 2025-01-01)
   - Histopathology: $3000 (current)
2. **Action**: Generate work orders on different dates
3. **Verify**: Correct pricing applied based on date

---

## Step 08: Email Notifications

### 🎯 Core Features to Test

#### 1. Reception Confirmation Email
- **Trigger**: When lab staff receives a sample
- **Test Path**: Receive any protocol
- **Expected Actions**:
  - [ ] Email sent to veterinarian
  - [ ] Contains protocol number (e.g., HP 24/001)
  - [ ] Includes temporary code for reference
  - [ ] Shows sample condition and any discrepancies
  - [ ] Link to veterinarian portal to track status

#### 2. Report Ready Email
- **Trigger**: When report is finalized and sent
- **Test Path**: Finalize and send a report
- **Expected Actions**:
  - [ ] Email sent to veterinarian
  - [ ] Subject: "Report Ready - Protocol [NUMBER]"
  - [ ] Link to download PDF
  - [ ] Summary of findings
  - [ ] Professional HTML template

#### 3. Notification Preferences
- **Location**: Veterinarian profile settings
- **Test Path**: Edit veterinarian profile → Notification Preferences
- **Expected Actions**:
  - [ ] Can toggle: notify_on_reception, notify_on_report_ready
  - [ ] Can use alternative email
  - [ ] Can choose to include attachments
  - [ ] Preferences respected in email sending

#### 4. Email Queue and Retry Logic
- **Location**: Django admin → Email Log
- **Test Path**: Check after sending emails
- **Expected Actions**:
  - [ ] All emails logged in `EmailLog`
  - [ ] Status: QUEUED → SENT/FAILED
  - [ ] Failed emails retried (up to 3 times)
  - [ ] Exponential backoff: 1min → 2min → 4min
  - [ ] Celery task ID tracked

#### 5. Email Templates
- **Location**: templates/emails/ directory
- **Test Path**: Trigger various email types
- **Expected Actions**:
  - [ ] Professional HTML templates
  - [ ] Spanish language
  - [ ] Lab branding
  - [ ] Responsive design

### 🧪 Test Scenarios

#### Test 8.1: Full Email Flow
1. **Setup**: Create test veterinarian with email preferences
2. **Action**: Submit protocol as veterinarian
3. **Action**: Receive protocol as lab staff
4. **Verify**: Reception email sent
5. **Action**: Create and finalize report
6. **Action**: Send report
7. **Verify**: Report ready email sent
8. **Check**: Email logs for all steps

#### Test 8.2: Preference Testing
1. **Setup**: Create veterinarian with all notifications OFF
2. **Action**: Submit and receive protocol
3. **Verify**: NO email sent
4. **Action**: Update preferences to enable reception only
5. **Action**: Receive another protocol
6. **Verify**: Only reception email sent

#### Test 8.3: Email Error Handling
1. **Setup**: Configure invalid SMTP or use console backend
2. **Action**: Trigger email sending
3. **Check**: Email logs for failed status
4. **Verify**: Retry attempts
5. **Check**: Error messages logged

---

## Step 16 Check: Laboratory Staff Role Consolidation

### ✅ Feature: Lab Staff Role Merge
- **Location**: User management and dashboard views
- **Background**: Step 16 merged PERSONAL_LAB and HISTOPATOLOGO roles into unified PERSONAL_LAB with granular permissions

#### 🎯 Core Features to Test

##### 1. Unified Role System
- **Location**: Django Admin → Users
- **Test Path**: Check user role options
- **Expected**:
  - [ ] Only 3 roles available: VETERINARIO, PERSONAL_LAB, ADMIN
  - [ ] HISTOPATOLOGO role removed from options
  - [ ] Existing histopathologists now show as PERSONAL_LAB
  - [ ] Lab staff profile links to `LaboratoryStaff` model

##### 2. LaboratoryStaff Model Integration
- **Location**: Admin → Laboratory Staff
- **Test Path**: View lab staff profiles
- **Expected**:
  - [ ] All fields from old Histopathologist present
  - [ ] `can_create_reports` boolean field exists
  - [ ] Signature image field functional
  - [ ] License number uniqueness enforced

##### 3. Permission System
- **Location**: Dashboard and report creation
- **Test Path**: Login as different lab staff users
- **Expected**:
  - [ ] Lab staff without `can_create_reports` cannot access report creation
  - [ ] Lab staff with `can_create_reports=True` can create reports
  - [ ] 404 error when unauthorized user tries report URL
  - [ ] Dashboard shows/hides features based on permissions

##### 4. Dashboard Consolidation
- **Location**: `/dashboard/`
- **Test Path**: Access dashboard as lab staff
- **Expected**:
  - [ ] Single unified dashboard for all lab staff
  - [ ] No separate histopathologist dashboard
  - [ ] Report creation button only shows if `can_create_reports=True`
  - [ ] Processing features always visible for all lab staff

##### 5. Report Author Assignment
- **Location**: Report creation/editing
- **Test Path**: Create and save reports
- **Expected**:
  - [ ] Report author field links to `LaboratoryStaff`
  - [ ] Dropdown shows only active lab staff with `can_create_reports=True`
  - [ ] Existing reports show correct lab staff author
  - [ ] Historical reports migrated correctly

#### 🧪 Test Scenarios

##### Test 16.1: Role Migration Verification
1. **Check**: Old histopathologist users
   - Verify they now have role PERSONAL_LAB
   - Verify LaboratoryStaff profile exists
   - Verify all professional data preserved

##### Test 16.2: Permission Testing
1. **Setup**: Two lab staff users
   - User A: `can_create_reports=True`
   - User B: `can_create_reports=False`
2. **Action**: Both try to create report
3. **Expected**: User A succeeds, User B gets 404

##### Test 16.3: Dashboard Access
1. **Action**: Login as lab staff (without report permission)
2. **Verify**: Dashboard loads, shows processing features
3. **Action**: Check for report creation buttons
4. **Expected**: No report creation options visible

##### Test 16.4: Admin Permission Management
1. **Location**: Admin → Laboratory Staff
2. **Action**: Edit lab staff permissions
3. **Expected**:
   - Can toggle `can_create_reports`
   - Can bulk enable/disable permissions
   - Audit log entry created for changes

---

## Testing Checklist

### General Setup
- [ ] System running: `docker compose up`
- [ ] Test data loaded: `python manage.py loaddata test_data.json`
- [ ] Email viewing: Check `docker compose logs worker` or use MailHog

### Pre-Step 05: Verify Role Consolidation (Step 16)
- [ ] HISTOPATOLOGO role removed from system
- [ ] All histopathologists migrated to LaboratoryStaff model
- [ ] `can_create_reports` permission field functional
- [ ] Dashboard unified for all lab staff
- [ ] Report creation properly restricted by permissions

### Test Users Needed
Create these users for testing:
- Veterinarian: `vet@example.com` (password: `TestPass123!`)
- Lab Staff: `lab@example.com` (password: `TestPass123!`) with report permissions
- Lab Staff: `tech@example.com` (password: `TestPass123!`) without report permissions
- Admin: `admin@example.com` (password: `TestPass123!`)

### Pre-Test Requirements
- [ ] At least 2 protocols in RECEIVED status
- [ ] At least 1 veterinarian with complete profile
- [ ] Lab staff user with signature image uploaded
- [ ] Pricing catalog entries configured

---

## Database Verification

### Expected Database Tables
After testing, verify these tables have data:

#### Step 05 Tables
```sql
-- Check processing data
SELECT COUNT(*) FROM protocols_cassette;
SELECT COUNT(*) FROM protocols_slide;
SELECT COUNT(*) FROM protocols_cassetteslide;
SELECT COUNT(*) FROM protocols_processingslog;
```

#### Step 06 Tables
```sql
-- Check report data
SELECT COUNT(*) FROM protocols_report;
SELECT COUNT(*) FROM protocols_cassetteobservation;
SELECT COUNT(*) FROM protocols_reportimage;
```

#### Step 07 Tables
```sql
-- Check work order data
SELECT COUNT(*) FROM protocols_workorder;
SELECT COUNT(*) FROM protocols_pricingcatalog;
SELECT COUNT(*) FROM protocols_workorderpricing;
```

#### Step 08 Tables
```sql
-- Check email data
SELECT COUNT(*) FROM protocols_emaillog;
SELECT COUNT(*) FROM protocols_notificationpreference;
```

### Quick Health Checks
```sql
-- Check protocols status distribution
SELECT status, COUNT(*) FROM protocols_protocol GROUP BY status;

-- Check work orders by month
SELECT DATE_TRUNC('month', created_at), COUNT(*) 
FROM protocols_workorder 
GROUP BY DATE_TRUNC('month', created_at);

-- Check email delivery rates
SELECT email_type, status, COUNT(*) 
FROM protocols_emaillog 
GROUP BY email_type, status;
```

---

## Test Data Creation Script

Use this script to create test data quickly:

```bash
# Create test users and data
docker compose exec web python manage.py shell <<EOF
from django.contrib.auth import get_user_model
from accounts.models import Veterinarian, LaboratoryStaff, Address
from protocols.models import Protocol, CytologySample, HistopathologySample
from django.utils import timezone

User = get_user_model()

# Create test users
vet = User.objects.create_user(
    email='vet@example.com',
    password='TestPass123!',
    role=User.Role.VETERINARIO
)

lab_staff = User.objects.create_user(
    email='lab@example.com',
    password='TestPass123!',
    role=User.Role.PERSONAL_LAB
)

# Create veterinarian profile
address = Address.objects.create(
    province='Santa Fe',
    locality='Santa Fe',
    street='San Martín',
    number='1234'
)

vet_profile = Veterinarian.objects.create(
    user=vet,
    first_name='Juan',
    last_name='Pérez',
    license_number='MP-12345',
    phone='+54 342 1234567',
    address=address,
    is_verified=True
)

# Create lab staff profile
lab_profile = LaboratoryStaff.objects.create(
    user=lab_staff,
    first_name='Ana',
    last_name='García',
    license_number='MP-67890',
    position='Histopatólogo',
    can_create_reports=True
)

# Create test protocol
protocol = Protocol.objects.create(
    veterinarian=vet_profile,
    protocol_type=Protocol.ProtocolType.HISTOPATHOLOGY,
    temporary_code='TMP-HP-20241201-001',
    status=Protocol.Status.RECEIVED,
    protocol_number='HP 24/001',
    species='Canino',
    animal_id='Max',
    presumptive_diagnosis='Masa mamaria',
    submission_date=timezone.now().date(),
    reception_date=timezone.now()
)

# Create sample
sample = HistopathologySample.objects.create(
    protocol=protocol,
    material_submitted='Masas mamarias 3x2x1cm',
    number_containers=1,
    preservation='Formol 10%'
)

print("Test data created successfully!")
EOF
```

---

## Common Issues and Solutions

### Issue: Cannot Create Cassettes
**Solution**: Ensure protocol is in RECEIVED status

### Issue: PDF Generation Fails
**Solution**: Check that report author has signature image

### Issue: Emails Not Sending
**Solution**: Check Celery worker status: `docker compose logs worker`

### Issue: Work Order Price Wrong
**Solution**: Verify PricingCatalog has active entries for current date

### Issue: Permission Denied for Reports
**Solution**: Ensure lab staff has `can_create_reports=True`

---

## Reporting Results

After testing, please document:
1. ✅ Working features
2. ❌ Broken features with error messages
3. ⚠️ Features with partial functionality
4. 📝 Notes or observations

Upload screenshots of any issues to help with debugging.