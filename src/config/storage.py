"""
Custom static files storage backends.

Provides a WhiteNoise-based storage that gracefully handles missing manifest
entries instead of crashing the entire request with a ValueError. This is
critical during deployments where the manifest may be temporarily stale (e.g.
the volume-mounted staticfiles.json hasn't been regenerated yet, or the web
process hasn't restarted to pick up the new manifest).
"""

from whitenoise.storage import CompressedManifestStaticFilesStorage


class ForgivingManifestStaticFilesStorage(
    CompressedManifestStaticFilesStorage
):
    """
    WhiteNoise storage that falls back to unhashed URLs for missing entries.

    Django's default ``manifest_strict = True`` raises ``ValueError`` when a
    file referenced via ``{% static %}`` isn't found in ``staticfiles.json``.
    Setting it to ``False`` makes the template tag return the original
    (unhashed) path instead, so the page still renders — WhiteNoise will
    serve the file if it exists on disk.
    """

    manifest_strict = False
