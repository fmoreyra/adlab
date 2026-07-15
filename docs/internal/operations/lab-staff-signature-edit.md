# Firma digital de personal de laboratorio — no se podía editar

## Síntoma

Con firma ya cargada, el personal de laboratorio no encontraba cómo actualizarla:

1. En el panel, la tarjeta **Firma Digital** apuntaba a **Mi Perfil** (`accounts:profile`), que solo edita nombre/email.
2. Si entraban a `/accounts/lab-staff/signature/` con firma existente, la vista redirigía al dashboard con *«Su firma digital ya está cargada»* salvo `?force=1` (no visible en la UI).

## Fix

1. Tarjeta del dashboard → `accounts:lab_staff_signature` («Gestionar firma»).
2. Bloque «Firma digital» en el perfil genérico del lab/admin.
3. `LabStaffSignatureView` siempre muestra el formulario para cargar o reemplazar.

## Verificación

```bash
make test-with-sqlite ARGS="accounts.tests_report_access pages.tests.DashboardViewsTest"
```

Manual: login lab con firma → Panel → Firma Digital → ver formulario «Actualizar firma» → subir PNG → éxito.
