# Step 01.1: Email Verification for External Users

## Problem Statement

After implementing the base authentication system (Step 01), we identified a critical requirement: veterinarians are external users who will receive important notifications about sample results, reports, and work orders. We need to ensure that:

1. **Email addresses are valid and accessible** - Veterinarians must have access to the email they register with
2. **Notifications reach their destination** - No typos or fake emails that would cause notification failures
3. **Professional standards** - Medical/laboratory systems require verified communications
4. **Legal compliance** - Demonstrate consent for receiving lab communications

**Solution**: Implement email verification with activation links for external users (veterinarians), while internal users (lab staff, histopathologists, admins) can be activated by administrators directly.

---

## Requirements

### Functional Requirements (RF01.1)

- **RF01.1.1**: Veterinarians must verify their email before being able to login
- **RF01.1.2**: System sends verification email immediately after registration
- **RF01.1.3**: Verification links expire after 24 hours
- **RF01.1.4**: Users can request a new verification link if the original expires
- **RF01.1.5**: Internal users (lab staff, admins) bypass email verification
- **RF01.1.6**: System tracks verification status and timestamp
- **RF01.1.7**: Unverified users see clear instructions when attempting to login
- **RF01.1.8**: Verification emails use professional HTML templates

### Non-Functional Requirements

- **Security**: Verification tokens must be cryptographically secure (32-byte urlsafe)
- **Expiration**: Tokens expire after 24 hours to prevent stale links
- **Single Use**: Tokens can only be used once
- **User Experience**: Clear error messages and instructions in Spanish
- **Email Deliverability**: Professional email formatting to avoid spam filters
- **Audit**: All verification events logged
- **Performance**: Verification check must not impact login performance

---

## User Roles & Verification Requirements

| Role | Email Verification Required? | Why |
|------|------------------------------|-----|
| **Veterinario** | ✅ YES | External user, receives critical notifications |
| **Personal de Laboratorio** | ❌ NO | Internal user, activated by admin |
| **Histopatólogo** | ❌ NO | Internal user, activated by admin |
| **Administrador** | ❌ NO | Internal user, created by system admin |

---

## Data Model Updates

### User Model (accounts.User)

**New Fields**:
```python
email_verified: BOOLEAN DEFAULT FALSE
email_verification_token: VARCHAR(255) UNIQUE NULLABLE (indexed)
email_verification_sent_at: TIMESTAMP NULLABLE
```

**New Methods**:
```python
can_login() -> bool                          # Check if user can login based on verification
generate_email_verification_token() -> str   # Generate and save verification token
is_verification_token_expired() -> bool      # Check if token is older than 24 hours
```

### Database Schema

```sql
ALTER TABLE accounts_user ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE accounts_user ADD COLUMN email_verification_token VARCHAR(255) UNIQUE;
ALTER TABLE accounts_user ADD COLUMN email_verification_sent_at TIMESTAMP;

CREATE INDEX idx_verification_token ON accounts_user(email_verification_token);
```

---

## User Flows

### Flow 1: New Veterinarian Registration (Happy Path)

```
1. User visits /accounts/register/
2. User fills registration form:
   - Email: vet@clinic.com
   - Name: Dr. Juan Pérez
   - Password: ********
3. User submits form
4. System:
   ✓ Creates user account (is_active=True, email_verified=False)
   ✓ Generates verification token (32-byte urlsafe)
   ✓ Sends verification email
   ✓ Logs audit event
5. User sees: "Registro exitoso. Por favor verifique su email..."
6. User checks email and clicks verification link
7. System:
   ✓ Validates token
   ✓ Marks email as verified
   ✓ Invalidates token
   ✓ Logs audit event
8. User sees: "¡Email verificado! Ya puede iniciar sesión."
9. User can now login successfully
```

### Flow 2: Unverified User Attempts Login

```
1. User visits /accounts/login/
2. User enters credentials (correct email/password)
3. System authenticates user (password is correct)
4. System checks: user.can_login()
   → Returns False (email not verified)
5. User sees: "Por favor verifique su email antes de iniciar sesión..."
6. User can click "Reenviar email de verificación"
```

### Flow 3: Expired Verification Link

```
1. User clicks verification link (after 24+ hours)
2. System checks token age
3. System detects token is expired
4. User sees: "Este enlace ha expirado. Solicite un nuevo enlace."
5. User is redirected to /accounts/resend-verification/
6. User enters email
7. System generates new token and sends new email
```

