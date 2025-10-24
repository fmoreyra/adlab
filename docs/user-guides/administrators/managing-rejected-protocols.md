# Gestión de Protocolos Rechazados - Administradores

Esta guía explica cómo los administradores gestionan protocolos con muestras rechazadas y el proceso de reenvío.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🎯 Resumen

Como administrador, puedes gestionar protocolos que fueron rechazados por problemas de calidad de muestra, incluyendo la capacidad de reenviarlos si fue un error en la evaluación inicial.

## 📋 Ver Protocolos Rechazados

### Acceder a la Lista de Rechazados

1. **Ir al Dashboard de Administración**
2. **Hacer clic en "Protocolos Rechazados"** en la sección de herramientas
3. **Ver lista completa** con información detallada

_[Espacio para captura de pantalla: Dashboard con enlace a protocolos rechazados]_

### Información que Verás

#### Datos del Protocolo
- **Código temporal**: Identificador único (ej: HP 25/002)
- **Veterinario**: Nombre y email del solicitante
- **Animal**: Identificación y especie
- **Fecha de rechazo**: Cuándo fue rechazada la muestra
- **Motivo**: Razón detallada del rechazo
- **Personal que rechazó**: Quién tomó la decisión

#### Estado Actual
- **Estado**: RECHAZADO (no tiene número de protocolo)
- **Condición de muestra**: Rechazada
- **Observaciones**: Detalles del problema
- **Discrepancias**: Si las hubo

_[Espacio para captura de pantalla: Lista de protocolos rechazados]_

## 🔄 Reenviar Protocolo Rechazado

### Cuándo Reenviar

#### Casos Válidos para Reenvío
- **Error en evaluación inicial**: La muestra era aceptable
- **Veterinario envió nueva muestra**: Con las correcciones necesarias
- **Condiciones mejoradas**: Problema resuelto
- **Acuerdo con veterinario**: Decisión conjunta

#### Cuándo NO Reenviar
- **Muestra claramente inadecuada**: Sin posibilidad de análisis
- **Problemas de identificación**: Sin resolver
- **Veterinario no envió nueva muestra**: Solo quiere reenviar la misma

### Proceso de Reenvío

#### Paso 1: Seleccionar Protocolo
1. **En la lista de rechazados**, hacer clic en "Reenviar"
2. **Ver detalles del protocolo** y motivo de rechazo
3. **Confirmar que es apropiado** reenviar

_[Espacio para captura de pantalla: Botón de reenvío en lista]_

#### Paso 2: Completar Formulario
1. **Abrir formulario de reenvío** (página completa)
2. **Completar campo obligatorio**: Motivo del reenvío
   - **Mínimo 10 caracteres**
   - **Máximo 500 caracteres**
   - **Ser específico**: Explicar por qué se reenvía
3. **Revisar información del protocolo**
4. **Confirmar reenvío**

_[Espacio para captura de pantalla: Formulario de reenvío]_

#### Paso 3: Confirmación
1. **Estado cambia automáticamente** a SUBMITTED
2. **Protocolo disponible** para nueva recepción
3. **Se registra en historial** el cambio de estado
4. **Mensaje de confirmación** en pantalla

### Ejemplos de Motivos Válidos

#### Error en Evaluación
```
"Error en evaluación inicial. La muestra fue reexaminada por el supervisor y se determinó que cumple los estándares de calidad. La fijación es adecuada y la cantidad de material es suficiente para análisis."
```

#### Nueva Muestra Recibida
```
"El veterinario envió una nueva muestra siguiendo las recomendaciones. La muestra cumple todos los criterios de calidad y está lista para procesamiento."
```

#### Condiciones Mejoradas
```
"Problema de identificación resuelto. El veterinario proporcionó documentación adicional que aclara la discrepancia. La muestra puede procesarse normalmente."
```

## 📊 Auditoría y Seguimiento

### Historial de Cambios

