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
        result.append(
            {
                "name": c.name,
                "image": c.image.tags[0]
                if c.image.tags
                else (c.image.short_id or "—"),
                "status": c.status,
                "started_at": c.attrs.get("State", {}).get("StartedAt") or "—",
            }
        )
    return {"containers": result, "error": None}
