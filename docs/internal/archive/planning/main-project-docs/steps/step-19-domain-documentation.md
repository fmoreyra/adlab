# Step 19: User Documentation & Usage Guide

## Overview

This step creates comprehensive user-focused documentation that explains how to use the laboratory management system effectively. **ALL DOCUMENTATION MUST BE WRITTEN IN SPANISH** to serve the Spanish-speaking laboratory staff and veterinarians. The documentation focuses on practical workflows, user guides, and business processes without technical implementation details.

## Documentation Structure

### **User-Focused Documentation Architecture**

```
docs/
├── index.md                           # Main documentation index
├── getting-started/
│   ├── system-overview.md            # What the system does for users
│   ├── first-login.md                # How to log in for the first time
│   └── basic-navigation.md            # How to navigate the system
├── user-guides/
│   ├── veterinarians/                # Veterinarian user guide
│   │   ├── submitting-protocols.md   # How to submit protocols
│   │   ├── tracking-samples.md       # How to track sample progress
│   │   ├── accessing-reports.md      # How to view and download reports
│   │   └── creating-work-orders.md   # How to create work orders
│   ├── histopathologists/           # Histopathologist user guide
│   │   ├── analyzing-samples.md      # How to analyze samples
│   │   ├── creating-reports.md       # How to create pathology reports
│   │   └── quality-control.md        # How to ensure report quality
│   ├── lab-staff/                    # Laboratory staff guide
│   │   ├── receiving-samples.md     # How to receive and log samples
│   │   ├── processing-samples.md     # How to process samples
│   │   └── managing-inventory.md     # How to manage lab inventory
│   └── administrators/              # Administrator guide
│       ├── managing-users.md        # How to manage user accounts
│       ├── system-settings.md       # How to configure system settings
│       └── monitoring-system.md      # How to monitor system health
├── workflows/
│   ├── complete-sample-journey.md   # From submission to report delivery
│   ├── daily-operations.md          # Daily lab operations
│   └── emergency-procedures.md       # What to do in urgent cases
├── common-tasks/
│   ├── password-reset.md            # How to reset passwords
│   ├── email-notifications.md       # Understanding email notifications
│   ├── printing-labels.md           # How to print sample labels
│   └── downloading-reports.md        # How to download reports
├── troubleshooting/
│   ├── common-issues.md             # Common problems and solutions
│   ├── contact-support.md           # How to get help
│   └── faq.md                       # Frequently asked questions
└── assets/
    ├── images/                      # Screenshots and diagrams
    ├── videos/                      # Video tutorials
    └── templates/                   # Document templates
```

## Implementation Plan

### Phase 1: Core User Documentation (2-3 hours)

#### 1.1 Main Documentation Index

Create `docs/index.md`:

```markdown
# Guía de Usuario del Sistema de Gestión de Laboratorio

Bienvenido a la guía de usuario del Sistema de Gestión de Laboratorio. Esta guía te ayudará a usar el sistema de manera efectiva para gestionar protocolos, muestras e informes de patología.

**IMPORTANTE: Toda la documentación está en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🚀 Comenzar

- [¿Qué hace este sistema?](getting-started/system-overview.md) - Entender qué hace el sistema por ti
- [Primer acceso](getting-started/first-login.md) - Cómo iniciar sesión por primera vez
- [Navegación básica](getting-started/basic-navigation.md) - Cómo moverse por el sistema

## 👥 Guías por Rol

### Para Veterinarios
- [Enviar protocolos](user-guides/veterinarians/submitting-protocols.md) - Cómo enviar muestras para análisis
- [Seguir muestras](user-guides/veterinarians/tracking-samples.md) - Cómo ver el progreso de tus muestras
- [Ver informes](user-guides/veterinarians/accessing-reports.md) - Cómo ver y descargar informes
- [Crear órdenes de trabajo](user-guides/veterinarians/creating-work-orders.md) - Cómo crear órdenes de trabajo

### Para Histopatólogos
- [Analizar muestras](user-guides/histopathologists/analyzing-samples.md) - Cómo analizar muestras
- [Crear informes](user-guides/histopathologists/creating-reports.md) - Cómo crear informes de patología
- [Control de calidad](user-guides/histopathologists/quality-control.md) - Cómo asegurar la calidad

### Para Personal de Laboratorio
- [Recibir muestras](user-guides/lab-staff/receiving-samples.md) - Cómo recibir y registrar muestras
- [Procesar muestras](user-guides/lab-staff/processing-samples.md) - Cómo procesar muestras
- [Gestionar inventario](user-guides/lab-staff/managing-inventory.md) - Cómo gestionar inventario

### Para Administradores
- [Gestionar usuarios](user-guides/administrators/managing-users.md) - Cómo gestionar cuentas de usuario
- [Configurar sistema](user-guides/administrators/system-settings.md) - Cómo configurar el sistema
- [Monitorear sistema](user-guides/administrators/monitoring-system.md) - Cómo verificar que todo funciona

## 🔄 Procesos Completos

- [Viaje completo de una muestra](workflows/complete-sample-journey.md) - Desde envío hasta entrega del informe
- [Operaciones diarias](workflows/daily-operations.md) - Qué hacer cada día en el laboratorio
- [Casos urgentes](workflows/emergency-procedures.md) - Qué hacer cuando hay urgencias

## 🔧 Tareas Comunes

- [Cambiar contraseña](common-tasks/password-reset.md) - Cómo cambiar tu contraseña
- [Notificaciones por email](common-tasks/email-notifications.md) - Entender los emails que recibes
- [Imprimir etiquetas](common-tasks/printing-labels.md) - Cómo imprimir etiquetas de muestras
- [Descargar informes](common-tasks/downloading-reports.md) - Cómo descargar informes

## ❓ Ayuda y Soporte

- [Problemas comunes](troubleshooting/common-issues.md) - Problemas frecuentes y sus soluciones
- [Preguntas frecuentes](troubleshooting/faq.md) - Preguntas que se hacen frecuentemente
- [Contactar soporte](troubleshooting/contact-support.md) - Cómo obtener ayuda

---

*Última actualización: Enero 2025*
*Versión: 1.0*
```

#### 1.2 Getting Started Documentation

Create `docs/getting-started/system-overview.md`:

