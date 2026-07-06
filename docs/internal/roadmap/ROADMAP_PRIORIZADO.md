# Roadmap Priorizado — AdLab

Documento de trabajo para implementar los cambios acordados con la facultad.  
Los ítems se abordan **en orden de prioridad**; marcar el estado a medida que avancemos.

**Última actualización:** Julio 2026  
**Dominio objetivo:** `patologiavetfcvunl.ar`

---

## Cómo usar este documento

| Estado | Significado |
|--------|-------------|
| ⬜ Pendiente | Aún no iniciado |
| 🔄 En curso | Trabajo activo |
| ✅ Hecho | Implementado y verificado |
| ⏸️ Postergado | Fuera del alcance de esta etapa |
| 🚫 Deshabilitado | Código de dominio conservado; UI/rutas retiradas |

Para cada ítem, anotar en **Notas / PR** el branch, PR o commit cuando corresponda.

---

## 1. Interfaz del Veterinario y Carga de Datos

Prioridad operativa: calidad de datos en origen y experiencia móvil.

> **Plan detallado:** [PLAN_PUNTO_1_VETERINARIO.md](PLAN_PUNTO_1_VETERINARIO.md)  
> **Orden sugerido dentro del bloque:** 1.3 ✅ → 1.2 ✅ → 1.1 ✅

### 1.1 Normalización de campos (Raza y Edad)

- **Estado:** ✅ Hecho (Jun 2026)
- **Objetivo:** Evitar texto libre que ensucie la base de datos.
- **Implementado:**
  - Edad opcional: inputs años + meses → `Protocol.age` compuesto
  - Raza: select por especie (`choices.py`) + `Otra` con texto auxiliar
  - JS mínimo filtra razas al cambiar especie (create/edit)
  - Tests en `protocols/test_age_breed.py`
- **Notas / PR:**

### 1.2 Optimización de notificaciones (móvil)

- **Estado:** ✅ Hecho (Jun 2026; pulido Jul 2026)
- **Objetivo:** Corregir demora y redirección interna al abrir una notificación desde el celular.
- **Implementado:**
  - Login con `?next=` en vista pública de protocolo
  - `AuthenticationService` respeta `next` seguro post-login
  - `link_url` como path relativo + migración de URLs legacy
  - Vista `/notifications/<id>/go/` (marca leída + redirect) en bandeja y campana
- **Pulido posterior (Jul 2026):**
  - Middleware de perfil incompleto **no interfiere** con rutas `/api/` (evitaba HTML en respuestas JSON y rompía la campana / DJDT)
  - APIs de notificaciones devuelven **401 JSON** si no hay sesión
  - Dropdown del navbar: **últimas 5** + enlace a **Central de notificaciones**
- **Diagnóstico:** [NOTIFICATION_DIAGNOSTIC_RESULTS.md](NOTIFICATION_DIAGNOSTIC_RESULTS.md)
- **Notas / PR:**

### 1.3 Validación de tipos de punción (Citología)

- **Estado:** ✅ Hecho (Jun 2026)
- **Objetivo:** Etiqueta **"Punción (PAAF)"** visible en el select de técnica de citología.
- **Implementado:** Choice renombrado, aliases legacy en formularios, migración `0020`.
- **Notas / PR:**

### 1.4 Timeline simplificado para el veterinario + recorte de emails

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** El veterinario no ve hitos internos del lab; solo el progreso que le importa hasta el informe. Menos emails en el camino feliz.
- **Principio:** el modelo `Protocol.Status` **no cambia**. Solo cambia la **presentación** y los canales hacia el veterinario.

#### Estados visibles para el veterinario

| Estado interno | Etiqueta veterinario |
|----------------|----------------------|
| `draft` | Borrador |
| `submitted` | Enviado |
| `received` | Recibido |
| `processing` / `ready` | **En laboratorio** |
| `report_sent` | Informe enviado |
| `rejected` | Rechazado |

#### Implementado

- Badge: `get_veterinarian_status_display` (ya existía).
- Historial colapsado: `build_veterinarian_status_history` / `build_status_history_for_user` en `protocol_detail_context.py`.
- Lab staff: historial completo (`build_staff_status_history`).
- **READY (opción A):** sin email ni in-app al marcar listo para diagnóstico.

#### Recorte de emails (flujo protocolo)

