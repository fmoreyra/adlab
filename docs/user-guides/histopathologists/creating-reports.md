# Guía de Creación de Informes para Histopatólogos

Esta guía explica cómo los histopatólogos crean y gestionan informes de patología en el Sistema de Gestión de Laboratorio.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 📋 Resumen

Los histopatólogos son responsables de analizar muestras y crear informes detallados de patología. Esta guía cubre el flujo de trabajo completo de creación de informes.

## ✅ Requisitos previos (obligatorios)

Antes de elaborar informes, verificá que tu cuenta cumpla lo siguiente:

| Requisito | Dónde se configura | Cómo comprobarlo |
|-----------|-------------------|------------------|
| Rol histopatólogo o personal de lab | Admin → Usuario | Podés acceder a recepción/procesamiento |
| Perfil **Personal de laboratorio** | Admin → Personal de laboratorio | Existe un registro vinculado a tu usuario |
| **Puede crear informes** | Mismo perfil | Sin esto verás un aviso gris en el protocolo |
| **Firma digital** cargada | [Cargar firma](../lab-staff/digital-signature.md) o Admin | Sin esto el sistema te redirige a `/accounts/lab-staff/signature/` |

> **Nota:** El rol de histopatólogo **no** alcanza por sí solo; hace falta el perfil unificado con permiso y firma.

---

## 🚀 Comenzando

### Acceder al Sistema
1. **Iniciar sesión**: Acceder al sistema con tus credenciales de histopatólogo
2. **Panel de control**: Ver tus protocolos asignados e informes pendientes

_[Espacio para captura de pantalla: Panel de histopatólogo mostrando protocolos asignados e informes pendientes]_

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

_[Espacio para captura de pantalla: Lista de protocolos asignados al histopatólogo]_

### Detalles del Protocolo

Hacer clic en un protocolo para ver información completa:
- Información del animal y propietario
- Historia clínica y signos
- Diagnóstico presuntivo del veterinario
- Detalles de la muestra
- Información de procesamiento

_[Espacio para captura de pantalla: Vista de detalles del protocolo para histopatólogos]_

## 📝 Crear Informes

### Dónde iniciar el informe (interfaz actual)

Podés empezar desde cualquiera de estos puntos cuando el protocolo está en estado **Listo**:

1. **Detalle del protocolo** — bloque azul/índigo **«Informe patológico»** → *Elaborar informe*
2. **Estado de procesamiento** — mismo bloque al final de la página
3. **Cola de informes pendientes** — menú de informes / `protocols:report_pending_list`

Si no tenés firma cargada, verás un aviso ámbar con enlace **Cargar firma ahora** en lugar de los botones de elaboración.

_[Espacio para captura de pantalla: Bloque Informe patológico en detalle de protocolo]_

### Paso 1: Iniciar Creación de Informe

1. **Seleccionar Protocolo**: Protocolo en estado *Listo* (procesamiento técnico completo)
2. **Hacer clic en «Elaborar informe»** (o *Crear informe* en la cola pendiente)
3. **Responsable del informe**: En el formulario, elegir el personal que firmará el PDF (debe tener firma digital)
4. **Plantilla de Informe**: El sistema carga los datos del protocolo

_[Espacio para captura de pantalla: Formulario de creación con campo Personal de laboratorio]_

### Paso 2: Información del Informe

#### Datos Básicos del Informe
- **Fecha del Informe**: Fecha de creación del informe
- **Versión del Informe**: Número de versión (auto-incrementado)
- **Tipo de Informe**: Estándar, Urgente o Especial
- **Nivel de Complejidad**: Simple, Moderado o Complejo

_[Espacio para captura de pantalla: Sección de información básica del informe]_

#### Descripción Macroscópica
- **Descripción de la Muestra**: Descripción física de la muestra
- **Tamaño y Medidas**: Dimensiones y peso
- **Color y Consistencia**: Características visuales
- **Observaciones Adicionales**: Cualquier característica notable

