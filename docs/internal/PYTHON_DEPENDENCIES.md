# Dependencias Python (uv)

Guía para agregar, actualizar y auditar paquetes Python en AdLab. **No existe un `requirements.txt` de runtime**: la fuente de verdad es `pyproject.toml` + `uv.lock`.

---

## Resumen

| Archivo | Rol |
|---------|-----|
| `pyproject.toml` | Declara qué paquetes necesita el proyecto (versiones mínimas o fijas) |
| `uv.lock` | Fija versiones exactas de todo el árbol (reproducible en Docker/CI/prod) |
| `bin/uv-install` | Usado en el build de la imagen: `uv sync --frozen` |
| `Dockerfile` | Copia `pyproject.toml` + `uv.lock` y ejecuta `bin/uv-install` |

**Regla de oro:** nunca instalar dependencias de aplicación con `pip install` dentro del contenedor. Eso no actualiza el lock ni la imagen del próximo deploy.

---

## Agregar o actualizar un paquete

### Opción recomendada: `uv add`

Desde el host (con contenedores levantados o vía `docker compose run`):

```bash
# Agrega al pyproject.toml y regenera uv.lock
make uv ARGS="add bleach>=6.2.0"

# Reconstruir la imagen web para que el cambio entre en runtime
docker compose build web
# o
make deps-install
```

Equivalente sin Makefile:

```bash
docker compose run --rm -w /app web uv add "django-storages[s3]==1.14.6"
docker compose build web
```

### Opción manual: editar `pyproject.toml`

1. Agregar la línea en `[project].dependencies`.
2. Regenerar el lock:

```bash
make uv ARGS="lock"
# o
docker compose run --rm --entrypoint uv -w /app web lock
```

3. Verificar que lock y manifest coinciden:

```bash
docker compose run --rm --entrypoint uv -w /app web lock --check
```

4. Rebuild: `docker compose build web` o `make deps-install`.

### Quitar un paquete

```bash
make uv ARGS="remove nombre-paquete"
docker compose build web
```

### Ver paquetes desactualizados

```bash
make uv-outdated
```

---

## Qué commitear

Siempre en el mismo PR/commit que introduce el uso del paquete:

- `pyproject.toml`
- `uv.lock`

Sin `uv.lock` actualizado, CI y otros desarrolladores pueden tener versiones distintas o fallos del tipo `ModuleNotFoundError` aunque el paquete figure en `pyproject.toml`.

---

## Cómo se instala en Docker

1. Build stage copia `pyproject.toml` y `uv.lock`.
2. `bin/uv-install`:
   - Si falta el lock o no coincide con el manifest → `uv lock`
   - Instala con `uv sync --frozen --no-install-project`
3. Paquetes quedan en `/home/python/.local` (`UV_PROJECT_ENVIRONMENT`).

Tras cambiar dependencias: **rebuild obligatorio** (`docker compose build web`). Un `docker compose up` sin rebuild sigue usando la imagen vieja.

---

## Auditoría de dependencias (código ↔ paquete)

Revisión al **2026-05-22**. Estado: `uv lock --check` OK; imports de runtime verificados en contenedor `web`.

| Paquete (`pyproject.toml`) | Uso en el proyecto |
|--------------------------|-------------------|
| `django` | Framework, ORM, auth, templates |
| `celery` | `config/celery.py`, `protocols/tasks.py`, `pages/tasks.py` |
| `redis` | Broker/cache; health en `up/views.py` |
| `psycopg` | PostgreSQL (`DATABASES`) |
| `gunicorn` | Servidor WSGI en producción (`config/gunicorn.py`) |
| `whitenoise` | Estáticos en prod (`middleware`, `config/storage.py`) |
| `pillow` | Imágenes (`PIL` en informes, firmas, PDF) |
| `reportlab` | PDFs de informes y órdenes (`pdf_service.py`, `views.py`) |
| `qrcode` | Etiquetas de protocolo (`protocols/views.py`) |
| `bleach` + `markdown` | Banner de dashboards (`dashboard_announcement_service.py`) |
| `django-storages[s3]` + `boto3` | Media en S3/Garage si `USE_S3_STORAGE=true` |
| `sentry-sdk` | Errores en prod (`config/settings.py`) |
| `django-debug-toolbar` | Solo con `DEBUG=true` |
| `psutil` + `docker` | Métricas del servidor en dashboard admin (`server_stats_service.py`) |
| `setuptools` | `distutils.util.strtobool` en settings/gunicorn (Python 3.14) |
| `ruff` | Lint/format (desarrollo/CI) |
| `safety` | Escaneo de vulnerabilidades (`make safety-check`) |
| `mkdocs`, `mkdocs-material`, `pymdown-extensions` | Documentación MkDocs (no runtime web) |

### Paquetes transitivos (no declarar en `pyproject.toml`)

Ejemplos presentes vía dependencias directas: `requests` (docker SDK), `urllib3`, `webencodings` (bleach). **uv** los resuelve en `uv.lock`; no hace falta listarlos salvo que se importen directamente en el código.

### Verificación rápida tras cambios

```bash
# Lock sincronizado
docker compose run --rm --entrypoint uv -w /app web lock --check

# Imports críticos en la imagen actual
docker compose run --rm -T web python3 -c "
import importlib
for p in ['django','celery','bleach','markdown','storages','boto3','reportlab','PIL']:
    importlib.import_module(p)
    print('OK', p)
"
```

---

## Errores frecuentes

| Síntoma | Causa habitual | Solución |
|---------|----------------|----------|
| `ModuleNotFoundError: No module named 'bleach'` | `pyproject.toml` actualizado pero imagen vieja o `uv.lock` sin commitear | `uv lock` / `uv add`, commit lock, `docker compose build web` |
| Tests OK en máquina, fallan en CI | Lock desactualizado en el repo | `uv lock --check` en CI; commitear `uv.lock` |
| `pip install X` en el servidor “arregló” prod | Cambio fuera de versionado | Quitar el hack; agregar con `uv add`, deploy con imagen nueva |

---

## Relacionado

- [README — Updating dependencies](../../README.md#-updating-dependencies)
- [IDE Setup](./IDE_SETUP.md) — paths de paquetes en el contenedor
- [Dashboard announcement](./DASHBOARD_ANNOUNCEMENT.md) — `bleach` + `markdown`
- [CLAUDE.md](../../CLAUDE.md) — comandos `make uv` / `make deps-install`