```markdown
# ¿Qué hace este sistema?

El Sistema de Gestión de Laboratorio te ayuda a gestionar todo el proceso de análisis de muestras de patología, desde que un veterinario envía una muestra hasta que recibe el informe final.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🎯 ¿Para qué sirve este sistema?

### Si eres Veterinario
- **Enviar muestras**: Puedes enviar protocolos con información de tus pacientes para análisis
- **Seguir el progreso**: Ves en tiempo real cómo va el análisis de tus muestras
- **Recibir informes**: Obtienes informes detallados por email cuando están listos
- **Crear órdenes de trabajo**: Puedes crear órdenes de trabajo para servicios especiales

### Si eres Histopatólogo
- **Analizar muestras**: Recibes muestras asignadas para análisis
- **Crear informes**: Documentas tus hallazgos en informes profesionales
- **Control de calidad**: Aseguras que tus informes cumplan estándares de calidad

### Si eres Personal de Laboratorio
- **Recibir muestras**: Registras las muestras que llegan al laboratorio
- **Procesar muestras**: Preparas las muestras para análisis
- **Gestionar inventario**: Mantienes control del inventario del laboratorio

### Si eres Administrador
- **Gestionar usuarios**: Creas y gestionas las cuentas de todos los usuarios
- **Configurar el sistema**: Ajustas las configuraciones según las necesidades
- **Monitorear**: Ves que todo funcione correctamente

## 🔄 ¿Cómo funciona el proceso?

### 1. El veterinario envía un protocolo
- Completa un formulario con información del paciente
- Incluye detalles de la muestra y análisis solicitado
- El sistema genera etiquetas para la muestra

### 2. El laboratorio recibe la muestra
- El personal registra la llegada de la muestra
- Verifica que la muestra esté en buen estado
- Actualiza el estado en el sistema

### 3. Se procesa la muestra
- El personal prepara la muestra para análisis
- Se asigna a un histopatólogo disponible
- Se registra cada paso del procesamiento

### 4. Se crea el informe
- El histopatólogo analiza la muestra
- Crea un informe detallado con sus hallazgos
- El sistema genera un PDF profesional

### 5. Se entrega el informe
- El informe se envía automáticamente por email al veterinario
- El veterinario puede descargar el PDF
- Se registra la entrega en el sistema

## 📱 ¿Cómo accedo al sistema?

- **Desde cualquier navegador**: Chrome, Firefox, Safari, Edge
- **Desde cualquier dispositivo**: Computadora, tablet, teléfono
- **Siempre disponible**: 24/7 desde cualquier lugar con internet
- **Fácil de usar**: Interfaz simple y clara

## 🔒 ¿Es seguro?

- **Contraseñas seguras**: Cada usuario tiene su propia cuenta
- **Acceso controlado**: Solo puedes ver lo que necesitas para tu trabajo
- **Datos protegidos**: Toda la información está segura y respaldada
- **Registro de actividades**: Se registra quién hace qué en el sistema

## 📧 ¿Recibiré notificaciones?

Sí, el sistema te enviará emails cuando:
- **Para veterinarios**: Cuando tu muestra es recibida, procesada, o el informe está listo
- **Para histopatólogos**: Cuando recibes una nueva muestra para analizar
- **Para personal**: Cuando llega una nueva muestra al laboratorio
- **Para administradores**: Cuando hay problemas o actualizaciones del sistema

## ❓ ¿Necesito entrenamiento especial?

No, el sistema está diseñado para ser fácil de usar:
- **Interfaz intuitiva**: Todo está donde esperas encontrarlo
- **Guías paso a paso**: Cada proceso tiene instrucciones claras
- **Ayuda disponible**: Siempre puedes pedir ayuda si la necesitas
- **Aprendizaje gradual**: Puedes aprender a tu propio ritmo

---

*Siguiente: [Primer acceso](first-login.md)*
```

Create `docs/getting-started/first-login.md`:

```markdown
# Primer acceso al sistema

Esta guía te ayudará a acceder al sistema por primera vez y configurar tu cuenta.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🔑 ¿Cómo obtengo mi cuenta?

### Si eres nuevo en el laboratorio
- **Contacta al administrador**: Pide al administrador del sistema que cree tu cuenta
- **Proporciona tu información**: Nombre, email, y el tipo de trabajo que haces
- **Espera la confirmación**: Recibirás un email con tus credenciales de acceso

### Si ya tienes cuenta
- **Usa tus credenciales**: Email y contraseña que te proporcionaron
- **Si olvidaste tu contraseña**: Sigue las instrucciones para restablecerla

## 🚀 Cómo iniciar sesión por primera vez

### Paso 1: Abrir el sistema
1. **Abre tu navegador**: Chrome, Firefox, Safari, o Edge
2. **Ve a la dirección**: La URL que te proporcionó el administrador
3. **Verás la pantalla de inicio**: Con opciones para iniciar sesión

![Pantalla de inicio de sesión](assets/images/login-screen.png)
*Captura de pantalla: Pantalla de inicio de sesión del sistema*

### Paso 2: Ingresar tus credenciales
1. **Email**: Ingresa tu dirección de email
2. **Contraseña**: Ingresa la contraseña que recibiste
3. **Hacer clic en "Iniciar Sesión"**

### Paso 3: Cambiar tu contraseña (primera vez)
- **El sistema te pedirá cambiar tu contraseña**
- **Elige una contraseña segura**: Al menos 8 caracteres con letras y números
- **Confirma tu nueva contraseña**
- **Guarda tu contraseña en un lugar seguro**

![Cambio de contraseña](assets/images/password-change.png)
*Captura de pantalla: Pantalla para cambiar contraseña en el primer acceso*

## 🏠 Tu panel de control

### ¿Qué verás al iniciar sesión?

Dependiendo de tu rol, verás diferentes opciones:

#### Si eres Veterinario
- **Mis Protocolos**: Protocolos que has enviado
- **Nuevo Protocolo**: Crear un nuevo protocolo
- **Informes Recibidos**: Informes que has recibido
- **Órdenes de Trabajo**: Órdenes de trabajo que has creado

#### Si eres Histopatólogo
- **Muestras Asignadas**: Muestras que tienes para analizar
- **Mis Informes**: Informes que estás creando
- **Informes Completados**: Informes que has terminado

#### Si eres Personal de Laboratorio
- **Muestras Pendientes**: Muestras que necesitan ser procesadas
- **Inventario**: Estado del inventario del laboratorio
- **Tareas del Día**: Lista de tareas pendientes

#### Si eres Administrador
- **Usuarios**: Gestionar cuentas de usuario
- **Configuración**: Ajustes del sistema
- **Reportes**: Estadísticas y reportes del sistema

![Panel de veterinario](assets/images/veterinarian-dashboard.png)
*Captura de pantalla: Panel de control para veterinarios*

## 🔧 Configurar tu perfil

### Información personal
1. **Hacer clic en tu nombre** (esquina superior derecha)
2. **Seleccionar "Mi Perfil"**
3. **Actualizar tu información**:
   - Nombre completo
   - Teléfono
   - Especialización (si aplica)
   - Preferencias de notificación

![Configuración de perfil](assets/images/profile-settings.png)
*Captura de pantalla: Configuración de perfil de usuario*

### Preferencias de notificación
- **Email**: Recibir notificaciones por email
- **Frecuencia**: Con qué frecuencia quieres recibir actualizaciones
- **Tipos de notificación**: Qué eventos quieres que te notifiquen

## 📱 Usar el sistema desde tu teléfono

### ¿Funciona en el teléfono?
- **Sí**: El sistema funciona en teléfonos y tablets
- **Navegador**: Usa cualquier navegador en tu teléfono
- **Misma dirección**: Usa la misma URL que en la computadora

### Consejos para usar en el teléfono
- **Girar la pantalla**: Para mejor visualización
- **Zoom**: Puedes hacer zoom para ver mejor
- **Guardar en pantalla de inicio**: Para acceso rápido

## ❓ ¿Qué hacer si no puedo iniciar sesión?

### Problemas comunes y soluciones

#### "Usuario o contraseña incorrectos"
- **Verifica tu email**: Asegúrate de escribir correctamente tu email
- **Verifica tu contraseña**: Revisa que no haya errores de tipeo
- **Mayúsculas y minúsculas**: La contraseña distingue entre mayúsculas y minúsculas

#### "Cuenta no encontrada"
- **Contacta al administrador**: Tu cuenta puede no estar creada aún
- **Verifica tu email**: Asegúrate de usar el email correcto

#### "Contraseña expirada"
- **Solicita nueva contraseña**: Usa la opción "¿Olvidaste tu contraseña?"
- **Contacta al administrador**: Si no puedes restablecerla

#### "Sesión expirada"
- **Inicia sesión nuevamente**: Simplemente vuelve a ingresar tus credenciales
- **Marca "Recordarme"**: Para evitar que expire la sesión

## 🆘 ¿Necesitas ayuda?

### Cómo obtener ayuda
1. **Revisar esta guía**: Busca la respuesta en la documentación
2. **Contactar soporte**: Usa el formulario de contacto en el sistema
3. **Llamar al laboratorio**: Para asuntos urgentes
4. **Hablar con el administrador**: Para problemas de acceso

### Información que necesitarás para soporte
- **Tu email**: La dirección con la que intentas iniciar sesión
- **Tu rol**: Veterinario, histopatólogo, personal, o administrador
- **Descripción del problema**: Qué está pasando exactamente
- **Navegador que usas**: Chrome, Firefox, Safari, etc.

---

*Anterior: [¿Qué hace este sistema?](system-overview.md)*  
*Siguiente: [Navegación básica](basic-navigation.md)*
```

