"""
Tests for server statistics service (admin dashboard monitoring).

Tests get_system_stats() and get_docker_stats() with mocked psutil and docker.
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from services.server_stats_service import (
    get_docker_stats,
    get_system_stats,
)


class GetSystemStatsTest(SimpleTestCase):
    """Tests for get_system_stats()."""

    @patch("services.server_stats_service.psutil")
    def test_returns_expected_structure(self, mock_psutil):
        """get_system_stats returns dict with cpu, ram, disk, io keys."""
        mock_psutil.cpu_percent.return_value = 12.3
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8 * 1024**3,
            used=2 * 1024**3,
            available=6 * 1024**3,
            percent=25.0,
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            total=100 * 1024**3,
            used=40 * 1024**3,
            free=60 * 1024**3,
            percent=40.0,
        )
        mock_io = MagicMock(read_bytes=1000, write_bytes=2000)
        mock_psutil.disk_io_counters.return_value = mock_io

        result = get_system_stats()

        self.assertIn("cpu", result)
        self.assertIn("ram", result)
        self.assertIn("disk", result)
        self.assertIn("io", result)
        self.assertEqual(result["cpu"]["percent"], 12.3)
        self.assertEqual(result["ram"]["percent"], 25.0)
        self.assertEqual(result["ram"]["total"], 8 * 1024**3)
        self.assertEqual(result["ram"]["used"], 2 * 1024**3)
        self.assertEqual(result["ram"]["available"], 6 * 1024**3)
        self.assertEqual(result["disk"]["percent"], 40.0)
        self.assertEqual(result["disk"]["total"], 100 * 1024**3)
        self.assertEqual(result["disk"]["used"], 40 * 1024**3)
        self.assertEqual(result["disk"]["free"], 60 * 1024**3)
        self.assertEqual(result["io"]["read_bytes"], 1000)
        self.assertEqual(result["io"]["write_bytes"], 2000)
        self.assertEqual(result["io"]["read_human"], "1000.0 B")
        self.assertEqual(result["io"]["write_human"], "2.0 KB")

    @patch("services.server_stats_service.psutil")
    def test_disk_io_counters_none(self, mock_psutil):
        """When disk_io_counters is None, io uses None and human-readable em dash."""
        mock_psutil.cpu_percent.return_value = 0.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=1024, used=512, available=512, percent=50.0
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            total=1024, used=512, free=512, percent=50.0
        )
        mock_psutil.disk_io_counters.return_value = None

        result = get_system_stats()

        self.assertIsNone(result["io"]["read_bytes"])
        self.assertIsNone(result["io"]["write_bytes"])
        self.assertEqual(result["io"]["read_human"], "—")
        self.assertEqual(result["io"]["write_human"], "—")

    @patch("services.server_stats_service.psutil")
    def test_cpu_percent_called_with_interval(self, mock_psutil):
        """cpu_percent is called with interval=0.5 for sampling."""
        mock_psutil.cpu_percent.return_value = 5.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=1024, used=256, available=768, percent=25.0
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            total=1024, used=256, free=768, percent=25.0
        )
        mock_psutil.disk_io_counters.return_value = MagicMock(
            read_bytes=0, write_bytes=0
        )

        get_system_stats()

        mock_psutil.cpu_percent.assert_called_once_with(interval=0.5)


class GetDockerStatsTest(SimpleTestCase):
    """Tests for get_docker_stats()."""

    def test_docker_client_exception_returns_error(self):
        """When docker.from_env() raises, returns error and empty containers."""
        mock_docker = MagicMock()
        mock_docker.from_env.side_effect = Exception(
            "Cannot connect to socket"
        )
        with patch.dict("sys.modules", {"docker": mock_docker}):
            result = get_docker_stats()
        self.assertEqual(result["containers"], [])
        self.assertEqual(result["error"], "Cannot connect to socket")

    def test_success_returns_containers_list(self):
        """When Docker is available, returns list of containers."""
        mock_container = MagicMock()
        mock_container.name = "web"
        mock_container.status = "running"
        mock_container.image.tags = ["adlab:latest"]
        mock_container.image.short_id = "abc123"
        mock_container.attrs = {"State": {"StartedAt": "2024-01-15T10:00:00Z"}}

        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]
        mock_docker = MagicMock()
        mock_docker.from_env.return_value = mock_client

        with patch.dict("sys.modules", {"docker": mock_docker}):
            result = get_docker_stats()

        self.assertIsNone(result["error"])
        self.assertEqual(len(result["containers"]), 1)
        self.assertEqual(result["containers"][0]["name"], "web")
        self.assertEqual(result["containers"][0]["image"], "adlab:latest")
        self.assertEqual(result["containers"][0]["status"], "running")
        self.assertEqual(
            result["containers"][0]["started_at"], "2024-01-15T10:00:00Z"
        )

    def test_container_without_image_tags_uses_short_id(self):
        """When image has no tags, use image short_id."""
        mock_container = MagicMock()
        mock_container.name = "worker"
        mock_container.status = "running"
        mock_container.image.tags = []
        mock_container.image.short_id = "def456"
        mock_container.attrs = {"State": {}}

        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]
        mock_docker = MagicMock()
        mock_docker.from_env.return_value = mock_client

        with patch.dict("sys.modules", {"docker": mock_docker}):
            result = get_docker_stats()

        self.assertEqual(result["containers"][0]["image"], "def456")
        self.assertEqual(result["containers"][0]["started_at"], "—")