### Flow 4: Internal User Creation (Lab Staff)

```
1. Admin creates lab staff user via Django admin
2. System:
   ✓ Creates user (is_active=True, email_verified=False)
   ✓ Sets role to "personal_lab" or "histopatologo"
   ✓ Sets initial password
3. Staff member can login immediately (bypasses verification)
4. No verification email sent
```

---

## API / View Design

### New Views

#### `POST /accounts/verify-email/<token>/`
Verify user email using token.

**Parameters**:
- `token`: Verification token (URL parameter)

**Success Response**:
- Redirects to login page
- Message: "¡Email verificado exitosamente! Ya puede iniciar sesión."
- Sets `email_verified = True`
- Invalidates token

**Error Responses**:
- Invalid/expired token: "Enlace de verificación inválido o expirado"
- Already verified: "Este email ya está verificado"

#### `GET/POST /accounts/resend-verification/`
Request new verification email.

**Request** (POST):
```json
{
  "email": "vet@example.com"
}
```

**Response**:
- Always returns success (security - don't reveal if email exists)
- Message: "Si el email existe y no está verificado, recibirá un enlace"
- Sends new verification email if conditions met

---

## Email Templates

### Verification Email

**Subject**: `Verifique su email - AdLab`

**Content**:
```html
Hola [Nombre],

Gracias por registrarse en el Sistema de Laboratorio de Anatomía Patológica.

Para activar su cuenta, por favor verifique su dirección de email:

[Verificar Email Button/Link]

Este enlace expirará en 24 horas.

Si no se registró en AdLab, puede ignorar este email.
```

**Template Location**: `accounts/templates/accounts/emails/email_verification.html`

---

## Business Logic

### 1. Verification Token Generation

```python
def generate_email_verification_token(self):
    """
    Generate cryptographically secure verification token.
    
    - Uses secrets.token_urlsafe(32) for security
    - Stores token and timestamp
    - Returns token for use in email
    """
    import secrets
    from django.utils import timezone
    
    self.email_verification_token = secrets.token_urlsafe(32)
    self.email_verification_sent_at = timezone.now()
    self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
    return self.email_verification_token
```

### 2. Login Eligibility Check

```python
def can_login(self):
    """
    Determine if user can login based on role and verification status.
    
    Rules:
    - Internal users (lab staff, admin): Only need is_active=True
    - External users (veterinarians): Need is_active=True AND email_verified=True
    """
    # Internal users don't need verification
    if self.role in [self.Role.PERSONAL_LAB, self.Role.HISTOPATOLOGO, self.Role.ADMIN]:
        return self.is_active
    
    # External users need verification
    if self.role == self.Role.VETERINARIO:
        return self.is_active and self.email_verified
    
    return self.is_active
```

### 3. Token Expiration Check

```python
def is_verification_token_expired(self):
    """Check if verification token is older than 24 hours."""
    if not self.email_verification_sent_at:
        return True
    
    from django.utils import timezone
    from datetime import timedelta
    
    token_age = timezone.now() - self.email_verification_sent_at
    return token_age > timedelta(hours=24)
```

### 4. Verification Process

```python
def verify_email(self):
    """Mark email as verified and invalidate token."""
    self.email_verified = True
    self.email_verification_token = None
    self.save(update_fields=['email_verified', 'email_verification_token'])
```

---

## Updated Views

### Registration View Changes

```python
def register_view(request):
    # ... existing code ...
    
    if form.is_valid():
        user = form.save()
        
        # NEW: Generate and send verification email
        token = user.generate_email_verification_token()
        send_verification_email(user, token, request)
        
        # NEW: Different success message
        messages.success(
            request,
            _("Registro exitoso. Por favor verifique su email para activar su cuenta. "
              "Revise su carpeta de spam si no lo encuentra."),
        )
        return redirect("accounts:login")
```

### Login View Changes

```python
def login_view(request):
    # ... existing authentication code ...
    
    if authenticated_user is not None:
        # NEW: Check if user can login (verification check)
        if not authenticated_user.can_login():
            messages.error(
                request,
                _("Por favor verifique su email antes de iniciar sesión. "
                  "Revise su bandeja de entrada y carpeta de spam. "
                  "¿No recibió el email? <a href='/accounts/resend-verification/'>Reenviar</a>"),
            )
            return render(request, "accounts/login.html", {"form": form})
        
        # ... rest of login logic ...
```

---

## URLs

```python
# accounts/urls.py

urlpatterns = [
    # ... existing URLs ...
    path("verify-email/<str:token>/", views.verify_email_view, name="verify_email"),
    path("resend-verification/", views.resend_verification_view, name="resend_verification"),
]
```

---

## Acceptance Criteria

- [ ] ✅ Veterinarians receive verification email immediately after registration
- [ ] ✅ Verification email contains working link with unique token
- [ ] ✅ Unverified veterinarians cannot login (clear error message)
- [ ] ✅ Verified veterinarians can login successfully
- [ ] ✅ Internal users (lab staff, admin) can login without verification
- [ ] ✅ Verification tokens expire after 24 hours
- [ ] ✅ Users can request new verification email
- [ ] ✅ Tokens can only be used once
- [ ] ✅ All verification events logged in AuthAuditLog
- [ ] ✅ Email template is professional and mobile-responsive
- [ ] ✅ Spanish language throughout
- [ ] ✅ Clear instructions when verification needed
- [ ] ✅ Django admin shows verification status

---

## Testing Approach

### Unit Tests (accounts/tests.py)

```python
class EmailVerificationTest(TestCase):
    def test_veterinarian_cannot_login_without_verification(self):
        """Unverified veterinarian cannot login."""
        
    def test_lab_staff_can_login_without_verification(self):
        """Internal users bypass verification."""
        
    def test_verification_token_generation(self):
        """Token is unique and secure."""
        
    def test_verification_token_expiration(self):
        """Tokens expire after 24 hours."""
        
    def test_successful_email_verification(self):
        """User can verify email with valid token."""
        
    def test_verification_token_single_use(self):
        """Token cannot be reused."""
        
    def test_resend_verification_email(self):
        """User can request new verification email."""
        
    def test_can_login_method(self):
        """can_login() respects role and verification."""
```

### Integration Tests

```python
def test_registration_to_login_flow(self):
    """Complete flow: register → verify → login."""
    
def test_expired_token_resend_flow(self):
    """Flow: expired token → resend → verify → login."""
```

### Manual Testing Checklist

- [ ] Register new veterinarian
- [ ] Check inbox for verification email
- [ ] Click verification link
- [ ] Verify email is marked as verified in admin
- [ ] Login successfully
- [ ] Try to reuse same verification link (should fail)
- [ ] Register and try to login without verification (should fail)
- [ ] Test resend verification functionality
- [ ] Create lab staff user and verify they can login immediately
- [ ] Check email spam folder handling
- [ ] Test mobile email rendering

---

## Migration Strategy

### Option A: Soft Launch (Recommended)

1. **Deploy changes** without enforcing verification
2. **Existing users**: Automatically mark as verified
3. **New users**: Must verify email
4. **Communication**: Email existing users about new security feature

### Option B: Immediate Enforcement

1. **Deploy changes** with verification required
2. **Existing veterinarians**: Send verification emails immediately
3. **Grace period**: 7 days to verify before lockout
4. **Communication**: Email all users in advance

### Recommended: Option A (Soft Launch)

**Migration SQL**:
```sql
-- Mark all existing veterinarians as verified (grandfather clause)
UPDATE accounts_user 
SET email_verified = TRUE 
WHERE role = 'veterinario' 
  AND date_joined < '2025-10-12';  -- Before Step 01.1 deployment

-- Mark all internal users as verified
UPDATE accounts_user 
SET email_verified = TRUE 
WHERE role IN ('personal_lab', 'histopatologo', 'admin');
```

---

## Security Considerations

### 1. Token Security
- ✅ Use `secrets.token_urlsafe(32)` for cryptographic randomness
- ✅ Store hashed version in database (optional enhancement)
- ✅ Tokens are URL-safe and contain ~43 characters
- ✅ Database index on token for fast lookup

### 2. Token Expiration
- ✅ 24-hour expiration prevents stale links
- ✅ Check expiration on every verification attempt
- ✅ Clear expired tokens periodically (cleanup task)

### 3. Rate Limiting
- ✅ Limit resend requests (max 3 per hour per email)
- ✅ Prevent token enumeration attacks
- ✅ Log excessive resend requests

### 4. Email Security
- ✅ Don't reveal if email exists in resend flow
- ✅ Use professional sender address
- ✅ Include security notice in email footer
- ✅ HTTPS-only verification links

### 5. Audit Trail
- ✅ Log verification attempts (success/failure)
- ✅ Log resend requests
- ✅ Track token generation and usage

---

## Email Deliverability

### Best Practices

1. **SPF/DKIM/DMARC**: Configure for sending domain
2. **Sender Address**: Use `noreply@adlab.com` (or institutional domain)
3. **Subject Line**: Clear and professional
4. **HTML Template**: Professional design, mobile-responsive
5. **Plain Text Version**: Include for compatibility
6. **Unsubscribe Link**: Not applicable (transactional email)
7. **Testing**: Test with Gmail, Outlook, Yahoo

### Template Requirements

- Mobile-responsive design
- Clear call-to-action button
- Plain text fallback
- Professional branding
- Security notice
- Contact information

---

## Django Admin Updates

### User Admin Changes

**Display verification status**:
```python
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email", 
        "role", 
        "email_verified",  # NEW
        "is_active", 
        "last_login_at"
    ]
    
    list_filter = [
        "role", 
        "email_verified",  # NEW
        "is_active"
    ]
    
    # Add verification status to fieldsets
    fieldsets = (
        # ... existing fieldsets ...
        (_("Email Verification"), {
            "fields": (
                "email_verified",
                "email_verification_token",
                "email_verification_sent_at",
            ),
        }),
    )
    
    readonly_fields = [
        # ... existing fields ...
        "email_verification_token",
        "email_verification_sent_at",
    ]
    
    # Add admin action to resend verification
    actions = ["send_verification_email"]
    
    def send_verification_email(self, request, queryset):
        """Admin action to send verification email."""
        for user in queryset.filter(role=User.Role.VETERINARIO, email_verified=False):
            # Generate token and send email
            token = user.generate_email_verification_token()
            # ... send email ...
        self.message_user(request, f"Verification emails sent to {queryset.count()} user(s).")
```

---

## Implementation Checklist

### Backend
- [ ] Update User model with new fields
- [ ] Create database migration
- [ ] Implement `can_login()` method
- [ ] Implement token generation method
- [ ] Update registration view
- [ ] Update login view (add verification check)
- [ ] Create `verify_email_view`
- [ ] Create `resend_verification_view`
- [ ] Add new URLs
- [ ] Update admin interface

### Email
- [ ] Create HTML email template
- [ ] Create plain text email template
- [ ] Implement email sending function
- [ ] Test email deliverability
- [ ] Configure email settings (SMTP)

### Testing
- [ ] Write unit tests (target: 10+ new tests)
- [ ] Write integration tests
- [ ] Manual testing checklist
- [ ] Test email in different clients

### Documentation
- [ ] Update STEP_01_COMPLETE.md
- [ ] Create STEP_01.1_COMPLETE.md
- [ ] Update API documentation
- [ ] User guide for veterinarians

### Deployment
- [ ] Run migration (mark existing users as verified)
- [ ] Deploy new code
- [ ] Test in production
- [ ] Monitor email delivery
- [ ] Monitor verification rates

---

## Estimated Effort

**Time**: 0.5-1 day (4-8 hours)

**Breakdown**:
- Model changes & migration: 1 hour
- Views implementation: 2 hours
- Email templates: 1 hour
- Testing: 2 hours
- Admin updates: 1 hour
- Documentation: 1 hour

---

## Dependencies

### Must be completed first:
- ✅ Step 01: Authentication & User Management (COMPLETED)

### Blocks these steps:
- None (optional enhancement to Step 01)

### Related steps:
- Step 02: Veterinarian Profiles (will benefit from verified emails)
- Step 08: Email Notifications (shares email infrastructure)

---

## Success Metrics

- **Verification Rate**: >95% of new veterinarians verify within 24 hours
- **Email Delivery**: >98% of verification emails delivered
- **Support Requests**: <5% of users need help with verification
- **Login Failures**: <1% due to unverified status (with clear messaging)
- **System Impact**: No performance degradation on login

---

## Future Enhancements (Not in Scope)

- [ ] Phone number verification (SMS)
- [ ] Two-factor authentication (2FA)
- [ ] Social login (Google, Microsoft)
- [ ] Passwordless login (magic links)
- [ ] Email change verification
- [ ] Automatic retry for failed emails

---

## Notes

- This is a **critical security feature** for external users
- Email verification is **industry standard** for medical/lab systems
- Internal users (lab staff) **bypass verification** (activated by admins)
- Existing users will be **grandfathered in** (marked as verified)
- Clear **user communication** is essential for adoption

---

**Status**: 📝 Documented, Ready for Implementation  
**Next**: Implement in agent mode, then test and deploy