| Momento | Email | In-app |
|---------|-------|--------|
| Enviado (`SUBMITTED`) | No | Sí |
| Recibido (`RECEIVED`) | Sí (discrepancias en el mismo mail si hay) | Sí (body ampliado si hay observaciones) |
| Rechazado | Sí | Sí |
| Listo (`READY`) | No | No |
| Informe disponible | Sí (+ PDF) | Sí |
| Orden de trabajo | No (UI deshabilitada) | No |

Camino feliz: **2 emails** (recepción + informe). Auth (verificación / reset) sin cambios.

#### Áreas del código

- `protocol_detail_context.py`, `protocol_detail.html`, `views.py` (submit / reception)
- `protocol_service.py` (sin notify en READY)
- `emails.py`, `email_service.py`, `sample_reception.html`, `notification_service.py`

---

## 2. Rediseño del Módulo de Laboratorio (Histopatología)

Prioridad operativa: reducir fricción con guantes puestos en el banco.

### 2.1 Simplificación del flujo de estados

- **Estado:** ✅ Hecho (Jun 2026)
- **Objetivo:** Eliminar pantallas y acciones obligatorias de pasos manuales intermedios.
- **Implementado:**
  - Cassettes: un botón **Procesar** colapsa fijación, inclusión y entacado (`mark_processed()`).
  - Slides: un botón **Marcar listo** desde pendiente (`mark_ready_from_pending()`).
  - Timeline simplificado en `protocol_status.html`; sin migración de schema.
- **Áreas del código:** `protocols/models.py`, `protocol_service.py`, templates `_cassette_timeline`, `_slide_timeline`, `_processing_actions`.
- **Notas / PR:** Ver [PLAN_PUNTO_2_LAB_HP.md](PLAN_PUNTO_2_LAB_HP.md).

### 2.2 Unificación de Cassettes y Slides (pantalla única)

- **Estado:** ✅ Hecho (Jun 2026)
- **Objetivo:** Cargar cassettes y slides en un solo paso, con descripción libre por cassette.

#### Sección superior — Cassettes

- Campo libre para listar cassettes y describir qué piezas u órganos contiene cada uno.
- Romper la estructura rígida actual de “superior / inferior”.

#### Sección inferior — Slides (vidrios)

- Multi-select de cassettes por slide; `posicion=COMPLETO` en backend.
- POST atómico en `SampleRegistrationView` (`/processing/register/<pk>/`).

- **Implementado:** `sample_register.html`, redirects desde `cassette_create` / `slide_register`, navegación unificada (**Registrar muestra**).
- **Pulido (Jul 2026):** códigos preview (`HP 26/006-C1`), orden numérico de slides, seeds demo, docs de lab staff.
- **Notas / PR:** Ver [PLAN_PUNTO_2_LAB_HP.md](PLAN_PUNTO_2_LAB_HP.md).

### 2.3 Observaciones por portaobjeto en citología (cierre de banco)

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Anotar observaciones de banco por cada portaobjeto de CT al cerrar el procesamiento, sin edición ni revertir etapas.
- **Implementado:**
  - Solo **citología**; HP sigue con observaciones en **Registrar muestra**.
  - Detalle del protocolo → «Procesamiento de laboratorio»: textarea **opcional por slide** en `received` / `processing`.
  - **Marcar listo para diagnóstico** guarda observaciones en `Slide.observaciones` y cierra el protocolo (`READY`).
  - Campo vacío → no sobrescribe texto previo (p. ej. recepción automática).
  - Tras `READY`: tabla solo lectura.
- **Fuera de alcance:** marcar listo por slide, revertir, calidad/coloración, registro unificado CT.
- **Áreas del código:** `_protocol_processing_section.html`, `ProtocolMarkReadyView`, `mark_ready_for_diagnosis`.
- **Docs:** `processing-samples.md`, `receiving-samples.md`, `complete-sample-journey.md`.

---

## 3. Informes, Formato y Galería

Prioridad operativa: entregables institucionales listos para uso oficial.

> **Nota de alcance (Jul 2026):** el formato institucional del PDF (**3.1**) se implementó con la plantilla Word de la facultad. Los ítems **3.2** y **3.3** ya estaban completos de forma independiente.

### 3.1 Formato y encabezado del PDF

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Reemplazar diseño provisorio por formato legal e institucional definitivo.
- **Implementado:**
  - Banners de encabezado y pie extraídos del Word oficial (`assets/static/images/reports/`)
  - Layout institucional en ReportLab (`report_pdf_builder.py`): HP y CT, secciones RESULTADOS/OBSERVACIONES
  - Mapeo de campos: remisión, material, animal, propietario, MV comitente, fijación, tinción, firma
  - Especificación: `docs/internal/reports/pdf-template-spec.md`
