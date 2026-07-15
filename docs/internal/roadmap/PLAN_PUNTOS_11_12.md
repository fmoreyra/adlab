# Plan de implementación — Puntos 11 y 12 (seguridad y habilitación de veterinarios)

Addenda acordada **post-reunión** (Jul 2026). Complementa [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md).

**Estado general:** ✅ Punto 11 hecho · ⬜ Punto 12 pendiente  
**Última revisión:** Julio 2026

El **punto 11** cierra el gap entre registro público abierto y veterinarios realmente habilitados para operar. El **punto 12** reduce abuso automatizado en endpoints públicos. Son complementarios: 11 limita el daño operativo; 12 reduce volumen de basura y email bombing.

**Dependencias sugeridas:** 5.1 (SMTP operativo) para emails de habilitación/eliminación. El filtro del punto 7 (`is_verified` en búsqueda lab) quedó actualizado con el punto 11.

**Guía de prueba manual:** [VETERINARIAN_APPROVAL_TESTING.md](../VETERINARIAN_APPROVAL_TESTING.md)

---

## Resumen ejecutivo

| Ítem | Complejidad | Estimación | Estado |
|------|-------------|------------|--------|
| 11 Habilitación de veterinarios (admin + gate operativo) | Media–Alta | 2–3 días | ✅ Hecho (Jul 2026) |
| 12 Protección de endpoints públicos (rate limit + CAPTCHA) | Media | 0,5–1 día | ⬜ Pendiente |

**Orden sugerido:** 11 primero (impacto operativo directo); 12 en paralelo o inmediatamente después.

---

## Contexto del problema

Hoy el sistema tiene tres capas de confianza desalineadas:

| Capa | Campo | ¿Bloquea algo hoy? |
|------|-------|-------------------|
| Verificación de email | `User.email_verified` | Sí — login |
| Perfil completo | `Veterinarian.is_profile_complete_for_access()` | Sí — uso general (middleware) |
| Verificación profesional | `Veterinarian.is_verified` | Sí — crear protocolos HP/CT y búsqueda lab |

Cualquier persona puede registrarse en `/accounts/register/` y verificar su email, pero **no opera** hasta que un administrador habilite la cuenta en el panel dedicado.

---

## 11. Habilitación de veterinarios — ✅ Hecho (Jul 2026)

### Implementado

| Ítem | Detalle |
|------|---------|
| Gate operativo | `VeterinarianApprovedMixin` en creación HP/CT |
| Filtro lab (punto 7) | `is_verified=True` en `get_enabled_veterinarians_queryset()` |
| Pantalla MV | `/accounts/veterinarian/pending-approval/` |
| Singleton contacto | `VeterinarianPendingApprovalSettings` + caché Redis |
| Panel admin | `/dashboard/admin/veterinarians/` (Habilitar / Eliminar / Reactivar) |
| Edición pantalla | `/dashboard/admin/veterinarian-pending/` |
| Servicio | `VeterinarianApprovalService` (approve, delete, reactivate) |
| Emails | `veterinarian_approved.html`, `veterinarian_account_removed.html` |
| Auditoría | `AuthAuditLog`: `VETERINARIAN_APPROVED`, `VETERINARIAN_DELETED`, `VETERINARIAN_REACTIVATED` |
| Soft delete | Sin protocolos → anonimiza email; con protocolos → solo desactiva |
| Migraciones | `accounts/0009_veterinarian_approval`, `protocols/0024_veterinarian_approval` |
| Tests | `accounts/test_veterinarian_approval.py` |

Guía operativa: [managing-users.md](../../user-guides/administrators/managing-users.md).  
Prueba manual: [VETERINARIAN_APPROVAL_TESTING.md](../VETERINARIAN_APPROVAL_TESTING.md).

---

## 11. Habilitación de veterinarios (especificación original)

### Decisiones de producto (acordadas)

