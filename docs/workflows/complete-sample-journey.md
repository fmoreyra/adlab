# El viaje completo de una muestra

Esta guía explica todo el proceso que sigue una muestra desde que el veterinario la envía hasta que recibe el informe final.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🎯 ¿Qué verás en esta guía?

Esta guía te muestra:
- **Todo el proceso paso a paso** desde el envío hasta la entrega
- **Qué hace cada persona** en cada etapa
- **Cuánto tiempo toma** cada paso
- **Qué notificaciones recibes** en cada momento

## 📋 Resumen del proceso

Una muestra pasa por estas etapas principales:
1. **El veterinario envía el protocolo**
2. **El laboratorio recibe la muestra**
3. **Se procesa la muestra**
4. **Se analiza la muestra**
5. **Se entrega el informe**

## 🚀 Etapa 1: El veterinario envía el protocolo

> **Nota (Jul 2026):** el veterinario debe tener cuenta **habilitada por un administrador** (`is_verified`) para crear protocolos online. En la fase piloto, el personal de lab también puede cargar protocolos a nombre del MV comitente (punto 7).

### ¿Qué hace el veterinario?
1. **Inicia sesión** en el sistema
2. **Llena el formulario** con información del paciente
3. **Envía el protocolo** al laboratorio
4. **Imprime las etiquetas** para la muestra

### ¿Qué pasa en el sistema?
- **Se crea el protocolo** con un código temporal único
- **Se genera la etiqueta** con código QR
- **Se envía confirmación** por email al veterinario
- **Estado**: DRAFT → SUBMITTED

### ¿Cuánto tiempo toma?
- **Inmediato**: El protocolo se registra al instante

_[Espacio para captura de pantalla: Veterinario completando el formulario de protocolo]_

## 📦 Etapa 2: El laboratorio recibe la muestra

### ¿Qué hace el personal de laboratorio?
1. **Recibe la muestra física** con las etiquetas
2. **Verifica que coincida** con el protocolo
3. **Inspecciona la condición** de la muestra
4. **Registra la llegada** en el sistema
5. **Asigna número de protocolo definitivo** (ej: HP 24/001)
6. **Actualiza el estado** a "Recibido"

### ¿Qué pasa en el sistema?
- **Se asigna número de protocolo**: HP 24/001
- **Se actualiza el estado** a RECEIVED
- **Se envía email** al veterinario confirmando recepción
- **Se crea registro de historial**: Con fecha y hora de recepción

### ¿Cuánto tiempo toma?
- **1-2 días hábiles**: Desde el envío hasta la recepción

_[Espacio para captura de pantalla: Personal de laboratorio registrando la llegada de la muestra]_

## ❌ Etapa 2.5: La muestra es rechazada (Si Aplica)

### ¿Cuándo se rechaza una muestra?
- **Calidad insuficiente**: Para análisis confiable
- **Muestra mal fijada**: Conservación inadecuada
- **Cantidad insuficiente**: Material insuficiente para diagnóstico
- **Identificación incorrecta**: Etiquetas ilegibles o incorrectas
- **Condiciones de transporte**: Muestra deteriorada por mal manejo

### ¿Qué hace el personal de laboratorio?
1. **Evalúa la muestra** según criterios de calidad
2. **Documenta el motivo** del rechazo con detalle
3. **Selecciona "Rechazada"** en condición de muestra
4. **Completa observaciones** (obligatorio)
5. **Confirma el rechazo** en el sistema

### ¿Qué pasa en el sistema?
- **NO se asigna número de protocolo**: Solo mantiene código temporal
- **Se actualiza el estado** a REJECTED
- **Se registra en historial**: Para auditoría
- **Se envía email de rechazo** al veterinario con:
  - Motivo detallado del rechazo
  - Recomendaciones para nueva muestra
  - Instrucciones para reenvío
  - Contacto del laboratorio

### ¿Qué hace el veterinario?
1. **Recibe email de rechazo** con explicación detallada
2. **Contacta al laboratorio** si tiene dudas
3. **Prepara nueva muestra** siguiendo recomendaciones
4. **Envía nueva muestra física** al laboratorio
5. **El protocolo se reactiva automáticamente** cuando llega la nueva muestra

### ¿Cuánto tiempo toma?
- **Inmediato**: El rechazo se registra al instante
- **Reenvío**: Depende de cuándo el veterinario envíe nueva muestra

### ¿Qué pasa después?
- **El protocolo vuelve a SUBMITTED** cuando llega nueva muestra
- **Se reinicia el proceso** desde la recepción
- **No se cobra** por la muestra rechazada

_[Espacio para captura de pantalla: Formulario de rechazo de muestra]_

## 🔬 Etapa 3: Se procesa la muestra

