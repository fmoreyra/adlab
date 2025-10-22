# Documentation Setup Guide

This guide explains how to set up, build, and maintain the documentation site for the Laboratory Management System.

---

## 📚 Overview

The documentation uses **MkDocs** with the **Material theme** to create a professional, searchable documentation website from Markdown files.

### Key Features
- ✅ Professional Material Design theme
- ✅ Full-text search in Spanish
- ✅ Mobile-responsive
- ✅ Dark/light mode toggle
- ✅ Static site served via Django/WhiteNoise
- ✅ Easy to update and maintain

---

## 🚀 Quick Start

### Prerequisites

- Docker and docker-compose running
- Django application container running

### 1. Install Dependencies

Dependencies are already defined in `pyproject.toml` and installed when the Docker container builds:
- `mkdocs==1.6.0`
- `mkdocs-material==9.5.40`
- `pymdown-extensions==10.11.2`

To rebuild the container with dependencies:
```bash
docker compose build web
```

### 2. Preview Locally

**Using Makefile (Recommended):**
```bash
make docs-serve
```

**Manual (inside container):**
```bash
docker compose exec web mkdocs serve -a 0.0.0.0:8000
```

Open http://127.0.0.1:8000 in your browser.

### 3. Build for Production

**Using Makefile (Recommended):**
```bash
make docs-build
```

**Manual (inside container):**
```bash
docker compose exec web mkdocs build -d public_collected/docs --clean
```

Output goes to `public_collected/docs/`.

---

## 📁 Documentation Structure

```
docs/
├── index.md                    # Homepage
├── getting-started/            # Onboarding guides
├── user-guides/                # Role-specific guides
│   ├── veterinarians/
│   ├── histopathologists/
│   ├── lab-staff/
│   └── administrators/
├── workflows/                  # Business processes
├── common-tasks/               # Common operations
├── troubleshooting/            # Help & support
├── assets/
│   └── images/                 # All screenshots
│       ├── getting-started/
│       ├── user-guides/
│       ├── workflows/
│       ├── common-tasks/
│       └── troubleshooting/
└── internal/                   # Technical docs
```

---

## 🖼️ Adding Screenshots

### 1. Take Screenshots

Follow guidelines in `SCREENSHOT_CHECKLIST.md`:
- **Format**: PNG
- **Max Width**: 1920px
- **Max Size**: 500KB
- **Browser**: Chrome at 100% zoom
- **Hide**: Personal/sensitive data

### 2. Save in Correct Location

```
docs/assets/images/{section}/{descriptive-name}.png
```

Examples:
```
docs/assets/images/user-guides/veterinarians/dashboard.png
docs/assets/images/workflows/status-timeline.png
docs/assets/images/common-tasks/label-example.png
```

### 3. Reference in Markdown

```markdown
![Description](assets/images/section/filename.png)
```

Example:
```markdown
![Panel de control del veterinario](assets/images/user-guides/veterinarians/dashboard.png)
```

### 4. Optimize Images

```bash
# Install optimizer (optional)
brew install pngquant

# Optimize single file
pngquant --quality=65-80 input.png --output output.png

# Or use online: tinypng.com
```

---

## ✏️ Editing Documentation

### File Format

All documentation is in **Markdown** format (.md files).

### Common Markdown Syntax

```markdown
# Heading 1
## Heading 2
### Heading 3

**Bold text**
*Italic text*

- Bullet point
1. Numbered list

[Link text](path/to/page.md)

![Image alt text](assets/images/path/image.png)

> Quote or note

`inline code`

\```python
# Code block
def example():
    return "Hello"
\```
```

### Material Extensions

**Admonitions** (colored boxes):
```markdown
!!! note "Title"
    Content here

!!! warning "Advertencia"
    Warning content

!!! tip "Consejo"
    Tip content
```

**Tabs**:
```markdown
=== "Tab 1"
    Content for tab 1

=== "Tab 2"
    Content for tab 2
```

**Task Lists**:
```markdown
- [x] Completed task
- [ ] Pending task
```

---

## 🔄 Workflow

### Adding New Documentation

1. **Create markdown file** in appropriate directory
2. **Add to navigation** in `mkdocs.yml`
3. **Preview locally**: `make docs-serve`
4. **Build**: `make docs-build`
5. **Commit changes** to git

### Updating Existing Documentation

1. **Edit markdown file**
2. **Check preview**: `make docs-serve` (auto-reloads)
3. **Build**: `make docs-build`
4. **Commit changes**

### Adding Screenshots

1. **Take screenshot** following guidelines
2. **Save to `assets/images/`** in correct subdirectory
3. **Update markdown** to reference image
4. **Check in preview**: `make docs-serve`
5. **Update checklist**: Mark as complete in `SCREENSHOT_CHECKLIST.md`
6. **Commit** both image and markdown

---

## 🔧 Configuration

### Main Configuration

File: `mkdocs.yml`

Key sections:
- `site_name`: Documentation title
- `theme`: Material theme configuration
- `nav`: Navigation structure
- `plugins`: Search, minify, etc.
- `markdown_extensions`: Enhanced Markdown features

### Theme Customization

Edit `mkdocs.yml` to customize:

**Colors**:
```yaml
theme:
  palette:
    primary: indigo
    accent: indigo
```

