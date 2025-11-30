"""
Performance monitoring utilities for dashboard API views.

Provides tools to measure and monitor query performance, response times,
and database query counts for dashboard metrics.
"""

import time
from contextlib import contextmanager
from typing import Dict, List

from django.core.cache import cache
from django.db import connection


class PerformanceMonitor:
    """Monitor and track performance metrics for dashboard operations."""

    def __init__(self):
        self.start_time = None
        self.initial_query_count = 0
        self.initial_query_time = 0.0
        self.metrics = {}

    def start_monitoring(self):
        """Start monitoring performance metrics."""
        self.start_time = time.time()
        self.initial_query_count = len(connection.queries)
        self.initial_query_time = sum(
            float(query["time"]) for query in connection.queries
        )

    def stop_monitoring(self) -> Dict:
        """Stop monitoring and return performance metrics."""
        if self.start_time is None:
            return {}

        end_time = time.time()
        total_time = end_time - self.start_time

        final_query_count = len(connection.queries)
        final_query_time = sum(
            float(query["time"]) for query in connection.queries
        )

        query_count = final_query_count - self.initial_query_count
        query_time = final_query_time - self.initial_query_time

        self.metrics = {
            "total_time": round(total_time, 3),
            "query_count": query_count,
            "query_time": round(query_time, 3),
            "avg_query_time": round(query_time / max(query_count, 1), 3),
            "queries_per_second": round(
                query_count / max(total_time, 0.001), 1
            ),
        }

        return self.metrics

    def get_slow_queries(self, threshold: float = 0.1) -> List[Dict]:
        """Get queries that took longer than the threshold."""
        if self.start_time is None:
            return []

        slow_queries = []
        for query in connection.queries[self.initial_query_count :]:
            query_time = float(query["time"])
            if query_time > threshold:
                slow_queries.append(
                    {
                        "sql": query["sql"][:200] + "..."
                        if len(query["sql"]) > 200
                        else query["sql"],
                        "time": query_time,
                    }
                )

        return slow_queries


@contextmanager
def monitor_performance(operation_name: str = "operation"):
    """
    Context manager to monitor performance of dashboard operations.

    Usage:
        with monitor_performance("wip_calculation") as monitor:
            result = calculate_wip_metrics()

        print(f"Operation took {monitor.metrics['total_time']}s")
    """
    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    try:
        yield monitor
    finally:
        metrics = monitor.stop_monitoring()

        # Log performance metrics (in production, use proper logging)
        print(f"Performance: {operation_name}")
        print(f"  Total time: {metrics.get('total_time', 0)}s")
        print(f"  Query count: {metrics.get('query_count', 0)}")
        print(f"  Query time: {metrics.get('query_time', 0)}s")
        print(f"  Avg query time: {metrics.get('avg_query_time', 0)}s")

        # Check for slow queries
        slow_queries = monitor.get_slow_queries()
        if slow_queries:
            print(f"  Slow queries ({len(slow_queries)}):")
            for query in slow_queries[:3]:  # Show top 3 slowest
                print(f"    {query['time']}s: {query['sql']}")


def get_cache_stats() -> Dict:
    """Get cache statistics for dashboard metrics."""
    cache_keys = [
        "dashboard_wip_metrics",
        "dashboard_volume_metrics_mes_ambos",
        "dashboard_productivity_metrics_mes",
        "dashboard_aging_metrics",
        "dashboard_alerts_metrics",
    ]

    stats = {}
    for key in cache_keys:
        stats[key] = cache.get(key) is not None

    return stats


def clear_dashboard_cache():
    """Clear all dashboard-related cache entries."""
    cache_keys = [
        "dashboard_wip_metrics",
        "dashboard_aging_metrics",
        "dashboard_alerts_metrics",
    ]

    # Clear volume cache (multiple period/type combinations)
    for periodo in ["semana", "mes", "año"]:
        for tipo in ["ambos", "histopathology", "cytology"]:
            cache_keys.append(f"dashboard_volume_metrics_{periodo}_{tipo}")

    # Clear productivity cache (multiple periods)
    for periodo in ["semana", "mes", "año"]:
        cache_keys.append(f"dashboard_productivity_metrics_{periodo}")

    for key in cache_keys:
        cache.delete(key)

    return len(cache_keys)


class PerformanceThresholds:
    """Performance thresholds for dashboard operations."""

    # Response time thresholds (seconds)
    WIP_RESPONSE_TIME = 0.5
    VOLUME_RESPONSE_TIME = 0.3
    PRODUCTIVITY_RESPONSE_TIME = 1.0  # More complex query
    AGING_RESPONSE_TIME = 0.8
    ALERTS_RESPONSE_TIME = 0.2

    # Query count thresholds
    WIP_MAX_QUERIES = 5
    VOLUME_MAX_QUERIES = 3
    PRODUCTIVITY_MAX_QUERIES = 2  # Should be 1 after optimization
    AGING_MAX_QUERIES = 2
    ALERTS_MAX_QUERIES = 3

    # Query time thresholds (seconds)
    MAX_QUERY_TIME = 0.1
    MAX_TOTAL_QUERY_TIME = 0.5


def check_performance_thresholds(operation: str, metrics: Dict) -> Dict:
    """
    Check if performance metrics meet the defined thresholds.

    Returns a dictionary with threshold check results.
    """
    thresholds = PerformanceThresholds()

    checks = {
        "passed": True,
        "warnings": [],
        "errors": [],
    }

    # Check response time
    total_time = metrics.get("total_time", 0)
    max_time = getattr(thresholds, f"{operation.upper()}_RESPONSE_TIME", 1.0)

    if total_time > max_time:
        checks["passed"] = False
        checks["errors"].append(
            f"Response time {total_time}s exceeds threshold {max_time}s"
        )
    elif total_time > max_time * 0.8:
        checks["warnings"].append(
            f"Response time {total_time}s is close to threshold {max_time}s"
        )

    # Check query count
    query_count = metrics.get("query_count", 0)
    max_queries = getattr(thresholds, f"{operation.upper()}_MAX_QUERIES", 5)

    if query_count > max_queries:
        checks["passed"] = False
        checks["errors"].append(
            f"Query count {query_count} exceeds threshold {max_queries}"
        )
    elif query_count > max_queries * 0.8:
        checks["warnings"].append(
            f"Query count {query_count} is close to threshold {max_queries}"
        )

    # Check total query time
    query_time = metrics.get("query_time", 0)
    if query_time > thresholds.MAX_TOTAL_QUERY_TIME:
        checks["passed"] = False
        checks["errors"].append(
            f"Total query time {query_time}s exceeds threshold {thresholds.MAX_TOTAL_QUERY_TIME}s"
        )

    return checks