### Fase 2: Guías de Usuario (4-5 horas)

#### 2.1 Guía para Veterinarios - Enviar Protocolos

Crear `docs/user-guides/veterinarians/submitting-protocols.md`:

```markdown
# Cómo enviar protocolos para análisis

Esta guía te explica paso a paso cómo enviar protocolos para que el laboratorio analice muestras de tus pacientes.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🎯 ¿Qué es un protocolo?

Un protocolo es la información que envías al laboratorio cuando quieres que analicen una muestra de tu paciente. Incluye:
- Información del animal
- Detalles de la muestra
- Tu diagnóstico presuntivo
- Historia clínica

## 🚀 Cómo empezar

### Paso 1: Acceder al sistema
1. **Abre tu navegador** y ve a la dirección del sistema
2. **Inicia sesión** con tu email y contraseña
3. **Verás tu panel de control** con tus protocolos recientes

![Panel de veterinario](assets/images/veterinarian-dashboard.png)
*Captura de pantalla: Panel de control para veterinarios*

### Paso 2: Crear nuevo protocolo
1. **Hacer clic en "Nuevo Protocolo"** (botón verde en tu panel)
2. **Se abrirá el formulario** para llenar la información

![Botón nuevo protocolo](assets/images/new-protocol-button.png)
*Captura de pantalla: Botón para crear nuevo protocolo*

## 📝 Llenar el formulario del protocolo

### Información del Animal
**Campos obligatorios:**
- **Nombre del animal**: Como lo conoces
- **Especie**: Perro, gato, caballo, etc.
- **Raza**: Si la conoces
- **Edad**: Años o meses
- **Sexo**: Macho o hembra

![Información del animal](assets/images/animal-information.png)
*Captura de pantalla: Sección para información del animal*

### Información del Propietario
- **Nombre completo**: Del dueño del animal
- **Teléfono**: Para contactos urgentes
- **Email**: Para recibir el informe
- **Dirección**: Para envío de documentos

### Información de la Muestra
**Tipo de análisis:**
- **Citología**: Para aspirados con aguja fina, frotis
- **Histopatología**: Para biopsias, especímenes quirúrgicos

**Detalles de la muestra:**
- **Qué tipo de muestra es**: Biopsia, aspirado, etc.
- **Cuándo la tomaste**: Fecha de recolección
- **Tu diagnóstico presuntivo**: Qué sospechas que puede ser

![Información de la muestra](assets/images/sample-information.png)
*Captura de pantalla: Sección para información de la muestra*

### Historia Clínica
**Información importante:**
- **Historia clínica**: Qué le ha pasado al animal
- **Signos clínicos**: Qué síntomas tiene
- **Tratamientos previos**: Qué medicamentos ha recibido
- **Instrucciones especiales**: Si hay algo específico que quieres que revisen

## ✅ Revisar y enviar

### Antes de enviar
1. **Revisa toda la información** que escribiste
2. **Verifica que esté completa** y correcta
3. **Puedes guardar como borrador** si quieres completarlo después

### Enviar el protocolo
1. **Hacer clic en "Enviar Protocolo"**
2. **El sistema te confirmará** que se envió correctamente
3. **Recibirás un número de protocolo** para seguimiento

![Confirmación de envío](assets/images/protocol-sent-confirmation.png)
*Captura de pantalla: Confirmación de que el protocolo fue enviado*

## 📊 Seguir el progreso de tu protocolo

### Estados del protocolo
Tu protocolo pasará por estos estados:
- **Enviado**: El laboratorio recibió tu protocolo
- **Recibido**: Llegó la muestra física al laboratorio
- **Procesando**: La muestra está siendo preparada
- **Analizando**: El histopatólogo está analizando
- **Informe listo**: El informe está terminado
- **Entregado**: Te enviaron el informe por email

### Cómo ver el estado
1. **Ir a "Mis Protocolos"** en tu panel
2. **Ver la lista** de todos tus protocolos
3. **Hacer clic en uno** para ver detalles

![Lista de protocolos](assets/images/protocol-list.png)
*Captura de pantalla: Lista de protocolos con sus estados*

## 📧 Notificaciones por email

Recibirás emails automáticamente cuando:
- **Tu muestra llega** al laboratorio
- **El análisis comienza**
- **El informe está listo**
- **Hay algún problema** con la muestra

![Ejemplo de notificación](assets/images/email-notification.png)
*Captura de pantalla: Ejemplo de notificación por email*

## 🏷️ Etiquetas para las muestras

### Después de enviar el protocolo
1. **Imprime las etiquetas** que genera el sistema
2. **Pega las etiquetas** en los contenedores de las muestras
3. **Envía las muestras** al laboratorio con las etiquetas

![Etiqueta de muestra](assets/images/sample-label.png)
*Captura de pantalla: Etiqueta generada para la muestra*

## ❓ Preguntas frecuentes

### ¿Puedo cambiar algo después de enviar?
**No**, una vez enviado no puedes editar. Pero puedes:
- **Agregar notas** en los detalles del protocolo
- **Contactar al laboratorio** si hay errores importantes

### ¿Cuánto tiempo toma?
- **Citología**: 1-2 días hábiles
- **Histopatología**: 3-5 días hábiles
- **Casos urgentes**: Se procesan más rápido

### ¿Qué pasa si mi muestra se daña?
**Contacta al laboratorio inmediatamente**. Evaluarán si aún se puede analizar o si necesitas enviar una nueva muestra.

### ¿Cómo sé que mi protocolo llegó bien?
- **Recibirás un email** de confirmación
- **Puedes ver el estado** en "Mis Protocolos"
- **El laboratorio te contactará** si hay algún problema

## 🆘 Si necesitas ayuda

### Problemas comunes
- **No puedo enviar el protocolo**: Revisa que todos los campos obligatorios estén llenos
- **No recibo emails**: Verifica tu carpeta de spam
- **No veo mi protocolo**: Refresca la página o cierra y abre el navegador

### Cómo obtener ayuda
1. **Revisar esta guía** para encontrar la respuesta
2. **Contactar soporte** usando el formulario en el sistema
3. **Llamar al laboratorio** para asuntos urgentes

---

*Siguiente: [Seguir muestras](tracking-samples.md)*
```

