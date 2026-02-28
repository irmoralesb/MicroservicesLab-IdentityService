# Observability subpackage — Azure Monitor (Application Insights + Log Analytics)
# observability/
# ├── __init__.py
# ├── metrics/
# │   ├── __init__.py
# │   ├── azure_metrics.py   # OpenTelemetry metrics (exported via Azure Monitor)
# │   └── decorators.py      # Metric collection decorators
# ├── logging/
# │   ├── __init__.py
# │   ├── azure_log_handler.py  # Structured logging helpers (exported via Azure Monitor)
# │   └── decorators.py         # Logging decorators
# └── tracing/
#     ├── __init__.py
#     ├── azure_monitor.py   # Tracer accessors and span enrichment helpers
#     └── decorators.py      # Tracing decorators