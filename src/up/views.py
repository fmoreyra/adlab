from django.conf import settings
from django.core.mail import send_mail
from django.db import connection
from django.http import HttpResponse
from redis import Redis

redis = Redis.from_url(settings.REDIS_URL)


def index(request):
    return HttpResponse("")


def databases(request):
    redis.ping()

    # Test database connection and ensure it's closed after use
    try:
        connection.ensure_connection()
        # Test the connection with a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    finally:
        # Ensure connection is closed after the health check
        connection.close()

    return HttpResponse("")


def send_test_email(request):
    """
    Dev-only: send a hardcoded test email to verify email configuration.

    Only available when DEBUG is True. Use ?to=your@email.com to set recipient
    (defaults to test@example.com).
    """
    if not settings.DEBUG or settings.TESTING:
        return HttpResponse("Not found", status=404)

    to_email = request.GET.get("to", "test@example.com").strip()
    if not to_email:
        to_email = "test@example.com"

    try:
        send_mail(
            subject="[AdLab] Email de prueba",
            message=(
                "Este es un correo de prueba del sistema AdLab.\n\n"
                "Si recibiste este mensaje, la configuración de envío de emails "
                "está funcionando correctamente.\n\n"
                "— AdLab"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return HttpResponse(
            f"Email enviado correctamente a {to_email}. Revisa tu bandeja (y spam).",
            content_type="text/plain; charset=utf-8",
        )
    except Exception as e:
        return HttpResponse(
            f"Error al enviar el email: {e}",
            status=500,
            content_type="text/plain; charset=utf-8",
        )
