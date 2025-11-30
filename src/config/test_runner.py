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

        # Skip aggressive database dropping to avoid deadlocks
        # Django will handle database creation/cleanup properly
        return super().setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        """Clean up test databases with proper connection termination."""
        print("Tearing down test databases with custom runner...")

        # Get test database name before closing connections
        # old_config is a list of dicts: [{'NAME': 'test_db', ...}, ...]
        test_db_name = None
        if old_config:
            for db_config in old_config:
                if isinstance(db_config, dict) and "NAME" in db_config:
                    test_db_name = db_config["NAME"]
                    break

        # Close all Django connections first
        for connection in connections.all():
            with contextlib.suppress(Exception):
                connection.close()

        # Force close any lingering connections
        self._force_close_connections()

        # Terminate all PostgreSQL connections to the test database
        if test_db_name:
            self._terminate_all_db_connections(test_db_name)

        # Proceed with normal teardown - Django will handle it
        try:
            super().teardown_databases(old_config, **kwargs)
        except Exception as e:
            # If teardown fails due to lingering connections, that's OK
            # The database will be cleaned up on next test run
            if "being accessed by other users" in str(e):
                print(
                    f"Warning: Could not drop test database due to lingering connections: {e}"
                )
                print(
                    "This is harmless - the database will be cleaned up on the next test run."
                )
            else:
                raise

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

    def _terminate_all_db_connections(self, db_name):
        """Terminate all connections to a specific database."""
        import time

        try:
            # Connect to postgres database (not the test database) to terminate connections
            # We need to use a different connection since we can't connect to a DB while terminating its connections

            # Create a temporary connection to the postgres database
            from django.db import connection

            original_db_name = connection.settings_dict["NAME"]

            # Temporarily switch to postgres database
            connection.settings_dict["NAME"] = "postgres"
            connection.close()  # Close existing connection

            try:
                with connection.cursor() as cursor:
                    # Terminate all connections to the test database
                    cursor.execute(
                        """
                        SELECT pg_terminate_backend(pid) 
                        FROM pg_stat_activity 
                        WHERE datname = %s 
                        AND pid <> pg_backend_pid();
                    """,
                        [db_name],
                    )

                    terminated = cursor.fetchall()
                    count = sum(1 for row in terminated if row[0])
                    if count > 0:
                        print(
                            f"Terminated {count} connections to test database: {db_name}"
                        )

                    # Wait a bit for connections to close
                    time.sleep(1)
            finally:
                # Restore original database name
                connection.settings_dict["NAME"] = original_db_name
                connection.close()

        except Exception as e:
            # This is not critical - Django will handle cleanup
            print(
                f"Note: Could not terminate all connections to {db_name}: {e}"
            )

    def _terminate_test_db_connections(self):
        """Terminate any lingering connections to the test database."""
        # Get the test database name
        test_db_name = None
        for alias, connection_config in connections.databases.items():
            if (
                "TEST" in connection_config
                and "NAME" in connection_config["TEST"]
            ):
                test_db_name = connection_config["TEST"]["NAME"]
                break

        if not test_db_name:
            return

        self._terminate_all_db_connections(test_db_name)
