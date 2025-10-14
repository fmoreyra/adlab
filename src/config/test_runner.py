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
        print("Setting up test databases with custom runner...")

        # Ensure no persistent connections during tests
        for connection in connections.all():
            connection.close()

        # Force close any lingering connections
        self._force_close_connections()

        # Try to drop existing test database if it exists
        self._drop_test_database_if_exists()

        return super().setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        """Clean up test databases with proper connection termination."""
        print("Tearing down test databases with custom runner...")

        # Close all connections before cleanup
        for connection in connections.all():
            connection.close()

        # Force close any lingering connections
        self._force_close_connections()

        # Try to terminate any lingering connections to test database
        with contextlib.suppress(Exception):
            self._terminate_test_db_connections()

        # Proceed with normal teardown
        super().teardown_databases(old_config, **kwargs)

    def _force_close_connections(self):
        """Force close all database connections."""
        try:
            # Close all connections
            for alias in connections:
                connection = connections[alias]
                if connection.connection is not None:
                    connection.close()
                    print(f"Closed connection for {alias}")
        except Exception as e:
            print(f"Error closing connections: {e}")

    def _drop_test_database_if_exists(self):
        """Drop the test database if it exists to avoid connection conflicts."""
        try:
            # Get the test database name
            test_db_name = None
            for alias, connection in connections.databases.items():
                if "TEST" in connection and "NAME" in connection["TEST"]:
                    test_db_name = connection["TEST"]["NAME"]
                    break

            if not test_db_name:
                return

            # Get database connection info
            db_config = connections["default"].settings_dict
            host = db_config.get("HOST", "localhost")
            port = db_config.get("PORT", "5432")
            user = db_config.get("USER", "postgres")

            # Build psql command to drop the test database
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
                f'DROP DATABASE IF EXISTS "{test_db_name}";',
            ]

            # Set PGPASSWORD if available
            env = os.environ.copy()
            if "PASSWORD" in db_config:
                env["PGPASSWORD"] = db_config["PASSWORD"]

            # Execute the command
            result = subprocess.run(
                psql_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print(f"Dropped existing test database: {test_db_name}")
            else:
                print(f"Could not drop test database: {result.stderr}")

        except Exception as e:
            print(f"Error dropping test database: {e}")

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

            # Build psql command to terminate all connections
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
                f"""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = '{test_db_name}' 
                AND pid <> pg_backend_pid()
                AND state = 'idle';
                """,
            ]

            # Set PGPASSWORD if available
            env = os.environ.copy()
            if "PASSWORD" in db_config:
                env["PGPASSWORD"] = db_config["PASSWORD"]

            # Execute the command with retry
            for attempt in range(3):
                result = subprocess.run(
                    psql_cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    print(
                        f"Terminated lingering connections to test database: {test_db_name} (attempt {attempt + 1})"
                    )
                    # Wait a bit for connections to close
                    import time

                    time.sleep(0.5)
                else:
                    print(
                        f"Failed to terminate connections (attempt {attempt + 1}): {result.stderr}"
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
