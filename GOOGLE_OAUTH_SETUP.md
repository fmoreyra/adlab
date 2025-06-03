# Google OAuth Setup for Veterinary System

This document explains how to set up Google OAuth authentication for the veterinary laboratory system.

## Overview

The system now supports two ways for veterinarians to register and log in:

1. **Traditional Registration**: Username/password with manual profile creation
2. **Google OAuth**: Sign in with Google account and complete veterinary profile

Both authentication methods now use **consistent FCV branding and styling** across all pages.

## Google OAuth Configuration

### 1. Create Google OAuth Application

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Configure the OAuth consent screen
6. Create OAuth 2.0 credentials with these settings:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/accounts/google/login/callback/`

### 2. Configure Django Settings

Add your Google OAuth credentials to your environment variables:

```bash
export GOOGLE_OAUTH2_CLIENT_ID="your-client-id-here"
export GOOGLE_OAUTH2_CLIENT_SECRET="your-client-secret-here"
```

### 3. Update Social Application in Django Admin

1. Access Django admin at `http://localhost:8000/admin/`
2. Go to "Social Applications" under "Social Accounts"
3. Edit the Google OAuth application
4. Update the Client ID and Secret key with your Google credentials
5. Make sure the application is associated with your site

## User Flow

### For Google OAuth Users

1. User clicks "Sign in with Google" on the login page
2. User is redirected to Google for authentication
3. After successful Google authentication, user is redirected to complete profile page
4. User fills in veterinary-specific information:
   - Phone number (required)
   - License number (required)
   - Address (optional)
5. Profile is created with `is_approved = False`
6. User sees pending approval message
7. Admin approves the user in Django admin
8. User can now access the dashboard

### For Traditional Registration Users

1. User fills out complete registration form
2. Profile is created with `is_approved = False`
3. User sees pending approval message
4. Admin approves the user in Django admin
5. User can log in and access dashboard

## Admin Approval Workflow

All new users (both Google OAuth and traditional registration) require admin approval:

1. New users are created with `is_approved = False`
2. Admins can view pending approvals in Django admin
3. Admin interface shows visual indicators (⏳ for pending, ✓ for approved)
4. Bulk approval actions are available
5. Only approved users can access the dashboard

## Styled Templates and URLs

### Custom Styled Templates

All authentication pages now feature consistent **FCV purple branding** (#8B4F9D, #9D7DB6, #B49BC8):

- **`/accounts/login/`**: Main login page with Google OAuth integration
- **`/accounts/signup/`**: Registration page with Google OAuth option
- **`/accounts/password/reset/`**: Password reset page
- **`/accounts/google/login/`**: Google OAuth connection page
- **Base template**: Shared styling framework for all authentication pages

### URL Structure
- `/users/login/`: Traditional veterinary login (redirects to `/accounts/login/`)
- `/users/register/`: Traditional veterinary registration
- `/users/complete-profile/`: Profile completion for social login users
- `/accounts/`: Django-allauth URLs (login, logout, social auth)

### Design Features

**Consistent Branding:**
- FCV logo and header on all pages
- Purple gradient color scheme matching the lab branding
- Professional medical/veterinary aesthetic
- Responsive design for mobile and desktop

**Enhanced UX:**
- Clear visual hierarchy with titles and subtitles
- Smooth hover animations and transitions
- Proper error handling and messaging in Spanish
- Accessible form design with proper labels
- Google branding with official Google colors and icon

## Testing

The system includes comprehensive tests covering:
- Traditional registration and login
- Google OAuth profile completion
- Validation and error handling
- Admin approval workflow
- All edge cases and error conditions
- **Template rendering and styling** (37 tests total)

Run tests with:
```bash
./run manage test users.tests
```

## Security Considerations

1. **Email Verification**: Currently disabled for development (`ACCOUNT_EMAIL_VERIFICATION = "none"`)
2. **HTTPS**: Use HTTPS in production for OAuth callbacks
3. **Environment Variables**: Store OAuth credentials securely
4. **Admin Approval**: All users require manual approval for security
5. **CSRF Protection**: All forms include CSRF tokens
6. **Input Validation**: Comprehensive form validation on all fields

## Production Deployment

For production deployment:

1. Update `ALLOWED_HOSTS` in settings
2. Set `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`
3. Use HTTPS for all OAuth redirect URIs
4. Store credentials in secure environment variables
5. Update Google OAuth redirect URIs to production domain
6. Configure email backend for password reset functionality

## Troubleshooting

### Common Issues

1. **OAuth Redirect Mismatch**: Ensure redirect URI in Google Console matches exactly
2. **Missing Credentials**: Check environment variables are set correctly
3. **Site Configuration**: Verify SITE_ID and Site domain in Django admin
4. **Permissions**: Ensure Google+ API is enabled in Google Cloud Console
5. **Template Not Found**: Check that template directories are properly configured

### Debug Steps

1. Check Django admin for Social Applications configuration
2. Verify environment variables: `echo $GOOGLE_OAUTH2_CLIENT_ID`
3. Check Django logs for OAuth errors
4. Test with different Google accounts
5. Verify template loading: check `TEMPLATES` setting in Django settings

## Features

### Current Features
- ✅ Google OAuth integration with styled templates
- ✅ Consistent FCV branding across all authentication pages
- ✅ Profile completion workflow
- ✅ Admin approval system
- ✅ Comprehensive validation
- ✅ Beautiful responsive UI
- ✅ Comprehensive test coverage (37 tests)
- ✅ Spanish language interface
- ✅ Password reset functionality
- ✅ Mobile-friendly design

### Future Enhancements
- Email verification in production
- Additional OAuth providers (Facebook, Microsoft)
- Automated approval for verified domains
- Enhanced profile management
- Two-factor authentication
- Email templates matching the design system 