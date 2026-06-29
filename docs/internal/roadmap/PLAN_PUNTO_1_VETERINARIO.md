# Plan de implementación — Punto 1: Interfaz del Veterinario y Carga de Datos

Documento de planificación detallada. Complementa [ROADMAP_PRIORIZADO.md](ROADMAP_PRIORIZADO.md).

**Estado general del bloque:** ⬜ Pendiente  
**Última revisión:** Junio 2026

---

## Resumen ejecutivo

| Ítem | Complejidad | Estimación | Dependencias externas |
|------|-------------|------------|------------------------|
| 1.3 Punción / PAAF | Baja | 0,5–1 h | Confirmar etiqueta deseada |
| 1.2 Notificaciones móvil | Media | 4–8 h | Repro en prod / dispositivo real |
| 1.1 Raza y Edad | Media–Alta | 8–16 h | Listado oficial de razas por especie |

**Orden recomendado:** 1.3 → 1.2 → 1.1  
(quick win + bugs de UX antes del cambio de formularios más grande)

---

## 1.1 Normalización de campos — Raza y Edad

### Situación actual

- Modelo `Protocol`: `breed` y `age` son `CharField` de texto libre (`max_length=100` / `50`).
- Formularios afectados (todos con `TextInput` / `CharField` libre):
  - `CytologyProtocolForm` — creación citología
  - `HistopathologyProtocolForm` — creación histopatología
  - `ProtocolEditForm` — edición de borradores
  - `ProtocolForm` (ModelForm base)
- **Especie** ya está normalizada con `SPECIES_CHOICES` en `protocols/forms.py`.
- No existen `clean_breed()` ni `clean_age()`.
- PDF e informes muestran `protocol.breed` y `protocol.age` tal cual se guardaron.

### Problema

Entradas como `"labrador"`, `"Labrador Retriever"`, `"LAB"`, `"2a"`, `"dos años"` impiden reportes consistentes y búsquedas confiables.

### Enfoque propuesto

**Principio:** normalizar en el formulario; **no migrar el modelo** en esta etapa (compatibilidad con datos existentes y PDFs).

#### Raza

1. Crear `protocols/choices.py` con catálogo `BREEDS_BY_SPECIES`:
   - Claves alineadas con `SPECIES_CHOICES` (Canino, Felino, Bovino, …).
   - Opciones comunes por especie (a validar con la facultad).
   - Opciones transversales: `Mestizo/CRIollo`, `Sin especificar`, `Otra`.
2. UI con **select dependiente de especie** (Alpine.js, ya usado en el proyecto):
   - Al cambiar especie → repoblar select de raza.
   - Si elige `Otra` → mostrar campo texto auxiliar `breed_other` (solo en formulario, no en modelo).
3. `clean_breed()`: guardar valor canónico del select o el texto de `breed_other`.
4. **Edición de borradores existentes:** si el valor guardado no está en la lista, preseleccionar `Otra` y rellenar `breed_other`.

#### Edad

1. Reemplazar texto libre por **dos campos de formulario** (no migración):
   - `age_value`: entero 0–999 (requerido si se informa edad).
   - `age_unit`: select — `días` | `semanas` | `meses` | `años`.
2. `clean_age()` compone y normaliza: `"6 meses"`, `"2 años"` (minúscula en unidad, plural consistente).
3. Persistir en el campo existente `Protocol.age` (string).
4. Al editar: parsear heurísticamente valores legacy (`"2 años"` → value=2, unit=años); si no parsea, mostrar aviso y pedir re-selección.

### Archivos a tocar

| Archivo | Cambio |
|---------|--------|
| `src/protocols/choices.py` | **Nuevo** — razas por especie, unidades de edad |
| `src/protocols/forms.py` | Campos compuestos, `clean_*`, helpers de parseo |
| `src/protocols/templates/protocols/protocol_form.html` | Select raza + edad estructurada + Alpine |
| `src/protocols/templates/protocols/protocol_edit.html` | Idem |
| `src/protocols/tests.py` | Tests de validación y composición |
| `src/protocols/admin.py` | Opcional: mantener texto libre en admin o alinear |

### Fuera de alcance (fase 2)

- Migración de datos históricos (script de normalización masiva).
- Modelo `Breed` en base de datos (solo si el catálogo crece mucho o requiere admin).
- Campo edad numérico en BD para analytics.

### Criterios de aceptación

- [ ] Veterinario no puede enviar raza libre salvo opción `Otra`.
- [ ] Edad siempre guardada como `"N unidad"` con unidad válida.
- [ ] Borradores editables sin perder datos previos.
- [ ] PDF y detalle de protocolo muestran el mismo formato que antes.
- [ ] Tests cubren creación, edición y casos legacy.

### Decisiones pendientes (facultad)