### ¿Qué hace el personal de laboratorio?

#### Para Histopatología
1. **Prepara los cassettes**: Coloca el tejido en cassettes
2. **Etiqueta cada cassette**: Con identificación única (A, B, C...)
3. **Procesa el tejido**: Fijación, deshidratación, inclusión
4. **Realiza cortes**: Secciones en microtomo
5. **Monta las laminillas**: Crea los slides
6. **Aplica tinciones**: Hematoxilina-eosina u otras
7. **Registra cada paso** en el sistema

#### Para Citología
1. **Recepción:** el sistema registra los portaobjetos según la cantidad recibida.
2. **Banco:** tinción (p. ej. Diff-Quick) según protocolo del laboratorio.
3. **Cierre en el sistema:** en el detalle del protocolo, anote **observaciones opcionales por portaobjeto** y confirme **Marcar listo para diagnóstico**.
4. **Sin pantalla de registro de slides:** a diferencia de histopatología, no hay «Registrar muestra» para CT.

### ¿Qué pasa en el sistema?
- **Se actualiza el estado** a PROCESSING
- **Se registran cassettes y slides**: En el sistema (HP en «Registrar muestra»; CT en recepción + observaciones al cerrar banco)
- **Citología:** las observaciones de banco quedan en cada portaobjeto; el protocolo pasa a **READY** sin notificar al veterinario (sigue viendo «En laboratorio»)
- **Se asigna a un histopatólogo** disponible
- **Se envía notificación** al histopatólogo

### ¿Cuánto tiempo toma?
- **Histopatología**: 2-3 días para procesamiento
- **Citología**: 1 día para preparación

_[Espacio para captura de pantalla: Personal procesando la muestra en el laboratorio]_

## 🔍 Etapa 4: Se analiza la muestra

### ¿Qué hace el histopatólogo?
1. **Recibe la muestra asignada**
2. **Revisa la información** del protocolo
3. **Examina macroscópicamente** la muestra
4. **Analiza microscópicamente** cada laminilla
5. **Documenta observaciones** para cada cassette
6. **Toma fotografías** microscópicas si es necesario
7. **Formula diagnóstico** basado en hallazgos
8. **Crea el informe** con:
   - Descripción macroscópica
   - Observaciones microscópicas
   - Diagnóstico
   - Comentarios y recomendaciones
9. **Carga su firma digital** en el sistema (obligatorio la primera vez: `/accounts/lab-staff/signature/`)
10. **Firma el informe** mediante el PDF (imagen de firma del profesional asignado)

### ¿Qué pasa en el sistema?
- **Se actualiza el estado** según progreso:
  - READY: Lista para análisis
  - En análisis (mientras trabaja)
  - Informe en borrador
- **Se registran observaciones**: Para cada cassette
- **Bloque «Informe patológico»** en detalle de protocolo y procesamiento (si tiene permiso y firma)
- **Se genera PDF** del informe (solo si hay responsable asignado y firma cargada)
- **Se calcula hash SHA-256**: Para integridad del documento

### ¿Cuánto tiempo toma?
- **Citología**: 1-2 días hábiles
- **Histopatología simple**: 1-2 días
- **Histopatología compleja**: 2-3 días
- **Casos que requieren consulta**: Tiempo adicional

_[Espacio para captura de pantalla: Histopatólogo analizando la muestra]_

## 📄 Etapa 5: Se entrega el informe

### ¿Qué hace el sistema?

#### Generación y Envío Automático
1. **Genera el informe PDF** profesional con:
   - Encabezado con logos
   - Información del paciente
   - Historia clínica
   - Descripción macroscópica
   - Observaciones microscópicas
   - Diagnóstico
   - Comentarios
   - Firma digital del histopatólogo
   - Hash SHA-256 para verificación

2. **Envía el informe** por email:
   - Al email principal del veterinario
   - Al email alternativo (si configurado)
   - PDF adjunto
   - Enlace para descarga desde el sistema

3. **Actualiza el estado** a REPORT_SENT

4. **Registra la entrega** en EmailLog:
   - Fecha y hora de envío
   - ID de tarea de Celery
   - Estado de entrega

### ¿Qué recibe el veterinario?
- **Email con el informe** adjunto
- **Acceso al PDF** desde el sistema
- **Notificación en el sistema**: En el panel de control
- **Confirmación de entrega**

### ¿Cuánto tiempo toma?
- **Inmediato**: El informe se entrega al instante después de finalizar

_[Espacio para captura de pantalla: Email de entrega de informe al veterinario]_

## 📊 Línea de Tiempo Visual

