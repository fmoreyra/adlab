# MkDocs Material Documentation System

Complete setup for serving professional, searchable documentation with MkDocs Material and Django.

---

## 🎯 Quick Start

### Prerequisites
- Docker and docker-compose running
- Django application container running

### Using Makefile Commands (Recommended)

All documentation commands run inside the Docker container:

```bash
# 1. Preview documentation with live reload
make docs-serve
# Opens at http://127.0.0.1:8000

# 2. Build for production
make docs-build
# Outputs to public_collected/docs/

# 3. Preview image path updates (dry run)
make docs-update-paths-preview

# 4. Update all image placeholders
make docs-update-paths
```

### Alternative: Direct Commands

If you have MkDocs installed locally:

```bash
# Install dependencies
pip install -e .

# Preview documentation
mkdocs serve

# Build for production
./scripts/build-docs.sh
```

### Access in Django
After building, documentation is available at:
- `/static/docs/` (via WhiteNoise)

---

## 📚 What's Included

### Documentation Files
- **28 user guides** in Spanish (veterinarians, histopathologists, lab staff, admins)
- **3 workflow documents** (sample journey, daily ops, emergencies)
- **8 common tasks** guides
- **3 troubleshooting** documents
- **Technical docs** in `internal/`

### Configuration
- `mkdocs.yml` - Complete MkDocs Material configuration
- `pyproject.toml` - Updated with MkDocs dependencies
- `scripts/build-docs.sh` - Build script with status output

### Image Management
- `assets/images/` - Organized folder structure (9 subdirectories)
- `SCREENSHOT_CHECKLIST.md` - 106 screenshots tracked by priority
- `scripts/update-image-paths.py` - Python script to update image references

### Setup Guides
- `DOCUMENTATION_SETUP.md` - Complete setup and maintenance guide
- This file - Quick reference and integration guide

---

## 📸 Adding Screenshots

### Current Status
- **Total needed**: 106 screenshots
- **Completed**: 0
- **Checklist**: `docs/SCREENSHOT_CHECKLIST.md`

### Workflow

#### 1. Take Screenshots
Follow guidelines in `SCREENSHOT_CHECKLIST.md`:
- PNG format, max 1920px wide
- Chrome browser, 100% zoom
- Consistent style, hide personal data

#### 2. Save to Correct Location
```
docs/assets/images/{section}/{descriptive-name}.png
```

#### 3. Update Markdown References
**Option A: Manual**
Replace:
```markdown
_[Espacio para captura de pantalla: Description]_
```

With:
```markdown
![Description](assets/images/section/filename.png)
```

**Option B: Automated (Using Makefile)**
```bash
# Preview changes (dry run)
make docs-update-paths-preview

# Apply changes
make docs-update-paths
```

**Option C: Automated (Manual)**
```bash
# Preview changes - run inside container
docker compose exec web python3 scripts/update-image-paths.py
# Choose option 1

# Apply changes - run inside container
docker compose exec web python3 scripts/update-image-paths.py
# Choose option 2
```

#### 4. Check in Preview
```bash
make docs-serve
# Verify image displays correctly at http://127.0.0.1:8000
```

#### 5. Update Checklist
Mark screenshot as complete in `SCREENSHOT_CHECKLIST.md`

---

## 🏗️ Building Documentation

### Development Build (Live Reload)

**Using Makefile (Recommended):**
```bash
make docs-serve
```

**Manual (inside container):**
```bash
docker compose exec web mkdocs serve -a 0.0.0.0:8000
```

**Local (if MkDocs installed):**
```bash
mkdocs serve
```

- Builds in memory
- Auto-reloads on file changes
- Great for writing/editing
- Access at http://127.0.0.1:8000

### Production Build

**Using Makefile (Recommended):**
```bash
make docs-build
```

**Manual (inside container):**
```bash
docker compose exec web mkdocs build -d public_collected/docs --clean
```

**Local (if MkDocs installed):**
```bash
./scripts/build-docs.sh
```

**What it does**:
1. Validates `mkdocs.yml`
2. Processes all markdown files
3. Applies Material theme
4. Generates static HTML/CSS/JS
5. Copies images and assets
6. Creates search index
7. Minifies output
8. Outputs to `public_collected/docs/`

### Build Output
```
public_collected/docs/
├── index.html
├── getting-started/
├── user-guides/
├── workflows/
├── common-tasks/
├── troubleshooting/
├── assets/
├── search/
└── sitemap.xml
```

---

## 🚀 Integrating with Django

### Option 1: Serve as Static Files (Recommended)

Built documentation is automatically served by WhiteNoise from `public_collected/docs/`.

**No code changes needed!**

Access at:
```
https://your-domain.com/static/docs/
```