#### 2.2 Guía de Usuario para Histopatólogos

Crear `docs/user-guides/histopathologists/report-creation.md`:

```markdown
# Guía de Creación de Informes para Histopatólogos

Esta guía explica cómo los histopatólogos crean y gestionan informes de patología en el Sistema de Gestión de Laboratorio.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 📋 Resumen

Los histopatólogos son responsables de analizar muestras y crear informes detallados de patología. Esta guía cubre el flujo de trabajo completo de creación de informes.

## 🚀 Comenzando

### Acceder al Sistema

1. **Iniciar sesión**: Acceder al sistema con tus credenciales de histopatólogo
2. **Panel de control**: Ver tus protocolos asignados e informes pendientes

![Panel de Histopatólogo](assets/images/histopathologist-dashboard.png)
*Captura de pantalla: Panel de histopatólogo mostrando protocolos asignados e informes pendientes*

### Navegación

Áreas clave de navegación:
- **Panel de Control**: Resumen de tu trabajo
- **Protocolos Asignados**: Protocolos asignados a ti
- **Mis Informes**: Informes en los que estás trabajando
- **Informes Completados**: Informes terminados
- **Control de Calidad**: Revisión y aseguramiento de calidad

## 📊 Asignación de Protocolos

### Ver Protocolos Asignados

1. **Ir a "Protocolos Asignados"** desde la navegación
2. **Filtrar por Estado**: Usar filtros para encontrar protocolos por estado
3. **Opciones de Ordenamiento**: Ordenar por fecha, prioridad o número de protocolo

![Lista de Protocolos Asignados](assets/images/assigned-protocols.png)
*Captura de pantalla: Lista de protocolos asignados al histopatólogo*

### Detalles del Protocolo

Hacer clic en un protocolo para ver información completa:

![Vista de Detalles del Protocolo](assets/images/protocol-details-histopathologist.png)
*Captura de pantalla: Vista de detalles del protocolo para histopatólogos*

## 📝 Crear Informes

### Paso 1: Iniciar Creación de Informe

1. **Seleccionar Protocolo**: Elegir un protocolo de tu lista asignada
2. **Hacer clic en "Crear Informe"**: Iniciar el proceso de creación de informe
3. **Plantilla de Informe**: El sistema carga la plantilla apropiada

![Botón Crear Informe](assets/images/create-report-button.png)
*Captura de pantalla: Botón Crear Informe en la página de detalles del protocolo*

### Paso 2: Información del Informe

#### Datos Básicos del Informe
- **Fecha del Informe**: Fecha de creación del informe
- **Versión del Informe**: Número de versión (auto-incrementado)
- **Tipo de Informe**: Estándar, Urgente o Especial
- **Nivel de Complejidad**: Simple, Moderado o Complejo

![Información Básica del Informe](assets/images/report-basic-info.png)
*Captura de pantalla: Sección de información básica del informe*

#### Descripción Macroscópica
- **Descripción de la Muestra**: Descripción física de la muestra
- **Tamaño y Medidas**: Dimensiones y peso
- **Color y Consistencia**: Características visuales
- **Observaciones Adicionales**: Cualquier característica notable

![Descripción Macroscópica](assets/images/macroscopic-description.png)
*Captura de pantalla: Sección del formulario de descripción macroscópica*

### Paso 3: Análisis Microscópico

#### Gestión de Cassettes
- **Agregar Cassettes**: Crear cassettes para diferentes secciones de tejido
- **Etiquetas de Cassette**: Etiquetar cada cassette apropiadamente
- **Conteo de Secciones**: Número de secciones por cassette

![Gestión de Cassettes](assets/images/cassette-management.png)
*Captura de pantalla: Interfaz de gestión de cassettes*

#### Observaciones Microscópicas
Para cada cassette:

1. **Seleccionar Cassette**: Elegir el cassette a analizar
2. **Agregar Observaciones**: Registrar hallazgos microscópicos
3. **Usar Plantillas**: Seleccionar de plantillas de observación comunes
4. **Texto Personalizado**: Agregar observaciones personalizadas

![Observaciones Microscópicas](assets/images/microscopic-observations.png)
*Captura de pantalla: Formulario de observaciones microscópicas con opciones de plantilla*

#### Plantillas de Observación
Las plantillas comunes incluyen:
- **Patrones Inflamatorios**: Agudo, crónico, granulomatoso
- **Patrones Neoplásicos**: Benigno, maligno, metastásico
- **Cambios Degenerativos**: Necrosis, fibrosis, calcificación
- **Agentes Infecciosos**: Bacterias, hongos, parásitos

![Plantillas de Observación](assets/images/observation-templates.png)
*Captura de pantalla: Plantillas de observación disponibles*

### Paso 4: Diagnóstico y Conclusiones

#### Diagnóstico
- **Diagnóstico Primario**: Diagnóstico patológico principal
- **Diagnósticos Secundarios**: Hallazgos adicionales
- **Diagnósticos Diferenciales**: Posibilidades alternativas
- **Nivel de Confianza**: Alta, moderada o baja confianza

![Sección de Diagnóstico](assets/images/diagnosis-section.png)
*Captura de pantalla: Sección de diagnóstico y conclusiones*

#### Conclusiones
- **Resumen**: Breve resumen de hallazgos
- **Correlación Clínica**: Relación con signos clínicos
- **Recomendaciones**: Seguimiento o tratamiento sugerido
- **Pronóstico**: Resultado esperado

### Paso 5: Control de Calidad

#### Auto-Revisión
Antes de finalizar:
1. **Revisar Todas las Secciones**: Verificar completitud y precisión
2. **Verificar Ortografía**: Usar corrector ortográfico integrado
3. **Verificar Formato**: Asegurar formato apropiado
4. **Validar Datos**: Confirmar que todos los campos requeridos están completados

![Lista de Verificación de Control de Calidad](assets/images/quality-control-checklist.png)
*Captura de pantalla: Lista de verificación de control de calidad antes de la finalización*

#### Revisión por Pares (Opcional)
- **Solicitar Revisión**: Pedir a un colega que revise el informe
- **Comentarios de Revisión**: Abordar cualquier retroalimentación
- **Hacer Revisiones**: Actualizar informe basado en retroalimentación

## 📄 Finalización del Informe

### Proceso de Revisión Final

1. **Revisión Completa**: Asegurar que todas las secciones están completas
2. **Guardar Borrador**: Guardar como borrador para completar más tarde
3. **Finalizar Informe**: Marcar informe como listo para entrega

![Finalización del Informe](assets/images/report-finalization.png)
*Captura de pantalla: Interfaz de finalización de informe*

### Generación de PDF

Al finalizar:
1. **Generar PDF**: El sistema crea un informe PDF profesional
2. **Revisar PDF**: Verificar formato y contenido del PDF
3. **Entrega por Email**: El informe se envía automáticamente al veterinario

![Vista Previa del Informe PDF](assets/images/pdf-report-preview.png)
*Captura de pantalla: Vista previa del informe PDF generado*

## 📊 Gestión de Informes

### Ver Tus Informes

1. **Ir a "Mis Informes"**: Ver todos tus informes
2. **Opciones de Filtro**: Filtrar por estado, fecha o protocolo
3. **Buscar**: Buscar informes específicos

![Lista de Mis Informes](assets/images/my-reports-list.png)
*Captura de pantalla: Lista de informes del histopatólogo*

### Seguimiento del Estado del Informe

Los informes tienen los siguientes estados:
- **Borrador**: Siendo trabajado
- **Bajo Revisión**: Siendo revisado por pares
- **Finalizado**: Listo para entrega
- **Enviado**: Entregado al veterinario

### Editar Informes

- **Informes Borrador**: Pueden ser editados libremente
- **Informes Finalizados**: No pueden ser editados (crear nueva versión)
- **Control de Versiones**: El sistema rastrea todas las versiones

## 🔍 Aseguramiento de Calidad

### Estándares de Informe

Asegurar que los informes cumplan con estándares de calidad:
- **Completitud**: Todas las secciones requeridas llenas
- **Precisión**: Terminología y ortografía correctas
- **Claridad**: Lenguaje claro y conciso
- **Consistencia**: Formato y estilo consistentes

### Métricas de Calidad

El sistema rastrea métricas de calidad:
- **Tiempo de Completación del Informe**: Tiempo para completar informes
- **Tasa de Revisión**: Frecuencia de revisiones
- **Retroalimentación de Revisión por Pares**: Calidad de revisiones por pares

![Panel de Métricas de Calidad](assets/images/quality-metrics.png)
*Captura de pantalla: Panel de métricas de calidad para histopatólogos*

## 📚 Mejores Prácticas

### Consejos para Escribir Informes

1. **Usar Terminología Estándar**: Seguir estándares de patología veterinaria
2. **Ser Específico**: Proporcionar descripciones detalladas
3. **Incluir Medidas**: Cuantificar hallazgos cuando sea posible
4. **Correlacionar con Clínica**: Conectar hallazgos con signos clínicos
5. **Proporcionar Pronóstico**: Dar información clara del pronóstico

### Consejos de Eficiencia

1. **Usar Plantillas**: Aprovechar plantillas de observación
2. **Atajos de Teclado**: Aprender atajos del sistema
3. **Procesamiento por Lotes**: Procesar casos similares juntos
4. **Guardados Regulares**: Guardar trabajo frecuentemente

## ❓ Preguntas Comunes

### P: ¿Puedo editar un informe finalizado?
R: No, los informes finalizados no pueden ser editados. Crear una nueva versión si se necesitan cambios.

### P: ¿Cómo manejo casos difíciles?
R: Usar el sistema de revisión por pares o consultar con colegas a través del sistema.

### P: ¿Qué pasa si necesito agregar más cassettes?
R: Puedes agregar cassettes en cualquier momento antes de finalizar el informe.

### P: ¿Cuánto tiempo deberían tomar los informes para completarse?
R: Los informes estándar deberían completarse dentro de 2-3 días hábiles de recepción de la muestra.

## 🆘 Obtener Ayuda

- **Materiales de Entrenamiento**: Acceder a videos de entrenamiento y guías
- **Soporte Técnico**: Contactar soporte de TI para problemas del sistema
- **Preguntas Clínicas**: Consultar con patólogos senior
- **Aseguramiento de Calidad**: Contactar equipo de QA para preguntas de estándares

---

*Siguiente: [Análisis de Muestras](sample-analysis.md)*
```