- **Áreas del código:** `report_pdf_builder.py`, `pdf_service.py`, assets estáticos
- **Notas / PR:** Tipografía v1 en Helvetica; Calibri opcional si la facultad lo confirma. Validación visual pendiente con un informe real en prod.

### 3.2 Automatización del nombre del archivo PDF

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Al descargar o guardar el informe final, usar nomenclatura oficial.
- **Formato acordado (provisorio hasta confirmación facultad):** `HP-YY-NNN.pdf` a partir de `protocol_number` (ej. `HP 26/006` → `HP-26-006.pdf`).
- **Implementado:**
  - `Report.generate_pdf_filename()` → `HP-26-006.pdf`
  - Descarga (`ReportPDFView`) y persistencia en storage usan el mismo nombre
- **Áreas del código:** `protocols/models.py`, `views_reports.py`, `pdf_service.py`
- **Notas / PR:** Confirmar con facultad si el formato exacto difiere.

### 3.3 Corrección en la carga de imágenes (galería macro/micro)

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Solucionar demora o falla al adjuntar fotos macro y micro con referencias al final del informe.
- **Implementado:**
  - Embebido en PDF vía PIL (JPEG; soporta WebP/PNG que ReportLab no maneja nativo)
  - Downscale de imágenes grandes al embeber (máx. 1600 px)
  - Validación de payload real de imagen en upload
  - Borrado de archivos en storage al eliminar del formset
- **Áreas del código:** `report_image_service.py`, `pdf_service.py`, `forms_reports.py`
- **Notas / PR:**

---

## 4. Migración al Dominio Final

Prioridad operativa: producción bajo dominio institucional antes de correos y ajustes finales de backend.

> **Confirmado (Jul 2026):** el cambio de dominio sigue previsto y es prioritario una vez cerrados los ítems de informes que no dependen del formato (3.2, 3.3). Requiere DNS y acceso al servidor; no es solo un cambio de código.

### 4.1 Configuración del entorno de producción

