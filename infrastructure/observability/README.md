# Observability — Azure Monitor (Application Insights + Log Analytics)

This directory contains the complete observability implementation for the
Identity Service using **Azure Monitor** as the backend for metrics, logs,
and distributed traces.

## Overview

```
observability/
├── metrics/
│   ├── azure_metrics.py     # OpenTelemetry metric definitions and helpers
│   └── decorators.py        # Metric collection decorators
├── logging/
│   ├── azure_log_handler.py # Structured logging helpers
│   └── decorators.py        # Logging decorators
├── tracing/
│   ├── azure_monitor.py     # Tracer accessors and span enrichment
│   └── decorators.py        # Tracing decorators
└── README.md                # This file
```

## Architecture

| Pillar     | Azure Service           | How it works                                                           |
|------------|-------------------------|------------------------------------------------------------------------|
| **Traces** | Application Insights    | `configure_azure_monitor()` sets up an OpenTelemetry TracerProvider     |
| **Metrics**| Application Insights    | OpenTelemetry Metrics API → Azure Monitor exporter (custom metrics)     |
| **Logs**   | Log Analytics Workspace | Python `logging` records captured by the OTel logging bridge            |
| **Viz**    | Azure Monitor           | Dashboards, Application Map, Transaction Search, Live Metrics           |

A single call to `configure_azure_monitor()` in `main.py` wires all three
pillars — no manual exporter or collector setup is needed.

## Azure Portal Setup

### Prerequisites

- Azure subscription with Contributor (or higher) access.
- Azure CLI installed locally (`az --version`).

### 1. Create a Resource Group

```bash
az group create --name rg-microserviceslab --location eastus
```

### 2. Create a Log Analytics Workspace

```bash
az monitor log-analytics workspace create \
  --resource-group rg-microserviceslab \
  --workspace-name law-microserviceslab \
  --location eastus
```

### 3. Create Application Insights (workspace-based)

```bash
LAW_ID=$(az monitor log-analytics workspace show \
  --resource-group rg-microserviceslab \
  --workspace-name law-microserviceslab \
  --query id -o tsv)

az monitor app-insights component create \
  --app ai-identity-service \
  --location eastus \
  --resource-group rg-microserviceslab \
  --workspace "$LAW_ID" \
  --application-type web
```

### 4. Get the Connection String

```bash
az monitor app-insights component show \
  --app ai-identity-service \
  --resource-group rg-microserviceslab \
  --query connectionString -o tsv
```

Copy the output and set it as the `APPLICATIONINSIGHTS_CONNECTION_STRING`
environment variable (see below).

## Environment Variables

| Variable                                | Required | Default | Description                                         |
|-----------------------------------------|----------|---------|-----------------------------------------------------|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | **Yes**  | `""`    | Connection string from Application Insights resource |
| `AZURE_MONITOR_ENABLED`                | No       | `true`  | Master toggle for all observability                  |
| `AZURE_MONITOR_SAMPLE_RATE`            | No       | `1.0`   | Trace sampling rate (0.0 – 1.0)                     |
| `AZURE_MONITOR_LOG_LEVEL`             | No       | `INFO`  | Minimum log level exported to Azure                  |

### Example `.env`

```env
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxxx;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=xxxx
AZURE_MONITOR_ENABLED=true
AZURE_MONITOR_SAMPLE_RATE=1.0
AZURE_MONITOR_LOG_LEVEL=INFO
```

## What's Instrumented

### Automatic (via `azure-monitor-opentelemetry` distro)

- **FastAPI HTTP requests** — request/response timing, status codes, routes
- **SQLAlchemy queries** — database spans with query details
- **Python logging** — all log records are exported as Application Insights traces

### Custom (via decorators)

| Decorator                  | Applied to                | Pillar  |
|---------------------------|---------------------------|---------|
| `@track_authentication`   | `AuthenticateService`    | Metrics |
| `@log_authentication`     | `AuthenticateService`    | Logging |
| `@trace_authentication`   | `AuthenticateService`    | Tracing |
| `@track_user_operation`   | `UserService`            | Metrics |
| `@log_user_operation_decorator` | `UserService`       | Logging |
| `@trace_user_operation`   | `UserService`            | Tracing |
| `@track_token_operation`  | `TokenService`           | Metrics |
| `@log_token_operation_decorator` | `TokenService`     | Logging |
| `@trace_token_operation`  | `TokenService`           | Tracing |
| `@track_password_operation` | `UserService`           | Metrics |
| `@log_password_operation_decorator` | `UserService`   | Logging |
| `@trace_password_operation` | `UserService`           | Tracing |
| `@track_database_operation` | All repositories         | Metrics |
| `@track_security_event`   | `AuthenticateService`    | Metrics |
| `@log_security_event_decorator` | `AuthenticateService` | Logging |
| `@trace_security_event`   | `AuthenticateService`    | Tracing |

## Querying Data in Azure Portal

### Application Insights → Transaction Search

Find individual requests with full distributed traces including custom span
attributes (e.g., `auth.type`, `user.id`, `token.type`).

### Application Insights → Logs (KQL)

```kql
-- Recent authentication events
traces
| where message contains "Authentication"
| project timestamp, message, customDimensions
| order by timestamp desc
| take 50

-- Custom metrics
customMetrics
| where name == "authentication_attempts_total"
| summarize sum(valueSum) by bin(timestamp, 5m), tostring(customDimensions.status)
| render timechart

-- Failed logins
traces
| where customDimensions.event_type == "authentication"
  and customDimensions.status == "failure"
| project timestamp, customDimensions.email, customDimensions.failure_reason
| order by timestamp desc

-- Security events
traces
| where customDimensions.event_type == "security"
| project timestamp, message, customDimensions.severity
| order by timestamp desc
```

### Application Insights → Application Map

Visual overview of the Identity Service and its SQL Server dependency with
average latency and failure rates.

### Application Insights → Live Metrics

Real-time request rate, failure rate, and server health while testing.

## Graceful Degradation

If `AZURE_MONITOR_ENABLED=false` or the connection string is empty, the
application starts normally without any observability exports. The
decorators still execute (they use the OpenTelemetry no-op providers) so
there is zero runtime impact.