**Ejemplo de descripción macroscópica:**
```
Se recibe biopsia de piel de 2x1x0.5 cm, de coloración blanquecina,
consistencia firme, superficie lisa con áreas de ulceración focal.
Peso: 1.2 gramos. Se procesa en su totalidad en 2 cassettes.
```

_[Espacio para captura de pantalla: Sección del formulario de descripción macroscópica]_

### Paso 3: Análisis Microscópico

#### Gestión de Cassettes
- **Agregar Cassettes**: Crear cassettes para diferentes secciones de tejido
- **Etiquetas de Cassette**: Etiquetar cada cassette apropiadamente (A, B, C, etc.)
- **Conteo de Secciones**: Número de secciones por cassette

_[Espacio para captura de pantalla: Interfaz de gestión de cassettes]_

#### Observaciones Microscópicas
Para cada cassette:

1. **Seleccionar Cassette**: Elegir el cassette a analizar
2. **Agregar Observaciones**: Registrar hallazgos microscópicos
3. **Usar Plantillas**: Seleccionar de plantillas de observación comunes
4. **Texto Personalizado**: Agregar observaciones personalizadas

_[Espacio para captura de pantalla: Formulario de observaciones microscópicas con opciones de plantilla]_

#### Plantillas de Observación

Las plantillas comunes incluyen:

**Patrones Inflamatorios:**
- Inflamación aguda
- Inflamación crónica
- Granulomatosa
- Piogranulomatosa
- Necrotizante

**Patrones Neoplásicos:**
- Neoplasia benigna
- Neoplasia maligna
- Metastásico
- Con invasión vascular/linfática

**Cambios Degenerativos:**
- Necrosis (coagulativa, licuefactiva, caseosa)
- Fibrosis
- Calcificación
- Atrofia
- Hiperplasia

**Agentes Infecciosos:**
- Bacterias (cocos, bacilos)
- Hongos (levaduras, hifas)
- Parásitos
- Inclusiones virales

_[Espacio para captura de pantalla: Plantillas de observación disponibles]_

**Ejemplo de observación microscópica:**
```
Cassette A: Se observa epidermis con hiperqueratosis ortoqueratósica
moderada y acantosis leve. En la dermis superficial y media hay
infiltrado inflamatorio mixto moderado a severo compuesto por neutrófilos,
macrófagos, linfocitos y células plasmáticas distribuido de forma
difusa. Se observan múltiples folículos pilosos dilatados con ruptura
y reacción granulomatosa asociada (furunculosis). No se observan
agentes infecciosos con las tinciones de rutina.
```

### Paso 4: Diagnóstico y Conclusiones

#### Diagnóstico
- **Diagnóstico Primario**: Diagnóstico patológico principal
- **Diagnósticos Secundarios**: Hallazgos adicionales
- **Diagnósticos Diferenciales**: Posibilidades alternativas
- **Nivel de Confianza**: Alta, moderada o baja confianza

**Formato recomendado para diagnóstico:**
```
Piel, biopsia, Canino:
- Dermatitis y foliculitis piogranulomatosa severa difusa con
  furunculosis (patrón compatible con demodicosis)
- Hiperqueratosis ortoqueratósica moderada
```

_[Espacio para captura de pantalla: Sección de diagnóstico]_

#### Conclusiones y Comentarios
- **Resumen**: Breve resumen de hallazgos
- **Correlación Clínica**: Relación con signos clínicos
- **Recomendaciones**: Seguimiento o tratamiento sugerido
- **Pronóstico**: Resultado esperado
- **Estudios Adicionales**: Si se recomiendan

**Ejemplo de comentarios:**
```
Los hallazgos histopatológicos son consistentes con dermatitis y
foliculitis piogranulomatosa severa con furunculosis. Este patrón es
típicamente observado en casos de demodicosis complicada con infección
bacteriana secundaria. Se recomienda raspado cutáneo profundo para
confirmar presencia de Demodex spp. y cultivo bacteriano para guiar
terapia antimicrobiana. El pronóstico depende de la respuesta al
tratamiento y control del ácaro si se confirma demodicosis.
```

