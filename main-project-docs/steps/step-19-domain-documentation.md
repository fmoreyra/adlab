# Step 19: Domain Documentation & Usage Guide

## Overview

This step creates comprehensive domain documentation that explains how the laboratory management system should be used. **ALL DOCUMENTATION MUST BE WRITTEN IN SPANISH** to serve the Spanish-speaking laboratory staff and veterinarians. The documentation includes usage examples, workflow descriptions, and placeholder sections for screenshots and visual guides.

## Documentation Structure

### **Documentation Architecture**

```
docs/
├── index.md                    # Main documentation index
├── getting-started/
│   ├── overview.md            # System overview
│   ├── installation.md        # Installation guide
│   └── first-steps.md         # Getting started guide
├── user-guides/
│   ├── veterinarians/         # Veterinarian user guide
│   ├── histopathologists/     # Histopathologist user guide
│   ├── staff/                 # Laboratory staff guide
│   └── administrators/        # System administrator guide
├── workflows/
│   ├── protocol-submission.md # Protocol submission workflow
│   ├── sample-processing.md   # Sample processing workflow
│   ├── report-generation.md   # Report generation workflow
│   └── work-orders.md         # Work order workflow
├── features/
│   ├── authentication.md      # User authentication
│   ├── email-notifications.md # Email system
│   ├── pdf-generation.md      # PDF generation
│   ├── dashboards.md          # User dashboards
│   └── monitoring.md          # System monitoring
├── api/
│   ├── rest-api.md            # REST API documentation
│   ├── webhooks.md            # Webhook documentation
│   └── integration.md         # Third-party integration
├── administration/
│   ├── user-management.md     # User management
│   ├── system-configuration.md # System configuration
│   ├── backup-restore.md      # Backup and restore
│   └── troubleshooting.md     # Troubleshooting guide
└── assets/
    ├── images/                # Screenshots and diagrams
    ├── videos/                # Video tutorials
    └── templates/             # Document templates
```

## Implementation Plan

### Phase 1: Core Documentation Structure (2-3 hours)

#### 1.1 Main Documentation Index

Create `docs/index.md`:

```markdown
# Documentación del Sistema de Gestión de Laboratorio

Bienvenido a la documentación completa del Sistema de Gestión de Laboratorio. Este sistema está diseñado para optimizar las operaciones del laboratorio de patología, desde la presentación de protocolos hasta la entrega de informes.

**IMPORTANTE: Toda la documentación está en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🚀 Inicio Rápido

- [Resumen del Sistema](getting-started/overview.md) - Entender qué hace el sistema
- [Guía de Instalación](getting-started/installation.md) - Configurar el sistema
- [Primeros Pasos](getting-started/first-steps.md) - Comenzar con operaciones básicas

## 👥 Guías de Usuario

### Veterinarios
- [Presentación de Protocolos](user-guides/veterinarians/protocol-submission.md) - Enviar muestras para análisis
- [Acceso a Informes](user-guides/veterinarians/report-access.md) - Ver y descargar informes
- [Órdenes de Trabajo](user-guides/veterinarians/work-orders.md) - Crear y gestionar órdenes de trabajo

### Histopatólogos
- [Creación de Informes](user-guides/histopathologists/report-creation.md) - Crear informes de patología
- [Análisis de Muestras](user-guides/histopathologists/sample-analysis.md) - Analizar muestras
- [Control de Calidad](user-guides/histopathologists/quality-control.md) - Asegurar la calidad de los informes

### Personal de Laboratorio
- [Recepción de Muestras](user-guides/staff/sample-reception.md) - Recibir y procesar muestras
- [Procesamiento de Muestras](user-guides/staff/sample-processing.md) - Procesar muestras para análisis
- [Gestión de Inventario](user-guides/staff/inventory-management.md) - Gestionar inventario del laboratorio

### Administradores
- [Gestión de Usuarios](user-guides/administrators/user-management.md) - Gestionar usuarios del sistema
- [Configuración del Sistema](user-guides/administrators/system-configuration.md) - Configurar ajustes del sistema
- [Monitoreo](user-guides/administrators/monitoring.md) - Monitorear rendimiento del sistema

## 🔄 Flujos de Trabajo

- [Flujo de Presentación de Protocolos](workflows/protocol-submission.md) - Proceso completo de presentación de protocolos
- [Flujo de Procesamiento de Muestras](workflows/sample-processing.md) - Procesamiento de muestras desde recepción hasta análisis
- [Flujo de Generación de Informes](workflows/report-generation.md) - Creación y entrega de informes
- [Flujo de Órdenes de Trabajo](workflows/work-orders.md) - Creación y gestión de órdenes de trabajo

## ⚙️ Características

- [Autenticación y Seguridad](features/authentication.md) - Autenticación de usuarios y seguridad
- [Notificaciones por Email](features/email-notifications.md) - Sistema de email automatizado
- [Generación de PDF](features/pdf-generation.md) - Generación de informes y documentos
- [Paneles de Usuario](features/dashboards.md) - Interfaces de usuario personalizadas
- [Monitoreo del Sistema](features/monitoring.md) - Monitoreo de rendimiento y métricas

## 🔌 Integración

- [API REST](api/rest-api.md) - Documentación de API para desarrolladores
- [Webhooks](api/webhooks.md) - Configuración y uso de webhooks
- [Integración de Terceros](api/integration.md) - Integración con sistemas externos

## 🛠️ Administración

- [Gestión de Usuarios](administration/user-management.md) - Gestionar usuarios del sistema
- [Configuración del Sistema](administration/system-configuration.md) - Configuración y ajustes del sistema
- [Respaldo y Restauración](administration/backup-restore.md) - Respaldo y recuperación de datos
- [Solución de Problemas](administration/troubleshooting.md) - Problemas comunes y soluciones

## 📞 Soporte

- [Preguntas Frecuentes](support/faq.md) - Preguntas frecuentes
- [Contactar Soporte](support/contact.md) - Cómo obtener ayuda
- [Solicitudes de Características](support/feature-requests.md) - Solicitar nuevas características

---

*Last updated: January 2025*
*Version: 1.0*
```