### Fase 3: Documentación de Procesos Completos (3-4 horas)

#### 3.1 Viaje Completo de una Muestra

Crear `docs/workflows/complete-sample-journey.md`:

```markdown
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

### ¿Qué hace el veterinario?
1. **Inicia sesión** en el sistema
2. **Llena el formulario** con información del paciente
3. **Envía el protocolo** al laboratorio
4. **Imprime las etiquetas** para la muestra

### ¿Qué pasa en el sistema?
- **Se crea el protocolo** con un número único
- **Se genera la etiqueta** con código QR
- **Se envía confirmación** por email al veterinario

### ¿Cuánto tiempo toma?
- **Inmediato**: El protocolo se registra al instante

![Veterinario enviando protocolo](assets/images/veterinarian-submitting.png)
*Captura de pantalla: Veterinario completando el formulario de protocolo*

## 📦 Etapa 2: El laboratorio recibe la muestra

### ¿Qué hace el personal de laboratorio?
1. **Recibe la muestra física** con las etiquetas
2. **Verifica que coincida** con el protocolo
3. **Registra la llegada** en el sistema
4. **Actualiza el estado** a "Recibido"

### ¿Qué pasa en el sistema?
- **Se actualiza el estado** del protocolo
- **Se envía email** al veterinario confirmando recepción
- **Se inicia el procesamiento**

### ¿Cuánto tiempo toma?
- **1-2 días hábiles**: Desde el envío hasta la recepción

![Personal recibiendo muestra](assets/images/lab-staff-receiving.png)
*Captura de pantalla: Personal de laboratorio registrando la llegada de la muestra*

## 🔬 Etapa 3: Se procesa la muestra

### ¿Qué hace el personal de laboratorio?
1. **Prepara la muestra** para análisis
2. **Aplica las etiquetas** correctas
3. **Registra el procesamiento** en el sistema
4. **Asigna a un histopatólogo**

### ¿Qué pasa en el sistema?
- **Se actualiza el estado** a "Procesando"
- **Se asigna automáticamente** a un histopatólogo disponible
- **Se envía notificación** al histopatólogo

### ¿Cuánto tiempo toma?
- **1 día hábil**: Para preparar la muestra

![Procesamiento de muestra](assets/images/sample-processing.png)
*Captura de pantalla: Personal procesando la muestra en el laboratorio*

## 🔍 Etapa 4: Se analiza la muestra

### ¿Qué hace el histopatólogo?
1. **Recibe la muestra asignada**
2. **Revisa la información** del protocolo
3. **Analiza la muestra** microscópicamente
4. **Crea el informe** con sus hallazgos

### ¿Qué pasa en el sistema?
- **Se actualiza el estado** a "Analizando"
- **Se registra el progreso** del análisis
- **Se prepara el informe** para entrega

### ¿Cuánto tiempo toma?
- **Citología**: 1-2 días hábiles
- **Histopatología**: 3-5 días hábiles

![Histopatólogo analizando](assets/images/histopathologist-analyzing.png)
*Captura de pantalla: Histopatólogo analizando la muestra*

## 📄 Etapa 5: Se entrega el informe

### ¿Qué hace el sistema?
1. **Genera el informe PDF** profesional
2. **Envía el informe** por email al veterinario
3. **Actualiza el estado** a "Entregado"
4. **Registra la entrega** en el sistema

### ¿Qué recibe el veterinario?
- **Email con el informe** adjunto
- **Acceso al PDF** desde el sistema
- **Confirmación de entrega**

### ¿Cuánto tiempo toma?
- **Inmediato**: El informe se entrega al instante

![Entrega de informe](assets/images/report-delivery.png)
*Captura de pantalla: Email de entrega de informe al veterinario*

## 📊 Seguimiento del progreso

### Estados que verás
Tu protocolo pasará por estos estados:
- **Enviado**: Protocolo recibido por el laboratorio
- **Recibido**: Muestra física llegó al laboratorio
- **Procesando**: Muestra siendo preparada
- **Analizando**: Histopatólogo analizando
- **Informe listo**: Informe terminado
- **Entregado**: Informe enviado al veterinario

### Cómo ver el progreso
1. **En tu panel**: Verás el estado actual
2. **En "Mis Protocolos"**: Lista detallada de todos tus protocolos
3. **Por email**: Notificaciones automáticas en cada cambio

![Seguimiento de estado](assets/images/status-tracking.png)
*Captura de pantalla: Vista de seguimiento del estado del protocolo*

## ⏰ Tiempos totales

### Tiempo completo del proceso
- **Citología**: 3-4 días hábiles total
- **Histopatología**: 5-7 días hábiles total
- **Casos urgentes**: 1-2 días hábiles menos

### Desglose de tiempos
- **Envío**: Inmediato
- **Recepción**: 1-2 días
- **Procesamiento**: 1 día
- **Análisis**: 1-5 días (según tipo)
- **Entrega**: Inmediato

## 📧 Notificaciones que recibirás

### Para veterinarios
- **Protocolo recibido**: "Hemos recibido tu protocolo"
- **Muestra recibida**: "Tu muestra llegó al laboratorio"
- **Análisis iniciado**: "El análisis de tu muestra ha comenzado"
- **Informe listo**: "Tu informe está listo"

### Para histopatólogos
- **Nueva muestra**: "Tienes una nueva muestra para analizar"
- **Recordatorio**: "Tienes muestras pendientes de análisis"

### Para personal de laboratorio
- **Nuevo protocolo**: "Ha llegado un nuevo protocolo"
- **Muestra pendiente**: "Tienes muestras pendientes de procesar"

## 🚨 ¿Qué pasa si hay problemas?

### Problemas comunes y soluciones

#### La muestra se daña
- **El laboratorio te contactará** inmediatamente
- **Evaluarán si se puede analizar** o si necesitas enviar otra
- **No se te cobrará** si el problema no fue tuya

#### Información incorrecta
- **Contacta al laboratorio** lo antes posible
- **Pueden corregir** información básica
- **Para cambios importantes** pueden pedirte un nuevo protocolo

#### Retrasos en el proceso
- **El laboratorio te notificará** si hay retrasos
- **Te explicarán la razón** del retraso
- **Te darán una nueva fecha** estimada

## ❓ Preguntas frecuentes

### ¿Puedo acelerar el proceso?
**Sí**, puedes marcar casos como urgentes:
- **Durante el envío**: Marca "Urgente" en el formulario
- **Contacta al laboratorio**: Para casos muy urgentes
- **Costo adicional**: Los casos urgentes pueden tener costo extra

### ¿Qué pasa si no recibo el informe?
- **Revisa tu email**: Incluyendo la carpeta de spam
- **Verifica en el sistema**: El informe estará disponible ahí
- **Contacta al laboratorio**: Si no lo encuentras

### ¿Puedo pedir una segunda opinión?
**Sí**, puedes:
- **Pedir revisión**: Por otro histopatólogo
- **Solicitar consulta**: Con un especialista
- **Costo adicional**: Las segundas opiniones tienen costo extra

## 🆘 Si necesitas ayuda

### Durante el proceso
- **Revisa el estado** en tu panel de control
- **Contacta al laboratorio** si tienes dudas
- **Usa el chat de soporte** en el sistema

### Para problemas urgentes
- **Llama al laboratorio** directamente
- **Menciona tu número de protocolo**
- **Explica el problema** claramente

---

*Relacionado: [Operaciones diarias](daily-operations.md)*
```

