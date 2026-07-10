# Plan de implementación — Punto 7: Carga de protocolos por Personal de Laboratorio

Addenda acordada **post-reunión** (Jul 2026). Complementa [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md).

**Estado general del bloque:** ✅ Hecho (Jul 2026)  
**Última revisión:** Julio 2026

> **Nota (punto 11):** el filtro de búsqueda lab exige también `Veterinarian.is_verified=True` (implementado Jul 2026). Ver [PLAN_PUNTOS_11_12.md](PLAN_PUNTOS_11_12.md) y [VETERINARIAN_APPROVAL_TESTING.md](../VETERINARIAN_APPROVAL_TESTING.md).

> Otros pedidos de la misma reunión (categoría animal, portaobjetos, imágenes PDF) están en [PLAN_PUNTOS_8_9_10.md](PLAN_PUNTOS_8_9_10.md) como **puntos 8, 9 y 10** del roadmap.

---

## Contexto

En la **fase piloto**, la facultad quiere operar el sistema con el **personal de laboratorio** cargando protocolos **a nombre del veterinario comitente**, antes de abrir el uso cotidiano a veterinarios externos.

Objetivo operativo: cuando llega una muestra (protocolo en papel o datos por otro canal), el lab la ingresa al sistema sin depender de que el MV haya creado el protocolo online.

El veterinario comitente:

- **Debe existir** previamente en el sistema.
- **No opera** el sistema en esta etapa (no carga ni sigue casos).
- **Debe poder recibir el informe por email** (canal de comunicación principal).

---

## Resumen ejecutivo

| Ítem | Complejidad | Estimación | Estado |
|------|-------------|------------|--------|
| 7.1 Carga delegada por lab (MVP) | Media–Alta | 2–4 días | ✅ Hecho |

**Orden sugerido:** 7.1 como PR único o 7.1a (búsqueda + create) + 7.1b (acciones lab en detalle).

---

## Decisiones acordadas

| Tema | Decisión |
|------|----------|
| Veterinario comitente | **Debe existir** antes de cargar el protocolo; no alta rápida desde lab en v1 |
| Paso previo | **Búsqueda** de veterinarios existentes (nombre, apellido, matrícula, email) |
| Email habilitado | MV con **`User.email_verified=True`**, **`User.is_active=True`** y **`Veterinarian.is_verified=True`** (habilitado por admin) |
| Flujo de estados | **Opción A:** borrador → enviar → recepcionar (igual que hoy; el lab hace los pasos iniciales) |
| Rol histopatólogo | **Fuera de alcance** funcional (legacy en código; no diseñar para ese rol) |
| Quién puede cargar | **`PERSONAL_LAB`**; **admin** también vía `User.is_lab_staff` (patrón actual del sistema) |
| Registro público MV | **No cerrar** por ahora — el enlace de registro sigue disponible |
| Comunicación con MV | Email verificado = canal confiable para informe (y recepción si aplica) |
| Perfil completo MV | **No requerido** para aparecer en búsqueda ni para recibir informe; solo verificación de email |

### Admin vs personal de lab

- Cada usuario tiene **un solo rol** (`ADMIN`, `PERSONAL_LAB`, etc.).
- `User.is_lab_staff` incluye `PERSONAL_LAB`, `HISTOPATOLOGO` (legacy) **y** `ADMIN`.
- Por coherencia con recepción/procesamiento, **admin puede cargar protocolos** sin perfil `LaboratoryStaff`.
- Si en el futuro se quisiera restringir solo a `PERSONAL_LAB`, habría que cambiar el mixin (hoy no aplica).

---

## Situación actual en código

| Capacidad | Veterinario | Personal de lab |
|-----------|-------------|-----------------|
| Crear protocolo (HP/CT) | ✅ | ❌ (`VeterinarianProfileRequiredMixin`) |
| Editar borrador | ✅ Propio | ✅ (`ProtocolOwnerOrStaffMixin`) |
| Enviar borrador | ✅ Propio | ✅ (`ProtocolOwnerOrStaffMixin`) |
| Recepcionar | ❌ | ✅ |
| Procesar / informar | ❌ | ✅ |

Cada `Protocol` tiene FK obligatorio a `Veterinarian`. **`Protocol.created_by`** audita quién del lab cargó el caso (migración `0022`).

Vistas de creación delegada: `/protocols/lab/create/…` (`LabProtocolVeterinarianSearchView`, etc.).

---

## 7.1 Carga delegada por lab — ✅ Hecho (Jul 2026)

### Implementado

- `Protocol.created_by` (FK `User`, null=True) — migración `0022_protocol_created_by.py`
- `protocols/lab_protocol.py` — búsqueda y sesión de MV seleccionado
- Vistas: `LabProtocolVeterinarianSearchView`, `LabProtocolSelectTypeView`, `LabProtocolCreateCytologyView`, `LabProtocolCreateHistopathologyView`
- Rutas `/protocols/lab/create/…`
- Dashboard lab: acción **«Cargar protocolo»** (`dashboard_lab_staff.html`)
- Lab puede editar/enviar borradores (`ProtocolOwnerOrStaffMixin`); historial con descripción «Cargado por personal de laboratorio»
- Tests: `protocols/test_lab_protocol_create.py`
- Filtro: `user__is_active=True`, `user__email_verified=True`, `is_verified=True`

### Flujo UX objetivo

```
Panel de Laboratorio
  └─ [Cargar protocolo]
       └─ Buscar veterinario comitente *
            └─ Solo MV habilitados por admin (email verificado + is_verified)
       └─ Elegir tipo (HP / CT)
       └─ Formulario actual (mismos campos que el MV)
            └─ [Guardar borrador]
            └─ [Enviar protocolo]     → código temporal
       └─ [Recepcionar muestra]      → flujo actual de recepción
       └─ … procesamiento → informe → email al MV
```

