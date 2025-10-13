"""
Custom test runner that properly handles database cleanup in Docker environments.
"""

import contextlib
import os
import subprocess

from django.db import connections
from django.test.runner import DiscoverRunner


class DockerTestRunner(DiscoverRunner):
    """
    Custom test runner that ensures proper database cleanup in Docker environments.

    This runner addresses the issue where test databases can't be dropped due to
    lingering connections from other processes or containers.
    """

    def setup_databases(self, **kwargs):
        """Set up test databases with proper connection handling."""
        # Ensure no persistent connections during tests
        for connection in connections.all():
            connection.close()

        return super().setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        """Clean up test databases with proper connection termination."""
        # Close all connections before cleanup
        for connection in connections.all():
            connection.close()

        # Try to terminate any lingering connections to test database
        with contextlib.suppress(Exception):
            self._terminate_test_db_connections()

        # Proceed with normal teardown
        super().teardown_databases(old_config, **kwargs)

    def _terminate_test_db_connections(self):
        """Terminate any lingering connections to the test database."""
        # Get the test database name
        test_db_name = None
        for alias, connection in connections.databases.items():
            if "TEST" in connection and "NAME" in connection["TEST"]:
                test_db_name = connection["TEST"]["NAME"]
                break

        if not test_db_name:
            return

        # Try to terminate connections using psql if available
        try:
            # Get database connection info
            db_config = connections["default"].settings_dict
            host = db_config.get("HOST", "localhost")
            port = db_config.get("PORT", "5432")
            user = db_config.get("USER", "postgres")

            # Build psql command
            psql_cmd = [
                "psql",
                "-h",
                host,
                "-p",
                str(port),
                "-U",
                user,
                "-d",
                "postgres",  # Connect to postgres database
                "-c",
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid();",
            ]

            # Set PGPASSWORD if available
            env = os.environ.copy()
            if "PASSWORD" in db_config:
                env["PGPASSWORD"] = db_config["PASSWORD"]

            # Execute the command
            result = subprocess.run(
                psql_cmd, env=env, capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                print(
                    f"Terminated lingering connections to test database: {test_db_name}"
                )

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ):
            # psql not available or command failed - this is OK, continue
            pass
        except Exception:
            # Any other error - continue with normal cleanup
            pass
