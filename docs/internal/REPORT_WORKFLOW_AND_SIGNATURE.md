# Informes patológicos: flujo en UI, permisos y firma digital

Documentación técnica de las mejoras en **Step 06** (generación de informes) desplegadas en `main` a partir de mayo 2026.

Commits de referencia:

- `55d7f86` — bloque «Informe patológico» en detalle de protocolo y estado de procesamiento
- `0eb3c69` — firma digital obligatoria para elaborar/finalizar/descargar PDF

---

## Resumen funcional

| Capa | Comportamiento |
|------|----------------|
| **Rol** | `personal_lab` o `histopatologo` (y admin como lab staff) acceden a recepción/procesamiento |
| **Permiso** | `LaboratoryStaff.can_create_reports` («Puede crear informes») habilita el flujo de informes |
| **Firma** | `LaboratoryStaff.signature_image` obligatoria **antes** de crear, finalizar, **enviar** o generar PDF |
| **Responsable del informe** | FK `Report.laboratory_staff` (profesional que firma el PDF; se asigna a quien finaliza) |

El rol **no** implica automáticamente informes ni firma: el admin configura perfil + permisos en Django Admin.

**Admin:** también debe tener firma digital cargada antes de enviar un informe. Si aún no tiene fila `LaboratoryStaff`, el sistema la crea al abrir `/accounts/lab-staff/signature/` y exige la imagen **antes** de mostrar el formulario de envío (no después del email).

---

## Acciones en detalle de protocolo y procesamiento

### Context builder

`src/protocols/protocol_detail_context.py`:

- `build_protocol_report_action_context()` — flags del bloque de informe
- `build_protocol_detail_action_context()` — acciones de laboratorio + veterinario + informe

### Plantillas

| Plantilla | Uso |
|-----------|-----|
| `_protocol_report_workflow.html` | Card «Informe patológico» (CTA principal, cola pendiente, PDF) |
| `_protocol_detail_actions.html` | Acciones de lab y vet |
| `protocol_detail.html` | Incluye ambos bloques si aplica |
| `processing/protocol_status.html` | Mismo bloque de informe + enlace «Ver protocolo» |
| `_protocol_report_images_preview.html` | Miniatura de imágenes en detalle de protocolo / procesamiento |
| `reports/protocol_images_gallery.html` | Galería completa (`/protocols/<id>/informe/imagenes/`) |
| `reports/protocol_image_detail.html` | Detalle de una imagen con navegación anterior/siguiente |

### Imágenes microscópicas (ReportImage)

- Modelo `ReportImage` con `ImageField` → almacenamiento en **default storage** (Garage/S3 en producción, `media/` en local).
- Subida en **editar informe** (`ReportEditView` + `ReportImageFormSet`, `enctype="multipart/form-data"`).
- Inclusión en el **PDF** al finalizar (misma generación que `persist_report_pdf`).
- Visualización desde **detalle de protocolo** (preview + enlace a galería) y desde **informe** / acciones laterales.
- Permisos: personal de lab ve imágenes en borrador; veterinario solo en informes `finalized` / `sent` de sus protocolos.

#### Proxy Django (obligatorio en producción)

Garage **no** está expuesto como dominio público. Nunca usar `image.url` en templates: con `USE_S3_STORAGE` eso genera URLs internas del estilo `http://garage:3900/adlab-media/...` que el navegador no puede abrir.

El archivo se sirve **solo** vía proxy autenticado:

| Ruta | Nombre |
|------|--------|
| `/protocols/<pk>/informe/imagenes/` | `protocols:protocol_report_images` |
| `/protocols/<pk>/informe/imagenes/<image_pk>/` | `protocols:protocol_report_image_detail` |
| `/protocols/<pk>/informe/imagenes/<image_pk>/archivo/` | `protocols:protocol_report_image_file` |

