# Step 01: Authentication & User Management

## Problem Statement

The system requires a secure authentication mechanism to control access to different modules based on user roles. Currently, the laboratory has no centralized authentication system, and the legacy Clarion system has minimal security controls. The new system must support multiple user types (veterinarians, laboratory personnel, histopathologists, and administrators) with different permission levels.

## Requirements

### Functional Requirements (RF01)

- **RF01.1**: Registration of veterinarians with validation of professional license (matrícula)
- **RF01.2**: Secure authentication with username and password
- **RF01.3**: Password recovery mechanism via email
- **RF01.4**: Profile management for different user types:
  - Veterinario Cliente (Veterinary Client)
  - Personal de Laboratorio (Laboratory Staff)
  - Histopatólogo (Histopathologist)
  - Administrador (Administrator)
- **RF01.5**: Storage of digital signatures for histopathologists

### Non-Functional Requirements

- **Security**: Passwords must be hashed using modern algorithms (bcrypt, Argon2)
- **Password Policy**: Minimum 8 characters, medium complexity
- **Account Lockout**: Block account after N failed login attempts
- **Session Management**: Secure session handling with appropriate timeout
- **Audit**: Log all authentication events (successful/failed logins)

## Data Model

### Users Table
```sql
users (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  email: VARCHAR(255) UNIQUE NOT NULL,
  password_hash: VARCHAR(255) NOT NULL,
  role: ENUM('veterinario', 'personal_lab', 'histopatologo', 'admin') NOT NULL,
  is_active: BOOLEAN DEFAULT TRUE,
  failed_login_attempts: INTEGER DEFAULT 0,
  last_login_at: TIMESTAMP,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

### Password Reset Tokens Table
```sql
password_reset_tokens (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id: INTEGER NOT NULL,
  token: VARCHAR(255) UNIQUE NOT NULL,
  expires_at: TIMESTAMP NOT NULL,
  used_at: TIMESTAMP,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
)
```

### Sessions Table (if using session-based auth)
```sql
sessions (
  id: VARCHAR(255) PRIMARY KEY,
  user_id: INTEGER NOT NULL,
  data: TEXT,
  expires_at: TIMESTAMP NOT NULL,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
)
```

### Audit Log Table
```sql
auth_audit_log (
  id: INTEGER PRIMARY KEY AUTO_INCREMENT,
  user_id: INTEGER,
  email: VARCHAR(255),
  action: VARCHAR(50) NOT NULL, -- 'login_success', 'login_failed', 'logout', 'password_reset'
  ip_address: VARCHAR(45),
  user_agent: TEXT,
  created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## API Design

### Authentication Endpoints

#### POST /api/auth/register
Register a new veterinary client account.

**Request:**
```json
{
  "email": "vet@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "nombre": "Juan",
  "apellido": "Pérez",
  "nro_matricula": "12345",
  "telefono": "+54 342 1234567"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Cuenta creada exitosamente",
  "user": {
    "id": 123,
    "email": "vet@example.com",
    "role": "veterinario"
  }
}
```

#### POST /api/auth/login
Authenticate user and create session.

**Request:**
```json
{
  "email": "vet@example.com",
  "password": "SecurePass123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": 123,
    "email": "vet@example.com",
    "nombre": "Juan",
    "apellido": "Pérez",
    "role": "veterinario"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // if using JWT
}
```

#### POST /api/auth/logout
End user session.

**Request:** (requires authentication)
```json
{}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Sesión cerrada exitosamente"
}
```

#### POST /api/auth/forgot-password
Request password reset email.

**Request:**
```json
{
  "email": "vet@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Si el email existe, recibirá instrucciones para restablecer su contraseña"
}
```

#### POST /api/auth/reset-password
Reset password using token.

**Request:**
```json
{
  "token": "abc123def456",
  "password": "NewSecurePass123",
  "confirm_password": "NewSecurePass123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Contraseña actualizada exitosamente"
}
```

#### GET /api/auth/me
Get current authenticated user information.

**Response (200 OK):**
```json
{
  "user": {
    "id": 123,
    "email": "vet@example.com",
    "nombre": "Juan",
    "apellido": "Pérez",
    "role": "veterinario",
    "nro_matricula": "12345"
  }
}
```

## Business Logic

### Password Hashing
- Use bcrypt with cost factor of 10-12
- Alternative: Argon2id with appropriate parameters
- Never store passwords in plain text

### Session Management
- Session timeout: 2 hours of inactivity for veterinarians
- Session timeout: 8 hours for laboratory staff (longer workday)
- Option to "Remember me" extends to 30 days
- Invalidate all sessions on password change

### Account Lockout
- Lock account after 5 failed login attempts
- Lockout duration: 15 minutes
- Send email notification on account lockout
- Administrator can manually unlock accounts

### Password Reset Flow
1. User requests password reset
2. Generate unique token with 1-hour expiration
3. Send email with reset link containing token
4. User clicks link and enters new password
5. Validate token and update password
6. Invalidate token after use

### Role-Based Access Control (RBAC)
- **Veterinario**: Can submit protocols, view their own cases
- **Personal de Laboratorio**: Can receive samples, process samples, view all protocols + create reports (with permission)
- **Administrador**: Full system access including user management

**Note**: Step-16 consolidates PERSONAL_LAB and HISTOPATOLOGO roles into unified PERSONAL_LAB role with granular report creation permissions.

### Laboratory Staff Authentication Flow
- **Separate Login Pages**: 
  - `/accounts/login/` - General login (for veterinarians)
  - `/accounts/histopathologist/login/` - Dedicated login (will be removed after Step-16)
- **Admin Creation**: Only administrators can create laboratory staff accounts
- **Complete Profile Creation**: Single forms create User account + respective profiles
- **Internal User Setup**: Laboratory staff created with `is_active=True`, `email_verified=True`, `is_staff=True`
- **Audit Logging**: All user creation events logged with `USER_CREATED` action

**Post-Step-16 State**: After Step-16 implementation, all laboratory staff will use unified authentication and role structure.

## Acceptance Criteria

1. ✅ Users can register with valid email and password
2. ✅ System validates matrícula for veterinarian registration
3. ✅ Users can log in with correct credentials
4. ✅ Failed login attempts are logged and limited
5. ✅ Account locks after 5 failed attempts
6. ✅ Users can request password reset via email
7. ✅ Password reset tokens expire after 1 hour
8. ✅ Users can log out and session is invalidated
9. ✅ Passwords are hashed and never exposed
10. ✅ Different user roles have appropriate access levels
11. ✅ All authentication events are logged in audit table
12. ✅ Session timeout works correctly
13. ✅ Histopathologists have dedicated login page without registration link (pre-Step-16)
14. ✅ Administrators can create complete histopathologist accounts (User + Profile) (pre-Step-16)
15. ✅ [Step-16] Laboratory staff role consolidation implemented with unified permissions
15. ✅ Histopathologist creation is properly audited and logged
16. ✅ Main webpage pathologist button uses dedicated login URL

## Testing Approach

### Unit Tests
- Password hashing and verification
- Token generation and validation
- Role permission checking
- Input validation for registration/login

### Integration Tests
- Complete registration flow
- Login → access protected resource → logout flow
- Password reset flow end-to-end
- Account lockout mechanism
- Session timeout behavior

### Security Tests
- SQL injection attempts on login
- Brute force login attempts
- Password complexity validation
- Token tampering detection
- Session hijacking prevention

### E2E Tests
- User registers → receives confirmation → logs in
- User forgets password → receives email → resets password → logs in
- User fails login 5 times → account locked → admin unlocks → logs in

## Technical Considerations

### 🔧 Pending Technical Decisions

1. **Authentication Mechanism**:
   - Option A: Session-based (cookies) - simpler, better for traditional web apps
   - Option B: JWT tokens - stateless, better for API-first architecture
   - Option C: OAuth 2.0 / OpenID Connect - future integration with university systems

2. **Session Storage** (if session-based):
   - Database
   - Redis (recommended for performance)
   - Memory (only for development)

3. **Password Hashing Algorithm**:
   - bcrypt (widely supported, proven)
   - Argon2 (more modern, better security)

4. **Email Service**:
   - Institutional SMTP
   - Third-party service (SendGrid, SES, Mailgun)

### Security Best Practices
- Implement rate limiting on login endpoint
- Use HTTPS only in production
- Set secure, httpOnly, sameSite flags on cookies
- Implement CSRF protection for session-based auth
- Regular security audits of authentication code

## Dependencies

### Must be completed first:
- None (this is a foundational step)

### Blocks these steps:
- Step 02: Veterinarian Profiles (requires user authentication)
- Step 03: Protocol Submission (requires authenticated users)
- All other steps (require authentication)

## Estimated Effort

**Time**: 1-1.5 weeks (Sprint 1-2)

**Breakdown**:
- Database schema: 0.5 days
- Backend API implementation: 3-4 days
- Frontend login/registration UI: 2-3 days
- Password reset functionality: 1-2 days
- Testing: 2 days
- Security hardening: 1 day

## Implementation Notes

### Development Phases
1. **Phase 1**: Basic login/logout with database sessions
2. **Phase 2**: Registration and profile creation
3. **Phase 3**: Password reset functionality
4. **Phase 4**: Account lockout and audit logging
5. **Phase 5**: Role-based access control enforcement

### Testing Checklist
- [ ] Unit tests for all authentication functions
- [ ] Integration tests for auth flows
- [ ] Security tests for common vulnerabilities
- [ ] Manual testing of all user roles
- [ ] Performance testing with concurrent logins
- [ ] Email delivery testing for password resets

### Deployment Considerations
- Ensure database migrations are reversible
- Set up monitoring for failed login attempts
- Configure email templates before production
- Document initial admin account creation process
- Plan for password policy enforcement on existing users (if migrating)