| Tema | Decisión |
|------|----------|
| Quién habilita | **Solo administrador** (`User.Role.ADMIN`) |
| Registro público | **Abierto pero limitado** — puede registrarse y completar perfil; no opera hasta habilitación |
| Acciones del MV pendiente | **No** puede crear protocolos HP/CT; redirect a pantalla de contacto con el administrador |
| Matrícula | **Opcional** por diseño; la habilitación no la exige |
| Herramienta admin | **Vista dedicada** en el panel (no Django Admin) — buscador simple con dos acciones |
| Eliminación | **Soft delete** con reglas según historial (ver §11.4) |
| Emails | En **habilitar** y en **eliminar** |
| Punto 7 (lab) | Búsqueda de MV debe filtrar también `is_verified=True` (actualizar `lab_protocol.py`) |

### Estados del veterinario

```
Registro público
    ↓
Email verificado          → puede iniciar sesión
    ↓
Perfil completo           → dashboard, ver/editar perfil, ver informes propios
    ↓
is_verified = True        → puede crear protocolos HP/CT
                          → aparece en búsqueda del lab (punto 7)
```

### 11.1 Gate operativo (`is_verified`)

**Objetivo:** `is_verified` deja de ser decorativo y pasa a ser el único gate de operación.

| Acción | Sin `is_verified` | Con `is_verified` |
|--------|-------------------|-------------------|
| Login (email verificado) | Sí | Sí |
| Completar / editar perfil | Sí | Sí |
| Dashboard | Sí (con aviso) | Sí |
| Ver informes propios | Sí | Sí |
| Crear protocolo HP/CT | **No** → pantalla pendiente | Sí |
| Aparecer en búsqueda lab | **No** | Sí |

#### Implementación prevista

| Cambio | Detalle |
|--------|---------|
| Mixin | `VeterinarianApprovedMixin` (o extensión de `VeterinarianProfileRequiredMixin`): perfil incompleto → completar perfil; perfil completo sin verificar → redirect pantalla pendiente |
| Vistas protegidas | `ProtocolSelectTypeView`, `ProtocolCreateCytologyView`, `ProtocolCreateHistopathologyView` |
| Lab search | `get_enabled_veterinarians_queryset()` añade `is_verified=True` |
| Badge perfil | «Pendiente de habilitación» (reemplazar «Pendiente Verificación») |

**No usar middleware global** — solo bloquear creación de protocolos, no todo el sistema.

### 11.2 Pantalla «Pendiente de habilitación» (veterinario)

**Objetivo:** UX clara cuando el MV intenta crear un protocolo sin estar habilitado.

Patrón: singleton administrable como [DashboardAnnouncement](../DASHBOARD_ANNOUNCEMENT.md).

#### Modelo propuesto: `VeterinarianPendingApprovalSettings`

| Campo | Uso |
|-------|-----|
| `title` | Título de la pantalla |
| `message` | Markdown — instrucciones, qué datos enviar |
| `contact_phone` | Teléfono del laboratorio |
| `contact_email` | Email de contacto |
| `is_active` | Mostrar / ocultar contenido |
| `updated_by`, `updated_at` | Auditoría |

| Componente | Ruta / archivo |
|------------|----------------|
| Vista admin edición | `/dashboard/admin/veterinarian-pending/` |
| Template MV | `accounts/veterinarian_pending_approval.html` |
| Servicio | Caché Redis (mismo patrón que banner) |

### 11.3 Panel admin — Gestión de veterinarios

**Objetivo:** Herramienta simple para administradores no técnicos.

| Elemento | Detalle |
|----------|---------|
| URL | `/dashboard/admin/veterinarians/` |
| Acceso | `AdminRequiredMixin` |
| Entrada | Tarjeta en `dashboard_admin.html` con contador de pendientes |
| UI | Misma estructura que `LabProtocolVeterinarianSearchView` / `lab_protocol_veterinarian_search.html` |

#### Filtros (tab o desplegable)

| Filtro | Query | Default |
|--------|-------|---------|
| **Pendientes** | `email_verified=True`, `is_verified=False`, `user__is_active=True` | Sí |
| Habilitados | `is_verified=True`, `user__is_active=True` | |
| Inactivos | `user__is_active=False` | |
| Todos | Sin filtro de estado | |