\* Si el MV no aparece: debe darse de alta y **verificar email** antes (admin o registro público).

### Filtro “email habilitado” (búsqueda)

```python
Veterinarian.objects.filter(
    user__is_active=True,
    user__email_verified=True,
).exclude(email="")
```

Búsqueda por: `first_name`, `last_name`, `license_number`, `email` (icontains).

Mostrar en resultados: nombre, matrícula, email (parcial enmascarado opcional).

### Alcance técnico

#### Modelo

| Cambio | Motivo |
|--------|--------|
| `Protocol.created_by` (FK `User`, null=True, blank=True) | Auditoría: quién del lab cargó el protocolo |
| Migración | Campo nuevo |

Opcional futuro: `Protocol.entry_source` (`veterinarian` / `lab_staff`) para reportes.

#### Permisos

- Nuevo mixin o reutilizar `StaffRequiredMixin` en vistas de creación lab.
- Veterinario seleccionado vía sesión o URL firmada tras búsqueda (no desde POST libre).

#### Vistas y URLs (propuesta)

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/protocols/lab/create/` | `LabProtocolVeterinarianSearchView` | Búsqueda y selección de MV |
| `/protocols/lab/create/select-type/` | `LabProtocolSelectTypeView` | HP o CT (MV en sesión) |
| `/protocols/lab/create/cytology/` | `LabProtocolCreateCytologyView` | Form CT |
| `/protocols/lab/create/histopathology/` | `LabProtocolCreateHistopathologyView` | Form HP |

Reutilizar `CytologyProtocolForm`, `HistopathologyProtocolForm`, `protocol_form.html`.

En `form_valid`: `form.save(veterinarian=selected_vet)`, `protocol.created_by = request.user`.

#### UI

- Dashboard lab (`dashboard_lab_staff.html`): tarjeta **“Cargar protocolo”**.
- Detalle protocolo: badge **“Cargado por laboratorio”** si `created_by` es lab staff.
- Acciones lab en borrador: **Editar** y **Enviar** (hoy solo en bloque vet si `owns_protocol`).
- Historial de estados: descripción “Cargado por personal de laboratorio” / “Enviado por personal de laboratorio”.

#### Notificaciones y emails

| Momento | Comportamiento piloto |
|---------|----------------------|
| Envío (`SUBMITTED`) | In-app al MV si cuenta usable; no bloquear flujo |
| Recepción | Email según preferencias (`notify_on_reception`) |
| Informe listo | **Siempre** a `NotificationPreference.get_recipient_email()` (MV verificado) |

El informe **no depende** de que el MV haya completado perfil ni de que entre al sistema.

#### Alta de veterinarios piloto (operativa, fuera del código 7.1)

1. Registro público o alta admin.
2. MV recibe mail de verificación y **hace clic en el link**.
3. Queda `email_verified=True` → aparece en búsqueda del lab.
4. Lab carga protocolos a su nombre.

---

## Fuera de alcance (v1 / 7.1)

- Alta de veterinario desde pantalla del lab
- Flujo unificado “recepción + carga” en un solo paso
- Deshabilitar registro público de veterinarios
- Cambios al rol histopatólogo
- Exigir perfil completo del MV para carga delegada

---

## Dependencias

| Dependencia | Motivo |
|-------------|--------|
| **5.1 SMTP operativo** | Verificación de email de MV y envío de informes |
| Veterinarios precargados + verificados | Sin MV en búsqueda no hay carga delegada |

Orden sugerido en roadmap: **7.1 puede planificarse en paralelo a 5.1**, pero **probar en prod** requiere correo.

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| MV incorrecto seleccionado | Búsqueda clara (nombre + matrícula + email); confirmación antes de enviar |
| MV sin email verificado | Filtro estricto en búsqueda; mensaje “debe verificar email” |
| Confusión acciones vet vs lab | Mantener bloques separados en `_protocol_detail_actions.html` |
| Sin auditoría | `created_by` + `ProtocolStatusHistory` |
| Duplicar lógica de forms | Un solo `save(veterinarian=…)`; vistas paralelas solo cambian origen del MV |

---

## Tests mínimos

- Lab staff: búsqueda solo devuelve MV con `email_verified=True`
- MV no verificado no aparece en búsqueda
- Lab crea HP/CT → `protocol.veterinarian` correcto, `created_by` = lab user
- Lab edita y envía borrador → código temporal generado
- Recepción posterior OK
- Informe final → email a `veterinarian.email` con MV verificado
- Veterinario no accede a URLs `/protocols/lab/create/…`
- Admin puede cargar protocolo (vía `is_lab_staff`)

---

## Archivos probables

| Archivo | Cambio |
|---------|--------|
| `protocols/models.py` | `Protocol.created_by` |
| `protocols/views.py` | Vistas lab create + búsqueda |
| `protocols/urls.py` | Rutas `/lab/create/…` |
| `protocols/forms.py` | Form búsqueda MV (opcional) |
| `protocols/protocol_detail_context.py` | Acciones editar/enviar para lab en borrador |
| `protocols/templates/…` | Búsqueda, badge, dashboard |
| `pages/templates/pages/dashboard_lab_staff.html` | Acción rápida |
| `protocols/tests.py` o `test_lab_protocol_create.py` | Tests del flujo |

---

## Referencias

- [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md) — bloque 7
- [PLAN_PUNTOS_8_9_10.md](PLAN_PUNTOS_8_9_10.md) — otros pedidos post-reunión
- [PLAN_PUNTO_1_VETERINARIO.md](PLAN_PUNTO_1_VETERINARIO.md) — flujo original MV
- [email-setup.md](../configuration/email-setup.md) — SMTP para verificación e informes