### Fase 4: Documentación de Tareas Comunes (2-3 horas)

#### 4.1 Tareas Comunes para Todos los Usuarios

Crear `docs/common-tasks/password-reset.md`:

```markdown
# Cómo cambiar tu contraseña

Esta guía te explica cómo cambiar tu contraseña si la olvidaste o quieres cambiarla por seguridad.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🔑 ¿Cuándo necesitas cambiar tu contraseña?

### Cambios obligatorios
- **Primera vez**: Cuando accedes al sistema por primera vez
- **Contraseña expirada**: Cuando tu contraseña ha expirado
- **Seguridad**: Cuando el administrador te pide cambiarla

### Cambios voluntarios
- **Por seguridad**: Quieres una contraseña más segura
- **Sospecha de acceso**: Crees que alguien más conoce tu contraseña
- **Fácil de recordar**: Quieres una contraseña más fácil de recordar

## 🚀 Cómo cambiar tu contraseña

### Método 1: Desde dentro del sistema (si ya estás logueado)

#### Paso 1: Acceder a tu perfil
1. **Hacer clic en tu nombre** (esquina superior derecha)
2. **Seleccionar "Mi Perfil"** del menú
3. **Buscar la sección "Seguridad"**

![Acceso al perfil](assets/images/profile-access.png)
*Captura de pantalla: Cómo acceder a tu perfil de usuario*

#### Paso 2: Cambiar contraseña
1. **Hacer clic en "Cambiar Contraseña"**
2. **Ingresar tu contraseña actual**
3. **Escribir tu nueva contraseña**
4. **Confirmar la nueva contraseña**
5. **Hacer clic en "Guardar"**

![Cambio de contraseña](assets/images/password-change-form.png)
*Captura de pantalla: Formulario para cambiar contraseña*

### Método 2: Si olvidaste tu contraseña

#### Paso 1: Ir a la página de inicio de sesión
1. **Ir a la página de inicio** del sistema
2. **Hacer clic en "¿Olvidaste tu contraseña?"**
3. **Ingresar tu email**

![Olvidé mi contraseña](assets/images/forgot-password-link.png)
*Captura de pantalla: Enlace "¿Olvidaste tu contraseña?" en la página de inicio*

#### Paso 2: Recibir email de restablecimiento
1. **Revisar tu email** (incluyendo carpeta de spam)
2. **Buscar el email** del sistema
3. **Hacer clic en el enlace** del email

![Email de restablecimiento](assets/images/reset-password-email.png)
*Captura de pantalla: Email con enlace para restablecer contraseña*

#### Paso 3: Crear nueva contraseña
1. **Se abrirá una página** para crear nueva contraseña
2. **Escribir tu nueva contraseña**
3. **Confirmar la nueva contraseña**
4. **Hacer clic en "Restablecer"**

![Crear nueva contraseña](assets/images/create-new-password.png)
*Captura de pantalla: Formulario para crear nueva contraseña*

## 🔒 Consejos para una contraseña segura

### ¿Qué hace una contraseña segura?
- **Al menos 8 caracteres**: Mientras más larga, más segura
- **Letras y números**: Mezcla de letras y números
- **Mayúsculas y minúsculas**: Usa ambos tipos de letras
- **Símbolos especiales**: Si es posible, incluye !, @, #, etc.

### Ejemplos de contraseñas seguras
- **Buenas**: `MiPerro123!`, `Lab2025#`, `Vet2024$`
- **Malas**: `123456`, `password`, `admin`