#### 1.2 Getting Started Documentation

Create `docs/getting-started/overview.md`:

```markdown
# Resumen del Sistema

El Sistema de Gestión de Laboratorio es una plataforma web integral diseñada para optimizar las operaciones del laboratorio de patología. Gestiona el flujo de trabajo completo desde la presentación de muestras hasta la entrega de informes.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🎯 Qué Hace Este Sistema

### Funcionalidad Principal

1. **Gestión de Protocolos**
   - Los veterinarios envían protocolos para análisis de muestras
   - Seguimiento del estado del protocolo durante todo el proceso
   - Gestión de revisiones y actualizaciones de protocolos

2. **Procesamiento de Muestras**
   - El personal del laboratorio recibe y procesa muestras
   - Generación de etiquetas de muestras con códigos QR
   - Seguimiento de la condición de la muestra y etapas de procesamiento

3. **Generación de Informes**
   - Los histopatólogos crean informes detallados de patología
   - Generación de informes PDF profesionales
   - Entrega de informes por email a veterinarios

4. **Gestión de Órdenes de Trabajo**
   - Crear y gestionar órdenes de trabajo
   - Seguimiento del estado de facturación y pago
   - Generación de PDFs de órdenes de trabajo

5. **Gestión de Usuarios**
   - Control de acceso basado en roles
   - Autenticación y autorización de usuarios
   - Seguimiento de actividades y registros de auditoría

## 🏗️ Arquitectura del Sistema

### Roles de Usuario

- **Veterinarios**: Enviar protocolos, ver informes, crear órdenes de trabajo
- **Histopatólogos**: Crear y finalizar informes, analizar muestras
- **Personal de Laboratorio**: Recibir muestras, procesar muestras, gestionar inventario
- **Administradores**: Gestionar usuarios, configurar sistema, monitorear rendimiento

### Stack Tecnológico

- **Backend**: Django (Python)
- **Base de Datos**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript (Tailwind CSS)
- **Cola de Tareas**: Celery con Redis
- **Email**: SMTP con procesamiento asíncrono
- **Generación de PDF**: ReportLab
- **Monitoreo**: Prometheus, Grafana, Loki

## 📊 Métricas Clave

El sistema rastrea métricas importantes incluyendo:
- Tasas de presentación de protocolos
- Tiempos de generación de informes
- Actividad y participación del usuario
- Rendimiento y confiabilidad del sistema

## 🔒 Características de Seguridad

- Autenticación y autorización de usuarios
- Control de acceso basado en roles
- Registro de auditoría para todas las acciones
- Almacenamiento y transmisión segura de archivos
- Cifrado y seguridad de email

## 📱 Interfaz de Usuario

El sistema proporciona:
- Interfaz web responsiva
- Paneles específicos por rol
- Navegación intuitiva
- Diseño compatible con dispositivos móviles
- Cumplimiento de accesibilidad

---

*Siguiente: [Guía de Instalación](installation.md)*
```

Create `docs/getting-started/installation.md`:

```markdown
# Guía de Instalación

Esta guía te ayudará a instalar y configurar el Sistema de Gestión de Laboratorio.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 📋 Prerrequisitos

### Requisitos del Sistema

- **Sistema Operativo**: Linux (Ubuntu 20.04+ recomendado)
- **Python**: 3.9 o superior
- **PostgreSQL**: 12 o superior
- **Redis**: 6.0 o superior
- **Memoria**: Mínimo 4GB RAM
- **Almacenamiento**: Mínimo 20GB de espacio libre

### Dependencias de Software

- Docker y Docker Compose (para despliegue containerizado)
- Git (para acceso al repositorio de código)
- Certificado SSL (para despliegue en producción)

## 🚀 Métodos de Instalación

### Método 1: Despliegue con Docker (Recomendado)

#### Paso 1: Clonar Repositorio
```bash
git clone <repository-url>
cd laboratory-system
```

#### Paso 2: Configurar Entorno
```bash
cp .env.example .env
# Editar .env con tu configuración
```

#### Paso 3: Iniciar Servicios
```bash
docker-compose up -d
```

#### Paso 4: Inicializar Base de Datos
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Método 2: Instalación Manual

#### Paso 1: Instalar Dependencias de Python
```bash
pip install -r requirements.txt
```

#### Paso 2: Configurar Base de Datos
```bash
# Crear base de datos PostgreSQL
createdb laboratory_system

# Ejecutar migraciones
python manage.py migrate
```

#### Paso 3: Crear Superusuario
```bash
python manage.py createsuperuser
```

#### Paso 4: Iniciar Servicios
```bash
# Iniciar servidor de desarrollo Django
python manage.py runserver

# Iniciar worker de Celery (en terminal separada)
celery -A config worker -l info
```

## ⚙️ Configuración

### Variables de Entorno

Crear un archivo `.env` con las siguientes variables:

```bash
# Configuración de Base de Datos
DATABASE_URL=postgresql://user:password@localhost:5432/laboratory_system

# Configuración de Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion

# Seguridad
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=False

# Configuración de Redis
REDIS_URL=redis://localhost:6379/0

# Almacenamiento de Archivos
MEDIA_ROOT=/ruta/a/archivos/media
STATIC_ROOT=/ruta/a/archivos/static
```

### Configuración de Django

Configuraciones clave a configurar en `settings.py`:

```python
# Configuración del Sitio
SITE_URL = "https://tu-dominio.com"
SITE_NAME = "Sistema de Gestión de Laboratorio"

# Configuración de Email
DEFAULT_FROM_EMAIL = "noreply@tu-dominio.com"

# Configuración de Carga de Archivos
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
```

## 🔧 Configuración Post-Instalación

### 1. Crear Roles de Usuario

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# Crear grupos
veterinarians_group = Group.objects.create(name='Veterinarios')
histopathologists_group = Group.objects.create(name='Histopatólogos')
staff_group = Group.objects.create(name='Personal de Laboratorio')
admins_group = Group.objects.create(name='Administradores')

# Asignar permisos (ejemplo)
protocol_permissions = Permission.objects.filter(
    content_type__app_label='protocols'
)
veterinarians_group.permissions.set(protocol_permissions)
```

