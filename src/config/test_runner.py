"""
Custom test runner that properly handles database cleanup in Docker environments.
"""

import contextlib

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

            # Try to drop the database using Django's connection
            from django.db import connection

            # Terminate all connections to the test database first
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = %s 
                    AND pid <> pg_backend_pid();
                """,
                    [test_db_name],
                )

            # Wait a moment for connections to close
            import time

            time.sleep(1)

            # Now drop the database
            with connection.cursor() as cursor:
                cursor.execute(f'DROP DATABASE IF EXISTS "{test_db_name}";')
                print(f"Dropped existing test database: {test_db_name}")

        except Exception as e:
            print(f"Error dropping test database: {e}")
            # Continue anyway - Django will handle the database creation

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

        # Try to terminate connections using Django's connection
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = %s 
                    AND pid <> pg_backend_pid()
                    AND state = 'idle';
                """,
                    [test_db_name],
                )

                print(
                    f"Terminated lingering connections to test database: {test_db_name}"
                )

                # Wait a bit for connections to close
                import time

                time.sleep(0.5)

        except Exception as e:
            print(f"Error terminating connections: {e}")
            # Continue anyway - this is not critical
