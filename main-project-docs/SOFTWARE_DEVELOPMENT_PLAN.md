# Plan de Desarrollo de Software
## Sistema Informático para Laboratorio de Anatomía Patológica Veterinaria

**Basado en**: Proyecto Final de Ingeniería Industrial - MARÍA SOL KLEIN  
**Documento**: Plan de Implementación Técnica  
**Versión**: 1.0  
**Fecha**: Octubre 2024  
**Estado**: Pendiente aprobación y decisiones técnicas

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Análisis de Requerimientos](#2-análisis-de-requerimientos)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Stack Tecnológico](#4-stack-tecnológico-decisiones-pendientes)
5. [Plan de Desarrollo](#5-plan-de-desarrollo)
6. [Estrategia de Testing](#6-estrategia-de-testing)
7. [Estrategia de Deployment](#7-estrategia-de-deployment)
8. [Seguridad](#8-seguridad)
9. [Backup y Recuperación](#9-backup-y-recuperación)
10. [Monitoreo y Mantenimiento](#10-monitoreo-y-mantenimiento)
11. [Capacitación y Cambio Organizacional](#11-capacitación-y-cambio-organizacional)
12. [Costos y Recursos](#12-costos-y-recursos)
13. [Riesgos y Mitigación](#13-riesgos-y-mitigación)
14. [Métricas de Éxito](#14-métricas-de-éxito)
15. [Anexos](#15-anexos)
16. [Decisiones Técnicas Pendientes](#16-decisiones-técnicas-pendientes---resumen)
17. [Próximos Pasos](#17-próximos-pasos-inmediatos)

---

## 1. RESUMEN EJECUTIVO

### 1.1 Propósito del Documento
Este documento establece el plan de desarrollo para implementar el sistema informático propuesto en el proyecto de mejora del Laboratorio de Anatomía Patológica Veterinaria de la FCV-UNL. El plan es agnóstico a tecnologías específicas y servirá como guía para la implementación técnica posterior.

### 1.2 Contexto del Proyecto
El laboratorio actualmente utiliza sistemas obsoletos (Clarion 2.0 en Windows XP) y procesos manuales que comprometen la eficiencia operativa. El nuevo sistema busca:
- Eliminar redundancia en el registro de información
- Automatizar generación de informes y órdenes de trabajo
- Mejorar trazabilidad de muestras
- Aumentar capacidad de atención en 15.9%
- Reducir tiempo de procesamiento para histopatólogos

### 1.3 Objetivos del Sistema
- **Primario**: Digitalizar y optimizar el flujo completo de gestión de muestras
- **Secundarios**:
  - Facilitar acceso remoto para clientes veterinarios
  - Centralizar información en base de datos normalizada
  - Generar reportes y métricas en tiempo real
  - Mejorar comunicación laboratorio-clientes

---

## 2. ANÁLISIS DE REQUERIMIENTOS

### 2.1 Actores del Sistema

#### 2.1.1 Veterinario Cliente
- Registro en el sistema
- Envío de protocolos de remisión online
- Consulta de estado de solicitudes
- Descarga de informes de resultados

#### 2.1.2 Personal de Laboratorio
- Registro de recepción de muestras
- Ingreso de datos de procesamiento (cassettes, portaobjetos)
- Consulta de protocolos
- Gestión de inventario y trazabilidad

#### 2.1.3 Histopatólogo
- Consulta de información completa de casos
- Redacción de informes de resultados
- Firma digital de documentos
- Envío automatizado de informes y OT

#### 2.1.4 Administrador del Sistema
- Gestión de usuarios y permisos
- Configuración del sistema
- Acceso a reportes globales
- Mantenimiento de catálogos

### 2.2 Requerimientos Funcionales

#### RF01: Gestión de Usuarios
- **RF01.1**: Registro de veterinarios con validación de matrícula profesional
- **RF01.2**: Autenticación segura con usuario y contraseña
- **RF01.3**: Recuperación de contraseña
- **RF01.4**: Gestión de perfiles (cliente, personal laboratorio, histopatólogo, admin)
- **RF01.5**: Almacenamiento de firma digital de histopatólogos

#### RF02: Gestión de Protocolos de Remisión
- **RF02.1**: Formulario diferenciado para análisis citológico e histopatológico
- **RF02.2**: Validación de campos obligatorios según modelo (Tabla 4.3 del documento)
- **RF02.3**: Generación de código temporal pre-recepción
- **RF02.4**: Asignación automática de número de protocolo (formato "HP AA/NRO" o "CT AA/NRO")
- **RF02.5**: Almacenamiento de datos del animal sin crear entidad separada (decisión de diseño IV.3.3)

#### RF03: Registro de Recepción de Muestras
- **RF03.1**: Búsqueda de protocolos por código temporal
- **RF03.2**: Confirmación de llegada física de muestra
- **RF03.3**: Generación de etiquetas con número de protocolo definitivo
- **RF03.4**: Registro de fecha y hora de recepción
- **RF03.5**: Notificación automática al veterinario

#### RF04: Gestión de Procesamiento Histopatológico
- **RF04.1**: Registro de cassettes con identificador único
- **RF04.2**: Especificación de material incluido en cada cassette
- **RF04.3**: Diferenciación visual de cassettes (amarillo=multicorte, naranja=coloración especial)
- **RF04.4**: Registro de portaobjetos con asociación a cassettes
- **RF04.5**: Seguimiento de etapas: fraccionado, identificación, fijación, entacado, corte, montaje, coloración
- **RF04.6**: Trazabilidad completa muestra-cassette-portaobjetos

#### RF05: Procesamiento Citológico
- **RF05.1**: Registro simplificado (solo tinción)
- **RF05.2**: Asociación directa muestra-portaobjetos

#### RF06: Consulta de Información
- **RF06.1**: Búsqueda de protocolos por número, fecha, veterinario, estado
- **RF06.2**: Visualización de historial completo del caso
- **RF06.3**: Acceso a datos del paciente animal
- **RF06.4**: Consulta de procesamiento realizado
- **RF06.5**: Filtros y ordenamiento de resultados

#### RF07: Redacción y Envío de Informes
- **RF07.1**: Generación automática de plantilla con datos precargados:
  - Datos del protocolo (especie, raza, edad, diagnóstico presuntivo)
  - Datos del procesamiento (portaobjetos, cassettes, material incluido)
  - Datos del cliente
  - Datos del histopatólogo (nombre, matrícula, firma)
- **RF07.2**: Editor de texto para observaciones por cassette
- **RF07.3**: Generación de PDF con formato institucional
- **RF07.4**: Envío automático por email con un clic
- **RF07.5**: Generación simultánea de Orden de Trabajo (OT)
- **RF07.6**: Archivo de documentos enviados

#### RF08: Gestión de Órdenes de Trabajo
- **RF08.1**: Cálculo automático de montos según servicios
- **RF08.2**: Registro de pagos adelantados
- **RF08.3**: Agrupación de múltiples protocolos en una OT
- **RF08.4**: Exclusión de protocolos del Hospital de Salud Animal
- **RF08.5**: Generación de PDF con formato requerido por Finanzas

#### RF09: Tablero de Gestión Visual
- **RF09.1**: Indicadores de WIP (Work In Progress) por etapa del proceso
- **RF09.2**: Separación citología/histopatología
- **RF09.3**: Métricas de protocolos procesados (semanal, mensual, anual)
- **RF09.4**: Visualización en tiempo real
- **RF09.5**: Actualización automática

#### RF10: Reportes y Estadísticas
- **RF10.1**: Volumen de trabajo histórico
- **RF10.2**: Tiempos de respuesta (TAT - Turnaround Time)
- **RF10.3**: Productividad por histopatólogo
- **RF10.4**: Tipos de análisis más frecuentes
- **RF10.5**: Clientes más frecuentes
- **RF10.6**: Exportación a formatos estándar (CSV, Excel, PDF)

### 2.3 Requerimientos No Funcionales

#### RNF01: Rendimiento
- Tiempo de respuesta < 2 segundos para operaciones normales
- Tiempo de respuesta < 5 segundos para generación de reportes
- Soporte para mínimo 50 usuarios concurrentes
- Capacidad de almacenar histórico de 10+ años

#### RNF02: Disponibilidad
- Disponibilidad del sistema: 99% (excluyendo mantenimientos programados)
- Ventana de mantenimiento: fines de semana o período de receso (6 semanas/año)
- Backup automático diario
- Plan de recuperación ante desastres

#### RNF03: Seguridad
- Autenticación obligatoria para todos los módulos
- Encriptación de contraseñas (hash + salt)
- Comunicación segura (HTTPS/TLS)
- Control de acceso basado en roles (RBAC)
- Registro de auditoría de operaciones críticas
- Protección contra inyección SQL, XSS, CSRF
- Cumplimiento de normativas de protección de datos personales

#### RNF04: Usabilidad
- Interfaz intuitiva que requiera capacitación mínima
- Diseño responsive para uso en desktop, tablet, smartphone
- Mensajes de error claros y accionables
- Ayuda contextual en formularios complejos
- Accesibilidad básica (WCAG 2.0 nivel AA)

#### RNF05: Compatibilidad
- Compatibilidad con navegadores modernos (últimas 2 versiones):
  - Chrome, Firefox, Safari, Edge
- Funcionamiento con conexiones lentas (3G mínimo)
- Compatibilidad con lectores de códigos de barras/QR (futura expansión)

#### RNF06: Mantenibilidad
- Código documentado y siguiendo estándares
- Arquitectura modular y desacoplada
- Base de datos normalizada según esquema Tabla 4.5
- Versionado de código fuente
- Documentación técnica completa

#### RNF07: Escalabilidad
- Diseño que permita crecimiento a 2000+ protocolos/año
- Posibilidad de agregar nuevos tipos de análisis
- Arquitectura preparada para integración con otros sistemas
- Capacidad de expansión a múltiples laboratorios (futuro)

#### RNF08: Datos y Migración
- Migración de datos históricos desde sistema Clarion
- Limpieza y normalización de datos legacy
- Coexistencia temporal con sistema antiguo (período de transición)
- Exportación completa de datos en formato estándar

---

## 3. ARQUITECTURA DEL SISTEMA

### 3.1 Arquitectura General (Alto Nivel)

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Web App    │  │   Dashboard  │  │  Mobile Web  │  │
│  │  Veterinarios│  │  Laboratorio │  │   (futuro)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   CAPA DE APLICACIÓN                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │          API RESTful / GraphQL (TBD)               │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  • Módulo Autenticación                            │ │
│  │  • Módulo Protocolos                               │ │
│  │  • Módulo Procesamiento                            │ │
│  │  • Módulo Informes                                 │ │
│  │  • Módulo Notificaciones                           │ │
│  │  • Módulo Reportes                                 │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   CAPA DE DATOS                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Base de    │  │  Almacén de  │  │   Cache      │  │
│  │   Datos      │  │  Archivos    │  │   (Redis/    │  │
│  │  Relacional  │  │  (PDF, imgs) │  │  similar)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 SERVICIOS EXTERNOS                       │
│  • Servicio de Email (SMTP)                             │
│  • Servicio de Backup                                   │
│  • Servicio de Monitoreo                                │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Modelo de Datos

El sistema implementará el esquema relacional definido en la Tabla 4.5 del documento fuente:

**Tablas Principales:**
- Veterinario (id, apellido, nombre, teléfono, email, nro_matrícula)
- Orden_de_Trabajo (id, monto_total, pago_adelantado)
- Protocolo (id, fecha_remisión, especie, raza, sexo, edad, diagnóstico_presuntivo, apellido_propietario, nombre_propietario, identificación_animal, interés_académico, historia_clínica, id_ot)
- Muestra_Citología (id, técnica_utilizada, fecha_recepción, sitio_muestreo, id_veterinario, id_protocolo)
- Muestra_Histopatología (id, material_remitido, fecha_recepción, id_veterinario, id_protocolo)
- Cassette (id, material_incluido, id_muestra_hp)
- Portaobjetos (id, campo, técnica, id_muestra_ct, id_cassette)
- Cassette_Portaobjetos (tabla intermedia M:N, coloración, multicorte)
- Histopatólogo (id, apellido, nombre, nro_matrícula, cargo, firma)
- Informe_Resultados (id, fecha, observaciones, resultados, id_veterinario, id_histopatólogo)
- Domicilio (id, provincia, localidad, calle, número, código_postal, id_veterinario)

**Consideraciones de Diseño:**
- Uso de claves primarias auto-incrementales
- Claves foráneas con integridad referencial
- Índices en campos de búsqueda frecuente
- Normalización hasta 3FN mínimo
- Campos de auditoría (created_at, updated_at, deleted_at para soft deletes)

### 3.3 Patrones Arquitectónicos a Considerar

**🔧 DECISIÓN TÉCNICA PENDIENTE:**
- **Arquitectura Monolítica vs Microservicios**: Para fase inicial, arquitectura monolítica modular puede ser suficiente. Evaluar microservicios si hay planes de escalabilidad extrema.
- **Patrón de capas**: MVC, MVVM, o Clean Architecture
- **ORM vs Query Builder vs SQL directo**: Evaluar según stack tecnológico elegido

---

## 4. STACK TECNOLÓGICO (DECISIONES PENDIENTES)

### 4.1 Frontend

**🔧 DECISIÓN TÉCNICA PENDIENTE:**

**Opciones a evaluar:**
- Framework JavaScript moderno:
  - React.js + Context API / Redux
  - Vue.js + Vuex / Pinia
  - Angular
  - Svelte
- Framework CSS:
  - Tailwind CSS
  - Bootstrap
  - Material-UI / Vuetify
  - Custom CSS con preprocessador (SASS/LESS)

**Criterios de selección:**
- Curva de aprendizaje del equipo
- Ecosistema de componentes UI
- Rendimiento
- Soporte a largo plazo
- Facilidad para responsive design

### 4.2 Backend

**🔧 DECISIÓN TÉCNICA PENDIENTE:**

**Opciones a evaluar:**
- Lenguaje/Framework:
  - Node.js + Express / NestJS
  - Python + Django / Flask / FastAPI
  - PHP + Laravel / Symfony
  - Ruby on Rails
  - Java + Spring Boot
  - C# + .NET Core

**Criterios de selección:**
- Experiencia del equipo de desarrollo
- Rendimiento para operaciones de base de datos
- Ecosistema de librerías (PDF, email, etc.)
- Costo de hosting
- Facilidad de mantenimiento

### 4.3 Base de Datos

**🔧 DECISIÓN TÉCNICA PENDIENTE:**

**Opciones a evaluar:**
- PostgreSQL (recomendado para datos relacionales complejos)
- MySQL / MariaDB
- SQL Server

**Complementarios:**
- Redis para caché y sesiones
- Elasticsearch para búsquedas avanzadas (opcional)

**Criterios de selección:**
- Soporte de integridad referencial
- Rendimiento en consultas complejas
- Herramientas de administración
- Costo de licenciamiento
- Capacidad de backup y recuperación

### 4.4 Infraestructura y Deployment

**🔧 DECISIÓN TÉCNICA PENDIENTE:**

**Opciones de hosting:**
- Cloud:
  - AWS (EC2, RDS, S3)
  - Google Cloud Platform
  - Microsoft Azure
  - DigitalOcean
- On-premise (servidores universitarios)
- Híbrido

**Containerización:**
- Docker + Docker Compose
- Kubernetes (si se requiere alta escalabilidad)

**CI/CD:**
- GitHub Actions
- GitLab CI
- Jenkins
- CircleCI

**Criterios de selección:**
- Presupuesto disponible
- Políticas de seguridad de la universidad
- Requisitos de latencia
- Facilidad de gestión

### 4.5 Herramientas Adicionales

**🔧 DECISIÓN TÉCNICA PENDIENTE:**

- **Generación de PDF**: 
  - wkhtmltopdf
  - Puppeteer / Playwright
  - Librerías nativas (ReportLab para Python, TCPDF para PHP, etc.)

- **Servicio de Email**:
  - SMTP institucional
  - SendGrid
  - Amazon SES
  - Mailgun

- **Firma Digital**:
  - Firma electrónica simple (imagen)
  - Firma digital avanzada (PKI)
  - Integración con servicios externos

- **Monitoreo y Logs**:
  - ELK Stack (Elasticsearch, Logstash, Kibana)
  - Prometheus + Grafana
  - Sentry para tracking de errores
  - New Relic / DataDog

---

## 5. PLAN DE DESARROLLO

### 5.1 Metodología de Desarrollo

**Enfoque Recomendado**: Ágil - Scrum con sprints de 2 semanas

**Razones:**
- Permite entregas incrementales con valor
- Facilita feedback temprano del laboratorio
- Se adapta bien a equipos pequeños (1-3 desarrolladores)
- Posibilita ajustes según uso real del sistema

**Alternativa**: Si el equipo es muy pequeño (1 desarrollador), considerar Kanban para mayor flexibilidad

### 5.2 Fases del Proyecto

#### FASE 0: Preparación y Setup (2 semanas)
**Objetivos:**
- Finalizar decisiones tecnológicas pendientes
- Configurar entorno de desarrollo
- Establecer repositorio y pipeline CI/CD
- Definir estándares de código

**Entregables:**
- Documento de arquitectura técnica detallada
- Repositorio configurado
- Entorno de desarrollo local operativo
- Plan de trabajo detallado por sprint

---

#### FASE 1: MVP - Módulo de Gestión de Usuarios y Protocolos (4 semanas)

**Sprint 1-2: Autenticación y Registro**
- Modelo de datos: Veterinario, Domicilio, Histopatólogo
- Sistema de autenticación
- Registro de veterinarios (CU IV.2.1)
- Login diferenciado por rol
- Recuperación de contraseña

**Sprint 3-4: Protocolos de Remisión**
- Modelo de datos: Protocolo, Muestra_Citología, Muestra_Histopatología, OT
- Formularios de protocolo citológico e histopatológico (CU IV.2.2)
- Generación de código temporal
- Dashboard básico para veterinarios
- Consulta de protocolos remitidos (CU IV.2.3)

**Criterios de Aceptación:**
- Veterinarios pueden registrarse y enviar protocolos
- Sistema valida campos obligatorios
- Se generan códigos temporales únicos
- Veterinarios pueden ver sus protocolos enviados

**Pruebas:**
- Unitarias: Validaciones de formulario, generación de códigos
- Integración: Flujo completo registro → login → envío protocolo
- Usuario: Pruebas con 3-5 veterinarios reales

---

#### FASE 2: Recepción y Procesamiento (4 semanas)

**Sprint 5-6: Recepción de Muestras**
- Interfaz para personal de laboratorio
- Registro de recepción (CU IV.2.4)
- Asignación de número de protocolo definitivo
- Generación de etiquetas imprimibles
- Notificaciones por email al veterinario

**Sprint 7-8: Procesamiento de Muestras**
- Modelo de datos: Cassette, Portaobjetos, Cassette_Portaobjetos
- Ingreso de datos de procesamiento (CU IV.2.5)
- Registro de cassettes con material incluido
- Registro de portaobjetos
- Consulta de protocolos por personal (CU IV.2.6)
- Trazabilidad muestra-cassette-portaobjetos

**Criterios de Aceptación:**
- Personal puede buscar protocolos por código temporal
- Sistema asigna numeración correlativa automáticamente
- Se registran todos los pasos del procesamiento
- Trazabilidad completa es visible

**Pruebas:**
- Unitarias: Lógica de numeración, asociación cassette-portaobjetos
- Integración: Flujo completo recepción → procesamiento
- Usuario: Pruebas con técnico y personal del laboratorio

---

#### FASE 3: Informes y Órdenes de Trabajo (3 semanas)

**Sprint 9-10: Generación de Informes**
- Plantilla de informe con datos precargados
- Editor para observaciones por cassette (CU IV.2.7)
- Generación de PDF con formato institucional
- Firma digital del histopatólogo
- Generación automática de OT
- Envío por email automatizado
- Archivo de documentos

**Sprint 11: Refinamiento y Correcciones**
- Ajustes basados en feedback de histopatólogos
- Optimización de generación de PDF
- Mejora de plantillas de email
- Corrección de bugs

**Criterios de Aceptación:**
- Histopatólogo accede a formulario con datos del protocolo precargados
- PDF generado incluye todos los elementos requeridos (firma, logo, datos)
- Email se envía correctamente con informe y OT adjuntos
- Documentos quedan archivados y accesibles

**Pruebas:**
- Unitarias: Generación de PDF, cálculo de montos OT
- Integración: Flujo completo desde protocolo hasta envío de informe
- Usuario: Pruebas con histopatólogos y veterinarios destinatarios
- Rendimiento: Generación de 50 informes consecutivos

---

#### FASE 4: Tablero de Gestión y Reportes (2 semanas)

**Sprint 12-13: Visualización y Métricas**
- Dashboard de gestión visual (Figura 3.11)
- Indicadores de WIP por etapa
- Métricas de volumen (semana, mes, año)
- Módulo de reportes estadísticos (RF10)
- Exportación de datos
- Actualización en tiempo real

**Criterios de Aceptación:**
- Tablero muestra datos actualizados en tiempo real
- Métricas de WIP reflejan estado real del laboratorio
- Reportes se generan en < 5 segundos
- Exportación funciona en múltiples formatos

**Pruebas:**
- Rendimiento: Carga del dashboard con datos de 1 año
- Usuario: Validación con dirección del laboratorio
- Exactitud: Comparación métricas vs datos reales

---

#### FASE 5: Migración de Datos y Transición (3 semanas)

**Sprint 14: Migración de Datos Legacy**
- Análisis de datos en sistema Clarion
- Scripts de extracción
- Limpieza y normalización
- Importación a nuevo sistema
- Validación de integridad

**Sprint 15: Período de Coexistencia**
- Configuración de dual-entry (ambos sistemas)
- Capacitación exhaustiva al personal
- Documentación de usuario final
- Manuales y videos tutoriales

**Sprint 16: Transición Completa**
- Desactivación progresiva de sistema antiguo
- Monitoreo intensivo
- Soporte on-site durante primera semana
- Recolección de feedback
- Ajustes menores

**Entregables:**
- Base de datos migrada y validada
- Manual de usuario para cada rol
- Videos tutoriales
- Plan de contingencia
- Sistema en producción

---

#### FASE 6: Estabilización y Mejoras (Continuo)

**Post-lanzamiento (primeros 3 meses)**
- Soporte reactivo ante incidencias
- Corrección de bugs críticos en < 24h
- Bugs menores en siguiente sprint
- Recopilación de sugerencias de mejora
- Optimización de rendimiento basada en uso real

**Mejoras futuras (backlog)**
- Integración con código de barras/QR
- App móvil nativa
- Módulo de gestión de inventario de insumos
- Portal de colaboración inter-laboratorios
- Integración con sistemas de imagen (microscopio digital)
- Módulo de investigación y publicaciones
- Sistema de facturación electrónica

---

### 5.3 Cronograma Resumido

| Fase | Duración | Semanas Acumuladas |
|------|----------|-------------------|
| Fase 0: Preparación | 2 semanas | 0-2 |
| Fase 1: MVP - Usuarios y Protocolos | 4 semanas | 2-6 |
| Fase 2: Recepción y Procesamiento | 4 semanas | 6-10 |
| Fase 3: Informes y OT | 3 semanas | 10-13 |
| Fase 4: Tablero y Reportes | 2 semanas | 13-15 |
| Fase 5: Migración y Transición | 3 semanas | 15-18 |
| **TOTAL** | **18 semanas** | **~4.5 meses** |

**Nota**: Este cronograma asume:
- Equipo de 1-2 desarrolladores full-time
- Disponibilidad del equipo del laboratorio para pruebas y feedback
- No incluye período de estabilización post-lanzamiento

---

## 6. ESTRATEGIA DE TESTING

### 6.1 Tipos de Pruebas

#### 6.1.1 Pruebas Unitarias
- **Cobertura objetivo**: 80% del código
- **Framework**: TBD según stack elegido (Jest, PyTest, PHPUnit, etc.)
- **Alcance**:
  - Validaciones de formularios
  - Lógica de negocio (cálculo de montos, numeración)
  - Funciones de utilidad
  - Modelos de datos

#### 6.1.2 Pruebas de Integración
- **Herramientas**: TBD (Postman/Newman, REST Assured, etc.)
- **Alcance**:
  - Flujos completos de casos de uso
  - Interacción entre módulos
  - Operaciones de base de datos
  - Integración con servicios externos (email, PDF)

#### 6.1.3 Pruebas End-to-End (E2E)
- **Herramientas**: Selenium, Cypress, Playwright, o similar
- **Escenarios críticos**:
  - Flujo completo: registro → protocolo → recepción → procesamiento → informe → envío
  - Login y gestión de sesiones
  - Generación y descarga de PDFs
  - Navegación entre secciones

#### 6.1.4 Pruebas de Usuario (UAT)
- **Participantes**: Personal del laboratorio (3-5 personas)
- **Metodología**: 
  - Casos de uso reales con datos de prueba
  - Observación directa
  - Recolección de feedback estructurado
- **Frecuencia**: Al final de cada fase mayor

#### 6.1.5 Pruebas de Rendimiento
- **Herramientas**: JMeter, Locust, K6, o similar
- **Escenarios**:
  - Carga: 50 usuarios concurrentes
  - Stress: Identificar punto de quiebre
  - Generación masiva de PDFs
  - Consultas pesadas en dashboard

#### 6.1.6 Pruebas de Seguridad
- **Alcance**:
  - Penetration testing básico (OWASP Top 10)
  - Validación de control de acceso
  - Inyección SQL
  - XSS y CSRF
  - Análisis de dependencias vulnerables

### 6.2 Entornos de Prueba

**🔧 DECISIÓN TÉCNICA PENDIENTE: Configuración específica de entornos**

**Entornos requeridos:**
1. **Desarrollo (DEV)**: Local en máquina de cada desarrollador
2. **Testing (QA)**: Servidor compartido para pruebas internas
3. **Staging (STG)**: Replica de producción para pruebas finales
4. **Producción (PROD)**: Entorno real del laboratorio

**Datos de prueba:**
- Crear dataset sintético basado en casos reales anonimizados
- Incluir casos edge (protocolos con muchos cassettes, etc.)
- Mantener datos de prueba versionados

---

## 7. ESTRATEGIA DE DEPLOYMENT

### 7.1 Estrategia de Versioning

**🔧 DECISIÓN TÉCNICA PENDIENTE: Git branching model específico**

**Modelo recomendado: Git Flow simplificado**
- `main`: Código en producción
- `develop`: Rama de integración
- `feature/*`: Ramas para cada funcionalidad
- `hotfix/*`: Correcciones urgentes en producción
- `release/*`: Preparación de releases

### 7.2 Pipeline CI/CD

**Proceso automatizado:**
```
┌─────────────┐
│  Git Push   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  CI: Build & Test               │
│  • Linting                      │
│  • Pruebas Unitarias            │
│  • Pruebas de Integración       │
│  • Análisis de código estático  │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Build de Artefactos            │
│  • Compilación frontend         │
│  • Empaquetado backend          │
│  • Construcción de imágenes Docker │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Deploy a Staging               │
│  • Despliegue automático        │
│  • Smoke tests                  │
│  • Notificación al equipo       │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Aprobación Manual              │
│  • Revisión del equipo          │
│  • Validación funcional         │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Deploy a Producción            │
│  • Blue-Green o Rolling         │
│  • Rollback automático si falla │
│  • Monitoreo intensivo          │
└─────────────────────────────────┘
```

### 7.3 Estrategia de Deployment en Producción

**🔧 DECISIÓN TÉCNICA PENDIENTE: Estrategia específica**

**Opciones:**
1. **Blue-Green Deployment**: Dos entornos idénticos, switch instantáneo
2. **Rolling Deployment**: Actualización progresiva de instancias
3. **Canary Deployment**: Despliegue a subconjunto de usuarios primero

**Recomendación inicial**: Blue-Green por facilidad de rollback

### 7.4 Estrategia de Rollback

- Mantener versión anterior disponible durante 48h post-deployment
- Procedimiento de rollback documentado y probado
- Backup de base de datos pre-deployment
- Scripts de migración reversibles (up/down)

### 7.5 Ventanas de Mantenimiento

- **Preferidas**: Fines de semana o período de receso (6 semanas/año)
- **Duración típica**: 2-4 horas
- **Notificación**: Mínimo 1 semana de antelación a usuarios
- **Contingencia**: Plan B si el deployment falla

---

## 8. SEGURIDAD

### 8.1 Autenticación y Autorización

#### 8.1.1 Autenticación
**🔧 DECISIÓN TÉCNICA PENDIENTE: Mecanismo específico**

**Opciones:**
- Sesiones tradicionales con cookies
- JWT (JSON Web Tokens)
- OAuth 2.0 / OpenID Connect (para integración futura con sistemas universitarios)

**Requerimientos:**
- Contraseñas hasheadas con algoritmo moderno (bcrypt, Argon2)
- Política de contraseñas: mínimo 8 caracteres, complejidad media
- Recuperación de contraseña por email con token temporal
- Bloqueo tras N intentos fallidos

#### 8.1.2 Autorización
**Roles del sistema:**
1. **Administrador**: Acceso completo, gestión de usuarios
2. **Histopatólogo**: Consulta completa, redacción de informes
3. **Personal de Laboratorio**: Recepción, procesamiento, consultas
4. **Veterinario Cliente**: Envío de protocolos, consulta de sus casos

**Matriz de permisos a definir por endpoint/acción**

### 8.2 Protección de Datos

#### 8.2.1 Datos en Tránsito
- HTTPS obligatorio (TLS 1.2+)
- Certificado SSL válido
- HSTS (HTTP Strict Transport Security)

#### 8.2.2 Datos en Reposo
- Contraseñas: Hash irreversible
- Datos sensibles: Evaluar encriptación a nivel de base de datos
- Backups: Encriptados

#### 8.2.3 Cumplimiento Normativo
**🔧 ANÁLISIS LEGAL PENDIENTE**

Evaluar cumplimiento de:
- Ley de Protección de Datos Personales (Argentina)
- Regulaciones universitarias de manejo de información
- Confidencialidad de datos médicos veterinarios

**Medidas:**
- Consentimiento explícito de veterinarios en registro
- Política de privacidad clara
- Derecho a acceso, rectificación y eliminación de datos
- Registro de auditoría de accesos a información sensible

### 8.3 Prevención de Vulnerabilidades

**Medidas obligatorias:**
- Validación de entrada en frontend y backend
- Parametrización de queries (prevención de SQL injection)
- Sanitización de output (prevención de XSS)
- Tokens CSRF en formularios
- Rate limiting en endpoints críticos (login, registro)
- Actualización regular de dependencias
- Escaneo automático de vulnerabilidades conocidas

### 8.4 Auditoría

**Eventos a registrar:**
- Logins exitosos y fallidos
- Creación, modificación y eliminación de protocolos
- Envío de informes
- Cambios en configuración del sistema
- Accesos a datos de pacientes

**Información a almacenar:**
- Usuario
- Timestamp
- Acción realizada
- IP de origen
- Datos relevantes (ID de registro afectado, etc.)

**Retención**: Mínimo 1 año, evaluar requisitos legales

---

## 9. BACKUP Y RECUPERACIÓN

### 9.1 Estrategia de Backup

**🔧 DECISIÓN TÉCNICA PENDIENTE: Herramientas y ubicación específica**

#### 9.1.1 Base de Datos
- **Frecuencia**: 
  - Full backup: Diario, horario de baja actividad (ej: 2:00 AM)
  - Incremental: Cada 4 horas
  - Log de transacciones: Continuo (si soportado)
- **Retención**:
  - Backups diarios: 30 días
  - Backups semanales: 6 meses
  - Backups mensuales: 2 años
- **Ubicación**: Mínimo 2 ubicaciones (on-site + cloud/remote)

#### 9.1.2 Archivos (PDFs, imágenes)
- **Frecuencia**: Diario, sincronización incremental
- **Retención**: Misma política que base de datos
- **Consideración**: Volumen de archivos creciente, evaluar estrategia de archivo histórico

#### 9.1.3 Código Fuente
- Repositorio Git en plataforma con redundancia (GitHub, GitLab, Bitbucket)
- No requiere backup adicional (controlado por versiones)

### 9.2 Plan de Recuperación ante Desastres

**Escenarios:**

#### Escenario 1: Fallo de Hardware
- **RTO (Recovery Time Objective)**: 4 horas
- **RPO (Recovery Point Objective)**: Máximo 4 horas de datos perdidos
- **Procedimiento**:
  1. Activar servidor de respaldo o instancia cloud
  2. Restaurar último backup disponible
  3. Aplicar logs de transacciones si existen
  4. Validar integridad
  5. Redirigir DNS/tráfico
  6. Notificar a usuarios

#### Escenario 2: Corrupción de Datos
- **Detección**: Monitoreo automático de integridad
- **Procedimiento**:
  1. Identificar alcance de corrupción
  2. Aislar base de datos afectada
  3. Restaurar desde backup más reciente sin corrupción
  4. Validar con checksums
  5. Re-ingresar datos perdidos si es factible

#### Escenario 3: Ataque de Seguridad / Ransomware
- **Prevención**: Backups offline inmutables
- **Procedimiento**:
  1. Aislar sistemas comprometidos
  2. Análisis forense
  3. Restaurar desde backup limpio verificado
  4. Cambiar todas las credenciales
  5. Parchear vulnerabilidad
  6. Notificar a autoridades/usuarios según corresponda

### 9.3 Pruebas de Recuperación

- **Frecuencia**: Trimestral
- **Alcance**: Restauración completa en entorno de testing
- **Validación**: Verificar integridad de datos, accesibilidad del sistema
- **Documentación**: Actualizar procedimientos según aprendizajes

---

## 10. MONITOREO Y MANTENIMIENTO

### 10.1 Monitoreo de Aplicación

**🔧 DECISIÓN TÉCNICA PENDIENTE: Herramientas específicas**

#### 10.1.1 Métricas a Monitorear
**Infraestructura:**
- CPU, memoria, disco, red
- Tiempo de respuesta de endpoints
- Tasa de errores (4xx, 5xx)
- Disponibilidad del servicio (uptime)

**Aplicación:**
- Tiempo de generación de PDFs
- Tiempo de consultas a base de datos
- Tiempo de envío de emails
- Uso de cache

**Negocio:**
- Protocolos ingresados por día/semana
- Tiempos promedio por etapa del proceso
- Usuarios activos
- Informes enviados

#### 10.1.2 Alertas
**Niveles:**
- **Crítico**: Sistema caído, tasa de error >10%, base de datos inaccesible
  - Notificación: Inmediata por SMS/llamada + email + Slack
- **Alto**: Lentitud extrema, disco >90%, errores en emails
  - Notificación: Email + Slack en < 15 min
- **Medio**: Lentitud moderada, disco >80%, tasa error >5%
  - Notificación: Email diario resumido
- **Bajo**: Warnings, métricas anómalas pero no críticas
  - Notificación: Dashboard, revisión semanal

#### 10.1.3 Logs
- **Nivel de log**: INFO para operaciones normales, DEBUG solo en desarrollo
- **Centralización**: Todos los logs en sistema centralizado
- **Estructuración**: JSON estructurado para facilitar búsqueda
- **Rotación**: Diaria, retención 90 días en storage económico

### 10.2 Mantenimiento Preventivo

#### 10.2.1 Actualizaciones
- **Dependencias**: Revisión mensual de actualizaciones disponibles
- **Seguridad**: Actualizaciones de seguridad en < 48h de release
- **Framework/Lenguaje**: Evaluación trimestral de versiones LTS
- **Base de datos**: Actualización anual de versión minor, mayor solo si necesario

#### 10.2.2 Optimización
- **Queries**: Revisión trimestral de queries lentas (slow query log)
- **Índices**: Evaluación semestral de índices de base de datos
- **Cache**: Ajuste de políticas según patrones de uso
- **Archivos**: Evaluación semestral de estrategia de almacenamiento

#### 10.2.3 Limpieza
- **Datos temporales**: Limpieza semanal de datos no esenciales
- **Logs**: Archivado/eliminación según política de retención
- **Backups obsoletos**: Eliminación según política
- **Archivos huérfanos**: Detección y eliminación trimestral

### 10.3 Documentación

#### 10.3.1 Documentación Técnica
- **Arquitectura**: Diagramas actualizados en cada cambio mayor
- **API**: Especificación OpenAPI/Swagger mantenida automáticamente
- **Base de datos**: ERD actualizado, diccionario de datos
- **Deployment**: Runbooks para procedimientos operativos
- **Troubleshooting**: Guía de problemas comunes y soluciones

#### 10.3.2 Documentación de Usuario
- **Manual de usuario**: Por rol, con capturas de pantalla
- **Videos tutoriales**: Grabaciones de pantalla para procesos clave
- **FAQs**: Actualización basada en tickets de soporte
- **Changelog**: Registro de cambios visible para usuarios

---

## 11. CAPACITACIÓN Y CAMBIO ORGANIZACIONAL

### 11.1 Plan de Capacitación

#### 11.1.1 Capacitación para Personal del Laboratorio
**Duración**: 2 jornadas de 4 horas + 1 semana de soporte on-site

**Día 1: Conceptos y Recepción**
- Introducción al nuevo sistema (30 min)
- Demostración del flujo completo (30 min)
- Módulo de autenticación (15 min)
- Recepción de muestras - hands-on (1h 30min)
- Generación de etiquetas (30 min)
- Consulta de protocolos (30 min)
- Sesión de preguntas (15 min)

**Día 2: Procesamiento e Informes**
- Repaso día anterior (15 min)
- Registro de procesamiento - hands-on (1h 30min)
- Redacción de informes (histopatólogos) (1h)
- Dashboard y reportes (30 min)
- Troubleshooting básico (30 min)
- Sesión de preguntas (15 min)

**Materiales:**
- Manual impreso por participante
- Videos de respaldo
- Credenciales de prueba en entorno staging
- Casos de práctica con datos sintéticos

#### 11.1.2 Capacitación para Veterinarios Clientes
**Modalidad**: Autoaprendizaje + webinars opcionales

**Materiales:**
- Video tutorial de 10 minutos (registro y envío de protocolo)
- Manual PDF descargable
- FAQ en el sitio
- Email de bienvenida con guía rápida

**Webinars** (opcional, 2 sesiones de 1 hora):
- Sesión 1: Registro y envío de protocolos
- Sesión 2: Consulta de resultados y casos especiales
- Grabaciones disponibles posteriormente

#### 11.1.3 Soporte Post-Capacitación
- **Semana 1**: Presencia on-site de desarrollador para resolver dudas
- **Mes 1**: Soporte prioritario por email/teléfono (respuesta < 2h)
- **Meses 2-3**: Soporte normal (respuesta < 24h)
- **Continuo**: Sistema de tickets / email de soporte

### 11.2 Gestión del Cambio

#### 11.2.1 Comunicación
**Timeline de comunicación:**
- **3 meses antes**: Anuncio del proyecto, beneficios esperados
- **1 mes antes**: Demos del sistema, invitación a capacitaciones
- **2 semanas antes**: Recordatorios, fechas clave
- **1 semana antes**: Instrucciones finales, contingencias
- **Lanzamiento**: Comunicado oficial, canales de soporte
- **Post-lanzamiento**: Comunicados de mejoras, agradecimientos

**Canales:**
- Email institucional
- Reuniones presenciales con personal del laboratorio
- Anuncios en sitio web del laboratorio
- Material impreso en recepción

#### 11.2.2 Gestión de Resistencias
**Estrategias:**
- Involucrar al personal desde el diseño (ya hecho con encuestas)
- Destacar beneficios concretos para cada rol
- Mostrar reducción de tareas tediosas
- Período de coexistencia para adaptación gradual
- Champions internos: identificar early adopters que promuevan el cambio
- Recoger feedback activamente y actuar sobre él

#### 11.2.3 Métricas de Adopción
- % de veterinarios que envían protocolos online (objetivo: >80% en 6 meses)
- % de protocolos procesados completamente en sistema (objetivo: 100% en 1 mes)
- Reducción de consultas sobre estado de muestras (objetivo: -50% en 3 meses)
- Tiempo promedio para completar informe (objetivo: -30% en 3 meses)
- Satisfacción de usuarios (encuesta post-lanzamiento objetivo: >4/5)

---

## 12. COSTOS Y RECURSOS

### 12.1 Equipo de Desarrollo

**🔧 DECISIÓN PENDIENTE: Composición específica del equipo**

**Opción 1: Equipo Mínimo**
- 1 Desarrollador Full-Stack (senior/semi-senior): 4.5 meses full-time
- 1 Diseñador UX/UI: 1 mes part-time (20h)
- 1 QA Tester: 1 mes full-time (durante Fase 5)

**Opción 2: Equipo Óptimo**
- 1 Desarrollador Backend: 4.5 meses full-time
- 1 Desarrollador Frontend: 4 meses full-time
- 1 Diseñador UX/UI: 1 mes part-time
- 1 QA/DevOps: 2 meses full-time
- 1 Project Manager: 5 meses part-time (10h/semana)

**Estimación de costos (basado en mercado argentino 2024):**
- Según documento: Desarrollo estimado ~2000 USD (muy conservador para MVP mínimo)
- Estimación realista equipo mínimo: 8,000 - 12,000 USD
- Estimación realista equipo óptimo: 15,000 - 20,000 USD

### 12.2 Infraestructura

**Costos de hardware (del documento original):**
- Actualización hardware: ~626 USD one-time

**Costos de hosting y servicios (estimación anual):**
- **Opción Cloud**:
  - VPS (4GB RAM, 2 vCPU, 80GB SSD): ~15-30 USD/mes
  - Base de datos managed: ~20-40 USD/mes
  - Storage para archivos: ~5-10 USD/mes
  - Email service: ~10-20 USD/mes
  - Backup storage: ~5-10 USD/mes
  - **Total estimado**: ~660-1,200 USD/año

- **Opción On-Premise**:
  - Servidor: ~1,500-2,500 USD one-time
  - Mantenimiento eléctrico: costo marginal
  - Administración: requiere personal IT institucional

**Otros costos:**
- Dominio: ~10 USD/año
- Certificado SSL: ~0 USD (Let's Encrypt gratis) o ~50-200 USD/año (comercial)
- Herramientas de desarrollo: ~0 USD (usando opciones open source/free tier)

### 12.3 Mantenimiento (Anual)

**Costos del documento original:**
- Mantenimiento sistema: 600 USD/año
- Licencias software: 120 USD/año
- **Total**: 720 USD/año

**Desglose adicional recomendado:**
- Soporte técnico (20h/año a rate reducido): ~400-800 USD
- Actualizaciones y mejoras menores: incluido en soporte
- Monitoreo y herramientas: ~120 USD/año
- **Total realista**: ~1,200-1,600 USD/año

### 12.4 Resumen de Inversión

| Concepto | Costo Inicial | Costo Anual Recurrente |
|----------|---------------|------------------------|
| Desarrollo (equipo mínimo) | 8,000 - 12,000 USD | - |
| Hardware | 626 USD | - |
| Infraestructura setup | 300 USD | 660 - 1,200 USD |
| Capacitación y transición | incluido en desarrollo | - |
| Mantenimiento | - | 1,200 - 1,600 USD |
| **TOTAL** | **~9,000 - 13,000 USD** | **~2,000 - 3,000 USD/año** |

**Comparación con beneficios esperados (del Cap. VI):**
- Beneficio anual estimado: 3,102 USD/año
- ROI esperado: Positivo desde año 1
- Payback period: ~3-4 años

---

## 13. RIESGOS Y MITIGACIÓN

### 13.1 Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Problemas de rendimiento con volumen de datos** | Media | Alto | - Testing de carga desde fase temprana<br>- Optimización de queries<br>- Implementación de cache<br>- Plan de escalabilidad |
| **Fallas en generación de PDF** | Media | Alto | - Probar múltiples librerías<br>- Tener fallback a generación básica<br>- Testing exhaustivo con casos reales |
| **Pérdida de datos en migración** | Baja | Crítico | - Backups múltiples pre-migración<br>- Migración en etapas<br>- Validación rigurosa<br>- Período de coexistencia |
| **Incompatibilidad con navegadores** | Baja | Medio | - Testing cross-browser desde fase 1<br>- Uso de frameworks modernos con buen soporte<br>- Polyfills para compatibilidad |
| **Vulnerabilidades de seguridad** | Media | Alto | - Code reviews<br>- Análisis automático de vulnerabilidades<br>- Penetration testing<br>- Actualizaciones regulares |
| **Fallos en envío de emails** | Media | Medio | - Sistema de retry automático<br>- Logging detallado<br>- Alertas de fallos<br>- Servicio de email confiable |

### 13.2 Riesgos de Proyecto

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Retrasos en desarrollo** | Alta | Medio | - Buffer del 20% en estimaciones<br>- Priorización clara de funcionalidades<br>- Sprints cortos con entregas incrementales |
| **Cambios de alcance (scope creep)** | Alta | Alto | - Definición clara de MVP<br>- Proceso formal de change requests<br>- Backlog de mejoras futuras |
| **Falta de disponibilidad del personal del laboratorio para pruebas** | Media | Medio | - Coordinar fechas con anticipación<br>- Flexibilidad en horarios<br>- Incentivos para participación |
| **Resistencia al cambio** | Media | Alto | - Involucramiento temprano<br>- Comunicación constante<br>- Capacitación exhaustiva<br>- Champions internos |
| **Presupuesto insuficiente** | Media | Alto | - Estimación realista desde inicio<br>- Priorización de funcionalidades core<br>- Buscar financiamiento universitario |

### 13.3 Riesgos Operacionales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Falta de personal de soporte post-lanzamiento** | Media | Medio | - Documentación exhaustiva<br>- Capacitación de personal interno<br>- Contrato de mantenimiento con desarrolladores |
| **Falla de infraestructura** | Baja | Alto | - Redundancia en servidores<br>- Backups automáticos<br>- Plan de contingencia<br>- Monitoreo 24/7 |
| **Conectividad deficiente** | Media | Medio | - Optimización para conexiones lentas<br>- Modo offline básico (futuro)<br>- Mejora de WiFi del laboratorio |
| **Rotación de personal capacitado** | Media | Medio | - Documentación clara<br>- Videos de capacitación reutilizables<br>- Proceso de onboarding definido |

### 13.4 Plan de Contingencia

**Si el proyecto se retrasa significativamente:**
- Lanzar con funcionalidades core únicamente (Fases 1-3)
- Posponer tablero de gestión y reportes avanzados
- Mantener sistema antiguo para consultas históricas

**Si hay problemas técnicos graves en producción:**
- Rollback inmediato a versión anterior
- Revertir a sistema antiguo temporalmente si es necesario
- Comunicación transparente con usuarios
- Plan de corrección acelerada

**Si no hay adopción del sistema:**
- Análisis de causas (usabilidad, capacitación, resistencia)
- Ajustes rápidos basados en feedback
- Incentivos para uso (descuentos, prioridad)
- Obligatoriedad gradual si es necesario

---

## 14. MÉTRICAS DE ÉXITO

### 14.1 Métricas de Implementación

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| **Cumplimiento de plazos** | Máximo 15% de desvío | Fecha planificada vs real por fase |
| **Cumplimiento de presupuesto** | Máximo 10% de desvío | Presupuesto vs gasto real |
| **Cobertura de tests** | Mínimo 80% | Herramienta de coverage |
| **Bugs en producción (primer mes)** | Máximo 10 bugs críticos/altos | Sistema de tracking |
| **Disponibilidad del sistema** | >99% primer mes | Monitoreo de uptime |

### 14.2 Métricas de Adopción

| Métrica | Objetivo 1 mes | Objetivo 3 meses | Objetivo 6 meses |
|---------|----------------|------------------|------------------|
| **% protocolos enviados online** | >30% | >60% | >80% |
| **% de personal usando sistema** | 100% | 100% | 100% |
| **Consultas sobre estado de muestras** | -20% | -40% | -50% |
| **Errores en protocolos por info incompleta** | -30% | -50% | -70% |

### 14.3 Métricas de Impacto (del documento original)

| Métrica | Línea Base | Objetivo 6 meses | Objetivo 1 año |
|---------|------------|------------------|----------------|
| **Capacidad de atención** | 1,151 prot/año | 1,240 prot/año | 1,334 prot/año |
| **Tiempo de redacción de informe** | X min (medir) | -20% | -30% |
| **Tiempo total de procesamiento (TAT)** | X días (medir) | -15% | -25% |
| **Satisfacción de clientes** | 3.8/5 (encuesta) | 4.2/5 | 4.5/5 |
| **Satisfacción de personal** | 3.7/5 (encuesta) | 4.0/5 | 4.3/5 |

### 14.4 Métricas de Calidad

| Métrica | Objetivo |
|---------|----------|
| **Informes con errores** | <1% |
| **PDFs generados incorrectamente** | <0.5% |
| **Pérdida de trazabilidad de muestras** | 0% |
| **Emails no entregados** | <2% |
| **Tiempo de respuesta promedio** | <2 seg para operaciones normales |

### 14.5 Evaluación Post-Implementación

**A los 3 meses:**
- Encuesta de satisfacción a usuarios (veterinarios y personal)
- Análisis de métricas de uso y rendimiento
- Identificación de mejoras prioritarias
- Reporte a dirección del laboratorio

**A los 6 meses:**
- Evaluación formal de impacto vs objetivos del Capítulo V
- Análisis de ROI real vs proyectado
- Planificación de fase 2 de mejoras
- Publicación de caso de éxito (si aplica)

---

## 15. ANEXOS

### 15.1 Casos de Uso Detallados

Referirse a Anexo II del documento original para especificaciones completas:
- CU IV.2.1: Registrarse en el sistema
- CU IV.2.2: Completar protocolo de remisión de muestra
- CU IV.2.3: Consultar estado de protocolos
- CU IV.2.4: Registrar recepción de muestra
- CU IV.2.5: Ingresar datos de procesamiento
- CU IV.2.6: Consultar protocolo
- CU IV.2.7: Redactar Informe de Resultados

### 15.2 Mockups y Wireframes

Referirse a Anexo I del documento original para vistas del sistema:
- A1.1: Página de inicio y login clientes
- A1.2: Formulario de registro
- A1.3: Formulario de protocolo
- A1.4: Consulta de protocolos
- A1.5: Login personal de laboratorio
- A1.6: Consulta datos de protocolo
- A1.7: Registrar procesamiento
- A1.8: Formulario de informe de resultados

### 15.3 Modelo de Datos

**Diagrama Entidad-Relación**: Ver Figura 4.3 del documento original

**Esquema Relacional**: Ver Tabla 4.5 del documento original

### 15.4 Glosario de Términos

- **Protocolo**: Documento que acompaña la muestra con información del caso clínico
- **Muestra**: Material biológico enviado para análisis (citología o histopatología)
- **Cassette**: Contenedor para procesamiento de tejidos en histopatología
- **Portaobjetos (Slide)**: Lámina de vidrio donde se monta la muestra para observación microscópica
- **Taco de Parafina**: Bloque de parafina con tejido incluido para corte con micrótomo
- **OT (Orden de Trabajo)**: Documento que especifica servicios y costos
- **TAT (Turnaround Time)**: Tiempo total desde recepción de muestra hasta entrega de informe
- **WIP (Work In Progress)**: Trabajo en proceso, muestras en cada etapa del flujo

### 15.5 Referencias y Recursos

**Documentación Técnica:**
- UML 2 and the Unified Process (Arlow & Neustadt, 2005)
- BPMN Manual de Referencia (Freund et al., 2017)
- Sistemas de Información Gerencial (Laudon & Laudon, 2008)

**Mejores Prácticas:**
- Lean in Healthcare (Apostu et al., 2021)
- Business Process Reengineering (Mohapatra, 2013)
- Turnaround Time in Medical Laboratories (Dawande et al., 2022)

**Normativas:**
- Recomendaciones del Ministerio de Salud Argentina para servicios de anatomía patológica (2022)
- OWASP Top 10 (para seguridad web)
- WCAG 2.0 (para accesibilidad)

---

## 16. DECISIONES TÉCNICAS PENDIENTES - RESUMEN

### 16.1 Críticas (Deben resolverse en Fase 0)

1. **Stack Tecnológico Completo**:
   - Framework frontend (React/Vue/Angular/otros)
   - Framework backend (Node/Python/PHP/otros)
   - Base de datos (PostgreSQL/MySQL/otros)
   - ORM a utilizar

2. **Infraestructura**:
   - Cloud vs on-premise vs híbrido
   - Proveedor específico si es cloud
   - Estrategia de deployment (Blue-Green/Rolling/otros)

3. **Autenticación**:
   - Sesiones vs JWT vs OAuth
   - Proveedor de sesiones (Redis/base de datos/otros)

4. **Generación de PDF**:
   - Librería específica a utilizar
   - Estrategia de plantillas

### 16.2 Importantes (Deben resolverse en Fase 1-2)

5. **Arquitectura de Software**:
   - Patrón arquitectónico (MVC/Clean/otros)
   - Monolito vs microservicios (recomendado: monolito modular inicialmente)

6. **Gestión de Archivos**:
   - Storage local vs S3/similares
   - Estrategia de CDN (si aplica)

7. **Email**:
   - Servicio SMTP (institucional/SendGrid/SES/otros)
   - Plantillas (sistema de templates a usar)

8. **Monitoreo**:
   - Herramientas específicas (Sentry, ELK, Prometheus, etc.)
   - Estrategia de logging

### 16.3 Deseables (Pueden resolverse durante desarrollo)

9. **Testing**:
   - Frameworks específicos para cada tipo de test
   - Nivel de cobertura objetivo detallado

10. **CI/CD**:
    - Plataforma específica (GitHub Actions/GitLab CI/otros)
    - Modelo de branching (Git Flow/GitHub Flow/otros)

11. **Firma Digital**:
    - Nivel de firma (simple/avanzada)
    - Si se integra con proveedor externo o es imagen

12. **Búsqueda Avanzada**:
    - Si se usa Elasticsearch o búsqueda SQL básica

---

## 17. PRÓXIMOS PASOS INMEDIATOS

### Para el Cliente (Laboratorio):

1. **Revisar y aprobar este plan** de desarrollo
2. **Asignar un referente técnico** del laboratorio que participe en el proyecto
3. **Confirmar presupuesto** disponible
4. **Evaluar opciones de hosting** (usar infraestructura universitaria vs contratar cloud)
5. **Coordinar disponibilidad** del personal para pruebas y capacitación

### Para el Equipo de Desarrollo:

1. **Tomar decisiones técnicas críticas** (sección 16.1)
2. **Configurar repositorio** y estructura inicial del proyecto
3. **Crear documento de arquitectura técnica** detallada
4. **Preparar entorno de desarrollo** local
5. **Definir estándares de código** y configurar linters
6. **Iniciar Fase 1** según cronograma

### Para la Dirección/Sponsors:

1. **Aprobar financiamiento** del proyecto
2. **Comunicar el proyecto** a la comunidad del laboratorio
3. **Designar facilitador** para gestión del cambio organizacional
4. **Establecer comité de seguimiento** (reuniones quincenales recomendadas)

---

## CONCLUSIÓN

Este plan de desarrollo proporciona una hoja de ruta completa para implementar el sistema informático del Laboratorio de Anatomía Patológica Veterinaria. El enfoque es **incremental y centrado en el usuario**, priorizando funcionalidades core que generen valor inmediato.

**Factores clave de éxito:**
- ✅ Involucramiento activo del personal del laboratorio
- ✅ Decisiones técnicas informadas y documentadas
- ✅ Testing exhaustivo en cada fase
- ✅ Comunicación constante y transparente
- ✅ Flexibilidad para ajustar el plan según feedback real

**Riesgo principal identificado:** Resistencia al cambio → Mitigado con capacitación, comunicación y período de transición.

El proyecto tiene un **ROI positivo** y un impacto significativo en la eficiencia operativa del laboratorio, posicionándolo para continuar brindando un servicio de excelencia a la comunidad veterinaria regional.

---

**Documento elaborado para**: Laboratorio de Anatomía Patológica Veterinaria, FCV-UNL  
**Basado en**: Proyecto Final de Ingeniería Industrial - MARÍA SOL KLEIN  
**Fecha**: Octubre 2024  
**Versión**: 1.0  
**Estado**: Pendiente aprobación técnica y decisiones de implementación  
**Próxima revisión**: Tras decisiones técnicas de Fase 0