#### Información Registrada
- **Usuario que reenvió**: Quién tomó la decisión
- **Fecha y hora**: Cuándo se realizó el cambio
- **Motivo del reenvío**: Razón documentada
- **Estado anterior**: RECHAZADO
- **Estado nuevo**: SUBMITTED

#### Acceso al Historial
1. **En detalles del protocolo**
2. **Sección "Historial de Estado"**
3. **Ver todos los cambios** con timestamps
4. **Usuario responsable** de cada cambio

_[Espacio para captura de pantalla: Historial de cambios de estado]_

### Métricas y Reportes

#### Estadísticas Importantes
- **Total de rechazos**: Por período
- **Tasa de reenvío**: Porcentaje que se reenvían
- **Motivos más comunes**: De rechazo
- **Personal que rechaza**: Distribución de decisiones

#### Reportes Disponibles
- **Rechazos por mes**: Tendencias temporales
- **Rechazos por veterinario**: Identificar patrones
- **Rechazos por tipo de muestra**: Histopatología vs citología
- **Tiempo promedio**: Entre rechazo y reenvío

## 🚨 Mejores Prácticas

### Para Decisiones de Rechazo

#### Criterios Claros
- **Documentar específicamente** el problema
- **Ser consistente** en las evaluaciones
- **Consultar con supervisor** en casos dudosos
- **Comunicar claramente** al veterinario

#### Evitar Errores
- **No rechazar por prisas**: Tomar tiempo para evaluar
- **No asumir**: Preguntar si hay dudas
- **Documentar completamente**: Para auditoría
- **Revisar criterios**: Antes de decidir

### Para Reenvíos

#### Validación Previa
- **Verificar que el problema se resolvió**
- **Confirmar con el veterinario** si es necesario
- **Revisar nueva muestra** si aplica
- **Documentar el motivo** completamente

#### Comunicación
- **Notificar al veterinario** del reenvío
- **Explicar los próximos pasos**
- **Ofrecer apoyo** si es necesario
- **Mantener seguimiento** del caso

## 📧 Notificaciones

### Emails Automáticos

#### Al Veterinario
- **Muestra rechazada**: Con motivo detallado
- **Protocolo reenviado**: Confirmación de reactivación
- **Nueva muestra recibida**: Si aplica

#### Al Personal del Laboratorio
- **Protocolo reenviado**: Para nueva recepción
- **Cambio de estado**: Notificación de actualización

## ❓ Preguntas Frecuentes

### P: ¿Puedo reenviar un protocolo rechazado múltiples veces?
R: Sí, pero cada reenvío debe tener un motivo válido y documentado. El sistema mantiene historial completo.

### P: ¿Qué pasa si reenvío por error?
R: Puedes contactar al supervisor para revisar el caso. El sistema mantiene auditoría completa de todos los cambios.

### P: ¿Debo notificar al veterinario cuando reenvío?
R: El sistema envía notificación automática, pero es buena práctica contactar directamente para explicar la situación.

### P: ¿Puedo ver estadísticas de rechazos?
R: Sí, el sistema genera reportes de rechazos por período, veterinario, y tipo de muestra.

### P: ¿Qué hago si un veterinario disputa un rechazo?
R: Revisa el caso con el supervisor. Si es válido, puedes reenviar el protocolo. Si no, explica los criterios de calidad al veterinario.

## 🆘 Obtener Ayuda

### Contactos Importantes
- **Supervisor de laboratorio**: Para decisiones complejas
- **Histopatólogo jefe**: Para criterios técnicos
- **Soporte técnico**: Para problemas del sistema
- **Veterinario solicitante**: Para aclaraciones

### Escalación de Casos
1. **Caso complejo**: Consultar con supervisor
2. **Disputa de rechazo**: Revisar con histopatólogo
3. **Problema técnico**: Contactar soporte
4. **Emergencia**: Seguir protocolo de urgencias

---

*Anterior: [Gestionar usuarios](managing-users.md)*
*Siguiente: [Configurar sistema](system-settings.md)*