### 2. Configurar Plantillas de Email

El sistema incluye plantillas de email predeterminadas. Personalízalas en:
- `templates/emails/`
- `src/protocols/templates/emails/`

### 3. Configurar Monitoreo (Opcional)

```bash
# Iniciar stack de monitoreo
cd monitoring
docker-compose up -d
```

## ✅ Verificación

### Probar Instalación

1. **Acceder al sistema**: Navegar a `http://localhost:8000`
2. **Iniciar sesión**: Usar la cuenta de superusuario que creaste
3. **Verificar panel de administración**: Acceder a `/admin/` para verificar configuración de base de datos
4. **Probar email**: Enviar un email de prueba para verificar configuración de email

### Verificaciones de Salud

```bash
# Verificar aplicación Django
curl http://localhost:8000/health/

# Verificar workers de Celery
celery -A config inspect active

# Verificar conexión a base de datos
python manage.py dbshell
```

## 🚨 Solución de Problemas

### Problemas Comunes

#### Error de Conexión a Base de Datos
```bash
# Verificar estado de PostgreSQL
sudo systemctl status postgresql

# Verificar que la base de datos existe
psql -l | grep laboratory_system
```

#### Problemas de Configuración de Email
```bash
# Probar configuración de email
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail('Asunto de Prueba', 'Mensaje de prueba', 'desde@ejemplo.com', ['para@ejemplo.com'])
```

#### Problemas con Workers de Celery
```bash
# Verificar conexión a Redis
redis-cli ping

# Reiniciar workers de Celery
celery -A config control shutdown
celery -A config worker -l info
```

## 📚 Próximos Pasos

Después de una instalación exitosa:

1. [Guía de Primeros Pasos](first-steps.md) - Aprender uso básico del sistema
2. [Gestión de Usuarios](administration/user-management.md) - Configurar cuentas de usuario
3. [Configuración del Sistema](administration/system-configuration.md) - Configurar ajustes del sistema

---

*Anterior: [Resumen del Sistema](overview.md)*  
*Siguiente: [Primeros Pasos](first-steps.md)*
```

### Fase 2: Guías de Usuario (4-5 horas)

#### 2.1 Guía de Usuario para Veterinarios

Crear `docs/user-guides/veterinarians/protocol-submission.md`:

```markdown
# Guía de Presentación de Protocolos para Veterinarios

Esta guía explica cómo los veterinarios pueden presentar protocolos para análisis de muestras en el Sistema de Gestión de Laboratorio.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 📋 Resumen

La presentación de protocolos es el primer paso en el flujo de trabajo del laboratorio. Los veterinarios crean protocolos que contienen información sobre el animal, la muestra y el análisis solicitado.

## 🚀 Comenzando

### Acceder al Sistema

1. **Iniciar sesión**: Navegar a la URL del sistema e iniciar sesión con tus credenciales
2. **Panel de control**: Verás tu panel personalizado con protocolos recientes y notificaciones

![Panel de Veterinario](assets/images/veterinarian-dashboard.png)
*Captura de pantalla: Panel de veterinario mostrando protocolos recientes y acciones rápidas*

### Navegación

La navegación principal incluye:
- **Panel de Control**: Resumen de tus protocolos y actividades
- **Nuevo Protocolo**: Crear una nueva presentación de protocolo
- **Mis Protocolos**: Ver y gestionar tus protocolos enviados
- **Informes**: Acceder a informes completados
- **Órdenes de Trabajo**: Crear y gestionar órdenes de trabajo

## 📝 Crear un Nuevo Protocolo

### Paso 1: Acceder a la Creación de Protocolo

1. Hacer clic en **"Nuevo Protocolo"** desde el panel de control o menú de navegación
2. Serás llevado al formulario de creación de protocolo

![Botón Nuevo Protocolo](assets/images/new-protocol-button.png)
*Captura de pantalla: Botón Nuevo Protocolo en el panel de control*

### Paso 2: Llenar Información del Protocolo

#### Información Básica
- **Identificación del Animal**: Nombre, ID u otro identificador
- **Especie**: Seleccionar del menú desplegable (Canino, Felino, Equino, Bovino, Otro)
- **Raza**: Ingresar información de la raza
- **Edad**: Edad del animal
- **Sexo**: Macho, Hembra o Desconocido

![Información Básica del Protocolo](assets/images/protocol-basic-info.png)
*Captura de pantalla: Sección de información básica del formulario de protocolo*

#### Información del Propietario
- **Nombre del Propietario**: Nombre del propietario del animal
- **Contacto del Propietario**: Número de teléfono y email
- **Dirección del Propietario**: Información completa de la dirección

#### Información de la Muestra
- **Tipo de Análisis**: 
  - **Citología**: Para aspirados con aguja fina, frotis de impresión
  - **Histopatología**: Para biopsias de tejido, especímenes quirúrgicos
- **Tipo de Muestra**: Tipo específico de muestra
- **Fecha de Recolección**: Cuándo se recolectó la muestra
- **Diagnóstico Presuntivo**: Tu diagnóstico inicial o sospecha

![Sección de Información de Muestra](assets/images/sample-information.png)
*Captura de pantalla: Sección de información de muestra con selección de tipo de análisis*

#### Información Clínica
- **Historia Clínica**: Historia clínica detallada
- **Signos Clínicos**: Signos y síntomas observados
- **Tratamientos Previos**: Cualquier tratamiento administrado
- **Instrucciones Especiales**: Cualquier solicitud específica de manejo o procesamiento

### Paso 3: Revisar y Enviar

1. **Revisar Información**: Revisar cuidadosamente toda la información ingresada
2. **Guardar Borrador**: Usar "Guardar Borrador" para guardar para completar más tarde
3. **Enviar Protocolo**: Hacer clic en "Enviar Protocolo" para enviar para procesamiento