- Vista: `ProtocolReportImageFileView` (`views_reports.py`)
- Helper de URL: `ReportImage.get_file_url()` (usar en templates en lugar de `image.url`)
- Autorización: `user_can_view_report_images` (owner vet + lab staff + admin)
- El PDF ya usa el mismo patrón (`FileResponse` + `default_storage.open`)

Tests locales: `make test-with-sqlite ARGS="protocols.tests_report_images protocols.tests_protocol_detail_context"`.

### Cuándo se muestra el bloque de informe

- Usuario lab staff con `can_create_reports=True`
- Protocolo en `ready` o `report_sent`, **o** ya existe un informe
- Si falta firma del usuario actual: aviso ámbar con enlace a carga de firma (sin CTAs de elaboración)

### CTAs principales (según estado)

| Estado | Acción principal |
|--------|------------------|
| `ready`, sin informe | Elaborar informe → `protocols:report_create` |
| Informe `draft` | Continuar elaboración → `protocols:report_edit` |
| Informe `finalized` | Enviar al veterinario → `protocols:report_send` |
| Informe existente | Ver informe → `protocols:report_detail` |

---

## Firma digital obligatoria

### URL de carga

- **Ruta:** `/accounts/lab-staff/signature/`
- **Nombre:** `accounts:lab_staff_signature`
- **Vista:** `LabStaffSignatureView` (`src/accounts/views.py`)
- **Formulario:** `LaboratoryStaffSignatureForm` (`src/accounts/forms.py`)

### Redirección automática

`ReportSignatureRequiredMixin` (`src/accounts/mixins.py`) se aplica a:

- `ReportPendingListView`
- `ReportHistoryView`
- `ReportCreateView`
- `ReportEditView`
- `ReportFinalizeView`
- `ReportSendView`

Además, `ReportSendView.dispatch` (y `form_valid`) vuelven a exigir, **antes** de cualquier envío:

1. Firma del usuario actual (`user_requires_report_signature`, incluye **admin**)
2. Informe finalizado
3. Firmante del informe con firma (`report.signer_has_signature()`)

Si falta la firma del usuario, redirige a `/accounts/lab-staff/signature/?next=…` (no se muestra el formulario de email).

`ReportPDFView` valida firma del usuario lab staff en `dispatch` y del **firmante asignado** al informe en `get` (con serve desde storage si el PDF ya está persistido).

### Helpers

`src/accounts/report_access.py`:

- `get_laboratory_staff_for_reports(user)` — consulta directa a `LaboratoryStaff` (evita conflictos con properties de `User`)
- `get_or_create_laboratory_staff_profile(user)` — crea perfil desde histopatólogo legacy o stub para **admin**
- `get_report_finalizer_staff(user)` — perfil que se asigna como firmante al finalizar
- `user_requires_report_signature(user)` — `True` si lab con permiso de informes (o admin) no tiene imagen de firma
- Mensajes en español para UI y redirects

### PDF (`pdf_service.py`)

- `report.get_signer()` — `laboratory_staff` o `histopathologist` legacy
- `report.signer_has_signature()` — usa `has_signature()` del perfil
- Sin firmante o sin firma → `PDFGenerationError` (mensaje en español, sin `AttributeError`)

### Creación de informe (`report_service.py`)

- `create_report()` exige `LaboratoryStaff` con `has_signature()`
- Asigna `Report.laboratory_staff` desde el formulario (campo obligatorio en `ReportCreateForm`)
- Validación en `clean_laboratory_staff()` del formulario

### Fix de perfil (`User.laboratory_staff_profile`)

La property ahora resuelve con `LaboratoryStaff.objects.filter(user=self).first()` en lugar de un accessor incorrecto (`self.laboratory_staff`), que podía dejar informes sin responsable asignado.

---

## Matriz de permisos (referencia rápida)