### Consejos para recordar tu contraseña
- **Usa frases**: "MiPerroSeLlamaMax2024!"
- **Números significativos**: Tu año de nacimiento, número favorito
- **Evita información personal**: No uses tu nombre o fecha de nacimiento

## ❓ Problemas comunes y soluciones

### "No recibo el email de restablecimiento"
**Soluciones:**
- **Revisar carpeta de spam**: A veces llega ahí
- **Esperar unos minutos**: Puede tardar en llegar
- **Verificar el email**: Asegúrate de usar el email correcto
- **Contactar al administrador**: Si no llega en 15 minutos

### "El enlace del email no funciona"
**Soluciones:**
- **Copiar y pegar**: Copia el enlace completo del email
- **Verificar que no esté expirado**: Los enlaces expiran en 24 horas
- **Intentar de nuevo**: Solicita un nuevo email de restablecimiento

### "No puedo cambiar la contraseña desde mi perfil"
**Soluciones:**
- **Verificar contraseña actual**: Asegúrate de escribirla correctamente
- **Revisar requisitos**: La nueva contraseña debe cumplir los requisitos
- **Contactar soporte**: Si el problema persiste

### "Mi contraseña nueva no funciona"
**Soluciones:**
- **Verificar mayúsculas y minúsculas**: La contraseña distingue entre ellas
- **Revisar caracteres especiales**: Algunos símbolos pueden causar problemas
- **Intentar una contraseña más simple**: Sin caracteres especiales

## 🆘 Si necesitas ayuda

### Contactar soporte
1. **Usar el formulario de contacto** en el sistema
2. **Llamar al laboratorio** para asuntos urgentes
3. **Hablar con el administrador** del sistema

### Información que necesitarás
- **Tu email**: La dirección con la que intentas acceder
- **Tu nombre**: Para verificar tu identidad
- **Descripción del problema**: Qué está pasando exactamente

### Para emergencias
- **Llamar al laboratorio** directamente
- **Mencionar que es urgente**
- **Explicar que no puedes acceder al sistema**

---

*Relacionado: [Notificaciones por email](email-notifications.md)*
```

#### 4.2 Documentación de Problemas Comunes

Crear `docs/troubleshooting/common-issues.md`:

```markdown
# Problemas comunes y sus soluciones

Esta guía te ayuda a resolver los problemas más frecuentes que pueden ocurrir al usar el sistema.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🚫 No puedo iniciar sesión

### Problema: "Usuario o contraseña incorrectos"

**¿Qué significa?**
El sistema no reconoce tu email o contraseña.

**Soluciones:**
1. **Verificar tu email**: Asegúrate de escribir correctamente tu dirección de email
2. **Verificar tu contraseña**: Revisa que no haya errores de tipeo
3. **Mayúsculas y minúsculas**: La contraseña distingue entre mayúsculas y minúsculas
4. **Intentar restablecer contraseña**: Usar la opción "¿Olvidaste tu contraseña?"

![Error de inicio de sesión](assets/images/login-error.png)
*Captura de pantalla: Mensaje de error de inicio de sesión*

### Problema: "Cuenta no encontrada"

**¿Qué significa?**
El sistema no encuentra una cuenta con ese email.

**Soluciones:**
1. **Verificar el email**: Asegúrate de usar el email correcto
2. **Contactar al administrador**: Tu cuenta puede no estar creada aún
3. **Verificar con el laboratorio**: Confirmar que tu cuenta está activa

### Problema: "Sesión expirada"

**¿Qué significa?**
Tu sesión se cerró por seguridad después de un tiempo sin actividad.

**Soluciones:**
1. **Iniciar sesión nuevamente**: Simplemente vuelve a ingresar tus credenciales
2. **Marcar "Recordarme"**: Para evitar que expire la sesión
3. **Mantener el navegador abierto**: No cerrar la pestaña del sistema

## 📧 No recibo emails del sistema

### Problema: No llegan las notificaciones

**¿Qué puede estar pasando?**
- Los emails van a la carpeta de spam
- El email está mal escrito en el sistema
- Hay problemas con el servidor de email

**Soluciones:**
1. **Revisar carpeta de spam**: Los emails del sistema pueden llegar ahí
2. **Agregar a contactos**: Marcar el email del sistema como seguro
3. **Verificar tu email en el perfil**: Asegúrate de que esté correcto
4. **Contactar al administrador**: Si el problema persiste

![Carpeta de spam](assets/images/spam-folder.png)
*Captura de pantalla: Cómo revisar la carpeta de spam*

### Problema: Emails llegan pero no puedo abrir los archivos

**¿Qué puede estar pasando?**
- El archivo PDF está dañado
- Tu programa de email no puede abrir PDFs
- El archivo es muy grande