```
Día 1: Veterinario envía protocolo [SUBMITTED]
       ↓
Día 1-2: Muestra llega al laboratorio [RECEIVED]
       ↓  (Asignación de número HP 24/001)
       ↓
Día 2-4: Procesamiento de muestra [PROCESSING]
       ↓  (Cassettes, cortes, tinciones)
       ↓
Día 4-5: Lista para análisis [READY]
       ↓
Día 5-7: Análisis y creación de informe
       ↓  (Histopatólogo analiza y escribe)
       ↓
Día 7: Informe entregado [REPORT_SENT]
```

## 🔄 Estados del Protocolo

### Estados que verás
Tu protocolo pasará por estos estados:

1. **DRAFT** (Borrador)
   - Protocolo creado pero no enviado
   - Solo el veterinario puede verlo

2. **SUBMITTED** (Enviado)
   - Protocolo enviado al laboratorio
   - Tiene código temporal: TMP-HP-20241017-001
   - Esperando muestra física

3. **RECEIVED** (Recibido)
   - Muestra física llegó al laboratorio
   - Se asignó número definitivo: HP 24/001
   - Registrado y listo para procesamiento

4. **PROCESSING** (Procesando)
   - Muestra siendo preparada
   - Cassettes y slides en proceso
   - Personal técnico trabajando

5. **READY** (Listo)
   - Muestra lista para análisis
   - Asignado a histopatólogo
   - Esperando análisis microscópico

6. **REPORT_SENT** (Informe Enviado)
   - Informe completado
   - PDF generado y enviado
   - Disponible para descarga

_[Espacio para captura de pantalla: Vista de seguimiento del estado del protocolo]_

## ⏰ Tiempos Totales Esperados

### Tiempo Completo del Proceso

#### Citología
- **Total**: 3-5 días hábiles
- **Desglose**:
  - Envío a recepción: 1-2 días
  - Procesamiento: 1 día
  - Análisis: 1-2 días
  - Entrega: Inmediato

#### Histopatología
- **Total**: 5-8 días hábiles
- **Desglose**:
  - Envío a recepción: 1-2 días
  - Procesamiento: 2-3 días
  - Análisis: 2-3 días
  - Entrega: Inmediato

#### Casos Urgentes
- **50% menos tiempo**: Procesos acelerados
- **Requiere marcarlo**: Como urgente al enviar
- **Costo adicional**: Puede aplicar

## 📧 Notificaciones Durante el Proceso

### Para Veterinarios
1. **Protocolo recibido**: "Hemos recibido tu protocolo TMP-HP-20241017-001"
2. **Muestra recibida**: "Tu muestra HP 24/001 llegó al laboratorio"
3. **En procesamiento**: "Tu muestra está siendo procesada"
4. **Análisis iniciado**: "El análisis de tu muestra ha comenzado"
5. **Informe listo**: "Tu informe HP 24/001 está listo" (con PDF adjunto)

### Para Histopatólogos
1. **Nueva muestra**: "Tienes una nueva muestra HP 24/001 para analizar"
2. **Recordatorio**: "Tienes X muestras pendientes de análisis"

### Para Personal de Laboratorio
1. **Nuevo protocolo**: "Ha llegado un nuevo protocolo para procesar"
2. **Muestra pendiente**: "Tienes X muestras pendientes de procesar"

_[Espacio para captura de pantalla: Ejemplos de notificaciones por email]_

## 🚨 ¿Qué pasa si hay problemas?

### Problemas Comunes y Soluciones

#### La Muestra se Daña en Tránsito
- **El laboratorio te contactará** inmediatamente
- **Evaluarán si se puede analizar** o si necesitas enviar otra
- **Documentarán el problema**: Con fotografías
- **No se te cobrará** si el problema no fue por mala preparación

#### Información Incorrecta en el Protocolo
- **Contacta al laboratorio** lo antes posible
- **Pueden corregir** información básica
- **Para cambios importantes** pueden pedirte actualizar el protocolo
- **No retrasará mucho** el proceso si se detecta temprano

#### Muestra Insuficiente
- **El histopatólogo lo detectará**: Durante análisis
- **Te contactarán**: Para solicitar muestra adicional
- **Pueden hacer diagnóstico parcial**: Con lo disponible
- **Nueva muestra**: Seguirá proceso acelerado

#### Retrasos en el Proceso
- **El laboratorio te notificará** si hay retrasos
- **Te explicarán la razón**: Del retraso (equipo, personal, casos complejos)
- **Te darán nueva fecha**: Estimada de entrega
- **Priorizarán tu caso**: Si es posible

#### Hallazgos que Requieren Estudios Adicionales
- **El histopatólogo te contactará**: Para discutir
- **Explicará qué se necesita**: Inmunohistoquímica, coloraciones especiales, etc.
- **Solicitará autorización**: Para proceder
- **Tiempo adicional**: Según el estudio requerido

