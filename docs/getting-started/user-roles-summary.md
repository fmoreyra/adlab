# Resumen de Roles de Usuario y Capacidades

Esta página proporciona un resumen completo de las capacidades y características principales que cada tipo de usuario puede realizar en el Sistema de Gestión de Laboratorio.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

---

## 🏥 **VETERINARIO (Cliente Veterinario)**

**Flujo de Trabajo Principal**: Enviar protocolos → Seguir estado → Descargar informes

### Características Principales:

#### 📋 **Envío de Protocolos**
- Crear nuevos protocolos de citología
- Crear nuevos protocolos de histopatología
- Completar información del paciente y muestra
- Generar etiquetas de muestra automáticamente

#### 📊 **Gestión de Protocolos**
- Ver todos los protocolos enviados
- Seguir el estado del protocolo en tiempo real
- Editar protocolos antes de que comience el procesamiento
- Monitorear el progreso del protocolo a través del sistema

#### 📄 **Acceso a Informes**
- Descargar informes diagnósticos completados (PDF)
- Acceder a órdenes de trabajo para facturación
- Recibir notificaciones por email cuando los informes están listos
- Ver historial de informes y archivos

#### 👤 **Gestión de Perfil**
- Actualizar información personal y profesional
- Gestionar datos de contacto
- Actualizar información de matrícula
- Cambiar contraseña y configuraciones de seguridad

#### 📈 **Seguimiento de Estado**
- Actualizaciones de estado del protocolo en tiempo real
- Notificaciones por email para cambios de estado
- Seguimiento del progreso a través de todas las etapas de procesamiento

---

## 🔬 **PERSONAL_LAB (Personal de Laboratorio)**

**Flujo de Trabajo Principal**: Recibir muestras → Procesar muestras → Generar informes → Firmar documentos

### Características Principales:

#### 📦 **Recepción de Muestras**
- Confirmar la recepción de muestras en el laboratorio
- Asignar números de protocolo definitivos
- Registrar la llegada y condición de la muestra
- Manejar discrepancias y problemas de muestras

#### ⚙️ **Gestión de Procesamiento**
- Registrar cassettes para histopatología
- Registrar portaobjetos para análisis
- Seguir las etapas de procesamiento
- Actualizar el estado del procesamiento

#### 📝 **Generación de Informes**
- Crear informes diagnósticos completos (si tiene permiso)
- Acceder a información de caso precargada
- Generar informes PDF profesionales
- Finalizar y enviar informes automáticamente

#### ✍️ **Firmas Digitales**
- Firmar informes digitalmente
- Gestionar configuraciones de firma
- Autenticación profesional de documentos

#### 📋 **Actualizaciones de Estado**
- Actualizar el estado del procesamiento del protocolo
- Marcar hitos de procesamiento
- Manejar retrasos o problemas de procesamiento

#### 📄 **Creación de Órdenes de Trabajo**
- Generar órdenes de trabajo para protocolos completados
- Crear documentos de facturación
- Gestionar el estado de las órdenes de trabajo

**Permiso adicional:** las pantallas de órdenes de trabajo exigen que el usuario tenga **`is_staff=True`** («Staff status» en el admin de Django), además del rol PERSONAL_LAB. La recepción y el procesamiento de muestras no usan ese flag; un técnico sin `is_staff` verá el acceso deshabilitado o un aviso en el panel.

#### 📊 **Seguimiento de Inventario**
- Gestionar inventario de procesamiento de muestras
- Seguir el uso de cassettes y portaobjetos
- Monitorear suministros de procesamiento

#### 🎯 **Control de Calidad**
- Revisar y aprobar la calidad del procesamiento
- Asegurar el cumplimiento de estándares de informes
- Monitorear la precisión de los informes

**Nota**: El rol unificado de Personal de Laboratorio incluye tanto las funciones tradicionales de laboratorio como la capacidad de generar informes diagnósticos, dependiendo de los permisos asignados a cada miembro del personal.

---

## 👨‍💼 **ADMIN (Administrador)**

**Flujo de Trabajo Principal**: Gestión del sistema → Administración de usuarios → Configuración

### Características Principales:

#### 👥 **Gestión de Usuarios**
- Crear, editar y gestionar cuentas de usuario
- Asignar y cambiar roles de usuario
- Activar/desactivar cuentas de usuario
- Restablecer contraseñas de usuario
- Gestionar permisos de usuario

#### ⚙️ **Configuración del Sistema**
- Configurar parámetros y configuraciones del sistema
- Gestionar configuración de email
- Configurar preferencias de notificaciones
- Configurar mantenimiento del sistema

#### 📊 **Analíticas e Informes**
- Acceder a analíticas del sistema completo
- Ver métricas de rendimiento del laboratorio
- Monitorear volúmenes de procesamiento
- Generar informes de gestión
- Seguir tiempos de respuesta (TAT)

#### 🔍 **Logs de Auditoría**
- Revisar logs de actividad del sistema
- Monitorear eventos de seguridad
- Seguir acciones de usuario
- Acceder a logs de autenticación
- Revisar logs de entrega de email

#### 📋 **Gestión de Datos**
- Gestionar datos de referencia y catálogos
- Actualizar información de precios
- Gestionar listas de especies y razas
- Configurar categorías de diagnóstico
- Mantener la integridad de los datos del sistema

---

## 🔄 **Integración del Flujo de Trabajo del Sistema**

### Proceso Completo del Laboratorio:
1. **Veterinario** envía protocolo con información de la muestra
2. **Personal de Laboratorio** recibe y procesa la muestra
3. **Personal de Laboratorio (con permisos)** analiza y crea informe diagnóstico
4. **Sistema** genera automáticamente órdenes de trabajo y envía notificaciones
5. **Administrador** monitorea todo el proceso y gestiona la salud del sistema

### Beneficios Clave por Rol:
- **Veterinarios**: Ahorro de tiempo con envío online y seguimiento en tiempo real
- **Personal de Laboratorio**: Flujo de trabajo organizado con mejor trazabilidad y acceso completo al ciclo de vida de las muestras
- **Administradores**: Toma de decisiones basada en datos con analíticas completas

---

## 🎯 **Navegación Rápida**

### Para Veterinarios
- [Enviar protocolos](user-guides/veterinarians/submitting-protocols.md)
- [Seguir muestras](user-guides/veterinarians/tracking-samples.md)
- [Ver informes](user-guides/veterinarians/accessing-reports.md)

### Para Personal de Laboratorio
- [Recibir muestras](user-guides/lab-staff/receiving-samples.md)
- [Procesar muestras](user-guides/lab-staff/processing-samples.md)
- [Gestionar inventario](user-guides/lab-staff/managing-inventory.md)
- [Analizar muestras](user-guides/histopathologists/analyzing-samples.md) (si tiene permiso)
- [Crear informes](user-guides/histopathologists/creating-reports.md) (si tiene permiso)
- [Control de calidad](user-guides/histopathologists/quality-control.md) (si tiene permiso)

### Para Administradores
- [Gestionar usuarios](user-guides/administrators/managing-users.md)
- [Configurar sistema](user-guides/administrators/system-settings.md)
- [Monitorear sistema](user-guides/administrators/monitoring-system.md)

---

Este sistema basado en roles asegura que cada tipo de usuario tenga acceso a las herramientas específicas y la información que necesitan para realizar su trabajo de manera efectiva, manteniendo la seguridad y eficiencia del flujo de trabajo en todo el proceso del laboratorio.
