# Roadmap Priorizado — AdLab

Documento de trabajo para implementar los cambios acordados con la facultad.  
Los ítems se abordan **en orden de prioridad**; marcar el estado a medida que avancemos.

**Última actualización:** Junio 2026  
**Dominio objetivo:** `patologiavetfcvunl.ar`

---

## Cómo usar este documento

| Estado | Significado |
|--------|-------------|
| ⬜ Pendiente | Aún no iniciado |
| 🔄 En curso | Trabajo activo |
| ✅ Hecho | Implementado y verificado |
| ⏸️ Postergado | Fuera del alcance de esta etapa |

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

- **Estado:** ✅ Hecho (Jun 2026)
- **Objetivo:** Corregir demora y redirección interna al abrir una notificación desde el celular.
- **Implementado:**
  - Login con `?next=` en vista pública de protocolo
  - `AuthenticationService` respeta `next` seguro post-login
  - `link_url` como path relativo + migración de URLs legacy
  - Vista `/notifications/<id>/go/` (marca leída + redirect) en bandeja y campana
- **Diagnóstico:** [NOTIFICATION_DIAGNOSTIC_RESULTS.md](NOTIFICATION_DIAGNOSTIC_RESULTS.md)
- **Notas / PR:**

### 1.3 Validación de tipos de punción (Citología)

- **Estado:** ✅ Hecho (Jun 2026)
- **Objetivo:** Etiqueta **"Punción (PAAF)"** visible en el select de técnica de citología.
- **Implementado:** Choice renombrado, aliases legacy en formularios, migración `0020`.
- **Notas / PR:**

---

## 2. Rediseño del Módulo de Laboratorio (Histopatología)

Prioridad operativa: reducir fricción con guantes puestos en el banco.

### 2.1 Simplificación del flujo de estados

- **Estado:** ⬜ Pendiente
- **Objetivo:** Eliminar pantallas y acciones obligatorias de pasos manuales intermedios.
- **Pasos a eliminar o hacer opcionales:**
  - Registro de pasaje por alcoholes
  - Deshidratación
  - Inclusión en parafina
  - Taco
- **Alcance:**
  - Revisar máquina de estados de procesamiento (`Cassette`, `Slide`, etapas).
  - Ajustar vistas, permisos y transiciones para no bloquear el flujo clínico.
- **Áreas probables del código:** `protocols/views` de procesamiento, modelos de etapas, templates Vue/HTMX del banco.
- **Notas / PR:**

### 2.2 Unificación de Cassettes y Slides (pantalla única)

- **Estado:** ⬜ Pendiente
- **Objetivo:** Cargar cassettes y slides en un solo paso, con descripción libre por cassette.

#### Sección superior — Cassettes

- Campo libre para listar cassettes y describir qué piezas u órganos contiene cada uno.
- Romper la estructura rígida actual de “superior / inferior”.

#### Sección inferior — Slides (vidrios)

- Configuración visual del slide indicando qué cassettes se cortaron y montaron en él.
- Mantener la relación many-to-many `CassetteSlide` en backend, simplificando la UI.

- **Áreas probables del código:** vistas de registro de cassettes/slides, componentes Vue, `CassetteSlide`, templates de procesamiento.
- **Notas / PR:**

---

## 3. Informes, Formato y Galería

Prioridad operativa: entregables institucionales listos para uso oficial.

### 3.1 Formato y encabezado del PDF

- **Estado:** ⬜ Pendiente
- **Objetivo:** Reemplazar diseño provisorio por formato legal e institucional definitivo.
- **Alcance:**
  - Incorporar logos nuevos y limpios de la facultad.
  - Ajustar tipografía, márgenes, encabezado y pie de página según normativa institucional.
- **Áreas probables del código:** `services/pdf_service.py`, assets estáticos (logos), plantillas ReportLab.
- **Notas / PR:**

### 3.2 Automatización del nombre del archivo PDF

- **Estado:** ⬜ Pendiente
- **Objetivo:** Al descargar o guardar el informe final, usar nomenclatura oficial.
- **Ejemplo:** `HP-[Código-de-protocolo]` (confirmar formato exacto con facultad).
- **Alcance:**
  - Header `Content-Disposition` en descarga.
  - Nombre de archivo en adjuntos de correo, si aplica.
- **Áreas probables del código:** vistas de descarga de reportes, `pdf_service.py`, tareas de email.
- **Notas / PR:**

### 3.3 Corrección en la carga de imágenes (galería macro/micro)

- **Estado:** ⬜ Pendiente
- **Objetivo:** Solucionar demora o falla al adjuntar fotos macro y micro con referencias al final del informe.
- **Alcance:**
  - Diagnosticar timeout, procesamiento síncrono o límites de tamaño.
  - Verificar upload, almacenamiento y render en PDF.
- **Áreas probables del código:** `ReportImage`, vistas de informe, `pdf_service.py`, configuración de media/static.
- **Notas / PR:**

---

## 4. Migración al Dominio Final

Prioridad operativa: producción bajo dominio institucional antes de correos y ajustes finales de backend.

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

## 6. Módulos Postergados (etapas futuras)

Estos ítems quedan **fuera del alcance actual** para concentrar esfuerzo en el circuito médico del protocolo.

### 6.1 Órdenes de Trabajo y Finanzas

- **Estado:** ⏸️ Postergado
- **Incluye (congelado por ahora):**
  - Gestión de aranceles
  - Cálculo automático según cantidad de piezas/materiales
  - Saldos pendientes
  - Emisión de resúmenes de cuenta
- **Notas:** El código base (Step 07) permanece; no se prioriza UI ni reglas de negocio nuevas hasta completar ítems 1–5.

---

## Orden sugerido de implementación

```
1 → 2 → 3 → 4 → 5 → (6 cuando la facultad lo solicite)
```

Dentro de cada bloque, el orden puede ajustarse según dependencias técnicas descubiertas en desarrollo.

| # | Bloque | Ítems | Dependencias clave |
|---|--------|-------|-------------------|
| 1 | Veterinario / datos | 1.1, 1.2, 1.3 | Ninguna crítica |
| 2 | Laboratorio HP | 2.1, 2.2 | Puede impactar modelos de procesamiento |
| 3 | Informes / PDF | 3.1, 3.2, 3.3 | Assets de logos (3.1) antes de producción formal |
| 4 | Dominio / SSL | 4.1, 4.2 | Servidor y DNS listos |
| 5 | Correo / auth | 5.1, 5.2 | Dominio (4) recomendado para links en emails |
| 6 | Finanzas | — | Postergado |

---

## Registro de sesiones de trabajo

Usar esta sección para anotar qué ítem se tomó en cada sesión.

| Fecha | Ítem | Resultado |
|-------|------|-----------|
| | | |

---

## Referencias

- [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) — estado general del sistema
- [CLAUDE.md](../../../CLAUDE.md) — arquitectura y comandos de desarrollo
- [REPORT_WORKFLOW_AND_SIGNATURE.md](../REPORT_WORKFLOW_AND_SIGNATURE.md) — flujo de informes
- [production-deployment.md](../deployment/production-deployment.md) — despliegue
- [email-setup.md](../configuration/email-setup.md) — configuración SMTP
