# Guía para Gestionar Usuarios - Administradores

Esta guía explica cómo los administradores crean y gestionan cuentas de usuario en el sistema.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

---

## Resumen de roles

| Rol | Código | Alta en el sistema | Verificación de email |
|-----|--------|--------------------|------------------------|
| Veterinario | `VETERINARIO` | Autoregistro en `/accounts/register/` | Obligatoria |
| Personal de laboratorio | `PERSONAL_LAB` | Solo administrador (flujo unificado) | Obligatoria |
| Histopatólogo (legacy) | `HISTOPATOLOGO` | Sin altas nuevas; cuentas existentes | No requerida |
| Administrador | `ADMIN` | Django Admin o superusuario | No requerida |

---

## Crear personal de laboratorio (flujo unificado)

Desde julio 2026, **todos los usuarios internos de laboratorio** (técnicos, patólogos, personal con informes) se crean con un único formulario. El alta antigua de «Histopatólogo» quedó **deprecada** y redirige automáticamente al flujo nuevo.

### Dónde acceder

1. Iniciar sesión como **administrador**
2. Ir al **Panel de Administración** (`/dashboard/admin/`)
3. En **Gestión de Usuarios**, elegir **Crear Personal de Laboratorio**

También puede abrirse directamente: `/accounts/lab-staff/create/`

_[Espacio para captura de pantalla: Tarjeta «Crear Personal de Laboratorio» en el panel admin]_

### Datos del formulario

**Cuenta de acceso**

- Email (será el usuario de login)
- Nombre y apellido
- Contraseña inicial (mínimo 8 caracteres; compartirla de forma segura con el empleado)

**Perfil profesional**

- Número de matrícula (único en el sistema)
- Cargo y especialidad (opcionales)
- Teléfono (opcional)
- Firma digital (opcional en el alta; ver más abajo)

**Permisos**

| Campo | Efecto |
|-------|--------|
| **Puede crear informes** | Habilita cola de informes, elaboración, firma en PDF y enlace **Reportes** en la barra superior |
| **Acceso a órdenes de trabajo y panel admin** | Activa `is_staff` en Django (órdenes de trabajo y acceso al admin de Django) |

Por defecto, **Puede crear informes** viene desactivado: el empleado puede hacer recepción y procesamiento; el admin debe marcarlo si también elaborará informes.

### Qué hace el sistema al guardar

1. Crea el usuario con rol `PERSONAL_LAB`, activo y **email sin verificar**
2. Crea el perfil `LaboratoryStaff` vinculado
3. Envía un **email de verificación** al empleado (enlace válido 24 horas)
4. Registra el alta y el envío del email en el **log de auditoría** (`AuthAuditLog`)
5. Redirige al listado de personal de laboratorio en Django Admin

Si el envío de email falla (SMTP no configurado), la cuenta se crea igual; el admin debe reenviar la verificación desde Django Admin.

_[Espacio para captura de pantalla: Formulario de alta unificada de personal de laboratorio]_

---

## Primer ingreso del empleado

Flujo que debe completar el nuevo usuario:

```
1. Recibir email → Verificar cuenta (clic en el enlace)
2. Iniciar sesión con email y contraseña
3. Cargar firma digital (obligatorio en el primer ingreso)
4. (Opcional) Cambiar contraseña desde Perfil
5. Si tiene «Puede crear informes»: usar Reportes en el menú superior
```

### Verificación de email

- Sin verificar el email, **no puede iniciar sesión** (rol `PERSONAL_LAB`)
- Si el enlace expiró: pantalla de login → **Reenviar verificación**
- Los histopatólogos legacy (`HISTOPATOLOGO`) y administradores **no** requieren este paso

### Firma digital obligatoria

Todo el personal de laboratorio debe subir su firma en el **primer ingreso**, aunque no elabore informes. El sistema redirige automáticamente a `/accounts/lab-staff/signature/` hasta completar este paso.

- El administrador puede **pre-cargar la firma** en el formulario de alta (campo opcional)
- Si no se precarga, el empleado la sube en el primer acceso
- Para elaborar informes además se necesita el permiso **Puede crear informes**

Ver: [Firma digital para personal de laboratorio](../lab-staff/digital-signature.md)

---

## Crear veterinarios

Los veterinarios se registran solos:

1. Página pública **Registrarse** (`/accounts/register/`)
2. Completan datos profesionales y verifican el email
3. Completan el perfil veterinario en el primer acceso si falta información

El administrador puede revisar o editar cuentas en Django Admin → Usuarios / Veterinarios.

---

## Gestionar usuarios existentes

### Django Admin

- **Usuarios** (`/admin/accounts/user/`): activar/desactivar, roles, reenvío de verificación
- **Personal de laboratorio** (`/admin/accounts/laboratorystaff/`): permisos, firma, matrícula
- **Histopatólogos** (`/admin/accounts/histopathologist/`): solo cuentas legacy; **no** permite altas nuevas

### Edición habitual

- Activar o quitar **Puede crear informes** según las funciones del empleado
- Otorgar **Acceso staff** solo a quien gestione órdenes de trabajo o el admin de Django
- Desactivar cuentas de personal que ya no trabaja en el laboratorio (`is_active` en usuario o perfil)

---

## Histopatólogo (rol legacy)

| Situación | Acción recomendada |
|-----------|-------------------|
| Usuario histopatólogo **existente** | Sigue operando; el sistema migra el perfil a `LaboratoryStaff` cuando hace falta |
| **Nuevo** empleado con funciones de patología | Usar **Crear Personal de Laboratorio** y marcar **Puede crear informes** |
| URL antigua `/accounts/histopathologist/create/` | Redirige al formulario unificado |

---

## Seguridad y buenas prácticas

- Verificar la identidad del empleado antes de crear la cuenta
- Asignar el mínimo de permisos necesarios (`can_create_reports`, `is_staff`)
- Usar contraseñas iniciales fuertes y pedir cambio en el primer ingreso
- Revisar periódicamente cuentas activas y permisos
- Confirmar que el SMTP de producción esté configurado antes de dar de alta usuarios (ver [Configuración de email](../../internal/configuration/email-setup.md))

### Auditoría

Todas las altas y envíos de verificación quedan en **AuthAuditLog** con IP y agente de usuario, consultable desde Django Admin.

---

## Protocolos rechazados

- Ver lista de protocolos con muestras rechazadas
- Reenviar protocolos si hubo error en la evaluación inicial
- Auditoría del historial de estados

*Ver: [Gestionar protocolos rechazados](managing-rejected-protocols.md)*

---

## Referencias técnicas (desarrolladores)

- Vista: `CreateLaboratoryStaffView` — ruta `accounts:create_laboratory_staff`
- Formulario: `LaboratoryStaffCreationForm`
- Middleware: `LabStaffSignatureRequiredMiddleware`
- Documentación interna: [Informes, permisos y firma](../../internal/REPORT_WORKFLOW_AND_SIGNATURE.md)

---

*Siguiente: [Configurar sistema](system-settings.md)*
