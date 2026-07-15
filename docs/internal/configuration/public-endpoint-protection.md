# Protección de endpoints públicos

Rate limiting y Cloudflare Turnstile para formularios de autenticación expuestos a internet.

## Rate limiting

Implementado con [`django-ratelimit`](https://django-ratelimit.readthedocs.io/) usando el backend de caché de Django (Redis en producción, LocMem en desarrollo sin Redis).

| Endpoint | Método | Límite |
|----------|--------|--------|
| `/accounts/login/` | POST | 10/min por IP |
| `/accounts/register/` | POST | 3/h por IP |
| `/accounts/password-reset/` | POST | 3/h por IP |
| `/accounts/resend-verification/` | POST | 3/h por IP **y** por email |

Al exceder el límite, la respuesta es **200** con mensaje de error en español (no HTTP 429), para mantener la UX del formulario.

### Variables

| Variable | Default | Descripción |
|----------|---------|-------------|
| `RATELIMIT_ENABLE` | `true` | Activar/desactivar rate limiting global |

En tests (`config.settings_test`) el rate limiting está deshabilitado por defecto.

## Cloudflare Turnstile (registro)

Solo aplica al formulario de registro de veterinarios (`/accounts/register/`).

| Variable | Default | Descripción |
|----------|---------|-------------|
| `TURNSTILE_SITE_KEY` | *(vacío)* | Clave pública del widget |
| `TURNSTILE_SECRET_KEY` | *(vacío)* | Clave secreta para verificación server-side |

Si **ambas** claves están vacías (desarrollo local), Turnstile se omite automáticamente.

### Configuración en Cloudflare

1. Ir a [Cloudflare Dashboard](https://dash.cloudflare.com/) → Turnstile
2. Crear un widget para el dominio de producción
3. Copiar site key y secret key a `.env`
4. Reconstruir/reiniciar el contenedor web

```bash
export TURNSTILE_SITE_KEY=0x...
export TURNSTILE_SECRET_KEY=0x...
```

## Relación con el punto 11 (habilitación admin)

El rate limiting y Turnstile **complementan** la aprobación manual de veterinarios:

- Punto 11: un MV registrado no puede operar hasta que un admin lo habilite (`is_verified`)
- Punto 12: reduce spam de registros, fuerza bruta en login y abuso de emails de verificación/reset

## Archivos relevantes

- `src/accounts/rate_limit.py` — mixin y constantes de límites
- `src/accounts/services/turnstile_service.py` — verificación del token
- `src/accounts/views.py` — decoradores en vistas públicas
- `src/accounts/test_public_endpoint_protection.py` — tests

## Verificación manual

### Desarrollo (sin Turnstile)

1. Registro en `/accounts/register/` funciona sin widget CAPTCHA
2. Login repetido con credenciales incorrectas muestra error normal (límite alto en dev si Redis/LocMem acumula)

### Producción

1. Confirmar `TURNSTILE_SITE_KEY` y `TURNSTILE_SECRET_KEY` en `.env`
2. El formulario de registro muestra el widget Turnstile
3. Registro sin completar Turnstile → error en español
4. Tras varios intentos de login fallidos desde la misma IP → mensaje de límite excedido

---

[← Volver a Configuration](./README.md)