_[Espacio para captura de pantalla: Sección de conclusiones y comentarios]_

### Paso 5: Control de Calidad

#### Auto-Revisión
Antes de finalizar:
1. **Revisar Todas las Secciones**: Verificar completitud y precisión
2. **Verificar Ortografía**: Usar corrector ortográfico integrado
3. **Verificar Formato**: Asegurar formato apropiado
4. **Validar Datos**: Confirmar que todos los campos requeridos están completados
5. **Coherencia**: Que las observaciones justifiquen el diagnóstico

_[Espacio para captura de pantalla: Lista de verificación de control de calidad antes de la finalización]_

#### Lista de Verificación
- ☐ Información del paciente correcta
- ☐ Descripción macroscópica completa
- ☐ Todos los cassettes documentados
- ☐ Observaciones microscópicas detalladas
- ☐ Diagnóstico claro y específico
- ☐ Comentarios y recomendaciones incluidos
- ☐ Ortografía y gramática correctas
- ☐ Coherencia entre observaciones y diagnóstico

#### Revisión por Pares (Opcional)
- **Solicitar Revisión**: Pedir a un colega que revise el informe
- **Comentarios de Revisión**: Abordar cualquier retroalimentación
- **Hacer Revisiones**: Actualizar informe basado en retroalimentación

## 📄 Finalización del Informe

### Proceso de Revisión Final

1. **Revisión Completa**: Asegurar que todas las secciones están completas
2. **Guardar Borrador**: Guardar como borrador para completar más tarde
3. **Finalizar Informe**: Marcar informe como listo para entrega

_[Espacio para captura de pantalla: Interfaz de finalización de informe]_

### Firma Digital (obligatoria)

1. **Cargar firma antes del primer informe**: Ver [Firma digital para informes](../lab-staff/digital-signature.md)
2. **Al finalizar**: El PDF incluye la imagen de firma del **profesional asignado** al informe
3. **Datos en el PDF**: Nombre formal, matrícula y cargo del responsable seleccionado

Sin firma cargada, el botón **Finalizar** y **Ver PDF** no estarán disponibles.

### Generación de PDF

Al finalizar (con firma y responsable asignados):

1. **Generar PDF**: El sistema crea el informe con ReportLab (firma embebida)
2. **Revisar PDF**: Usar *Ver PDF* en el detalle del informe
3. **Enviar por email**: Paso separado desde *Enviar por email* cuando el informe está *Finalizado*

_[Espacio para captura de pantalla: Vista previa del informe PDF generado]_

## 📊 Gestión de Informes

### Ver Tus Informes

1. **Ir a "Mis Informes"**: Ver todos tus informes
2. **Opciones de Filtro**: Filtrar por estado, fecha o protocolo
3. **Buscar**: Buscar informes específicos

_[Espacio para captura de pantalla: Lista de informes del histopatólogo]_

### Seguimiento del Estado del Informe

Los informes tienen los siguientes estados:
- **Borrador** (DRAFT): Siendo trabajado
- **Finalizado** (FINALIZED): Listo para entrega
- **Enviado** (SENT): Entregado al veterinario

### Editar Informes

- **Informes Borrador**: Pueden ser editados libremente
- **Informes Finalizados**: No pueden ser editados directamente
- **Adendas**: Para agregar información a informes finalizados
- **Control de Versiones**: El sistema rastrea todas las versiones

## 🔍 Aseguramiento de Calidad

### Estándares de Informe

Asegurar que los informes cumplan con estándares de calidad:
- **Completitud**: Todas las secciones requeridas llenas
- **Precisión**: Terminología y ortografía correctas
- **Claridad**: Lenguaje claro y conciso
- **Consistencia**: Formato y estilo consistentes
- **Profesionalismo**: Presentación profesional

