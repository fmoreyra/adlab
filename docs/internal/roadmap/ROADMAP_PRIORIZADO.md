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

> **Cerrado (Jul 2026):** dominio **`patologiavetfcvunl.ar`** y SSL operativos en producción.

### 4.1 Configuración del entorno de producción

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Desplegar bajo el dominio definitivo **`patologiavetfcvunl.ar`**.
- **Implementado:**
  - `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, URLs absolutas en emails.
  - Configuración Nginx / reverse proxy.
  - Variables de entorno en servidor.
- **Documentación relacionada:** [production-deployment.md](../deployment/production-deployment.md), [nginx-setup.md](../deployment/nginx-setup.md).
- **Notas / PR:**

### 4.2 Certificados de seguridad (SSL)

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** HTTPS de punta a punta en el nuevo dominio.
- **Implementado:**
  - Certificados y renovación automática.
  - Redirección HTTP → HTTPS.
- **Documentación relacionada:** [ssl-certificates.md](../deployment/ssl-certificates.md).
- **Notas / PR:**

---

## 5. Infraestructura y Comunicaciones (Sistemas de Correo)

Prioridad operativa: correo operativo en producción; luego migrar a casilla institucional definitiva.

### 5.1 Integración de cuenta Gmail (arranque) + migración institucional (luego)

- **Estado:** ⬜ Pendiente de configurar (credenciales en próxima reunión) / ⏸️ migración institucional diferida
- **Decisión (Jul 2026):** por ahora se usará una **casilla Gmail** vía SMTP (App Password + 2FA) para desbloquear envíos reales. **No es la solución definitiva.**
- **Arranque (próxima reunión — pedir):**
  - Dirección de la casilla Gmail y App Password.
  - Confirmación de 2FA activada.
  - Variables SMTP en producción: `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=true`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- **Deuda técnica / riesgos a resolver luego:**
  - Cuotas diarias bajas de Gmail (límites de envío).
  - Deliverabilidad y reputación (From `@gmail.com` vs dominio institucional).
  - Sin panel de bounces/complaints; frágil ante cambios de política Google.
  - Migrar a casilla **institucional UNL** o SMTP autenticado en `patologiavetfcvunl.ar` (cambio principalmente de variables `EMAIL_*`; el código ya lo soporta).
- **Documentación relacionada:** [email-setup.md](../configuration/email-setup.md), Step 13 en archivo histórico.
- **Notas / PR:** Dejar explícito en producción que el SMTP Gmail es **provisorio**.

### 5.2 Flujo de verificación de usuarios (veterinarios externos)

- **Estado:** ⬜ Pendiente
- **Objetivo:** Confirmar que veterinarios externos **deben verificar email** antes de habilitar su perfil.
- **Alcance:**
  - Validar bloqueo de login sin verificación.
  - Probar registro → email → activación → acceso completo.
  - Revisar mensajes y tiempos de expiración de token (24 h).
- **Áreas probables del código:** `accounts/views.py`, `User.email_verified`, templates de verificación.
- **Notas / PR:** Ejecutar esta validación **después** de tener SMTP Gmail operativo (5.1 arranque).

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

## 7. Fase piloto — Carga de protocolos por laboratorio

Addenda acordada post-reunión (Jul 2026). Plan detallado: [PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md)

Prioridad operativa: el personal de lab carga protocolos a nombre del MV comitente mientras los veterinarios externos no operan el sistema en el día a día.

### 7.1 Carga delegada por personal de lab (MVP)

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Permitir a `PERSONAL_LAB` (y admin vía `is_lab_staff`) crear y enviar protocolos HP/CT **a nombre de un veterinario existente**.
- **Implementado:**
  - `Protocol.created_by` — migración `0022`
  - Vistas `/protocols/lab/create/…` (búsqueda MV → tipo → formulario reutilizado)
  - Dashboard lab: acción **«Cargar protocolo»**
  - Lab edita/envía borradores; historial «Cargado por personal de laboratorio»
  - Tests: `protocols/test_lab_protocol_create.py`
- **Filtro actual:** `User.email_verified=True`, `User.is_active=True`, **`Veterinarian.is_verified=True`** (punto 11, Jul 2026).
- **Notas / PR:** Ver [PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md).

---

## 8. Categoría de animal (HP y CT)

Addenda post-reunión (Jul 2026). Plan: [PLAN_PUNTOS_8_9_10.md](PLAN_PUNTOS_8_9_10.md) §8.

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Nuevo campo **categoría de animal** en protocolos de citología e histopatología.
- **Implementado:**
  - `Protocol.animal_category` — texto libre; formularios create/edit, detalle, PDF (`_build_animal_line`)
  - Migración `0023_animal_category_and_pdf_image_flag.py`
  - Tests en `test_roadmap_items_8_9_10.py`
- **Notas / PR:**

---

## 9. Editar / eliminar portaobjetos (solo HP)

Addenda post-reunión (Jul 2026). Plan: [PLAN_PUNTOS_8_9_10.md](PLAN_PUNTOS_8_9_10.md) §9.

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Corregir o borrar portaobjetos ya registrados en **histopatología**.
- **Implementado:**
  - Edición de slides HP en `sample_register.html` (`can_edit_existing_slides`)
  - `SlideDeleteView` + `delete_histopathology_slide()` con `ProcessingLog`
  - Bloqueo si slide en informe finalizado; CT sin cambios
  - Tests en `test_roadmap_items_8_9_10.py`
- **Notas / PR:**

---

## 10. Marcar imágenes para incluir en PDF del informe

Addenda post-reunión (Jul 2026). Plan: [PLAN_PUNTOS_8_9_10.md](PLAN_PUNTOS_8_9_10.md) §10.

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Booleano en `ReportImage` para elegir qué fotos micro/macro van al PDF.
- **Implementado:**
  - `ReportImage.include_in_pdf` — `default=True`
  - Checkbox en formset de edición; PDF filtra `include_in_pdf=True`
  - Migración `0023`; tests en `test_roadmap_items_8_9_10.py`
- **Notas / PR:**

---

## 11. Habilitación de veterinarios (registro abierto, operación controlada)

Addenda post-reunión (Jul 2026). Plan detallado: [PLAN_PUNTOS_11_12.md](PLAN_PUNTOS_11_12.md) §11.

Prioridad operativa: cerrar el gap entre **registro público** y **veterinarios habilitados** para crear protocolos y aparecer en la búsqueda del lab (punto 7).

### 11.1 Gate `is_verified` + pantalla de contacto

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** `Veterinarian.is_verified` bloquea creación HP/CT y búsqueda lab; MV pendiente ve pantalla de contacto administrable (patrón banner).
- **Implementado:**
  - `VeterinarianApprovedMixin` en vistas de creación HP/CT
  - Pantalla `/accounts/veterinarian/pending-approval/` + singleton `VeterinarianPendingApprovalSettings`
  - Filtro punto 7: `is_verified=True` en `lab_protocol.py`
- **Notas / PR:** Ver [VETERINARIAN_APPROVAL_TESTING.md](../VETERINARIAN_APPROVAL_TESTING.md)

### 11.2 Panel admin — Gestión de veterinarios

- **Estado:** ✅ Hecho (Jul 2026)
- **Objetivo:** Vista `/dashboard/admin/veterinarians/` (no Django Admin): buscador con **Habilitar** y **Eliminar** (soft delete); emails en ambos casos.
- **Implementado:**
  - `VeterinarianApprovalService` (approve, delete, reactivate)
  - Emails + `AuthAuditLog` + contador pendientes en panel admin
  - Soft delete: sin protocolos → anonimizar; con protocolos → solo desactivar
- **Notas / PR:** Guía operativa en [managing-users.md](../../user-guides/administrators/managing-users.md)

---

## 12. Protección de endpoints públicos (rate limit + CAPTCHA)

Addenda post-reunión (Jul 2026). Plan: [PLAN_PUNTOS_11_12.md](PLAN_PUNTOS_11_12.md) §12.

- **Estado:** ⬜ Pendiente
- **Objetivo:** Reducir abuso en registro, login, reset y reenvío de verificación.
- **Alcance v1:**
  - Rate limiting por IP (Redis): login, register, password-reset, resend-verification
  - Cloudflare Turnstile en **registro** (no en todos los forms)
- **Complementa** el punto 11 (menos basura en cola admin).
- **Notas / PR:**

---

## Orden sugerido de implementación

```
1 ✅ → 2 ✅ → 3 ✅ → 4 ✅ → 5.1 Gmail → 5.2 → 7 ✅ → 8–10 ✅ → 11 ✅ → 12 → (correo institucional) → (6.1 reactivar si la facultad lo pide)
```

| # | Bloque | Ítems | Dependencias clave |
|---|--------|-------|-------------------|
| 1 | Veterinario / datos | 1.1–1.3 ✅, 1.4 ✅ | Ninguna crítica |
| 2 | Laboratorio HP | 2.1 ✅, 2.2 ✅, 2.3 ✅ | Implementado Jun–Jul 2026 |
| 3 | Informes / PDF | 3.1, 3.2, 3.3 ✅ | Formato facultad aplicado Jul 2026 |
| 4 | Dominio / SSL | 4.1 ✅, 4.2 ✅ | Cerrado Jul 2026 (`patologiavetfcvunl.ar`) |
| 5 | Correo / auth | 5.1 Gmail provisorio → institucional luego; 5.2 | Credenciales Gmail en próxima reunión |
| 6 | Finanzas / OT | 6.1 🚫 UI off | Modelos intactos |
| 7 | Piloto lab — carga delegada | 7.1 ✅ | Filtro `is_verified` ✅ (punto 11) |
| 8 | Categoría de animal | ✅ | `0023` |
| 9 | Portaobjetos edit/delete (solo HP) | ✅ | CT excluido |
| 10 | Imágenes en PDF (flag) | ✅ | `include_in_pdf` |
| 11 | Habilitación MV | 11.1–11.2 ✅ | 5.1 recomendado para emails |
| 12 | Rate limit + CAPTCHA | ⬜ | Independiente; complementa 11 |

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
| Jul 2026 | 4.1, 4.2 | Dominio `patologiavetfcvunl.ar` + SSL cerrados en producción |
| Jul 2026 | 5.1 (decisión) | Arranque con Gmail SMTP (provisorio); migración a casilla institucional diferida |
| Jul 2026 | 7.1 (planificación) | Addenda post-reunión: carga de protocolos por lab; plan en PLAN_PUNTO_7 |
| Jul 2026 | 8, 9, 10 (planificación) | Addenda: categoría animal, edit/delete portaobjetos, flag imágenes PDF; plan en PLAN_PUNTOS_8_9_10 |
| Jul 2026 | 7.1, 8, 9, 10 | Implementación: carga delegada lab, `animal_category`, edit/delete slides HP, `include_in_pdf`; tests `test_lab_protocol_create`, `test_roadmap_items_8_9_10` |
| Jul 2026 | 11, 12 (planificación) | Habilitación MV (gate `is_verified`, panel admin, soft delete) + rate limit/CAPTCHA; plan en PLAN_PUNTOS_11_12 |
| Jul 2026 | 11 | Implementación: gate `VeterinarianApprovedMixin`, panel `/dashboard/admin/veterinarians/`, pantalla contacto, soft delete, filtro lab `is_verified`; tests `test_veterinarian_approval` |

---

## Referencias

- [PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md](PLAN_PUNTO_7_LAB_CARGA_PROTOCOLOS.md) — punto 7 (carga delegada lab)
- [PLAN_PUNTOS_8_9_10.md](PLAN_PUNTOS_8_9_10.md) — puntos 8–10
- [PLAN_PUNTOS_11_12.md](PLAN_PUNTOS_11_12.md) — puntos 11–12 (habilitación MV y seguridad auth)
- [VETERINARIAN_APPROVAL_TESTING.md](../VETERINARIAN_APPROVAL_TESTING.md) — prueba manual punto 11
- [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) — estado general del sistema
- [CLAUDE.md](../../../CLAUDE.md) — arquitectura y comandos de desarrollo
- [REPORT_WORKFLOW_AND_SIGNATURE.md](../REPORT_WORKFLOW_AND_SIGNATURE.md) — flujo de informes
- [production-deployment.md](../deployment/production-deployment.md) — despliegue
- [email-setup.md](../configuration/email-setup.md) — configuración SMTP
