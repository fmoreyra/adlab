# Documentation Quick Reference

Quick reference for working with the MkDocs documentation system.

---

## 📋 Makefile Commands (Recommended)

All commands run inside the Docker container automatically.

### Preview & Build

```bash
# Preview with live reload (http://127.0.0.1:8000)
make docs-serve

# Build production site (outputs to public_collected/docs/)
make docs-build
```

### Image Path Management

```bash
# Preview what changes would be made (dry run)
make docs-update-paths-preview

# Apply all image path updates
make docs-update-paths
```

---

## 🐳 Docker Commands (Manual)

If you prefer to run commands directly in the container:

```bash
# Preview documentation
docker compose exec web mkdocs serve -a 0.0.0.0:8000

# Build production site
docker compose exec web mkdocs build -d public_collected/docs --clean

# Update image paths (interactive)
docker compose exec web python3 scripts/update-image-paths.py
```

---

## 📁 File Locations

```
docs/
├── index.md                          # Documentation homepage
├── getting-started/                  # Onboarding guides
├── user-guides/                      # Role-specific guides
│   ├── veterinarians/               # 4 guides
│   ├── histopathologists/           # 3 guides
│   ├── lab-staff/                   # 4 guides (incl. firma digital)
│   └── administrators/              # 3 guides
├── workflows/                        # Complete process flows
├── common-tasks/                     # Common operations
├── troubleshooting/                  # Help & support
├── assets/images/                    # All screenshots
│   ├── getting-started/
│   ├── user-guides/
│   ├── workflows/
│   ├── common-tasks/
│   └── troubleshooting/
└── internal/                         # Technical documentation

Configuration:
├── mkdocs.yml                        # MkDocs configuration
├── pyproject.toml                    # Python dependencies
└── scripts/
    ├── build-docs.sh                 # Build script
    └── update-image-paths.py         # Image path updater
```

---

## ✏️ Common Workflows

### Adding a New Page

1. Create markdown file in appropriate directory
2. Add to navigation in `mkdocs.yml` under `nav:` section
3. Preview: `make docs-serve`
4. Build: `make docs-build`
5. Commit changes

### Adding Screenshots

1. Take screenshot following guidelines in `SCREENSHOT_CHECKLIST.md`
2. Save to `docs/assets/images/{section}/{name}.png`
3. Add to markdown: `![Description](assets/images/section/name.png)`
4. Preview: `make docs-serve`
5. Update checklist
6. Commit both image and markdown

### Updating Placeholders

1. Add screenshots to appropriate directories
2. Preview changes: `make docs-update-paths-preview`
3. Apply updates: `make docs-update-paths`
4. Verify: `make docs-serve`
5. Build: `make docs-build`

---

## 🎨 Markdown Syntax

### Basic Formatting

```markdown
# Heading 1
## Heading 2
### Heading 3

**Bold text**
*Italic text*

- Bullet point
1. Numbered list

[Link text](path/to/page.md)
![Image](assets/images/path/image.png)

`inline code`
```

### MkDocs Material Extensions

**Admonitions (colored boxes):**
```markdown
!!! note "Title"
    Content here

!!! warning "Advertencia"
    Warning content

!!! tip "Consejo"
    Tip content
```

**Tabs:**
```markdown
=== "Tab 1"
    Content for tab 1

=== "Tab 2"
    Content for tab 2
```

**Task Lists:**
```markdown
- [x] Completed task
- [ ] Pending task
```

---

## 🔍 Search Configuration

Search is automatically configured for Spanish:
- Full-text search across all documentation
- Search suggestions
- Result highlighting
- Case-insensitive

No configuration needed!

---

## 🚀 Deployment

### Static File Serving

Documentation is automatically served by Django/WhiteNoise:

1. Build: `make docs-build`
2. Output: `public_collected/docs/`
3. Access: `/static/docs/` (automatically served)

### Custom URL Route (Optional)

Add to `src/config/urls.py`:

```python
from django.views.generic import RedirectView

urlpatterns = [
    # ... existing patterns
    path('docs/', RedirectView.as_view(url='/static/docs/')),
]
```

Then access at: `/docs/`

---

## 📊 Project Status

### Completed
- ✅ MkDocs Material setup
- ✅ 28 user guides in Spanish
- ✅ Workflow documentation
- ✅ Image folder structure
- ✅ Screenshot checklist (106 items)
- ✅ Build scripts
- ✅ Makefile commands
- ✅ Docker integration

### In Progress
- 🚧 Screenshot capture (0/106)
- 🚧 User testing

---

## 🐛 Troubleshooting

### MkDocs not found
```bash
# Rebuild Docker container
docker compose build web
```

### Images not showing
- Check path: `assets/images/...`
- Path relative to `docs/` directory
- Use forward slashes: `/`
- Lowercase extension: `.png`

### Port 8000 already in use
```bash
# Stop any running mkdocs serve
docker compose exec web pkill -f "mkdocs serve"

# Or use different port
docker compose exec web mkdocs serve -a 0.0.0.0:8001
```

### Build fails
```bash
# Check container logs
docker compose logs web

# Rebuild container
docker compose build web

# Verify mkdocs.yml syntax
docker compose exec web mkdocs build --strict
```

---

## 📞 Getting Help

1. **Setup Guide**: `DOCUMENTATION_SETUP.md`
2. **Screenshot Checklist**: `SCREENSHOT_CHECKLIST.md`
3. **MkDocs Documentation**: https://www.mkdocs.org
4. **Material Theme**: https://squidfunk.github.io/mkdocs-material/
5. **Makefile help**: `make help`

---

*Last Updated: January 2025*