1. **Listado de razas** por especie — ¿tenemos listado oficial FCV o usamos uno estándar veterinario?
2. ¿**Edad es obligatoria** o sigue siendo opcional?
3. ¿Se admite **rango** (ej. `"3–5 años"`) o solo valor puntual?

---

## 1.2 Optimización de notificaciones (móvil)

### Situación actual

- Modelo `InAppNotification` con `link_url` absoluta (`URLField`).
- URLs generadas en `notification_service._build_protocol_url()`:
  ```python
  return f"{settings.SITE_URL}{path}"
  ```
- `SITE_URL` por defecto en producción: `https://adlab.com` (puede no coincidir con el host real).
- **Campana (dropdown):** `assets/js/app.js` — click en notificación navega con `<a href>` y dispara `markAsRead()` async.
- **Bandeja completa** (`inbox.html`): links directos **sin** marcar como leída al hacer click.
- `ProtocolPublicDetailView`: si no hay sesión, redirige a login **sin** parámetro `next`:
  ```python
  return redirect("accounts:login")  # sin ?next=
  ```
- `AuthenticationService.process_login()` **ignora** `request.GET.get("next")` y siempre redirige a `pages:dashboard`.

### Hipótesis de causa (demora / mala redirección en celular)

| # | Hipótesis | Probabilidad | Síntoma |
|---|-----------|--------------|---------|
| A | `SITE_URL` ≠ dominio real → cross-domain → pierde sesión | Alta | Login inesperado, termina en dashboard |
| B | Login exitoso ignora `next` → siempre dashboard | Alta | “No me lleva al protocolo” |
| C | Bandeja no marca leídas; badge desincronizado | Media | Confusión, re-clicks |
| D | Dropdown recarga lista completa en cada apertura | Baja–Media | Demora al abrir campana |
| E | Vista protocolo pesada en móvil | Baja | Lentitud post-navegación |

### Enfoque propuesto

#### Fase A — Diagnóstico (antes de codear)

1. Reproducir en móvil: campana vs bandeja vs notificación recién creada.
2. Inspeccionar en BD un `link_url` de producción: ¿host correcto?
3. Verificar `SITE_URL` en `.env` del servidor vs dominio de acceso.

#### Fase B — Correcciones backend

1. **Guardar rutas relativas** en `link_url` (ej. `/protocols/public/{uuid}/`) o campo `link_path` separado.
   - Alternativa mínima: seguir absolutas pero asegurar `SITE_URL` correcto al migrar dominio (punto 4).
2. **`ProtocolPublicDetailView`:** redirect con `next`:
   ```python
   login_url = reverse("accounts:login")
   return redirect(f"{login_url}?{urlencode({'next': request.get_full_path()})}")
   ```
3. **`AuthenticationService.process_login()`:** respetar `next` seguro post-login (validar URL interna con `url_has_allowed_host_and_scheme`).
4. **Template login:** asegurar que el formulario preserve `next` (hidden field si no existe).

#### Fase C — Correcciones frontend / UX

1. **Bandeja:** vista intermedia `NotificationGoView` (GET `/notificaciones/<id>/ir/`):
   - Marca como leída.
   - Redirige a `link_path` o URL resuelta.
   - Funciona sin JS (mejor en móvil).
2. **Dropdown:** usar misma ruta intermedia en lugar de URL absoluta directa.
3. **`markAsRead`:** usar `navigator.sendBeacon` o `fetch(..., { keepalive: true })` para no bloquear navegación en redes lentas.
4. **API list:** cachear última respuesta 30 s o precargar al login (opcional).

#### Fase D — Render de links

En API y templates, helper `_resolve_notification_href(notification, request)`:
- Si `link_url` es absoluta del mismo host → usar path relativo.
- Si es path relativo → usar tal cual.
- Evita depender de `SITE_URL` en el cliente.

### Archivos a tocar

| Archivo | Cambio |
|---------|--------|
| `src/protocols/services/notification_service.py` | Paths relativos o helper de URL |
| `src/protocols/views.py` | `next` en login redirect |
| `src/accounts/services/auth_service.py` | Honrar `next` post-login |
| `src/protocols/notification_views.py` | `NotificationGoView` |
| `src/protocols/notification_urls.py` / `pages/urls.py` | Ruta `ir/` |
| `src/protocols/templates/protocols/notifications/inbox.html` | Links vía vista intermedia |
| `assets/js/app.js` | Beacon + href intermedio |
| `src/templates/accounts/login.html` | Hidden `next` |
| `src/protocols/test_notifications.py` | Tests redirect y mark-read |

### Criterios de aceptación

