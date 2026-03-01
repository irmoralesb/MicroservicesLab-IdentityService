# Observability - Azure Monitor (Application Insights)

This directory contains the observability implementation for the Identity Service using **Azure Monitor** / **Application Insights** for logs, distributed tracing, and metrics.

## Overview

```
observability/
├── metrics/
│   ├── azure_metrics.py         # OpenTelemetry metrics and record_* helpers
│   ├── decorators.py            # Metric collection decorators
│   └── grafana-prometheus-dashboard.json   # (legacy; optional archive)
├── logging/
│   ├── azure_handler.py         # Azure Monitor logging handler and structured helpers
│   ├── decorators.py            # Logging decorators
│   └── grafana-loki-dashboard.json         # (legacy; optional archive)
├── tracing/
│   ├── azure_tracing.py         # Tracer setup and span enrichment
│   ├── decorators.py            # Tracing decorators
│   └── grafana-tempo-dashboard.json       # (legacy; optional archive)
└── README.md
```

## Configuration

Set the Application Insights connection string and optional toggles in your environment (e.g. `.env` or Azure App Service configuration):

```bash
# Required for Azure Monitor observability
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...

# Optional: enable/disable signals (default: true when connection string is set)
AZURE_LOGGING_ENABLED=true
AZURE_TRACING_ENABLED=true
AZURE_METRICS_ENABLED=true

# Logging
MIN_LOG_LEVEL_FOR_AZURE=INFO
AZURE_LOG_BATCH_DELAY_MILLIS=60000

# Tracing
TRACE_SAMPLE_RATE=1.0
ENABLE_TRACE_CONSOLE_EXPORT=false

# Metrics
METRICS_COLLECTION_INTERVAL=60
```

- **APPLICATIONINSIGHTS_CONNECTION_STRING**: Get this from the Azure Portal → your Application Insights resource → Overview → Connection string. When set, the service will send logs, traces, and (if enabled) custom metrics to Azure Monitor.
- **AZURE_LOGGING_ENABLED / AZURE_TRACING_ENABLED / AZURE_METRICS_ENABLED**: Set to `false` to disable a signal while keeping the others.
- **TRACE_SAMPLE_RATE**: Sampling rate for traces (0.0–1.0; 1.0 = 100%).

## Where to View Data

- **Logs**: Azure Portal → Application Insights → Logs. Query with KQL (e.g. `traces`, `customEvents`, or the log table used by the Python exporter).
- **Traces**: Application Insights → Transaction search, or Application map for distributed traces.
- **Metrics**: Application Insights → Metrics, or workbooks for custom metrics (e.g. `authentication_attempts_total`, `token_operations_total`, `database_operations_total`).

## What's Instrumented

- **Logs**: Authentication, user operations, token operations, password operations, security events, database operations, authorization checks. All use structured context (event_type, status, duration_seconds, user_id, etc.).
- **Traces**: Same domains with OpenTelemetry spans; FastAPI and SQLAlchemy are auto-instrumented.
- **Metrics**: Authentication, token, user, password, role, permission, session, database, and security metrics exported via OpenTelemetry to Azure.

## Documentation

- [Enable OpenTelemetry in Application Insights - Python](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=python)
- [Azure Monitor OpenTelemetry Distro for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/monitor-opentelemetry-readme)
- [Connection strings in Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/sdk-connection-string)