### Option 2: Add Custom Route

Edit `src/config/urls.py`:

```python
from django.views.generic import RedirectView

urlpatterns = [
    # ... existing patterns
    path('docs/', RedirectView.as_view(url='/static/docs/'), name='documentation'),
]
```

Access at:
```
https://your-domain.com/docs/
```

### Option 3: Add to Navigation

Edit your base template:

```html
<!-- In navigation bar -->
<a href="{% static 'docs/index.html' %}" class="nav-link">
    📚 Documentación
</a>
```

---

## 🔄 Maintenance Workflow

### Regular Updates

1. **Edit markdown** files as needed
2. **Preview changes**: `make docs-serve`
3. **Build**: `make docs-build`
4. **Commit changes** (markdown + built files)

### Adding New Pages

1. **Create markdown** file in appropriate directory
2. **Add to navigation** in `mkdocs.yml` under `nav:` section
3. **Preview**: `make docs-serve`
4. **Build**: `make docs-build`
5. **Commit**

### Adding Screenshots

See "Adding Screenshots" section above.

### Quarterly Reviews

- Review all documentation for accuracy
- Update screenshots if UI changed
- Check for broken links
- Update version info

---

## 📝 Documentation Standards

### Language
- **User Documentation**: Spanish (for end users)
- **Technical Documentation**: English (for developers)

### Structure
- Clear headings (H1 for title, H2 for sections)
- Short paragraphs (3-4 sentences)
- Bulleted lists for scannability
- Screenshots for visual guidance
- Cross-references to related pages

### Markdown Style
- Use `**bold**` for UI elements
- Use `code` for commands/values
- Use admonitions for important notes
- Include alt text for all images

---

## 🐛 Troubleshooting

### "mkdocs: command not found"
```bash
pip install -e .
```

### Images not showing in preview
- Check path: `assets/images/...`
- Paths are relative to `docs/` directory
- Use forward slashes: `/`
- File extension lowercase: `.png`

### Navigation issues in build
- Check `nav:` section in `mkdocs.yml`
- Ensure all files exist
- Paths are relative to `docs/`

### Search not working
- Search only works in built site
- Run `mkdocs serve` or build to test
- Check `plugins` section in `mkdocs.yml`

### Build fails
```bash
# Check Python version (needs 3.13+)
python3 --version

# Reinstall dependencies
pip install -e . --force-reinstall

# Clear cache
mkdocs build --clean
```

---

## 📊 Project Status

### ✅ Completed
- [x] MkDocs Material setup
- [x] Complete Spanish user documentation (28 files)
- [x] Workflow documentation (3 files)
- [x] Common tasks (4 files)
- [x] Troubleshooting guides (3 files)
- [x] Image folder structure (9 subdirectories)
- [x] Screenshot checklist (106 items)
- [x] Build scripts
- [x] Documentation setup guide
- [x] Integration with Django/WhiteNoise

### 🚧 In Progress
- [ ] Screenshot capture (0/106)
- [ ] Screenshot optimization
- [ ] Testing all workflows
- [ ] User feedback collection

### 📅 Future Enhancements
- [ ] Video tutorials
- [ ] Interactive demos
- [ ] Multi-language support (English version)
- [ ] Print-friendly PDF export
- [ ] Version selector (for different releases)

---

## 📞 Support

### Resources
- **Setup Guide**: `DOCUMENTATION_SETUP.md`
- **Screenshot Checklist**: `SCREENSHOT_CHECKLIST.md`
- **MkDocs Docs**: https://www.mkdocs.org
- **Material Theme**: https://squidfunk.github.io/mkdocs-material/

### Getting Help
1. Check `DOCUMENTATION_SETUP.md`
2. Run `mkdocs --help`
3. Check Material theme documentation
4. Ask development team

---

## 🎉 Summary

You now have:
- ✨ Professional documentation site with Material Design
- 🔍 Full-text search in Spanish
- 📱 Mobile-responsive design
- 🌓 Dark/light mode toggle
- 📚 28 comprehensive user guides
- 🖼️ Organized image structure (106 screenshots planned)
- 🛠️ Build scripts and automation
- 🚀 Ready to integrate with Django
- 📖 Complete setup and maintenance guides

### Next Steps
1. **Start containers**: `docker compose up`
2. **Preview docs**: `make docs-serve`
3. **Take screenshots**: Follow `SCREENSHOT_CHECKLIST.md`
4. **Preview path updates**: `make docs-update-paths-preview`
5. **Update paths**: `make docs-update-paths`
6. **Build**: `make docs-build`
7. **Deploy**: Documentation auto-served by Django at `/static/docs/`

---

*Created: January 2025*
*Version: 1.0*
