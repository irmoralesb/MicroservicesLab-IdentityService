"""
OpenTelemetry distributed tracing module for Grafana Tempo integration.

This module provides distributed tracing instrumentation following the same
patterns established for Prometheus metrics and Loki logging.

Components:
-----------
- tempo.py: Tracer setup, configuration, and span enrichment helpers
- decorators.py: Decorator functions for automatic span creation and instrumentation

Pattern:
--------
All tracing operations are wrapped in try-except blocks to prevent failures
from breaking business logic. Feature flag allows enabling/disabling tracing
without code changes.

Usage:
------
See infrastructure/observability/README.md for setup and configuration examples.
"""
