# Internal Documentation - Laboratory System

This directory contains technical documentation for developers, DevOps engineers, and system administrators working on the Laboratory Management System.

---

## 📚 Documentation Index

### 🚀 Getting Started

- [**README.md**](README.md) - Comprehensive project overview and setup instructions
- [**IDE_SETUP.md**](IDE_SETUP.md) - IDE configuration and development environment setup
- [**REORGANIZATION_SUMMARY.md**](REORGANIZATION_SUMMARY.md) - Documentation structure and organization

### ⚙️ Setup & Configuration

- [**setup/**](setup/) - Initial project setup guides
  - Development environment setup
  - Database configuration
  - Docker setup
  - Prerequisites and dependencies

- [**configuration/**](configuration/) - System configuration guides
  - Email configuration
  - Storage and backup configuration
  - Environment variables
  - Security settings

### 🚢 Deployment

- [**deployment/**](deployment/) - Production deployment documentation
  - Production deployment guide
  - Deployment strategies
  - Static files configuration
  - SSL/TLS setup
  - Gunicorn and Nginx configuration
  - Environment-specific configurations

### 🔧 Operations

- [**operations/**](operations/) - Day-to-day operations and maintenance
  - Monitoring and logging
  - Backup and restore procedures
  - Troubleshooting technical issues
  - Database maintenance
  - Performance tuning

### 📁 Archive

- [**archive/**](archive/) - Historical documentation and planning materials
  - Development steps
  - Planning documents
  - Meeting notes
  - Old documentation versions

---

## 🎯 Quick Links

### For Developers
- [README.md](README.md) - Start here for project overview
- [setup/](setup/) - Development environment setup
- [IDE_SETUP.md](IDE_SETUP.md) - Configure your IDE

### For DevOps/SysAdmins
- [deployment/](deployment/) - Production deployment
- [operations/](operations/) - System operations and maintenance
- [configuration/](configuration/) - System configuration

### For Project Managers
- [archive/](archive/) - Planning and historical documents
- [REORGANIZATION_SUMMARY.md](REORGANIZATION_SUMMARY.md) - Documentation structure

---

## 📖 User Documentation

For end-user documentation (veterinarians, histopathologists, lab staff, administrators), see:
- [**User Documentation**](../) - User-facing guides and manuals (in Spanish)

---

## 🔍 Documentation Structure

```
docs/
├── index.md                    # User documentation index (Spanish)
├── getting-started/            # User getting started guides
├── user-guides/                # Role-specific user guides
├── workflows/                  # Business process workflows
├── common-tasks/               # Common user tasks
├── troubleshooting/            # User troubleshooting
└── internal/                   # ← You are here (Technical docs)
    ├── index.md               # This file
    ├── README.md              # Project overview
    ├── IDE_SETUP.md           # IDE configuration
    ├── REORGANIZATION_SUMMARY.md
    ├── setup/                 # Setup guides
    ├── configuration/         # Configuration guides
    ├── deployment/            # Deployment guides
    ├── operations/            # Operations guides
    └── archive/               # Historical documents
```

---

## 🤝 Contributing

When adding technical documentation:
1. Place in the appropriate subdirectory
2. Update this index
3. Follow existing markdown conventions
4. Include code examples where relevant
5. Keep documentation up to date with code changes

---

*Last updated: January 2025*
