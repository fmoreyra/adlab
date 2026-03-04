"""
Tests for server statistics service (admin dashboard monitoring).

Tests get_system_stats() and get_docker_stats() with mocked psutil and docker.
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from services.server_stats_service import (
    get_docker_stats,
    get_media_bucket_stats,
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
        """When Docker is available, returns list of containers with RAM/CPU stats."""
        mock_container = MagicMock()
        mock_container.name = "web"
        mock_container.status = "running"
        mock_container.image.tags = ["adlab:latest"]
        mock_container.image.short_id = "abc123"
        mock_container.attrs = {"State": {"StartedAt": "2024-01-15T10:00:00Z"}}
        mock_container.stats.return_value = {
            "memory_stats": {
                "usage": 100 * 1024 * 1024,
                "limit": 512 * 1024 * 1024,
            },
            "cpu_stats": {
                "cpu_usage": {
                    "total_usage": 5000000000,
                    "percpu_usage": [1, 2],
                },
                "system_cpu_usage": 20000000000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 4000000000},
                "system_cpu_usage": 19000000000,
            },
        }

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
        self.assertEqual(
            result["containers"][0]["memory_usage_bytes"], 100 * 1024 * 1024
        )
        self.assertEqual(
            result["containers"][0]["memory_limit_bytes"], 512 * 1024 * 1024
        )
        self.assertIsNotNone(result["containers"][0]["memory_percent"])
        self.assertIsNotNone(result["containers"][0]["cpu_percent"])

    def test_container_without_image_tags_uses_short_id(self):
        """When image has no tags, use image short_id."""
        mock_container = MagicMock()
        mock_container.name = "worker"
        mock_container.status = "running"
        mock_container.image.tags = []
        mock_container.image.short_id = "def456"
        mock_container.attrs = {"State": {}}
        mock_container.stats.return_value = {}

        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]
        mock_docker = MagicMock()
        mock_docker.from_env.return_value = mock_client

        with patch.dict("sys.modules", {"docker": mock_docker}):
            result = get_docker_stats()

        self.assertEqual(result["containers"][0]["image"], "def456")
        self.assertEqual(result["containers"][0]["started_at"], "—")

    def test_container_stats_exception_keeps_containers_with_none_stats(self):
        """When stats(stream=False) raises, container still has stats keys as None."""
        mock_container = MagicMock()
        mock_container.name = "web"
        mock_container.status = "running"
        mock_container.image.tags = ["adlab:latest"]
        mock_container.image.short_id = "abc123"
        mock_container.attrs = {"State": {}}
        mock_container.stats.side_effect = Exception("stats failed")

        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]
        mock_docker = MagicMock()
        mock_docker.from_env.return_value = mock_client

        with patch.dict("sys.modules", {"docker": mock_docker}):
            result = get_docker_stats()

        self.assertIsNone(result["error"])
        self.assertEqual(len(result["containers"]), 1)
        self.assertEqual(result["containers"][0]["name"], "web")
        self.assertIsNone(result["containers"][0]["memory_usage_bytes"])
        self.assertIsNone(result["containers"][0]["memory_limit_bytes"])
        self.assertIsNone(result["containers"][0]["memory_percent"])
        self.assertIsNone(result["containers"][0]["cpu_percent"])


class GetMediaBucketStatsTest(SimpleTestCase):
    """Tests for get_media_bucket_stats()."""

    @patch("django.conf.settings")
    def test_returns_none_when_testing(self, mock_settings):
        """When TESTING is True, returns None."""
        mock_settings.TESTING = True
        mock_settings.USE_S3_STORAGE = True
        self.assertIsNone(get_media_bucket_stats())

    @patch("django.conf.settings")
    def test_returns_none_when_use_s3_storage_false(self, mock_settings):
        """When USE_S3_STORAGE is False, returns None."""
        mock_settings.TESTING = False
        mock_settings.USE_S3_STORAGE = False
        self.assertIsNone(get_media_bucket_stats())

    @patch("django.core.cache.cache")
    @patch("django.conf.settings")
    def test_returns_stats_when_s3_enabled(self, mock_settings, mock_cache):
        """When S3 is enabled and storage is mocked, returns bucket stats."""
        mock_settings.TESTING = False
        mock_settings.USE_S3_STORAGE = True
        mock_cache.get.return_value = None

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Size": 100}, {"Size": 200}]}
        ]
        mock_client = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_bucket = MagicMock()
        mock_bucket.name = "adlab-media"
        mock_storage = MagicMock()
        mock_storage.bucket = mock_bucket
        mock_storage.connection.meta.client = mock_client

        with patch("django.core.files.storage.default_storage", mock_storage):
            result = get_media_bucket_stats()

            assert result is not None
            self.assertEqual(result["bucket"], "adlab-media")
            self.assertEqual(result["object_count"], 2)
            self.assertEqual(result["total_size_bytes"], 300)
            mock_cache.set.assert_called_once()

    @patch("django.core.cache.cache")
    @patch("django.conf.settings")
    def test_returns_none_on_list_error(self, mock_settings, mock_cache):
        """When list_objects_v2 raises, returns None and does not raise."""
        mock_settings.TESTING = False
        mock_settings.USE_S3_STORAGE = True
        mock_cache.get.return_value = None

        mock_paginator = MagicMock()
        mock_paginator.paginate.side_effect = Exception("S3 error")
        mock_client = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_bucket = MagicMock()
        mock_bucket.name = "adlab-media"
        mock_storage = MagicMock()
        mock_storage.bucket = mock_bucket
        mock_storage.connection.meta.client = mock_client

        with patch("django.core.files.storage.default_storage", mock_storage):
            result = get_media_bucket_stats()

        self.assertIsNone(result)