Búsqueda: nombre, apellido, email, matrícula, CUIL.

#### Acciones expuestas (solo dos en UI principal)

| Acción | Efecto | Email |
|--------|--------|-------|
| **Habilitar** | `veterinarian.verify(admin_user, notes=…)` | «Su cuenta fue habilitada» |
| **Eliminar** | Soft delete según reglas §11.4 | «Su cuenta fue eliminada» |

**Acción adicional (sin promover en UI principal):** **Reactivar** cuentas inactivas sin protocolos — para MV legítimos eliminados por error.

Confirmaciones en español; eliminar con confirmación más fuerte (checkbox «Entiendo que no se puede deshacer»).

#### Servicio: `VeterinarianApprovalService`

```python
# accounts/services/veterinarian_approval_service.py

approve(veterinarian, approved_by, request) -> ApprovalResult
delete_account(veterinarian, deleted_by, request) -> DeletionResult
reactivate(veterinarian, reactivated_by, request) -> ReactivationResult
can_delete(veterinarian) -> tuple[bool, str, str]  # allowed, mode, reason
```

#### Emails nuevos

| Evento | Plantilla | `EmailLog.EmailType` (nuevo) |
|--------|-----------|------------------------------|
| Habilitación | `accounts/emails/veterinarian_approved.html` | `VETERINARIAN_APPROVED` |
| Eliminación | `accounts/emails/veterinarian_account_removed.html` | `VETERINARIAN_ACCOUNT_REMOVED` |

Registrar en `AuthAuditLog` (`VETERINARIAN_APPROVED`, `VETERINARIAN_DELETED`, etc.).

Si SMTP falla al habilitar: **habilitar igual** y mostrar warning al admin (no bloquear la operación).

Django Admin conserva acciones bulk para soporte técnico; la operación cotidiana es la vista del panel.

### 11.4 Soft delete y re-registro

**Problema:** `User.email` y `User.username` son `unique=True`. Un soft delete naive (`is_active=False`) bloquea re-registro con el mismo email.

#### Reglas acordadas

| Situación | Acción | Email liberado para nuevo registro |
|-----------|--------|-----------------------------------|
| Sin protocolos (`protocols` count = 0) | `is_active=False` + **anonimizar** email/username en `User` y `Veterinarian` + limpiar `license_number` si existe | **Sí** |
| Con protocolos (`Protocol` FK `PROTECT`) | Solo `is_active=False`; **no** anonimizar | **No** — admin debe **reactivar** |

#### Anonimización (cuentas basura)

Guardar email original en `AuthAuditLog.details` o campo `deleted_email` antes de:

```python
user.email = f"deleted+{user.pk}+{timestamp}@invalid.local"
user.username = user.email
veterinarian.email = user.email
veterinarian.license_number = None  # liberar unique si aplica
user.is_active = False
user.is_verified permanece en Veterinarian
```

#### Registro público

`VeterinarianRegistrationForm.clean_email()` hoy usa `User.objects.filter(email=email).exists()` sin filtrar activos — coherente con anonimización en eliminación de basura.

### 11.5 Tests previstos

- Mixin: MV verificado accede a create; pendiente → redirect pantalla contacto
- Lab search: solo `is_verified=True`
- `VeterinarianApprovalService`: approve, delete sin protocolos (anonimiza), delete con protocolos (bloquea o solo desactiva)
- Vista admin: permisos, habilitar envía email (mock), contador pendientes
- Pantalla pendiente: contenido desde singleton

### 11.6 Documentación operativa

Actualizar `docs/user-guides/administrators/managing-users.md`:

- Sección «Habilitar veterinarios»
- Procedimiento: panel admin → Pendientes → Habilitar / Eliminar
- Relación con registro público y punto 7

---

## 12. Protección de endpoints públicos

### Contexto

Sin rate limiting ni CAPTCHA, bots pueden:

- Llenar la cola de pendientes del admin (punto 11)
- Disparar emails de verificación / reset (costo SMTP)
- Intentar fuerza bruta en login (lockout es por cuenta, no por IP)

La habilitación admin **no reemplaza** esta capa; la complementa.

### Decisiones

| Tema | Decisión |
|------|----------|
| CAPTCHA en todos los forms | **No** — solo donde el abuso es más probable |
| Prioridad 1 | **Rate limiting** por IP (Redis ya disponible) |
| Prioridad 2 | **Cloudflare Turnstile** en registro |
| Forms autenticados (perfil, panel admin) | Rate limit opcional; **sin CAPTCHA** |

### 12.1 Rate limiting

Implementación sugerida: `django-ratelimit` o `limit_req` en Nginx.

| Endpoint | Método | Límite sugerido |
|----------|--------|-----------------|
| `/accounts/login/` | POST | 10/min por IP |
| `/accounts/register/` | POST | 3/hora por IP |
| `/accounts/password-reset/` | POST | 3/hora por IP |
| `/accounts/resend-verification/` | POST | 3/hora por IP + por email |

Respuesta al exceder: HTTP 429 o mensaje en formulario (español).

**Estado:** ✅ Implementado (`accounts/rate_limit.py`, vistas en `accounts/views.py`).

### 12.2 CAPTCHA (registro)

| Opción | Recomendación |
|--------|---------------|
| Cloudflare Turnstile | **Preferida** — menos intrusivo, buena privacidad |
| reCAPTCHA v3 | Alternativa |
| django-simple-captcha | No recomendada (UX/accesibilidad) |

Alcance v1: **solo** `VeterinarianRegistrationForm` / `RegisterView`.

Variables de entorno: `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` (o equivalente).

Login y password reset: añadir CAPTCHA solo si el rate limit no alcanza (fase 2).

**Estado:** ✅ Implementado (`turnstile_service.py`, `VeterinarianRegistrationForm`, `register.html`).

### 12.3 Tests previstos

- Rate limit: N+1 requests → 429 o error de formulario ✅
- Registro con token Turnstile inválido → rechazado ✅
- Registro con token válido (mock) → flujo normal ✅

Implementados en `accounts/test_public_endpoint_protection.py`.

### 12.4 Documentación

- `docs/internal/configuration/public-endpoint-protection.md` — variables Turnstile y límites ✅
- Actualizar `production-checklist.md` — marcar ítem cuando esté hecho ✅
- Referencia cruzada con punto 11 ✅

---

## Impacto en el punto 7 (actualización de decisión)

| Antes (plan 7 original) | Después (con punto 11) |
|-------------------------|------------------------|
| Búsqueda lab: `email_verified` + `is_active` | + **`is_verified=True`** ✅ |
| Registro público sin restricción operativa | Registro abierto; **uso limitado** hasta habilitación admin ✅ |

El filtro `is_verified` está implementado en `protocols/lab_protocol.py` desde Jul 2026.

---

## Orden de implementación sugerido (11 + 12)

```
11.1 Gate is_verified (mixin + lab search)
11.2 Pantalla pendiente + singleton contacto
11.3 Panel admin veterinarios + servicio + emails
11.4 Soft delete / reactivación
12.1 Rate limiting
12.2 Turnstile en registro
Docs + tests
```

PRs posibles: **11a** (gate + pantalla), **11b** (panel admin + emails + soft delete), **12** (rate limit + CAPTCHA).

---

## Referencias

- [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md) — bloques 11, 12
- [PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md) — búsqueda MV (filtro a actualizar)
- [DASHBOARD_ANNOUNCEMENT.md](../DASHBOARD_ANNOUNCEMENT.md) — patrón singleton administrable
- [managing-users.md](../../user-guides/administrators/managing-users.md) — guía operativa (actualizar)
- `src/accounts/models.py` — `Veterinarian.is_verified`, `User.email` unique
- `src/protocols/lab_protocol.py` — queryset de MV habilitados