**Soluciones:**
1. **Descargar el archivo**: Hacer clic derecho y "Guardar como"
2. **Usar otro programa**: Abrir con Adobe Reader o navegador
3. **Acceder desde el sistema**: El informe también está disponible en tu panel

## 🖥️ El sistema se ve raro o no funciona bien

### Problema: La página se ve mal

**¿Qué puede estar pasando?**
- Problemas con el navegador
- Conexión a internet lenta
- El sistema está en mantenimiento

**Soluciones:**
1. **Refrescar la página**: Presionar F5 o Ctrl+R
2. **Cerrar y abrir el navegador**: Reiniciar el navegador
3. **Probar otro navegador**: Chrome, Firefox, Safari, Edge
4. **Limpiar caché**: Borrar datos del navegador
5. **Verificar conexión**: Asegurarte de tener buena conexión a internet

![Página que se ve mal](assets/images/broken-page.png)
*Captura de pantalla: Ejemplo de página que se ve mal*

### Problema: Los botones no funcionan

**¿Qué puede estar pasando?**
- JavaScript deshabilitado
- Problemas con el navegador
- El sistema está cargando

**Soluciones:**
1. **Esperar un momento**: El sistema puede estar cargando
2. **Refrescar la página**: Recargar la página
3. **Verificar JavaScript**: Asegurarte de que JavaScript esté habilitado
4. **Probar otro navegador**: Cambiar de navegador

## 📱 Problemas en el teléfono

### Problema: No puedo usar el sistema en el teléfono

**¿Qué puede estar pasando?**
- El navegador del teléfono no es compatible
- La pantalla es muy pequeña
- Problemas de conexión

**Soluciones:**
1. **Usar navegador actualizado**: Chrome o Safari en el teléfono
2. **Girar la pantalla**: Para mejor visualización
3. **Hacer zoom**: Para ver mejor los botones
4. **Usar computadora**: Para tareas complejas

![Sistema en teléfono](assets/images/mobile-view.png)
*Captura de pantalla: Cómo se ve el sistema en el teléfono*

## 📄 No puedo ver o descargar informes

### Problema: El informe no se abre

**¿Qué puede estar pasando?**
- El archivo PDF está dañado
- No tienes programa para abrir PDFs
- Problemas de descarga

**Soluciones:**
1. **Descargar el archivo**: Hacer clic derecho y "Guardar como"
2. **Usar Adobe Reader**: Descargar programa gratuito para PDFs
3. **Abrir en el navegador**: Los navegadores pueden abrir PDFs
4. **Contactar al laboratorio**: Si el archivo está dañado

### Problema: No encuentro mi informe

**¿Qué puede estar pasando?**
- El informe aún no está listo
- Está en otra sección del sistema
- Hay problemas con la búsqueda

**Soluciones:**
1. **Verificar el estado**: Revisar si el protocolo está en "Informe listo"
2. **Buscar en "Mis Protocolos"**: El informe estará ahí
3. **Revisar email**: El informe se envía por email
4. **Contactar al laboratorio**: Si no lo encuentras

## ⏰ El sistema está lento

### Problema: Todo tarda mucho en cargar

**¿Qué puede estar pasando?**
- Conexión a internet lenta
- Muchos usuarios usando el sistema
- Problemas con el servidor

**Soluciones:**
1. **Verificar conexión**: Asegurarte de tener buena conexión
2. **Esperar un momento**: El sistema puede estar ocupado
3. **Intentar más tarde**: Si hay muchos usuarios
4. **Contactar soporte**: Si el problema persiste

## 🆘 Cuándo contactar soporte

### Contactar inmediatamente si:
- **No puedes acceder** al sistema por más de 1 hora
- **Pierdes información importante** del sistema
- **El sistema está completamente roto**
- **Hay problemas de seguridad**

### Información para dar al soporte:
- **Tu email**: Con el que intentas acceder
- **Tu rol**: Veterinario, histopatólogo, personal, administrador
- **Descripción del problema**: Qué está pasando exactamente
- **Cuándo empezó**: Hora y fecha del problema
- **Qué estabas haciendo**: Cuando ocurrió el problema
- **Navegador que usas**: Chrome, Firefox, Safari, etc.

### Cómo contactar soporte:
1. **Formulario de contacto** en el sistema
2. **Email de soporte**: support@laboratorio.com
3. **Teléfono del laboratorio**: Para asuntos urgentes
4. **Hablar con el administrador**: Para problemas de acceso

---

*Relacionado: [Preguntas frecuentes](faq.md)*
```

## Resumen de la Implementación

### **Objetivos del Paso 19**

Este paso crea documentación completa orientada al usuario que:

1. **Explica el sistema en términos simples** - Sin jerga técnica
2. **Guía a cada tipo de usuario** - Veterinarios, histopatólogos, personal, administradores
3. **Cubre procesos completos** - Desde el envío hasta la entrega
4. **Resuelve problemas comunes** - Soluciones prácticas para usuarios
5. **Está completamente en español** - Para servir al personal hispanohablante

### **Estructura de Documentación**

```
docs/
├── index.md                           # Página principal de la guía
├── getting-started/                   # Cómo empezar a usar el sistema
├── user-guides/                       # Guías específicas por rol
├── workflows/                         # Procesos completos del laboratorio
├── common-tasks/                      # Tareas que todos necesitan hacer
├── troubleshooting/                   # Ayuda para resolver problemas
└── assets/                           # Imágenes y recursos
```

### **Características Clave**

- **Lenguaje simple**: Sin términos técnicos complicados
- **Paso a paso**: Instrucciones claras y detalladas
- **Capturas de pantalla**: Imágenes que muestran exactamente qué hacer
- **Preguntas frecuentes**: Respuestas a dudas comunes
- **Solución de problemas**: Ayuda para resolver problemas
- **Completamente en español**: Para el personal del laboratorio

### **Beneficios para los Usuarios**

1. **Fácil de entender**: Cualquiera puede seguir las guías
2. **Ahorra tiempo**: No necesitan preguntar cómo hacer las cosas
3. **Reduce errores**: Instrucciones claras evitan confusiones
4. **Aumenta confianza**: Los usuarios se sienten seguros usando el sistema
5. **Mejora la adopción**: Más usuarios usarán el sistema correctamente

### **Próximos Pasos**

Después de crear esta documentación:

1. **Agregar capturas de pantalla** reales del sistema
2. **Probar las guías** con usuarios reales
3. **Actualizar según feedback** de los usuarios
4. **Crear videos tutoriales** para procesos complejos
5. **Mantener actualizada** cuando cambie el sistema

---

*Paso 19 - Documentación de Usuario y Guía de Uso*  
*Creado: Enero 2025*  
*Prioridad: Alta - Esencial para adopción de usuarios y entrenamiento*

**IMPORTANTE: Toda la documentación debe estar en español para servir al personal del laboratorio y veterinarios de habla hispana.**
