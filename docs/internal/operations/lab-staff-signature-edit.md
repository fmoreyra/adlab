# Firma digital de personal de laboratorio — no se podía editar

## Síntoma

Con firma ya cargada, el personal de laboratorio no encontraba cómo actualizarla:

1. En el panel, la tarjeta **Firma Digital** apuntaba a **Mi Perfil** (`accounts:profile`), que solo edita nombre/email.
2. Si entraban a `/accounts/lab-staff/signature/` con firma existente, la vista redirigía al dashboard con *«Su firma digital ya está cargada»* salvo `?force=1` (no visible en la UI).

## Fix (actualización)

1. Tarjeta del dashboard → `accounts:lab_staff_signature` («Gestionar firma»).
2. Bloque «Firma digital» en el perfil genérico del lab/admin.
3. `LabStaffSignatureView` siempre muestra el formulario (cargar/reemplazar).
4. Preview de la firma actual vía proxy `accounts:lab_staff_signature_file`.
5. Campo libre `signature_affiliation_text` (texto bajo la firma en el PDF).

## Verificación

```bash
make test-with-sqlite ARGS="accounts.tests_report_access protocols.tests_report_pdf_template"
```

Manual: login lab con firma → Panel → Firma Digital → ver preview + editar texto → guardar.