![Revisión de Protocolo](assets/images/protocol-review.png)
*Captura de pantalla: Página de revisión de protocolo antes del envío*

## 📊 Gestionar Tus Protocolos

### Ver Estado del Protocolo

Después del envío, puedes rastrear el progreso de tu protocolo:

1. **Ir a "Mis Protocolos"** desde el menú de navegación
2. **Ver Estado**: Cada protocolo muestra su estado actual:
   - **Borrador**: Aún no enviado
   - **Enviado**: Enviado al laboratorio
   - **Recibido**: Muestra recibida por el laboratorio
   - **Procesando**: Muestra siendo procesada
   - **Informe Listo**: Informe completado y disponible
   - **Informe Enviado**: Informe entregado por email

![Lista de Estado de Protocolos](assets/images/protocol-status-list.png)
*Captura de pantalla: Lista de protocolos con indicadores de estado*

### Detalles del Protocolo

Hacer clic en cualquier protocolo para ver información detallada:

![Detalles del Protocolo](assets/images/protocol-details.png)
*Captura de pantalla: Vista detallada del protocolo con toda la información*

### Editar Protocolos

- **Protocolos Borrador**: Pueden ser editados hasta ser enviados
- **Protocolos Enviados**: No pueden ser editados, pero puedes agregar notas
- **Agregar Notas**: Usar la sección de notas para proporcionar información adicional

## 📧 Notificaciones por Email

Recibirás notificaciones por email para eventos importantes:

- **Protocolo Recibido**: Cuando el laboratorio recibe tu muestra
- **Informe Listo**: Cuando tu informe está completado
- **Actualizaciones de Estado**: Para cambios significativos de estado

![Ejemplo de Notificación por Email](assets/images/email-notification.png)
*Captura de pantalla: Ejemplo de notificación por email para completación de informe*

## 🏷️ Etiquetas de Muestras

Después de la presentación del protocolo:

1. **Imprimir Etiquetas**: Generar etiquetas con código QR para tus muestras
2. **Adjuntar Etiquetas**: Adjuntar etiquetas a los contenedores de muestras
3. **Enviar Muestras**: Enviar muestras al laboratorio con etiquetado apropiado

![Ejemplo de Etiqueta de Muestra](assets/images/sample-label.png)
*Captura de pantalla: Etiqueta de muestra generada con código QR*

## ❓ Preguntas Comunes

### P: ¿Puedo editar un protocolo después del envío?
R: No, los protocolos enviados no pueden ser editados. Sin embargo, puedes agregar notas o contactar al laboratorio para correcciones.

### P: ¿Cuánto tiempo toma procesar una muestra?
R: El tiempo de procesamiento varía según el tipo de análisis:
- Citología: 1-2 días hábiles
- Histopatología: 3-5 días hábiles

### P: ¿Qué pasa si necesito agregar más información?
R: Usa la sección de notas en los detalles del protocolo para agregar información adicional.

### P: ¿Cómo rastreo el progreso de mi protocolo?
R: Verifica el estado en "Mis Protocolos" o espera las notificaciones por email.

## 🆘 Obtener Ayuda

Si encuentras problemas:

1. **Revisar FAQ**: Revisar preguntas frecuentes
2. **Contactar Soporte**: Usar el formulario de contacto de soporte
3. **Llamar al Laboratorio**: Contactar al laboratorio directamente para asuntos urgentes

---

*Siguiente: [Acceso a Informes](report-access.md)*
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

### Fase 3: Documentación de Flujos de Trabajo (3-4 horas)

#### 3.1 Flujo de Trabajo de Presentación de Protocolos

Crear `docs/workflows/protocol-submission.md`:

```markdown
# Flujo de Trabajo de Presentación de Protocolos

Este documento describe el flujo de trabajo completo de presentación de protocolos desde la creación inicial hasta el procesamiento en el laboratorio.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🔄 Resumen del Flujo de Trabajo

El flujo de trabajo de presentación de protocolos involucra múltiples partes interesadas y varias etapas:

```mermaid
graph TD
    A[Veterinario Crea Protocolo] --> B[Protocolo Enviado]
    B --> C[Laboratorio Recibe Protocolo]
    C --> D[Recepción de Muestra]
    D --> E[Procesamiento de Muestra]
    E --> F[Protocolo Asignado a Histopatólogo]
    F --> G[Análisis Comienza]