## 🔄 Reenvío de Protocolos Rechazados (Para Administradores)

### ¿Cuándo se puede reenviar un protocolo rechazado?

#### Casos Válidos para Reenvío
- **Error en evaluación inicial**: La muestra era aceptable
- **Veterinario envió nueva muestra**: Con las correcciones necesarias
- **Condiciones mejoradas**: Problema resuelto
- **Acuerdo con veterinario**: Decisión conjunta

### ¿Qué hace el administrador?
1. **Accede a "Protocolos Rechazados"** desde el dashboard
2. **Selecciona el protocolo** a reenviar
3. **Completa formulario** con motivo del reenvío (mínimo 10 caracteres)
4. **Confirma el reenvío**
5. **Sistema actualiza estado** a SUBMITTED automáticamente

### ¿Qué pasa en el sistema?
- **Estado cambia** de REJECTED a SUBMITTED
- **Se registra en historial** el cambio con motivo
- **Protocolo disponible** para nueva recepción
- **Se notifica al veterinario** del reenvío
- **Se mantiene auditoría** completa del proceso

### ¿Cuánto tiempo toma?
- **Inmediato**: El reenvío se procesa al instante
- **Nueva recepción**: Depende de cuándo llegue la nueva muestra

_[Espacio para captura de pantalla: Formulario de reenvío de protocolo rechazado]_

## ❓ Preguntas Frecuentes

### ¿Puedo acelerar el proceso?
**Sí**, puedes:
- **Marcar como urgente**: Durante el envío del protocolo
- **Contactar al laboratorio**: Para casos muy urgentes
- **Costo adicional**: Los casos urgentes pueden tener recargo
- **Disponibilidad**: Según carga de trabajo del laboratorio

### ¿Qué pasa si no recibo el informe?
1. **Revisa tu email**: Incluyendo la carpeta de spam
2. **Verifica en el sistema**: El informe estará disponible ahí
3. **Revisa tu configuración**: Email correcto en tu perfil
4. **Contacta al laboratorio**: Si no lo encuentras después de verificar

### ¿Puedo pedir una segunda opinión?
**Sí**, puedes:
- **Pedir revisión**: Por otro histopatólogo del laboratorio
- **Solicitar consulta**: Con un especialista externo
- **Discutir el caso**: Con el histopatólogo que hizo el análisis
- **Costo adicional**: Las segundas opiniones formal tienen costo extra

### ¿El veterinario puede hacer consultas sobre el informe?
**Sí, absolutamente**:
- **Contactar al histopatólogo**: Directamente o a través del laboratorio
- **Solicitar aclaraciones**: Sobre hallazgos o diagnóstico
- **Discutir el caso**: Para mejor comprensión
- **Sin costo adicional**: Las consultas sobre informes son parte del servicio

### ¿Cuánto tiempo se guardan los informes?
- **Indefinidamente**: En el sistema digital
- **Siempre accesibles**: Puedes descargar en cualquier momento
- **Laminillas**: Se guardan según política del laboratorio (típicamente 5-10 años)
- **Bloques de parafina**: Se guardan según política (típicamente 10+ años)

### ¿Qué hago si mi muestra fue rechazada?
**Revisa el email** con el motivo del rechazo. Contacta al laboratorio si tienes dudas. Prepara una nueva muestra siguiendo las recomendaciones y envíala. No se te cobrará por la muestra rechazada.

### ¿Puedo reenviar la misma muestra si fue rechazada?
**No**, debes enviar una nueva muestra. El laboratorio te dará instrucciones específicas sobre cómo prepararla correctamente.

### ¿Cuánto tiempo tengo para enviar una nueva muestra?
**No hay límite de tiempo**, pero es recomendable enviarla lo antes posible para no retrasar el diagnóstico de tu paciente.

## 🆘 Si Necesitas Ayuda

### Durante el Proceso
- **Revisa el estado**: En tu panel de control
- **Contacta al laboratorio**: Si tienes dudas
- **Usa el chat de soporte**: En el sistema (si está disponible)
- **Revisa esta guía**: Para entender cada etapa

### Para Problemas Urgentes
- **Llama al laboratorio**: Directamente
- **Menciona tu número de protocolo**: HP 24/001 o TMP-HP-20241017-001
- **Explica el problema**: Claramente
- **Horario**: Durante horas de oficina, o servicio de urgencias si está disponible

### Contactos
- **Recepción**: Para consultas sobre muestras recibidas
- **Procesamiento**: Para preguntas sobre preparación
- **Histopatólogo**: Para consultas sobre análisis
- **Administración**: Para facturación y pagos
- **Soporte técnico**: Para problemas del sistema

---

*Relacionado: [Operaciones diarias](daily-operations.md) | [Casos urgentes](emergency-procedures.md)*
