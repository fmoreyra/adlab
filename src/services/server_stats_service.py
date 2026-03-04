"""
Server statistics service for admin dashboard monitoring.

Collects CPU, RAM, disk, I/O and Docker container stats via psutil and Docker SDK.
Optional: if psutil or docker are not installed, functions return error payloads.
"""

import logging
from typing import Any, Dict, List

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_GARAGE_BUCKET_CACHE_KEY = "server_stats_garage_bucket"
_GARAGE_BUCKET_CACHE_TIMEOUT = 300  # 5 minutes

_SYSTEM_ERROR = {
    "cpu": {"percent": None},
    "ram": {"total": None, "used": None, "available": None, "percent": None},
    "disk": {"total": None, "used": None, "free": None, "percent": None},
    "io": {
        "read_bytes": None,
        "write_bytes": None,
        "read_human": "—",
        "write_human": "—",
    },
    "error": "Módulo psutil no instalado.",
}


def _format_bytes(value: int | None) -> str:
    """Format byte count as human-readable string."""
    if value is None:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def get_system_stats() -> Dict[str, Any]:
    """
    Collect system metrics using psutil.

    Returns:
        dict: CPU percent, RAM (total/used/available/percent), disk usage
        for '/', and disk I/O (read_bytes, write_bytes, human-readable).
        If psutil is not installed, returns error payload with null values.
    """
    if psutil is None:
        return _SYSTEM_ERROR.copy()

    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    io_counters = psutil.disk_io_counters()

    return {
        "cpu": {
            "percent": round(cpu_percent, 1),
        },
        "ram": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": round(mem.percent, 1),
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": round(disk.percent, 1),
        },
        "io": {
            "read_bytes": io_counters.read_bytes if io_counters else None,
            "write_bytes": io_counters.write_bytes if io_counters else None,
            "read_human": _format_bytes(
                io_counters.read_bytes if io_counters else None
            ),
            "write_human": _format_bytes(
                io_counters.write_bytes if io_counters else None
            ),
        },
    }


def get_media_bucket_stats() -> Dict[str, Any] | None:
    """
    Return object count and total size for the media bucket (Garage/S3), or None.

    Uses Django default_storage when USE_S3_STORAGE is True and not TESTING.
    Result is cached for 5 minutes to avoid listing the bucket on every poll.
    On exception (e.g. connection error), logs and returns None.
    """
    from django.conf import settings
    from django.core.cache import cache

    if getattr(settings, "TESTING", False):
        return None
    if not getattr(settings, "USE_S3_STORAGE", False):
        return None

    cached = cache.get(_GARAGE_BUCKET_CACHE_KEY)
    if cached is not None:
        return cached

    try:
        from django.core.files.storage import default_storage

        if (
            not hasattr(default_storage, "bucket")
            or default_storage.bucket is None
        ):
            return None
        client = default_storage.connection.meta.client
        bucket_name = default_storage.bucket.name
    except Exception as e:
        logger.warning("Garage bucket stats unavailable (storage): %s", e)
        return None

    try:
        paginator = client.get_paginator("list_objects_v2")
        count = 0
        total_size = 0
        for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get("Contents") or []:
                count += 1
                total_size += obj.get("Size", 0)
        result = {
            "bucket": bucket_name,
            "object_count": count,
            "total_size_bytes": total_size,
        }
        cache.set(
            _GARAGE_BUCKET_CACHE_KEY, result, _GARAGE_BUCKET_CACHE_TIMEOUT
        )
        return result
    except Exception as e:
        logger.warning("Garage bucket stats unavailable (list): %s", e)
        return None


def _parse_container_stats(c) -> Dict[str, Any]:
    """Return memory and CPU stats for a container, or None values on failure."""
    out = {
        "memory_usage_bytes": None,
        "memory_limit_bytes": None,
        "memory_percent": None,
        "cpu_percent": None,
    }
    try:
        stats = c.stats(stream=False)
    except Exception as e:
        logger.debug("Container %s stats failed: %s", c.name, e)
        return out

    # Memory
    mem = stats.get("memory_stats") or {}
    usage = mem.get("usage")
    limit = mem.get("limit")
    if usage is not None:
        out["memory_usage_bytes"] = usage
    if limit is not None:
        out["memory_limit_bytes"] = limit
        if usage is not None and limit and limit > 0:
            out["memory_percent"] = round((usage / limit) * 100, 1)

    # CPU (delta from precpu_stats in same snapshot)
    cpu_stats = stats.get("cpu_stats") or {}
    precpu = stats.get("precpu_stats") or {}
    cpu_usage = cpu_stats.get("cpu_usage") or {}
    precpu_usage = precpu.get("cpu_usage") or {}
    total_usage = (cpu_usage.get("total_usage") or 0) - (
        precpu_usage.get("total_usage") or 0
    )
    system_usage = (cpu_stats.get("system_cpu_usage") or 0) - (
        precpu.get("system_cpu_usage") or 0
    )
    num_cpus = len(cpu_usage.get("percpu_usage") or []) or 1
    if system_usage and system_usage > 0 and total_usage >= 0:
        out["cpu_percent"] = round(
            (total_usage / system_usage) * num_cpus * 100, 1
        )
    return out


def get_docker_stats() -> Dict[str, Any]:
    """
    List running Docker containers via Docker SDK.

    Requires Docker socket to be mounted (e.g. /var/run/docker.sock).
    Returns error message if Docker is unavailable.

    Returns:
        dict: Either {"containers": [...], "error": null} or
        {"containers": [], "error": "message"}.
    """
    try:
        import docker
    except ImportError:
        return {"containers": [], "error": "Módulo docker no instalado."}

    try:
        client = docker.from_env()
        containers = client.containers.list()
    except Exception as e:
        logger.warning("Docker stats unavailable: %s", e)
        return {"containers": [], "error": str(e)}

    result: List[Dict[str, Any]] = []
    for c in containers:
        entry = {
            "name": c.name,
            "image": c.image.tags[0]
            if c.image.tags
            else (c.image.short_id or "—"),
            "status": c.status,
            "started_at": c.attrs.get("State", {}).get("StartedAt") or "—",
        }
        entry.update(_parse_container_stats(c))
        result.append(entry)
    return {"containers": result, "error": None}
