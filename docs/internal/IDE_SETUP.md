# IDE Setup Guide - Using Docker Container Packages

This guide helps you configure your IDE to use the Python packages installed in the Docker container, eliminating import warnings and providing proper Django development support.

## 🚨 The Problem

You're seeing import warnings like:
```
Import "django.conf" could not be resolved
Import "django.contrib" could not be resolved
```

This happens because your IDE doesn't know about:
1. The Django environment setup in the Docker container
2. The correct Python path (`src/` directory)
3. Django's settings module
4. The UV-managed packages in `/home/python/.local/`

## ✅ Solutions Implemented

### 1. VS Code Remote Container (`.devcontainer/devcontainer.json`)
- ✅ Full Docker container development environment
- ✅ Pre-configured with all necessary extensions
- ✅ Automatic Python path configuration
- ✅ Port forwarding for Django (8000) and Flower (5555)

### 2. VS Code Configuration (`.vscode/settings.json`)
- ✅ Added Docker container Python paths
- ✅ Configured Django-aware type checking
- ✅ Set up proper Python interpreter path
- ✅ Enabled auto-import completions
- ✅ Added Docker terminal integration

### 3. Pyright Configuration (`pyrightconfig.json`)
- ✅ Configured Python path and version (3.14)
- ✅ Set up execution environment for Docker container
- ✅ Enabled workspace-wide type checking
- ✅ Added Docker container site-packages path

### 4. Project Configuration (`pyproject.toml`)
- ✅ Added Pyright and MyPy tool configurations
- ✅ Set Python version and paths
- ✅ Configured type checking mode

### 5. Docker IDE Setup Script (`scripts/setup-docker-ide.sh`)
- ✅ Automated IDE configuration
- ✅ Creates VS Code workspace file
- ✅ Generates PyCharm configuration
- ✅ Tests Django imports in container

## 🔧 How to Apply the Fix

### Option 1: Automated Setup (Recommended)
Run the setup script to automatically configure your IDE:

```bash
./scripts/setup-docker-ide.sh
```

This will:
- Check Docker is running
- Build containers if needed
- Extract Python paths from container
- Create VS Code workspace file
- Generate PyCharm configuration
- Test Django imports

### Option 2: VS Code Remote Container (Best Experience)
1. **Install Remote Containers extension**
2. **Open command palette**: `Cmd+Shift+P`
3. **Select**: "Remote-Containers: Reopen in Container"
4. **Wait for container to build and start**
5. **Enjoy full Docker development environment!**

### Option 3: Manual VS Code Configuration
1. **Open VS Code workspace**: `code laboratory-system.code-workspace`
2. **Select Python interpreter**: `Cmd+Shift+P` → "Python: Select Interpreter"
3. **Choose Docker container Python**: `/home/python/.local/bin/python`
4. **Restart language server**: `Cmd+Shift+P` → "Python: Restart Language Server"

### For Other IDEs:

#### PyCharm:
1. **Run setup script**: `./scripts/setup-docker-ide.sh`
2. **Open project** in PyCharm
3. **Configure interpreter**: `File` → `Settings` → `Project` → `Python Interpreter`
4. **Add remote interpreter**: Docker → Use Docker Compose
5. **Select service**: `web`
6. **Set interpreter path**: `/home/python/.local/bin/python`

#### Cursor:
1. **Use VS Code settings** (compatible)
2. **Or use Remote Container** approach
3. **Restart Cursor** after configuration

#### Vim/Neovim with LSP:
Add to your LSP config:
```lua
-- For nvim-lspconfig
require('lspconfig').pyright.setup({
    settings = {
        python = {
            analysis = {
                extraPaths = {
                    "./src",
                    "/home/python/.local/lib/python3.14/site-packages"
                },
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