### Métricas de Calidad

El sistema rastrea métricas de calidad:
- **Tiempo de Completación del Informe**: Tiempo para completar informes
- **Tasa de Revisión**: Frecuencia de revisiones necesarias
- **Retroalimentación**: Comentarios de veterinarios
- **Casos consultados**: Casos que requirieron consulta

_[Espacio para captura de pantalla: Panel de métricas de calidad para histopatólogos]_

## 📚 Mejores Prácticas

### Consejos para Escribir Informes

1. **Usar Terminología Estándar**: Seguir estándares de patología veterinaria
2. **Ser Específico**: Proporcionar descripciones detalladas
3. **Incluir Medidas**: Cuantificar hallazgos cuando sea posible (leve, moderado, severo)
4. **Correlacionar con Clínica**: Conectar hallazgos con signos clínicos
5. **Proporcionar Pronóstico**: Dar información clara del pronóstico
6. **Justificar Diagnóstico**: Las observaciones deben soportar el diagnóstico
7. **Ser Claro y Conciso**: Evitar jerga innecesaria

### Terminología Recomendada

#### Distribución de Lesiones
- **Focal**: Una sola área
- **Multifocal**: Múltiples áreas separadas
- **Localmente extensiva**: Un área grande continua
- **Difusa**: Afecta todo el tejido

#### Severidad
- **Leve**: Cambios mínimos
- **Moderado**: Cambios evidentes
- **Severo**: Cambios extensivos
- **Muy severo**: Cambios masivos

### Consejos de Eficiencia

1. **Usar Plantillas**: Aprovechar plantillas de observación
2. **Atajos**: Aprender atajos del sistema
3. **Procesamiento por Lotes**: Procesar casos similares juntos
4. **Guardados Regulares**: Guardar trabajo frecuentemente
5. **Dictar observaciones**: Si el sistema lo soporta

## ❓ Preguntas Comunes

### P: ¿Puedo editar un informe finalizado?
R: No, los informes finalizados no pueden ser editados. Para correcciones, debes crear una adenda o nueva versión del informe.

### P: ¿Cómo manejo casos difíciles?
R: Usar el sistema de revisión por pares o consultar con colegas a través del sistema. No dudes en pedir segunda opinión.

### P: ¿Qué pasa si necesito agregar más cassettes después de crear el informe?
R: Puedes agregar cassettes en cualquier momento antes de finalizar el informe. Después de finalizar, necesitarías crear una adenda.

### P: ¿Cuánto tiempo deberían tomar los informes para completarse?
R: Los informes estándar deberían completarse dentro de 2-3 días hábiles de recepción de la muestra. Casos complejos pueden tomar más tiempo.

### P: ¿Puedo incluir imágenes microscópicas en el informe?
R: Sí, puedes adjuntar imágenes microscópicas que serán incluidas en el PDF final.

### P: Me sale error al ver el PDF o la página falla
R: Casi siempre falta la **firma digital** del responsable asignado al informe o el informe no tiene personal asignado. Cargá tu firma en `/accounts/lab-staff/signature/` o pedí al admin que revise el perfil. Ver también [Problemas comunes — PDF](../../troubleshooting/common-issues.md).

## 🆘 Obtener Ayuda

### Soporte Disponible
- **Materiales de Entrenamiento**: Acceder a videos de entrenamiento y guías
- **Soporte Técnico**: Contactar soporte de TI para problemas del sistema
- **Preguntas Clínicas**: Consultar con patólogos senior
- **Aseguramiento de Calidad**: Contactar equipo de QA para preguntas de estándares

### Recursos Adicionales
- **Biblioteca de Casos**: Revisar casos previos similares
- **Literatura**: Acceder a referencias y publicaciones
- **Educación Continua**: Cursos y webinars disponibles

---

*Anterior: [Analizar muestras](analyzing-samples.md)*
*Siguiente: [Control de calidad](quality-control.md)*