```

## 👥 Partes Interesadas

- **Veterinario**: Crea y envía protocolos
- **Personal de Laboratorio**: Recibe y procesa muestras
- **Histopatólogo**: Analiza muestras y crea informes
- **Administrador del Sistema**: Gestiona configuración del sistema

## 📋 Pasos Detallados del Flujo de Trabajo

### Paso 1: Creación de Protocolo (Veterinario)

#### 1.1 Acceder al Sistema
- Iniciar sesión en el Sistema de Gestión de Laboratorio
- Navegar a "Nuevo Protocolo" desde el panel de control

![Proceso de Inicio de Sesión](assets/images/login-process.png)
*Captura de pantalla: Veterinario iniciando sesión en el sistema*

#### 1.2 Llenar Formulario de Protocolo
- Completar todos los campos requeridos
- Subir cualquier documento de apoyo
- Revisar información para precisión

![Formulario de Protocolo](assets/images/protocol-form-complete.png)
*Captura de pantalla: Formulario completo de presentación de protocolo*

#### 1.3 Enviar Protocolo
- Hacer clic en el botón "Enviar Protocolo"
- El sistema valida todos los campos requeridos
- El estado del protocolo cambia a "Enviado"

![Presentación de Protocolo](assets/images/protocol-submission.png)
*Captura de pantalla: Confirmación de presentación de protocolo*

### Paso 2: Recepción en Laboratorio (Personal de Laboratorio)

#### 2.1 Notificación de Protocolo
- El personal recibe notificación por email de nuevo protocolo
- El protocolo aparece en la lista "Recepción Pendiente"

![Notificación de Recepción](assets/images/reception-notification.png)
*Captura de pantalla: Notificación por email para nuevo protocolo*

#### 2.2 Recepción de Muestra
- El personal recibe muestra física
- Verifica que la muestra coincida con la información del protocolo
- Registra condición y calidad de la muestra

![Recepción de Muestra](assets/images/sample-reception-process.png)
*Captura de pantalla: Interfaz de recepción de muestra*

#### 2.3 Actualización de Estado del Protocolo
- El personal actualiza el estado del protocolo a "Recibido"
- El sistema envía email de confirmación al veterinario
- Comienza el procesamiento de la muestra

![Actualización de Estado](assets/images/status-update-received.png)
*Captura de pantalla: Actualización de estado del protocolo a "Recibido"*

### Paso 3: Procesamiento de Muestra (Personal de Laboratorio)

#### 3.1 Preparación de Muestra
- El personal prepara la muestra para análisis
- Crea etiquetas de muestra con códigos QR
- Registra detalles de procesamiento

![Preparación de Muestra](assets/images/sample-preparation.png)
*Captura de pantalla: Proceso de preparación y etiquetado de muestra*

#### 3.2 Control de Calidad
- El personal realiza verificaciones de control de calidad
- Documenta cualquier problema o preocupación
- Actualiza protocolo con notas de procesamiento

![Control de Calidad](assets/images/quality-control-processing.png)
*Captura de pantalla: Lista de verificación de control de calidad durante el procesamiento*

### Paso 4: Asignación de Histopatólogo

#### 4.1 Asignación Automática
- El sistema asigna automáticamente el protocolo al histopatólogo disponible
- Asignación basada en carga de trabajo y experiencia

![Proceso de Asignación](assets/images/assignment-process.png)
*Captura de pantalla: Asignación automática de protocolo a histopatólogo*

#### 4.2 Asignación Manual (si es necesario)
- El administrador puede asignar protocolos manualmente
- Considerar carga de trabajo y especialización del histopatólogo

![Asignación Manual](assets/images/manual-assignment.png)
*Captura de pantalla: Interfaz de asignación manual de protocolo*

### Paso 5: Análisis Comienza (Histopatólogo)

#### 5.1 Revisión de Protocolo
- El histopatólogo revisa la información del protocolo
- Verifica calidad y preparación de la muestra
- Comienza análisis microscópico

![Revisión de Protocolo](assets/images/histopathologist-protocol-review.png)
*Captura de pantalla: Histopatólogo revisando protocolo asignado*

#### 5.2 Creación de Informe
- El histopatólogo crea informe detallado
- Documenta todos los hallazgos y observaciones
- Prepara diagnóstico y conclusiones

![Creación de Informe](assets/images/report-creation-process.png)
*Captura de pantalla: Interfaz de creación de informe*

## 📊 Seguimiento de Estado

### Estados del Protocolo

| Estado | Descripción | Parte Responsable |
|--------|-------------|-------------------|
| Borrador | Protocolo siendo creado | Veterinario |
| Enviado | Protocolo enviado al laboratorio | Veterinario |
| Recibido | Muestra recibida por el laboratorio | Personal de Laboratorio |
| Procesando | Muestra siendo procesada | Personal de Laboratorio |
| Asignado | Asignado a histopatólogo | Sistema/Administrador |
| Análisis | Bajo análisis | Histopatólogo |
| Informe Listo | Informe completado | Histopatólogo |
| Informe Enviado | Informe entregado | Sistema |

### Notificaciones de Cambio de Estado

Cada cambio de estado activa notificaciones por email:

![Notificaciones de Estado](assets/images/status-notifications.png)
*Captura de pantalla: Notificación por email para cambio de estado*

## ⏱️ Expectativas de Tiempo

### Tiempos de Procesamiento Estándar

- **Presentación de Protocolo**: Inmediato
- **Recepción de Muestra**: 1-2 días hábiles
- **Procesamiento de Muestra**: 1 día hábil
- **Análisis (Citología)**: 1-2 días hábiles
- **Análisis (Histopatología)**: 3-5 días hábiles
- **Entrega de Informe**: Inmediato después de completarse

### Casos Urgentes

Los casos urgentes son priorizados:
- **Protocolo Urgente**: Marcado como urgente durante la presentación
- **Procesamiento Prioritario**: Acelerado a través del flujo de trabajo
- **Análisis Expedito**: Asignado a histopatólogo disponible
- **Notificación Inmediata**: Veterinario notificado inmediatamente

![Manejo de Casos Urgentes](assets/images/urgent-case-handling.png)
*Captura de pantalla: Manejo prioritario de casos urgentes*

## 🔍 Puntos de Control de Calidad

### Verificaciones de Calidad del Veterinario
- [ ] Todos los campos requeridos completados
- [ ] Información del animal precisa
- [ ] Historia clínica detallada
- [ ] Información de la muestra correcta

### Verificaciones de Calidad del Personal de Laboratorio
- [ ] Muestra coincide con protocolo
- [ ] Condición de la muestra aceptable
- [ ] Etiquetado apropiado aplicado
- [ ] Procesamiento documentado

### Verificaciones de Calidad del Histopatólogo
- [ ] Información del protocolo revisada
- [ ] Calidad de la muestra evaluada
- [ ] Análisis exhaustivo y completo
- [ ] Informe preciso y claro

## 🚨 Manejo de Excepciones

### Problemas Comunes y Soluciones

#### Problemas de Calidad de Muestra
- **Muestra de Mala Calidad**: Contactar veterinario para reemplazo
- **Muestra Incorrecta**: Verificar información del protocolo
- **Información Faltante**: Solicitar detalles adicionales

#### Problemas Técnicos
- **Tiempo de Inactividad del Sistema**: Usar procedimientos fuera de línea
- **Pérdida de Datos**: Restaurar desde respaldo
- **Problemas de Email**: Usar métodos alternativos de notificación

#### Retrasos en el Flujo de Trabajo
- **Personal No Disponible**: Reasignar a personal disponible
- **Problemas de Equipo**: Usar equipo de respaldo
- **Alto Volumen**: Priorizar casos urgentes

## 📈 Métricas de Rendimiento

### Indicadores Clave de Rendimiento

- **Tasa de Presentación de Protocolos**: Protocolos presentados por día
- **Tiempo de Recepción**: Tiempo desde presentación hasta recepción
- **Tiempo de Procesamiento**: Tiempo desde recepción hasta análisis
- **Tiempo de Análisis**: Tiempo desde asignación hasta completación del informe
- **Tiempo Total de Respuesta**: Tiempo total desde presentación hasta entrega

### Panel de Monitoreo

![Métricas de Flujo de Trabajo](assets/images/workflow-metrics.png)
*Captura de pantalla: Panel de métricas de rendimiento del flujo de trabajo*

## 🔧 Configuración del Sistema

### Configuración del Flujo de Trabajo

Los administradores pueden configurar:
- **Reglas de Auto-asignación**: Asignación automática de histopatólogo
- **Plantillas de Notificación**: Contenido de notificaciones por email
- **Transiciones de Estado**: Cambios de estado permitidos
- **Puntos de Control de Calidad**: Verificaciones de calidad requeridas

![Configuración del Flujo de Trabajo](assets/images/workflow-configuration.png)
*Captura de pantalla: Interfaz de configuración del flujo de trabajo*

## 📚 Mejores Prácticas

### Para Veterinarios
1. **Información Completa**: Proporcionar información detallada y precisa
2. **Instrucciones Claras**: Incluir instrucciones específicas de manejo
3. **Presentación Oportuna**: Enviar protocolos prontamente
4. **Seguimiento**: Verificar estado regularmente

### Para Personal de Laboratorio
1. **Recepción Rápida**: Procesar muestras prontamente al recibirlas
2. **Documentación de Calidad**: Documentar todos los problemas de calidad
3. **Etiquetado Apropiado**: Asegurar etiquetado preciso de muestras
4. **Actualizaciones de Estado**: Mantener información de estado actualizada

### Para Histopatólogos
1. **Análisis Exhaustivo**: Realizar análisis completo y preciso
2. **Informes Claros**: Escribir informes claros y comprensivos
3. **Completación Oportuna**: Cumplir con tiempos de respuesta establecidos
4. **Revisión de Calidad**: Revisar trabajo antes de finalización

## ❓ Preguntas Frecuentes

### P: ¿Qué pasa si cometo un error en mi presentación de protocolo?
R: Contactar al laboratorio inmediatamente. Los protocolos borrador pueden ser editados, pero los protocolos enviados requieren asistencia del laboratorio.

### P: ¿Cómo rastreo el progreso de mi protocolo?
R: Usar la sección "Mis Protocolos" en tu panel de control o esperar notificaciones por email.

### P: ¿Qué pasa si mi muestra se daña durante el envío?
R: Contactar al laboratorio inmediatamente. Evaluarán el daño y determinarán si el análisis aún es posible.

### P: ¿Puedo solicitar un histopatólogo específico?
R: Puedes hacer solicitudes en la sección de instrucciones especiales, pero la asignación depende de la disponibilidad y carga de trabajo.

## 🆘 Soporte y Escalación

### Canales de Soporte
- **Soporte por Email**: support@laboratory.com
- **Soporte Telefónico**: (555) 123-4567
- **Ayuda en Línea**: Documentación de ayuda del sistema
- **Entrenamiento**: Sesiones de entrenamiento disponibles

### Proceso de Escalación
1. **Nivel 1**: Solicitud de soporte estándar
2. **Nivel 2**: Involucramiento de supervisor
3. **Nivel 3**: Escalación de gestión
4. **Emergencia**: Contacto telefónico directo para asuntos urgentes

---

*Relacionado: [Flujo de Trabajo de Procesamiento de Muestras](sample-processing.md)*
```

