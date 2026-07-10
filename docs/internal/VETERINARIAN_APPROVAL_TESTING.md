# Guía de prueba manual — Habilitación de veterinarios (punto 11)

Checklist para validar el flujo completo de habilitación MV en entorno local o staging.

**Prerrequisitos**

- Migraciones aplicadas: `make manage ARGS="migrate"`
- Servicios levantados: `docker compose up -d`
- SMTP configurado (recomendado) o backend `console` en dev para ver emails en logs
- Credenciales de prueba: ver [setup/test-credentials.md](setup/test-credentials.md)

**Roles necesarios**

| Rol | Uso en la prueba |
|-----|------------------|
| Administrador | Habilitar/eliminar MV, editar pantalla de contacto |
| Veterinario (nuevo) | Registro, verificación, gate de creación |
| Personal de lab | Verificar filtro en búsqueda delegada |

---

## 1. Registro y acceso limitado (MV pendiente)

1. Cerrar sesión (o usar ventana privada).
2. Ir a `/accounts/register/` y registrar un veterinario nuevo (email distinto a cuentas existentes).
3. Verificar el email (link del correo o consola Django si `EMAIL_BACKEND=console`).
4. Iniciar sesión con la cuenta nueva.
5. Completar perfil en `/accounts/veterinarian/complete-profile/` si el middleware lo pide.
6. Ir al panel (`/dashboard/`).
   - **Esperado:** dashboard accesible; badge «Pendiente de habilitación» en perfil.
7. Ir a `/accounts/veterinarian/profile/`.
   - **Esperado:** badge «Pendiente de habilitación» (no «Pendiente Verificación»).
8. Intentar crear protocolo:
   - Clic en «Nuevo protocolo» o ir directo a `/protocols/select-type/`.
   - **Esperado:** redirect a `/accounts/veterinarian/pending-approval/` con mensaje de contacto.
9. Volver al dashboard y confirmar que **sí** puede ver/editar perfil e informes propios (si los hubiera).

---

## 2. Pantalla de contacto (admin edita contenido)

1. Iniciar sesión como **administrador**.
2. Ir a `/dashboard/admin/` → tarjeta **Veterinarios** o **Habilitar Veterinarios**.
3. Enlace «Editar pantalla de contacto» o ir a `/dashboard/admin/veterinarian-pending/`.
4. Completar título, mensaje Markdown, teléfono y email de contacto → **Guardar**.
5. Cerrar sesión admin; iniciar sesión como MV pendiente del paso 1.
6. Intentar crear protocolo de nuevo.
   - **Esperado:** pantalla con el título y contenido configurados + datos de contacto.

---

## 3. Panel admin — Habilitar veterinario

1. Iniciar sesión como **administrador**.
2. Ir a `/dashboard/admin/veterinarians/` (filtro **Pendientes** por defecto).
   - **Esperado:** contador de pendientes en tarjeta del panel admin.
   - **Esperado:** el MV del paso 1 aparece en la lista.
3. Buscar por nombre, email o CUIL.
4. Clic en **Habilitar** para ese MV.
   - **Esperado:** mensaje de éxito; MV desaparece de «Pendientes» y aparece en «Habilitados».
5. Revisar email de habilitación (bandeja o consola).
6. Revisar auditoría: Django Admin → Auth audit logs → acción «Veterinario Habilitado».

---

## 4. MV habilitado — Creación de protocolos

1. Iniciar sesión como el MV recién habilitado.
2. Ir a `/protocols/select-type/`.
   - **Esperado:** página de selección HP/CT (sin redirect a pendiente).
3. Crear un protocolo de citología o histopatología (borrador alcanza).
4. Ir a `/accounts/veterinarian/profile/`.
   - **Esperado:** badge «✓ Habilitado».

---

## 5. Búsqueda lab — Solo MV habilitados (punto 7 + 11)

**Preparación:** tener un MV con email verificado pero **sin** habilitar (registrar otro si hace falta).

1. Iniciar sesión como **personal de lab**.
2. Ir a **Cargar protocolo** → `/protocols/lab/create/` (búsqueda de MV).
3. Buscar el MV **habilitado** del paso 4.
   - **Esperado:** aparece en resultados; se puede seleccionar.
4. Buscar el MV **no habilitado** (email verificado, `is_verified=False`).
   - **Esperado:** no aparece en la lista.
5. Texto de ayuda en pantalla menciona «habilitados por un administrador».

---

## 6. Eliminar cuenta sin protocolos (soft delete + anonimización)

1. Registrar un tercer MV, verificar email, completar perfil (sin habilitar).
2. Como admin, en `/dashboard/admin/veterinarians/` → **Eliminar**.
3. Marcar checkbox «Entiendo que no se puede deshacer» → confirmar.
   - **Esperado:** mensaje de éxito; cuenta pasa a «Inactivos».
   - **Esperado:** email de eliminación enviado.
4. Intentar registrar de nuevo con el **mismo email**.
   - **Esperado:** registro permitido (email liberado por anonimización).
5. Auth audit log: acción «Veterinario Eliminado» con email original en `details`.

---

## 7. Eliminar cuenta con protocolos (solo desactivar)

1. Usar el MV habilitado del paso 4 (con al menos un protocolo).
2. Como admin, intentar **Eliminar**.
   - **Esperado:** aviso de que tiene protocolos asociados; email no quedará libre.
3. Confirmar eliminación.
   - **Esperado:** cuenta inactiva; email sin cambiar.
4. Intentar login con ese MV.
   - **Esperado:** login fallido (cuenta inactiva).

---

## 8. Reactivar cuenta eliminada por error

1. En filtro **Inactivos**, localizar MV del paso 7 (con protocolos, no anonimizado).
2. Clic en **Reactivar**.
   - **Esperado:** cuenta activa de nuevo; puede iniciar sesión.
3. Confirmar que cuentas anonimizadas (`*@invalid.local`) **no** muestran reactivar.

---

## 9. Regresión rápida (automática)

```bash
make test-with-sqlite ARGS="accounts.test_veterinarian_approval protocols.test_lab_protocol_create"
```

**Esperado:** todos los tests OK.

---

## Matriz de capas de confianza

| Capa | Campo | Bloquea |
|------|-------|---------|
| Email | `User.email_verified` | Login |
| Perfil | `Veterinarian.is_profile_complete_for_access()` | Uso general (middleware) |
| Habilitación admin | `Veterinarian.is_verified` | Crear protocolos HP/CT; búsqueda lab |

---

## Referencias técnicas

| Componente | Ubicación |
|------------|-----------|
| Mixin gate | `src/accounts/mixins.py` — `VeterinarianApprovedMixin` |
| Filtro lab | `src/protocols/lab_protocol.py` — `get_enabled_veterinarians_queryset()` |
| Servicio admin | `src/accounts/services/veterinarian_approval_service.py` |
| Pantalla contacto | `VeterinarianPendingApprovalSettings` + caché Redis |
| Panel admin | `/dashboard/admin/veterinarians/` |
| Tests | `src/accounts/test_veterinarian_approval.py` |

Guía operativa para administradores: [user-guides/administrators/managing-users.md](../user-guides/administrators/managing-users.md).