**Features**:
```yaml
theme:
  features:
    - navigation.tabs
    - search.suggest
    # ...more features
```

**Logo and Favicon**:
```yaml
theme:
  logo: assets/images/logo.png
  favicon: assets/images/favicon.png
```

---

## 🚢 Deployment

### Option 1: Serve as Static Files (Recommended)

Built documentation is in `public_collected/docs/`.

Django's WhiteNoise middleware serves it automatically at:
```
/static/docs/
```

No code changes needed!

### Option 2: Custom URL Route

Add to `src/config/urls.py`:

```python
from django.views.generic import RedirectView

urlpatterns = [
    # ... existing patterns
    path('docs/', RedirectView.as_view(url='/static/docs/')),
]
```

Access at:
```
/docs/
```

### Adding to Navigation

Add link to main template navigation:

```html
<a href="{% static 'docs/index.html' %}" class="nav-link">
    Documentación
</a>
```

---

## 🔍 Search Configuration

Search is configured in `mkdocs.yml`:

```yaml
plugins:
  - search:
      lang: es
      separator: '[\s\-,:!=\[\]()"/]+|...'
```

**Features**:
- Full-text search
- Spanish language support
- Search suggestions
- Highlighting results
- Case-insensitive

---

## 📦 Build Process

### Development Build

**Using Makefile (Recommended):**
```bash
make docs-serve
# Builds in memory, serves at http://127.0.0.1:8000
# Auto-reloads on file changes
```

**Manual (inside container):**
```bash
docker compose exec web mkdocs serve -a 0.0.0.0:8000
```

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

**What happens**:
1. Reads `mkdocs.yml` configuration
2. Processes all markdown files
3. Applies Material theme
4. Generates static HTML/CSS/JS
5. Copies images and assets
6. Creates search index
7. Minifies HTML/CSS/JS
8. Outputs to `public_collected/docs/`

### Build Artifacts

```
public_collected/docs/
├── index.html
├── getting-started/
│   ├── system-overview/
│   ├── first-login/
│   └── basic-navigation/
├── user-guides/
│   └── ...
├── assets/
│   ├── images/
│   ├── stylesheets/
│   └── javascripts/
├── search/
│   └── search_index.json
└── sitemap.xml
```

---

## 🐛 Troubleshooting

### Build Errors

**Error**: `mkdocs: command not found`
```bash
# Install dependencies
pip install -e .
```

**Error**: `Config file 'mkdocs.yml' does not exist`
```bash
# Run from project root
cd /path/to/laboratory-system
mkdocs build
```

**Error**: Navigation issues
- Check `nav` section in `mkdocs.yml`
- Ensure all referenced files exist
- Paths are relative to `docs/` directory

### Preview Issues

**Images not showing**:
- Check path is correct: `assets/images/...`
- Path is relative to `docs/` directory
- File extension is lowercase `.png`

**Search not working**:
- Search only works in built site, not in markdown files
- Run `mkdocs serve` or build to test search

### Performance

**Build is slow**:
- Large images? Optimize before adding
- Many files? Normal, just takes time
- Use `--clean` flag to clear cache

---

## 📝 Best Practices

### Writing Documentation

1. **Use clear headings** - H1 for title, H2 for sections
2. **Keep paragraphs short** - 3-4 sentences max
3. **Use lists** - Easier to scan than paragraphs
4. **Add screenshots** - Show, don't just tell
5. **Cross-reference** - Link to related pages
6. **Use admonitions** - Highlight important info
7. **Test locally** - Preview before committing

### Managing Screenshots

1. **Consistent style** - Same browser, zoom, size
2. **Descriptive names** - `dashboard.png` not `screenshot1.png`
3. **Optimize size** - Compress before committing
4. **Update checklist** - Track progress
5. **Version control** - Commit with documentation

### Maintenance

1. **Regular reviews** - Check for outdated info quarterly
2. **Update with features** - Document new features immediately
3. **User feedback** - Incorporate user suggestions
4. **Keep translations** - If adding English version
5. **Archive old docs** - Move to `internal/archive/`

---

## 🤝 Contributing

### Adding New Pages

1. Create markdown file in appropriate directory
2. Add to `nav` in `mkdocs.yml`
3. Follow existing page structure
4. Add screenshots if needed
5. Test locally with `mkdocs serve`
6. Submit for review

### Style Guide

- **Language**: Spanish for user docs, English for technical docs
- **Tone**: Friendly, helpful, clear
- **Format**: Use existing pages as templates
- **Images**: Follow screenshot guidelines
- **Links**: Use relative paths within docs

---

## 📞 Support

### Resources

- **MkDocs Documentation**: https://www.mkdocs.org
- **Material Theme**: https://squidfunk.github.io/mkdocs-material/
- **Markdown Guide**: https://www.markdownguide.org
- **Screenshot Checklist**: `SCREENSHOT_CHECKLIST.md`

### Getting Help

1. Check this guide
2. Check MkDocs/Material documentation
3. Ask development team
4. Check GitHub issues

---

## 🔄 Changelog

### Version 1.0 (January 2025)
- Initial MkDocs setup
- Material theme configuration
- Complete Spanish user documentation
- Image folder structure
- Screenshot checklist (106 items)
- Build scripts

---

*Last Updated: January 2025*