- [ ] Click en notificación (campana y bandeja) lleva al protocolo/informe correcto en < 2 s en 4G (vista ya cargada).
- [ ] Tras login con sesión expirada, vuelve al destino original (`next`).
- [ ] Notificación marcada leída al seguir el link.
- [ ] Links funcionan aunque `SITE_URL` y host del browser coincidan por path relativo.
- [ ] Tests automatizados para `next`, mark-read en redirect, y URL resolution.

### Relación con Punto 4 (dominio)

Al migrar a `patologiavetfcvunl.ar`, **obligatorio** actualizar `SITE_URL`. Las rutas relativas reducen el riesgo de regresión.

---

## 1.3 Validación de tipos de punción — Citología (PAAF)

### Situación actual (hallazgo importante)

**La opción PAAF ya existe** en el código:

```python
# protocols/forms.py — CYTOLOGY_TECHNIQUE_CHOICES
("Punción aspiración con aguja fina (PAAF)", _("Punción aspiración con aguja fina (PAAF)")),
```

Usada en:
- `CytologyProtocolForm` (creación)
- `CytologySampleEditForm` (edición)

Etiqueta visible: **"Técnica Utilizada"** (no "método de extracción").

### Posibles causas del reporte de la facultad

1. **Etiqueta larga** — buscaban solo **"Punción"** y no la encontraron visualmente.
2. **Entorno desactualizado** — producción con build anterior.
3. **Confusión de pantalla** — otro formulario (recepción lab, no veterinario).
4. **Datos legacy** — registros viejos con `"PAAF"` abreviado (tests usan ambos formatos).

### Enfoque propuesto

#### Paso 1 — Verificación (30 min)

1. Confirmar en staging/prod el desplegable de citología veterinario.
2. Preguntar a la facultad: ¿faltaba la opción o no la reconocían por el nombre?

#### Paso 2 — Ajuste según respuesta

**Opción A (recomendada):** Renombrar choice a etiqueta corta:
```python
("Punción (PAAF)", _("Punción (PAAF)")),
```
Valor canónico único; migración de datos opcional para unificar strings viejos.

**Opción B:** Agregar segunda entrada `"Punción"` — **no recomendado** (duplica data).

**Opción C:** Solo verificar deploy — sin cambio de código.

#### Paso 3 — Normalización de datos (opcional)

Script o migración de datos:
- `"PAAF"` → `"Punción (PAAF)"`
- Variantes conocidas → valor canónico

### Archivos a tocar

| Archivo | Cambio |
|---------|--------|
| `src/protocols/forms.py` | Ajuste de label/value en `CYTOLOGY_TECHNIQUE_CHOICES` |
| `src/protocols/migrations/` | Data migration opcional |
| `src/protocols/tests.py` | Actualizar strings en tests |

### Criterios de aceptación

- [ ] "Punción" visible claramente en el select de citología (crear y editar).
- [ ] Valor guardado consistente en BD.
- [ ] Tests actualizados.

---

## Plan de trabajo por sprints

### Sprint A — Quick wins (1–2 días)

- [ ] 1.3 Verificar en prod + ajustar etiqueta PAAF
- [ ] 1.2 Fase A diagnóstico (`SITE_URL`, repro móvil)
- [ ] Recopilar listado de razas de la facultad para 1.1

### Sprint B — Notificaciones (2–3 días)

- [ ] 1.2 Fases B–D (next, vista intermedia, beacon, tests)
- [ ] Deploy a staging y prueba en celular

### Sprint C — Raza y Edad (3–5 días)

- [ ] 1.1 Implementar choices + formularios + Alpine
- [ ] Tests + QA manual veterinario
- [ ] Documentar catálogo de razas en código

---

## Checklist de QA manual (Punto 1 completo)

### Veterinario — Crear protocolo citología

- [ ] Especie → filtra razas correctamente
- [ ] Raza "Otra" permite texto
- [ ] Edad compuesta se guarda bien
- [ ] Técnica "Punción (PAAF)" seleccionable

### Veterinario — Crear protocolo histopatología

- [ ] Misma normalización raza/edad

### Veterinario — Editar borrador

- [ ] Datos legacy editables
- [ ] Técnica citología editable

### Notificaciones — Móvil

- [ ] Campana → click → protocolo correcto
- [ ] Bandeja → click → protocolo + marca leída
- [ ] Sesión expirada → login → vuelve al protocolo
- [ ] Badge actualizado tras leer

---

## Registro de avance

| Fecha | Ítem | Notas |
|-------|------|-------|
| Jun 2026 | Planificación | Documento creado; PAAF ya en código |

---

## Referencias de código

- Formularios: `src/protocols/forms.py`
- Modelo Protocol: `src/protocols/models.py` (L90–104)
- Notificaciones JS: `assets/js/app.js`
- Servicio notificaciones: `src/protocols/services/notification_service.py`
- Vista pública protocolo: `src/protocols/views.py` → `ProtocolPublicDetailView`
- Login: `src/accounts/services/auth_service.py`