### Fase 4: Implementación del Servidor Markdown (2-3 horas)

#### 4.1 Configuración del Servidor Markdown

Crear `docs-server/requirements.txt`:

```txt
# Servidor de Documentación Markdown
mkdocs==1.5.3
mkdocs-material==9.4.8
mkdocs-mermaid2-plugin==1.1.1
mkdocs-git-revision-date-plugin==1.2.0
mkdocs-minify-plugin==0.7.2
mkdocs-redirects==1.2.1
mkdocs-git-committers-plugin-2==1.2.2
mkdocs-git-authors-plugin==0.7.0
mkdocs-awesome-pages-plugin==2.9.2
mkdocs-table-reader-plugin==1.0.2
mkdocs-macros-plugin==1.0.1
mkdocs-print-site-plugin==3.5.0
mkdocs-pdf-export-plugin==0.7.0
```

Crear `docs-server/mkdocs.yml`:

```yaml
site_name: Documentación del Sistema de Gestión de Laboratorio
site_description: Documentación completa para el Sistema de Gestión de Laboratorio
site_author: Equipo de Gestión de Laboratorio
site_url: https://docs.laboratory-system.com

# Repositorio
repo_name: laboratory-system/docs
repo_url: https://github.com/your-org/laboratory-system
edit_uri: edit/main/docs/

# Configuración
theme:
  name: material
  language: es
  palette:
    # Alternador de paleta para modo automático
    - media: "(prefers-color-scheme)"
      toggle:
        icon: material/brightness-auto
        name: Cambiar a modo claro

    # Alternador de paleta para modo claro
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Cambiar a modo oscuro

    # Alternador de paleta para modo oscuro
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Cambiar a preferencia del sistema

  features:
    - announce.dismiss
    - content.action.edit
    - content.action.view
    - content.code.annotate
    - content.code.copy
    - content.code.select
    - content.footnote.tooltips
    - content.tabs.link
    - content.tooltips
    - header.autohide
    - navigation.expand
    - navigation.footer
    - navigation.indexes
    - navigation.instant
    - navigation.instant.prefetch
    - navigation.instant.progress
    - navigation.prune
    - navigation.sections
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.top
    - search.highlight
    - search.share
    - search.suggest
    - toc.follow
    - toc.integrate

  icon:
    repo: fontawesome/brands/github
    edit: material/pencil
    view: material/eye

  logo: assets/images/logo.png
  favicon: assets/images/favicon.ico

# Plugins
plugins:
  - search:
      lang: es
  - mermaid2:
      arguments:
        theme: base
        themeVariables:
          primaryColor: '#ff6b6b'
          primaryTextColor: '#fff'
          primaryBorderColor: '#ff6b6b'
          lineColor: '#333'
          secondaryColor: '#006100'
          tertiaryColor: '#fff'
  - git-revision-date:
      enabled: true
      enable_creation_date: true
  - minify:
      minify_html: true
  - redirects:
      redirect_maps:
        'old-page.md': 'new-page.md'
  - git-committers:
      repository: your-org/laboratory-system
      branch: main
  - git-authors:
      repository: your-org/laboratory-system
      branch: main
  - awesome-pages
  - table-reader
  - macros
  - print-site
  - pdf-export

# Extensions
markdown_extensions:
  - abbr
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - toc:
      permalink: true
      title: On this page
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.betterem:
      smart_enable: all
  - pymdownx.caret
  - pymdownx.details
  - pymdownx.emoji:
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
      emoji_index: !!python/name:material.extensions.emoji.twemoji
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.magiclink:
      normalize_issue_symbols: true
      repo_url_shorthand: true
      user: your-org
      repo: laboratory-system
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
      combine_header_slug: true
      slugify: !!python/object/apply:pymdownx.slugs.slugify
        kwds:
          case: lower
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde

# Árbol de páginas
nav:
  - Inicio: index.md
  - Comenzando:
    - getting-started/overview.md
    - getting-started/installation.md
    - getting-started/first-steps.md
  - Guías de Usuario:
    - Veterinarios:
      - user-guides/veterinarians/protocol-submission.md
      - user-guides/veterinarians/report-access.md
      - user-guides/veterinarians/work-orders.md
    - Histopatólogos:
      - user-guides/histopathologists/report-creation.md
      - user-guides/histopathologists/sample-analysis.md
      - user-guides/histopathologists/quality-control.md
    - Personal de Laboratorio:
      - user-guides/staff/sample-reception.md
      - user-guides/staff/sample-processing.md
      - user-guides/staff/inventory-management.md
    - Administradores:
      - user-guides/administrators/user-management.md
      - user-guides/administrators/system-configuration.md
      - user-guides/administrators/monitoring.md
  - Flujos de Trabajo:
    - workflows/protocol-submission.md
    - workflows/sample-processing.md
    - workflows/report-generation.md
    - workflows/work-orders.md
  - Características:
    - features/authentication.md
    - features/email-notifications.md
    - features/pdf-generation.md
    - features/dashboards.md
    - features/monitoring.md
  - API:
    - api/rest-api.md
    - api/webhooks.md
    - api/integration.md
  - Administración:
    - administration/user-management.md
    - administration/system-configuration.md
    - administration/backup-restore.md
    - administration/troubleshooting.md
  - Soporte:
    - support/faq.md
    - support/contact.md
    - support/feature-requests.md

# Extra
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/your-org/laboratory-system
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/your-lab
    - icon: fontawesome/brands/linkedin
      link: https://linkedin.com/company/your-lab
  version:
    provider: mike

# Copyright
copyright: Copyright &copy; 2025 Sistema de Gestión de Laboratorio
```

