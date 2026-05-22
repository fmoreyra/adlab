# Firma digital para informes patológicos

Esta guía explica cómo el **personal de laboratorio** con permiso para elaborar informes debe cargar su firma digital antes de crear, finalizar o descargar PDFs.

**IMPORTANTE: Esta documentación está completamente en español.**

---

## ¿Quién debe cargar la firma?

Debes completar este paso si cumples **las tres** condiciones:

1. Tu usuario tiene rol **Personal de laboratorio** o **Histopatólogo**
2. En admin existe tu perfil **Personal de laboratorio** (`LaboratoryStaff`)
3. Tu perfil tiene activado **«Puede crear informes»** (`can_create_reports`)

Si solo hacés recepción o procesamiento técnico (sin ese permiso), **no** necesitás cargar firma para esas tareas.

---

## ¿Por qué es obligatoria?

El PDF del informe patológico incluye:

- Imagen de tu firma
- Nombre formal y matrícula
- Cargo (si está cargado)

Sin firma, el sistema **no permite**:

- Entrar a la cola de informes pendientes
- Crear o editar informes
- Finalizar un informe
- Descargar o ver el PDF

Esto evita errores y garantiza que todo informe salga firmado profesionalmente.

---

## Cómo cargar la firma

### Paso 1: Acceder al formulario

El sistema te redirige automáticamente cuando intentás elaborar un informe sin firma.

También podés ir directamente a:

**Menú / URL:** `/accounts/lab-staff/signature/`

_[Espacio para captura: pantalla «Firma digital» con selector de archivo]_

### Paso 2: Subir la imagen

1. Elegí un archivo **PNG** o **JPG** con fondo claro (recomendado: firma escaneada o exportada)
2. Hacé clic en **Guardar firma**
3. Verás el mensaje: *«Firma digital guardada. Ya puede elaborar y firmar informes.»*

### Paso 3: Continuar el flujo de informe

Volvé al protocolo en estado **Listo** o a **Informes pendientes** y usá el bloque **Informe patológico** o el botón **Elaborar informe**.

---

## Dónde aparece la firma en el sistema

| Pantalla | Qué verás |
|----------|-----------|
| Detalle del protocolo (lab) | Bloque «Informe patológico» con acciones |
| Estado de procesamiento | Mismo bloque + enlace al protocolo |
| Detalle del informe | Botones Editar / Finalizar / Ver PDF (si hay firma) |
| PDF generado | Imagen de firma + datos del profesional **asignado al informe** |

Al **crear** un informe, seleccionás el **personal responsable** en el formulario. Esa persona debe tener firma cargada (puede ser vos u otro colega con permiso).

---

## Actualizar o reemplazar la firma

1. Abrí de nuevo `/accounts/lab-staff/signature/?force=1`
2. Subí la nueva imagen
3. Los **nuevos** PDFs usarán la firma actualizada (los ya enviados no se modifican solos)

---

## Mensajes frecuentes

| Mensaje | Significado | Qué hacer |
|---------|-------------|-----------|
| *Debe cargar su firma digital antes de elaborar…* | Tu usuario no tiene imagen de firma | Subir firma en el enlace del aviso |
| *El personal seleccionado debe tener firma digital cargada* | Elegiste otro responsable sin firma | Que esa persona cargue la firma o elegite otro |
| *El profesional asignado al informe no tiene firma digital* | El informe apunta a alguien sin firma | Editar informe y cambiar responsable, o pedir que cargue firma |
| *La elaboración de informes requiere el permiso «Puede crear informes»* | Tu perfil no tiene el permiso | Pedir al administrador que lo active en admin |

---

## Para administradores

En **Django Admin → Personal de laboratorio**:

- Marcar **Puede crear informes**
- Subir **Firma digital** si el usuario no puede hacerlo desde la web
- Verificar **Activo**

---

## Preguntas frecuentes

### ¿La firma es la misma que la del perfil antiguo de histopatólogo?

Si tenés perfil unificado `LaboratoryStaff` (migración automática), la firma se gestiona **solo** en ese perfil. El modelo legacy `Histopathologist` ya no alcanza para informes nuevos.

### ¿Puedo elaborar informes sin ser histopatólogo?

Sí, si sos **personal de lab** con `can_create_reports=True` y firma cargada.

### ¿El veterinario necesita firma?

No. Los veterinarios solo **descargan** informes ya finalizados de sus protocolos.

---

*Anterior: [Procesar muestras](processing-samples.md)*  
*Relacionado: [Crear informes (histopatólogos)](../histopathologists/creating-reports.md)*
