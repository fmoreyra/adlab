# Guía para Procesar Muestras - Personal de Laboratorio

Esta guía explica cómo procesar muestras de histopatología y citología en el laboratorio.

**IMPORTANTE: Esta documentación está completamente en español para servir al personal del laboratorio y veterinarios de habla hispana.**

## 🔬 Procesamiento de Muestras de Histopatología

### Paso 1: Preparación de Cassettes
- Colocar tejido en cassettes apropiados
- Etiquetar cada cassette (A, B, C...)
- Registrar en el sistema

_[Espacio para captura de pantalla: Cassettes preparados]_

### Paso 2: Fijación
- Inmersión en formol 10%
- Tiempo apropiado según tamaño
- Verificar fijación completa

### Paso 3: Deshidratación e Inclusión
- Procesador automático de tejidos
- Baños de alcohol graduados
- Xileno y parafina

### Paso 4: Cortes y Montaje
- Microtomo para secciones de 4-5 μm
- Montaje en portaobjetos
- Identificación correcta

### Paso 5: Tinción
- Hematoxilina-eosina (rutina)
- Coloraciones especiales si se requieren
- Control de calidad de tinción

## 🧫 Procesamiento de Muestras de Citología

### Preparación de Extendidos
- Si no vienen preparados del veterinario
- Extendido en portaobjetos
- Fijación apropiada

### Tinción
- Wright, Diff-Quik, u otras
- Según protocolo del laboratorio

## 📊 Registro en el Sistema

Todo el seguimiento de etapas se hace desde **Estado del procesamiento** del protocolo (menú de procesamiento → abrir el protocolo). No hace falta cambiar de pantalla.

### Histopatología

1. **Crear cassettes**: En el estado del protocolo, use **Crear Cassettes**. Indique cantidad, material incluido y observaciones por cassette.
2. **Avanzar etapas del cassette**: En la misma pantalla, en cada tarjeta de cassette use el botón de avance (**Fijar** → **Incluir** → **Entacar**). El encasetado se registra automáticamente al crear el cassette.
3. **Registrar slides**: Use **Registrar Slides**. Complete la tabla:
   - **Cassette superior** (obligatorio): cassette montado en la parte superior del portaobjetos.
   - **Cassette inferior** (opcional): segundo cassette en el mismo slide, si aplica.
   - **Coloración**: por defecto Hematoxilina-Eosina; puede ajustarse por fila.
   - Use **+ Agregar slide** para más filas y **Registrar Slides** para guardar.
4. **Avanzar etapas del portaobjetos**: En la tabla de portaobjetos, use **Montar** → **Colorear** → **Marcar listo**.

### Citología

- Los portaobjetos se registran **automáticamente al confirmar la recepción** (cantidad recibida + Diff-Quick por defecto).
- En **Estado de procesamiento** avance las etapas del portaobjetos (**Montar** → **Colorear** → **Marcar listo**).

### Revertir una etapa (cassettes y portaobjetos)

Si hubo un error, use **Revertir etapa** en la columna Acciones. Se abrirá un cuadro de diálogo donde debe indicar el **motivo de la corrección** (obligatorio); queda registrado en el historial del protocolo.

Use **Ver historial** en cada fila de cassette o portaobjetos para abrir el detalle de etapas, material y el registro de auditoría de ese elemento.

### Finalizar procesamiento de laboratorio

Cuando **todos** los cassettes (histopatología) y portaobjetos estén en su última etapa, use **Marcar listo para diagnóstico** en la misma pantalla. El protocolo pasa a estado **Listo** y el caso queda disponible para informe u orden de trabajo.

Si faltan pasos, el sistema muestra una lista de pendientes (cassettes o portaobjetos incompletos).

### Órdenes de trabajo

Desde el estado **Listo** puede enlazarse a órdenes de trabajo solo si su usuario tiene **`is_staff` habilitado** («Staff status» en Administración → Usuarios). El rol de personal de laboratorio no alcanza por sí solo; un administrador debe activar ese flag para quien factura o arma OTs.

### General

- El protocolo pasa a estado de procesamiento según el flujo del laboratorio.
- Documente incidencias en observaciones o en el estado del protocolo.

_[Espacio para captura de pantalla: Estado del procesamiento con cassettes y portaobjetos]_

---

*Anterior: [Recibir muestras](receiving-samples.md)*
*Siguiente: [Gestionar inventario](managing-inventory.md)*