#### 4.2 Scripts de Configuración del Servidor

Crear `docs-server/setup.sh`:

```bash
#!/bin/bash

# Script de Configuración del Servidor de Documentación

echo "🚀 Configurando Servidor de Documentación del Sistema de Gestión de Laboratorio..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 es requerido pero no está instalado."
    exit 1
fi

# Verificar si pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 es requerido pero no está instalado."
    exit 1
fi

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️ Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias de documentación..."
pip install -r requirements.txt

# Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p docs/assets/images
mkdir -p docs/assets/videos
mkdir -p docs/assets/templates
mkdir -p site

# Copiar archivos de documentación si existen
if [ -d "../main-project-docs/steps" ]; then
    echo "📋 Copiando archivos de documentación..."
    cp -r ../main-project-docs/steps/* docs/ 2>/dev/null || true
fi

# Crear estructura inicial de documentación
echo "📝 Creando estructura inicial de documentación..."
mkdir -p docs/getting-started
mkdir -p docs/user-guides/veterinarians
mkdir -p docs/user-guides/histopathologists
mkdir -p docs/user-guides/staff
mkdir -p docs/user-guides/administrators
mkdir -p docs/workflows
mkdir -p docs/features
mkdir -p docs/api
mkdir -p docs/administration
mkdir -p docs/support

# Crear archivos placeholder
echo "📄 Creando archivos placeholder..."
touch docs/getting-started/overview.md
touch docs/getting-started/installation.md
touch docs/getting-started/first-steps.md

# Construir documentación
echo "🔨 Construyendo documentación..."
mkdocs build

echo "✅ Configuración del servidor de documentación completa!"
echo ""
echo "📖 Para iniciar el servidor de desarrollo:"
echo "   source venv/bin/activate"
echo "   mkdocs serve"
echo ""
echo "🌐 Para construir para producción:"
echo "   mkdocs build"
echo ""
echo "📤 Para desplegar a GitHub Pages:"
echo "   mkdocs gh-deploy"
```

Crear `docs-server/start.sh`:

```bash
#!/bin/bash

# Iniciar Servidor de Documentación

echo "🚀 Iniciando Servidor de Documentación del Sistema de Gestión de Laboratorio..."

# Verificar si el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Entorno virtual no encontrado. Ejecutar setup.sh primero."
    exit 1
fi

# Activar entorno virtual
source venv/bin/activate

# Verificar si MkDocs está instalado
if ! command -v mkdocs &> /dev/null; then
    echo "❌ MkDocs no encontrado. Instalando dependencias..."
    pip install -r requirements.txt
fi

# Iniciar servidor de desarrollo
echo "🌐 Iniciando servidor de desarrollo en http://localhost:8000"
echo "📝 Editar archivos de documentación en el directorio 'docs'"
echo "🔄 Los cambios se reflejarán automáticamente en el navegador"
echo ""
echo "Presionar Ctrl+C para detener el servidor"
echo ""

mkdocs serve --dev-addr=0.0.0.0:8000
```