| Usuario | Recepción / procesamiento | Ver bloque informe | Crear/editar / enviar | PDF / finalizar |
|---------|---------------------------|--------------------|------------------------|-----------------|
| Vet dueño | No | No (ve sus informes finalizados) | No | Descarga si finalizado (+ PDF o firmante OK) |
| Lab sin `can_create_reports` | Sí | Mensaje gris (permiso) | No | No |
| Lab con permiso, sin firma | Sí | Aviso «Cargar firma» | Redirect a firma **antes** de la acción | Redirect / error |
| Lab con permiso y firma | Sí | Bloque completo | Sí | Sí |
| Admin sin firma | Sí (sin onboarding middleware) | Depende del perfil | **Redirect a firma antes de enviar/finalizar** | Redirect a firma |
| Admin con firma | Sí | Igual que lab con perfil | Sí | Sí |

**Órdenes de trabajo:** siguen requiriendo `User.is_staff=True` además del rol; no dependen de la firma de informes.

---

## Administración en Django Admin

### Alta unificada de personal (julio 2026)

| Componente | Ubicación |
|------------|-----------|
| Formulario web | `CreateLaboratoryStaffView` → `/accounts/lab-staff/create/` |
| Redirect legacy | `/accounts/histopathologist/create/` → 301 al formulario unificado |
| Admin add histopatólogo | `HistopathologistAdmin.has_add_permission = False` |
| Éxito del alta | Redirect a `admin:accounts_laboratorystaff_changelist` |

El formulario `LaboratoryStaffCreationForm` crea `User` (`PERSONAL_LAB`, `email_verified=False`) + `LaboratoryStaff`, envía verificación por email y registra `USER_CREATED` / `EMAIL_VERIFICATION_SENT` en `AuthAuditLog`.

**Login:** `PERSONAL_LAB` requiere `email_verified=True` (`User.can_login()`).

**Firma:** `LabStaffSignatureRequiredMiddleware` redirige a `/accounts/lab-staff/signature/` para todo lab staff sin imagen de firma (no solo quienes crean informes).

Guía de usuario: [Gestionar usuarios](../user-guides/administrators/managing-users.md).

### Permisos en perfiles existentes

1. **Usuarios** → rol `personal_lab` / `histopatologo` (solo legacy)
2. **Personal de laboratorio** (`LaboratoryStaff`):
   - `can_create_reports` — habilita informes y enlace **Reportes** en navbar
   - `signature_image` — puede subirse desde admin o el usuario desde `/accounts/lab-staff/signature/`
   - `is_active` — debe estar activo
3. **Grant staff** en el formulario de alta → `User.is_staff` (órdenes de trabajo)

Migración histórica `0008_migrate_histopathologists_to_laboratory_staff` creó perfiles unificados con `can_create_reports=True` para histopatólogos existentes.

---

## Tests

| Archivo | Cobertura |
|---------|-----------|
| `accounts/tests_report_access.py` | Firma obligatoria, formulario, PDF sin firmante |
| `protocols/tests_protocol_detail_context.py` | Contexto del bloque de informe (con firma en setUp) |
| `protocols/tests.py` (`ReportViewsTest`) | Vistas de informe con `laboratory_staff` y firma |

Ejecutar:

```bash
make test-with-sqlite ARGS="accounts.tests_report_access protocols.tests_protocol_detail_context protocols.tests.ReportViewsTest"
```

---

## Despliegue en producción

Tras `git pull` y rebuild de contenedores:

1. Personal con permiso de informes **sin firma** será redirigido al cargar la firma la primera vez que intente elaborar un informe.
2. Informes antiguos **sin** `laboratory_staff` asignado: editar responsable en admin o reasignar desde el formulario de edición; el PDF fallará con mensaje claro hasta corregirlo.
3. Verificar en admin que cada histopatólogo activo tenga registro `LaboratoryStaff` + firma cargada.

---

## Documentación de usuario relacionada

- [Firma digital (personal de lab)](../user-guides/lab-staff/digital-signature.md)
- [Creación de informes (histopatólogos)](../user-guides/histopathologists/creating-reports.md)
- [Problemas comunes — PDF de informes](../troubleshooting/common-issues.md)
