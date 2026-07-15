# Completar perfil de veterinario — matrícula vacía y DNI

## Síntoma (producción)

Al completar el perfil profesional (`/accounts/veterinarian/complete-profile/`):

1. El campo **DNI** se valida como obligatorio pero no se marcaba visualmente con `*`.
2. Guardar fallaba con **500** si la matrícula quedaba vacía y ya existía otro veterinario sin matrícula:

```text
IntegrityError: duplicate key value violates unique constraint
"accounts_veterinarian_license_number_key"
DETAIL: Key (license_number)=() already exists.
```

## Causa

`Veterinarian.license_number` es `unique=True` y `null=True` (opcional).

Los formularios guardaban matrícula vacía como `""` (string vacío). En PostgreSQL:

- varios `NULL` son válidos bajo un unique constraint
- un solo `""` es permitido; el segundo `""` viola el unique

El primer veterinario sin matrícula ocupaba la “vacante” `""`; los siguientes reventaban en `VeterinarianProfileCompleteForm.save()`.

## Fix

1. `clean_license_number` / `save` / `Veterinarian.save()` normalizan vacío → `None`.
2. Migración de datos `accounts.0010_normalize_empty_license_number` convierte `""` existentes a `NULL`.
3. DNI: `required=True` en el form + asterisco en templates de completar/editar perfil.

## Verificación

```bash
make test-with-sqlite ARGS="accounts.tests.CompleteProfileViewTest"
make manage ARGS="migrate accounts"
```

Casos clave:

- `test_multiple_profiles_without_license_number` — dos perfiles sin matrícula OK
- `test_complete_profile_dni_required` — DNI obligatorio sin 500

## Deploy

Tras el deploy: `migrate` (aplica `0010`). Sin migración, los registros viejos con `license_number=''` siguen bloqueando nuevos perfiles sin matrícula.