Crear `docs-server/build.sh`:

```bash
#!/bin/bash

# Construir Documentación para Producción

echo "🔨 Construyendo Documentación del Sistema de Gestión de Laboratorio..."

# Verificar si el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Entorno virtual no encontrado. Ejecutar setup.sh primero."
    exit 1
fi

# Activar entorno virtual
source venv/bin/activate

# Limpiar construcción anterior
echo "🧹 Limpiando construcción anterior..."
rm -rf site/

# Construir documentación
echo "📚 Construyendo documentación..."
mkdocs build

# Verificar si la construcción fue exitosa
if [ $? -eq 0 ]; then
    echo "✅ Documentación construida exitosamente!"
    echo "📁 Directorio de salida: site/"
    echo ""
    echo "🌐 Para servir la documentación construida:"
    echo "   python -m http.server 8000 --directory site"
    echo ""
    echo "📤 Para desplegar a producción:"
    echo "   mkdocs gh-deploy"
else
    echo "❌ Construcción falló. Revisar los mensajes de error arriba."
    exit 1
fi
```

#### 4.3 Configuración de Docker

Crear `docs-server/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para mejor caché
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de documentación
COPY . .

# Crear usuario no-root
RUN useradd -m -u 1000 docsuser && chown -R docsuser:docsuser /app
USER docsuser

# Exponer puerto
EXPOSE 8000

# Verificación de salud
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Comando por defecto
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
```

Crear `docs-server/docker-compose.yml`:

```yaml
version: '3.8'

services:
  docs-server:
    build: .
    container_name: laboratory-docs
    ports:
      - "8000:8000"
    volumes:
      - ./docs:/app/docs
      - ./mkdocs.yml:/app/mkdocs.yml
    environment:
      - MKDOCS_DEV_ADDR=0.0.0.0:8000
    restart: unless-stopped
    networks:
      - docs-network

  # Opcional: Proxy reverso Nginx
  nginx:
    image: nginx:alpine
    container_name: docs-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - docs-server
    restart: unless-stopped
    networks:
      - docs-network

networks:
  docs-network:
    driver: bridge
```

#### 4.4 Configuración de Nginx

Crear `docs-server/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream docs_backend {
        server docs-server:8000;
    }

    server {
        listen 80;
        server_name docs.laboratory-system.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name docs.laboratory-system.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_proxied any;
        gzip_comp_level 6;
        gzip_types
            text/plain
            text/css
            text/xml
            text/javascript
            application/json
            application/javascript
            application/xml+rss
            application/atom+xml
            image/svg+xml;

        # Proxy al servidor MkDocs
        location / {
            proxy_pass http://docs_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Soporte WebSocket para recarga en vivo
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Caché de archivos estáticos
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
            proxy_pass http://docs_backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

#### 4.5 GitHub Actions para Despliegue Automático

Crear `docs-server/.github/workflows/docs.yml`:

```yaml
name: Desplegar Documentación

on:
  push:
    branches: [ main ]
    paths: [ 'docs/**', 'docs-server/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'docs/**', 'docs-server/**' ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Configurar Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Instalar dependencias
      run: |
        cd docs-server
        pip install -r requirements.txt

    - name: Construir documentación
      run: |
        cd docs-server
        mkdocs build

    - name: Desplegar a GitHub Pages
      if: github.ref == 'refs/heads/main'
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs-server/site
        cname: docs.laboratory-system.com
```

## Instrucciones de Uso

### 1. **Configurar Servidor de Documentación**

```bash
cd docs-server
chmod +x setup.sh
./setup.sh
```

### 2. **Iniciar Servidor de Desarrollo**

```bash
chmod +x start.sh
./start.sh
```

### 3. **Acceder a la Documentación**

- **Desarrollo Local**: http://localhost:8000
- **Producción**: https://docs.laboratory-system.com

### 4. **Agregar Capturas de Pantalla**

Colocar capturas de pantalla en `docs/assets/images/` y referenciarlas en markdown:

```markdown
![Descripción](assets/images/screenshot-name.png)
*Pie de foto: Descripción de lo que muestra la captura de pantalla*
```

### 5. **Construir para Producción**

```bash
chmod +x build.sh
./build.sh
```

## Características

### **📚 Características Ricas de Documentación**
- **Material Design**: Diseño moderno y responsivo
- **Búsqueda**: Búsqueda de texto completo en toda la documentación
- **Navegación**: Navegación jerárquica con migas de pan
- **Soporte Móvil**: Diseño responsivo para todos los dispositivos
- **Modo Oscuro**: Cambio automático entre modo oscuro/claro

### **🔄 Desarrollo en Vivo**
- **Recarga en Vivo**: Cambios reflejados inmediatamente
- **Recarga Caliente**: No necesidad de reiniciar servidor
- **Resaltado de Errores**: Errores de sintaxis resaltados en el navegador

### **📊 Características Avanzadas**
- **Diagramas Mermaid**: Diagramas de flujo y diagramas
- **Resaltado de Código**: Resaltado de sintaxis para bloques de código
- **Tabla de Contenidos**: Generación automática de TOC
- **Soporte de Impresión**: Páginas compatibles con impresión
- **Exportación PDF**: Exportar documentación como PDF

### **🔧 Personalización**
- **Temas**: Múltiples esquemas de color
- **Plugins**: Ecosistema extenso de plugins
- **CSS Personalizado**: Soporte de estilos personalizados
- **Macros**: Generación de contenido dinámico

---

*Paso 19 - Documentación de Dominio y Guía de Uso*  
*Creado: Enero 2025*  
*Prioridad: Alta - Esencial para adopción de usuarios y entrenamiento*

**IMPORTANTE: Toda la documentación debe estar en español para servir al personal del laboratorio y veterinarios de habla hispana.**