- **Estado:** ⬜ Pendiente
- **Objetivo:** Desplegar bajo el dominio definitivo **`patologiavetfcvunl.ar`**.
- **Alcance:**
  - `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, URLs absolutas en emails.
  - Configuración Nginx / reverse proxy.
  - Variables de entorno en servidor.
- **Documentación relacionada:** [production-deployment.md](../deployment/production-deployment.md), [nginx-setup.md](../deployment/nginx-setup.md).
- **Notas / PR:**

### 4.2 Certificados de seguridad (SSL)

- **Estado:** ⬜ Pendiente
- **Objetivo:** HTTPS de punta a punta en el nuevo dominio.
- **Alcance:**
  - Obtener/renovar certificados (Let's Encrypt u otro proveedor institucional).
  - Configurar renovación automática.
  - Forzar redirección HTTP → HTTPS.
- **Documentación relacionada:** [ssl-certificates.md](../deployment/ssl-certificates.md).
- **Notas / PR:**

---

## 5. Infraestructura y Comunicaciones (Sistemas de Correo)

Prioridad operativa: correo institucional operativo con verificación de usuarios validada.

### 5.1 Integración de cuenta Gmail institucional

- **Estado:** ⬜ Pendiente
- **Objetivo:** Configurar casilla institucional (`anatomia.pato...`) para envío automatizado.
- **Alcance:**
  - App Password o OAuth2 según política de Google.
  - Verificación en dos pasos y permisos de seguridad.
  - Variables SMTP en producción (`EMAIL_HOST`, `EMAIL_HOST_USER`, etc.).
- **Documentación relacionada:** [email-setup.md](../configuration/email-setup.md), Step 13 en archivo histórico.
- **Notas / PR:**

### 5.2 Flujo de verificación de usuarios (veterinarios externos)

- **Estado:** ⬜ Pendiente
- **Objetivo:** Confirmar que veterinarios externos **deben verificar email** antes de habilitar su perfil.
- **Alcance:**
  - Validar bloqueo de login sin verificación.
  - Probar registro → email → activación → acceso completo.
  - Revisar mensajes y tiempos de expiración de token (24 h).
- **Áreas probables del código:** `accounts/views.py`, `User.email_verified`, templates de verificación.
- **Notas / PR:**

---

## 6. Módulos deshabilitados / postergados

### 6.1 Órdenes de Trabajo y Finanzas

- **Estado:** 🚫 Deshabilitado en UI (Jul 2026) — modelos conservados
- **Decisión:** La facultad **no usará** órdenes de trabajo en esta etapa. Se retira la funcionalidad de la interfaz y las rutas HTTP; **no se eliminan modelos ni migraciones** (reactivación futura sin pérdida de datos).
- **Qué se retira:**
  - Rutas `/workorders/...` (no registradas en `urls.py`)
  - Enlaces en dashboards (lab staff y veterinario)
  - Acciones en detalle de protocolo (“Ver orden…”, “Agregar a orden…”)
  - Opción “Incluir orden de trabajo” al enviar informe
- **Qué se conserva:**
  - Modelos `WorkOrder`, `WorkOrderService`, `WorkOrderCounter`, `PricingCatalog`
  - Servicios, formularios y vistas en código (`views_workorder.py`, etc.) para reactivación
  - Tests de modelo/servicio (no de vistas HTTP)
  - Admin de Django (acceso técnico interno)
- **No se usa** feature flag por env var: deshabilitación simple por ausencia de URLs y de enlaces en plantillas.
- **Incluye (congelado para el futuro):**
  - Gestión de aranceles
  - Cálculo automático según cantidad de piezas/materiales
  - Saldos pendientes
  - Emisión de resúmenes de cuenta
- **Notas / PR:**

---

## Orden sugerido de implementación

```
1 ✅ → 2 ✅ → 3.1 + 3.2 + 3.3 ✅ → 4 → 5 → (6.1 reactivar si la facultad lo pide)
```

| # | Bloque | Ítems | Dependencias clave |
|---|--------|-------|-------------------|
| 1 | Veterinario / datos | 1.1–1.3 ✅, 1.4 menor | Ninguna crítica |
| 2 | Laboratorio HP | 2.1 ✅, 2.2 ✅ | Implementado Jun–Jul 2026 |
| 3 | Informes / PDF | 3.1, 3.2, 3.3 ✅ | Formato facultad aplicado Jul 2026 |
| 4 | Dominio / SSL | 4.1, 4.2 | Servidor y DNS listos |
| 5 | Correo / auth | 5.1, 5.2 | Dominio (4) recomendado para links en emails |
| 6 | Finanzas / OT | 6.1 🚫 UI off | Modelos intactos |

---

## Registro de sesiones de trabajo

Usar esta sección para anotar qué ítem se tomó en cada sesión.

| Fecha | Ítem | Resultado |
|-------|------|-----------|
| Jun 2026 | 2.1, 2.2 | Rediseño Lab HP: etapas colapsadas + registro unificado |
| Jun–Jul 2026 | 1.2 (pulido) | Fix campana/API JSON (middleware perfil incompleto); dropdown últimas 5 + central |
| Jul 2026 | Roadmap | Documentar dominio (4), deshabilitar OT (6.1), informes sin formato (3.2–3.3; 3.1 espera facultad) |
| Jul 2026 | 3.2, 3.3, 6.1 | Implementación: nombre PDF, galería imágenes, retiro UI de órdenes de trabajo |
| Jul 2026 | 1.4 | Timeline vet “En laboratorio”; recorte emails (READY off, submit in-app only, discrepancias en recepción) |
| Jul 2026 | 2.3 | Observaciones CT por portaobjeto al marcar listo para diagnóstico |
| Jul 2026 | Bloque 1 (verif. local) | 1.1–1.4 probados OK en entorno local |
| Jul 2026 | Bloque 2 (verif. local) | 2.1 HP, 2.2 registro unificado, 2.3 observaciones CT probados OK |
| Jul 2026 | Bloque 3 (verif. local) | 3.2 nombre PDF, 3.3 imágenes en PDF, envío al vet probados OK |
| Jul 2026 | 3.1 | Formato institucional PDF (banners Word, layout HP/CT, RESULTADOS/OBSERVACIONES) |

---

## Referencias

- [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) — estado general del sistema
- [CLAUDE.md](../../../CLAUDE.md) — arquitectura y comandos de desarrollo
- [REPORT_WORKFLOW_AND_SIGNATURE.md](../REPORT_WORKFLOW_AND_SIGNATURE.md) — flujo de informes
- [production-deployment.md](../deployment/production-deployment.md) — despliegue
- [email-setup.md](../configuration/email-setup.md) — configuración SMTP
