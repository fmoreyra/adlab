from django.conf import settings
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
