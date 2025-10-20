# IDE Setup Guide - Fixing Django Import Warnings

This guide helps you configure your IDE to properly resolve Django imports and eliminate import warnings.

## 🚨 The Problem

You're seeing import warnings like:
```
Import "django.conf" could not be resolved
Import "django.contrib" could not be resolved
```

This happens because your IDE doesn't know about:
1. The Django environment setup
2. The correct Python path (`src/` directory)
3. Django's settings module

## ✅ Solutions Implemented

### 1. VS Code Configuration (`.vscode/settings.json`)
- ✅ Added `src/` to Python analysis paths
- ✅ Configured Django-aware type checking
- ✅ Set up proper Python interpreter path
- ✅ Enabled auto-import completions

### 2. Pyright Configuration (`pyrightconfig.json`)
- ✅ Configured Python path and version
- ✅ Set up execution environment for `src/` directory
- ✅ Enabled workspace-wide type checking

### 3. Project Configuration (`pyproject.toml`)
- ✅ Added Pyright and MyPy tool configurations
- ✅ Set Python version and paths
- ✅ Configured type checking mode

## 🔧 How to Apply the Fix

### For VS Code Users:
1. **Restart VS Code** - The new settings will take effect
2. **Reload the window**: `Cmd+Shift+P` → "Developer: Reload Window"
3. **Select Python interpreter**: `Cmd+Shift+P` → "Python: Select Interpreter"

### For Other IDEs:

#### PyCharm:
1. Go to `File` → `Settings` → `Project` → `Python Interpreter`
2. Add `src/` to the `Content Root`
3. Set `DJANGO_SETTINGS_MODULE=config.settings` in environment variables

#### Cursor:
1. The VS Code settings should work automatically
2. Restart Cursor if needed

#### Vim/Neovim with LSP:
Add to your LSP config:
```lua
-- For nvim-lspconfig
require('lspconfig').pyright.setup({
    settings = {
        python = {
            analysis = {
                extraPaths = {"./src"},
                typeCheckingMode = "basic"
            }
        }
    }
})
```

## 🧪 Testing the Fix

After applying the configuration:

1. **Open any Django file** (e.g., `src/accounts/views.py`)
2. **Check the Problems panel** - import warnings should be gone
3. **Try auto-completion** - Django imports should work
4. **Hover over Django classes** - you should see type information

## 🐳 Docker Development

Since this project runs in Docker, the IDE configuration is designed to work with:
- **Local development**: IDE resolves imports for better editing experience
- **Docker execution**: Actual code runs in the container with proper Django setup

## 📁 File Structure

```
laboratory-system/
├── .vscode/
│   └── settings.json          # VS Code configuration
├── pyrightconfig.json         # Pyright type checker config
├── pyproject.toml            # Project config with tool settings
├── setup-dev.py              # Development setup script
└── src/                      # Django project root
    ├── config/
    ├── accounts/
    ├── protocols/
    └── pages/
```

## 🔍 Troubleshooting

### If warnings persist:

1. **Check Python interpreter**:
   ```bash
   # In VS Code: Cmd+Shift+P → "Python: Select Interpreter"
   # Make sure it points to your Python installation
   ```

2. **Verify Django installation**:
   ```bash
   python -c "import django; print(django.get_version())"
   ```

3. **Restart language server**:
   - VS Code: `Cmd+Shift+P` → "Python: Restart Language Server"
   - Cursor: Similar command

4. **Clear cache**:
   ```bash
   # Remove Python cache
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

### For Docker-only development:

If you only develop inside Docker and don't have Django installed locally:

1. **Install Django locally** (for IDE support):
   ```bash
   pip install django==5.2.7
   ```

2. **Or use remote development**:
   - VS Code Remote Containers extension
   - Develop directly inside the Docker container

## 📚 Additional Resources

- [Django IDE Setup Guide](https://docs.djangoproject.com/en/stable/intro/tutorial01/#creating-a-project)
- [VS Code Python Configuration](https://code.visualstudio.com/docs/python/python-tutorial)
- [Pyright Configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)

## ✅ Verification

After setup, you should see:
- ✅ No import warnings in Problems panel
- ✅ Django auto-completion working
- ✅ Type hints for Django classes
- ✅ Proper syntax highlighting
- ✅ Go-to-definition working for Django imports

---

**Note**: These configurations are designed to work with the existing Docker-based development workflow while providing better IDE support for local editing.
