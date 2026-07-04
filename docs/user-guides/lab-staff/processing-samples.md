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

El flujo combina dos pantallas: **registro de banco** (vista dedicada) y **resumen en el protocolo**.

### Histopatología

1. **Registrar cassettes y portaobjetos:** desde la cola de procesamiento o el detalle del protocolo, abra **Registrar muestra** (`/protocols/processing/register/<id>/`):
   - **Cassettes:** cantidad, material incluido (descripción libre) y observaciones opcionales.
   - **Portaobjetos:** multi-select de cassettes por fila, coloración opcional y observaciones.
   - **Guardar registro** confirma todo en un solo paso y permanece en la misma pantalla para agregar más.
2. **Cerrar procesamiento:** en el **detalle del protocolo** (sección «Procesamiento de laboratorio»), use **Marcar listo para diagnóstico** cuando el trabajo de banco esté terminado (planilla de papel).

Si ya hay cassettes, el formulario permite agregar solo portaobjetos nuevos.

### Citología

- Los portaobjetos se registran **automáticamente al confirmar la recepción** (cantidad recibida + Diff-Quick por defecto).
- Cierre el caso con **Marcar listo para diagnóstico** cuando el trabajo de banco esté terminado.

### Veterinarios externos

- En su panel solo ven **En laboratorio** mientras el caso está en banco o listo para diagnóstico interno.
- El avance visible hacia el informe final ocurre cuando el informe está disponible.

### Historial por ítem

No se muestra en la interfaz principal: el seguimiento fino queda en la planilla de papel. El sistema conserva registros internos solo para auditoría al cerrar el procesamiento.

### Órdenes de trabajo

Desde el estado **Listo** puede enlazarse a órdenes de trabajo solo si su usuario tiene **`is_staff` habilitado** («Staff status» en Administración → Usuarios). El rol de personal de laboratorio no alcanza por sí solo; un administrador debe activar ese flag para quien factura o arma OTs.

### General

- El protocolo pasa a estado de procesamiento según el flujo del laboratorio.
- Documente incidencias en observaciones o en el estado del protocolo.

_[Espacio para captura de pantalla: Detalle del protocolo con sección de procesamiento]_

---

*Anterior: [Recibir muestras](receiving-samples.md)*
*Siguiente: [Gestionar inventario](managing-inventory.md)*
