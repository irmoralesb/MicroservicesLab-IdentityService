# Intended structure for this subpackage
# observability/
# ├── __init__.py
# ├── metrics/
# │   ├── __init__.py
# │   ├── prometheus.py      # Prometheus metrics setup
# │   └── collectors.py      # Custom metric collectors
# ├── logging/
# │   ├── __init__.py
# │   ├── config.py          # Logging configuration
# │   └── formatters.py      # Custom log formatters
# └── events/
#     ├── __init__.py
#     └── handlers.py        # Event handling logic