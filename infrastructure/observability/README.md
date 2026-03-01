# Observability - Metrics, Logging & Distributed Tracing

This directory contains the complete observability implementation for the Identity Service, including Prometheus metrics, Loki logging, and Tempo distributed tracing with pre-configured Grafana dashboards.

## Overview

```
observability/
├── metrics/                           # Prometheus metrics
│   ├── prometheus.py                  # Metric definitions and helpers
│   ├── decorators.py                  # Metric collection decorators
│   └── grafana-prometheus-dashboard.json   # Grafana dashboard for metrics
├── logging/                           # Loki logging
│   ├── loki_handler.py                # Structured logging handlers
│   ├── decorators.py                  # Logging decorators
│   └── grafana-loki-dashboard.json    # Grafana dashboard for logs
├── tracing/                           # Tempo distributed tracing
│   ├── tempo.py                       # Tracer setup and span enrichment
│   ├── decorators.py                  # Tracing decorators
│   └── grafana-tempo-dashboard.json   # Grafana dashboard for traces
└── README.md                          # This file
```

## Distributed Tracing (Tempo)

### What's Traced

OpenTelemetry-based distributed tracing with automatic instrumentation for:

- **Authentication Operations**: Login flows with span context propagation
- **User Operations**: CRUD operations with parent-child span relationships
- **Token Operations**: Token generation and validation spans
- **Password Operations**: Password changes marked as security-relevant spans
- **Security Events**: Account locks and security-related operations
- **Database Operations**: Automatic SQLAlchemy query tracing
- **HTTP Requests**: Automatic FastAPI request/response tracing
- **Authorization Checks**: Permission and role validation spans

### Architecture

- **Protocol**: OpenTelemetry Protocol (OTLP) over gRPC
- **Exporter**: OTLP gRPC exporter to Tempo endpoint
- **Instrumentation**: 
  - Automatic FastAPI instrumentation via `FastAPIInstrumentor`
  - Automatic SQLAlchemy instrumentation via `SQLAlchemyInstrumentor`
  - Manual span creation via decorators for business logic
- **Sampling**: Configurable sampling rate (default 100% for development)
- **Context Propagation**: W3C Trace Context format for inter-service tracing

### Configuration

Set in `.env`:
```bash
# Tracing Configuration
TRACING_ENABLED=true
TEMPO_ENDPOINT=http://localhost:4317
TRACE_SAMPLE_RATE=1.0
ENABLE_TRACE_CONSOLE_EXPORT=false
SERVICE_NAME=identity-service
```

**Configuration Options:**
- `TRACING_ENABLED`: Enable/disable distributed tracing (default: true)
- `TEMPO_ENDPOINT`: Tempo OTLP gRPC endpoint URL (default: http://localhost:4317)
- `TRACE_SAMPLE_RATE`: Sampling rate 0.0-1.0 where 1.0 = 100% (default: 1.0)
- `ENABLE_TRACE_CONSOLE_EXPORT`: Also export traces to console for debugging (default: false)
- `SERVICE_NAME`: Service identifier in traces (default: identity-service)

### Span Attributes

All spans include standard OpenTelemetry semantic conventions plus domain-specific attributes:

**Authentication Spans:**
```python
auth.type: "login" | "refresh" | "verify"
auth.status: "success" | "failure" | "error"
auth.failure_reason: "invalid_credentials" | "account_locked" | ...
auth.duration_seconds: float
user.id: UUID
user.email: string (masked for privacy)
```

**User Operation Spans:**
```python
user.operation.type: "create" | "update" | "delete" | "get" | "list"
user.operation.status: "success" | "failure"
user.actor.id: UUID  # User performing the operation
user.target.id: UUID  # User being operated on
user.operation.duration_seconds: float
```

**Token Operation Spans:**
```python
token.operation.type: "generate" | "validate" | "refresh" | "revoke"
token.type: "access" | "refresh"
token.operation.status: "success" | "failure"
user.id: UUID
token.operation.duration_seconds: float
```

**Database Operation Spans (OpenTelemetry Semantic Conventions):**
```python
db.system: "mssql"
db.operation: "select" | "insert" | "update" | "delete"
db.sql.table: string
db.operation.status: "success" | "failure"
db.operation.duration_seconds: float
```

**Authorization Spans:**
```python
authz.resource: string  # e.g., "user"
authz.action: string  # e.g., "delete"
authz.granted: boolean
authz.required_roles: comma-separated string
authz.user_roles: comma-separated string
user.id: UUID
authz.duration_seconds: float
```

**Security Event Spans:**
```python
security.event.type: "account_locked" | "account_unlocked" | ...
security.event.severity: "low" | "medium" | "high" | "critical"
user.id: UUID
security.event.*: Additional context-specific attributes
```

### Decorator Usage

Tracing decorators follow the same pattern as metrics and logging decorators and should be stacked together:

```python
from infrastructure.observability.tracing.decorators import (
    trace_authentication,
    trace_user_operation,
    trace_password_operation,
    trace_token_operation,
    trace_authorization,
    trace_security_event,
)

# Stack decorators: metrics → logging → tracing
@track_authentication(auth_type='login')
@log_authentication(auth_type='login')
@trace_authentication(auth_type='login')
async def authenticate_user(email: str, password: str) -> UserModel | None:
    # Business logic automatically wrapped in span
    pass

@track_user_operation(operation_type='create')
@log_user_operation_decorator(operation_type='create')
@trace_user_operation(operation_type='create')
async def create_user(user: UserModel) -> UserModel:
    # Automatic span creation with user operation context
    pass
```

### Manual Span Creation

For fine-grained control, create spans manually:

```python
from infrastructure.observability.tracing.tempo import (
    get_tracer,
    enrich_authentication_span,
)

tracer = get_tracer(__name__)

with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    
    # Perform operation
    result = await some_operation()
    
    # Enrich with domain-specific attributes
    enrich_authentication_span(
        span=span,
        auth_type="login",
        status="success",
        user_id=user.id,
    )
```

### Span Context Propagation

OpenTelemetry automatically propagates trace context across service boundaries using W3C Trace Context headers:

- `traceparent`: Contains trace ID, span ID, and sampling decision
- `tracestate`: Additional vendor-specific trace information

For inter-service calls, use instrumented HTTP clients or manually inject context:

```python
from opentelemetry.propagate import inject

headers = {}
inject(headers)  # Injects traceparent and tracestate headers

response = await http_client.get(
    "http://other-service/api/endpoint",
    headers=headers
)
```

### Grafana Integration

**View Traces in Grafana:**

1. Navigate to **Explore** in Grafana
2. Select **Tempo** as data source
3. Use **Search** to find traces by:
   - Service name: `identity-service`
   - Operation name: `auth.login.authenticate_user`
   - Duration: `>100ms`
   - Status: `error`
   - Tags: `auth.status=failure`

**Trace to Logs/Metrics Correlation:**

Grafana allows correlation between traces, logs, and metrics:

1. **Trace → Logs**: Click trace span → View related logs by timestamp and trace ID
2. **Trace → Metrics**: See RED metrics (Rate, Errors, Duration) for traced operations
3. **Logs → Traces**: Click log entry with trace ID → Jump to related trace

**Sample TraceQL Queries:**

```traceql
# Find all failed authentication attempts
{ name="auth.login.authenticate_user" && auth.status="failure" }

# Find slow operations (>1 second)
{ duration > 1s }

# Find traces with errors
{ status=error }

# Find traces for specific user
{ user.id="<user-uuid>" }

# Find authorization denials
{ authz.granted=false }

# Find security events
{ security.event.severity="high" || security.event.severity="critical" }
```



## Metrics (Prometheus)

### What's Tracked

- **Authentication Metrics**: Login attempts, duration, failures by reason
- **User Operations**: Create, update, activate, deactivate operations
- **Token Operations**: Token generation, validation, revocation
- **Password Operations**: Password changes, validations
- **Security Events**: Account locks, unlocks, suspicious activity
- **Database Operations**: Query durations, operation counts
- **Authorization**: Role checks, permission validations
- **HTTP Metrics**: Request rates, response times, status codes

### Exposed Endpoint

Metrics are exposed at: `http://localhost:8000/metrics` (configurable via `METRICS_ENDPOINT`)

### Configuration

Set in `.env`:
```bash
METRICS_ENABLED=true
METRICS_ENDPOINT=/metrics
ENABLE_HTTP_METRICS=true
ENABLE_BUSINESS_METRICS=true
ENABLE_DATABASE_METRICS=true
METRICS_COLLECTION_INTERVAL=60
```

### Grafana Dashboard

Import the pre-configured dashboard:

1. Open Grafana UI
2. Go to **Dashboards → Import**
3. Upload `metrics/grafana-prometheus-dashboard.json`
4. Select your Prometheus data source
5. Click **Import**

**Dashboard includes:**
- Authentication attempts and duration (p95, p99)
- Failed login attempts by reason (pie chart)
- Active tokens gauge
- User operations rate
- Security events timeline
- Database operation percentiles
- HTTP request rates by endpoint
- Authorization check failures

## Logging (Loki)

### What's Logged

- **Authentication Events**: Login success/failure with masked emails
- **User Operations**: CRUD operations with user IDs
- **Token Operations**: Generation, validation with expiry times
- **Password Operations**: Changes flagged as security events
- **Security Events**: Account locks, suspicious activity with severity levels
- **Database Operations**: Query performance and errors
- **Authorization Checks**: Permission/role validation results

### Structured Context

All logs include:
- `event_type`: Type of event (authentication, user_operation, etc.)
- `status`: success/failure
- `duration_seconds`: Operation timing
- `user_id`: Associated user (when applicable)
- `timestamp`: ISO 8601 UTC timestamp
- `hostname`: Server hostname
- Additional event-specific metadata

### Configuration

Set in `.env`:
```bash
LOKI_ENABLED=true
LOKI_URL=http://localhost:3100
LOKI_LABELS=service=identity-service,environment=production
STRUCTURED_LOGGING_ENABLED=true
LOKI_BATCH_INTERVAL=60
LOKI_TIMEOUT=10.0
MIN_LOG_LEVEL_FOR_LOKI=INFO
```

### Grafana Dashboard

Import the pre-configured dashboard:

1. Open Grafana UI
2. Go to **Dashboards → Import**
3. Upload `logging/grafana-loki-dashboard.json`
4. Select your Loki data source
5. Click **Import**

**Dashboard includes:**
- Log volume by level (stacked time series)
- All logs viewer with filtering
- Authentication events by status
- Failed authentication details
- Security events by type and severity
- High/critical security event viewer
- User operations timeline
- Failed user operations
- Error log viewer
- Slow operations table (>1s)
- Token operations by type
- Password security events

## Quick Start with Docker Compose

### 1. Create `docker-compose.observability.yml`

```yaml
version: "3"

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki-data:/loki

  tempo:
    image: grafana/tempo:latest
    container_name: tempo
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    command: [ "-config.file=/etc/tempo.yaml" ]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
      - loki
      - tempo

volumes:
  prometheus-data:
  loki-data:
  tempo-data:
  grafana-data:
```

### 2. Create `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'identity-service'
    static_configs:
      - targets: ['host.docker.internal:8000']  # Windows/Mac
        # - targets: ['172.17.0.1:8000']         # Linux
    metrics_path: '/metrics'
```

### 3. Create `tempo.yaml`

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal

metrics_generator:
  registry:
    external_labels:
      source: tempo
  storage:
    path: /var/tempo/generator/wal
  traces_storage:
    path: /var/tempo/generator/traces
```

### 4. Start Services

```bash
docker-compose -f docker-compose.observability.yml up -d
```

### 5. Configure Grafana

**Access Grafana**: http://localhost:3000 (admin/admin)

**Add Prometheus Data Source:**
1. Configuration → Data Sources → Add data source
2. Select Prometheus
3. URL: `http://prometheus:9090`
4. Click **Save & Test**

**Add Loki Data Source:**
1. Configuration → Data Sources → Add data source
2. Select Loki
3. URL: `http://loki:3100`
4. Click **Save & Test**

**Add Tempo Data Source:**
1. Configuration → Data Sources → Add data source
2. Select Tempo
3. URL: `http://tempo:3200`
4. Click **Save & Test**

**Enable Trace to Logs Correlation:**
1. Edit Tempo data source
2. Under "Trace to logs", select Loki as target
3. Set tags: `service.name` (maps to Loki label)
4. Click **Save & Test**

**Import Dashboards:**
1. Import `metrics/grafana-prometheus-dashboard.json`
2. Import `logging/grafana-loki-dashboard.json`
3. Import `tracing/grafana-tempo-dashboard.json` (if available)

### 6. Update Application `.env`

```bash
# Prometheus metrics
METRICS_ENABLED=true
METRICS_ENDPOINT=/metrics

# Loki logging
LOKI_ENABLED=true
LOKI_URL=http://localhost:3100
LOKI_LABELS=service=identity-service,environment=development

# Tempo tracing
TRACING_ENABLED=true
TEMPO_ENDPOINT=http://localhost:4317
TRACE_SAMPLE_RATE=1.0
SERVICE_NAME=identity-service
```

## Example LogQL Queries (Loki)

```logql
# All authentication failures
{service="identity-service"} | json | event_type="authentication" | status="failure"

# Account lockout events
{service="identity-service"} | json | security_event_type="account_locked"

# High severity security events
{service="identity-service"} | json | event_type="security" | severity=~"high|critical"

# Slow operations (>1 second)
{service="identity-service"} | json | duration_seconds > 1

# Errors in production
{service="identity-service", environment="production"} | json | level="ERROR"

# User operations by specific user
{service="identity-service"} | json | event_type="user_operation" | user_id="<uuid>"

# Token generation events
{service="identity-service"} | json | event_type="token_operation" | operation_type="generate"
```

## Example PromQL Queries (Prometheus)

```promql
# Authentication failure rate (per second)
rate(authentication_attempts_total{status="failure"}[5m])

# p95 authentication duration
histogram_quantile(0.95, rate(authentication_duration_seconds_bucket[5m]))

# Total failed logins in last hour
sum(increase(failed_login_attempts[1h]))

# Active tokens by type
active_tokens{token_type="access"}

# HTTP 5xx error rate
rate(http_requests_total{status=~"5.."}[5m])

# Database query p99 latency
histogram_quantile(0.99, rate(database_operation_duration_seconds_bucket[5m]))

# Failed authorization checks
sum(increase(authorization_checks_total{is_authorized="false"}[1h]))
```

## Alerting Examples

### Prometheus Alerting Rules

Create `alerts.yml`:

```yaml
groups:
  - name: identity_service_alerts
    interval: 30s
    rules:
      - alert: HighAuthenticationFailureRate
        expr: rate(authentication_attempts_total{status="failure"}[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate"
          description: "More than 10 failed auth attempts per second for 5 minutes"

      - alert: AccountLockoutSpike
        expr: increase(security_events_total{event_type="account_locked"}[5m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Multiple account lockouts detected"
          description: "{{ $value }} accounts locked in 5 minutes"

      - alert: SlowDatabaseQueries
        expr: histogram_quantile(0.95, rate(database_operation_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"
          description: "p95 database latency is {{ $value }}s"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High HTTP 5xx error rate"
          description: "{{ $value }} errors per second"
```

## Production Considerations

### Security
- Use authentication for Grafana in production
- Secure Prometheus and Loki endpoints
- Don't log sensitive data (passwords, tokens)
- Emails are automatically masked in logs

### Performance
- Adjust `LOKI_BATCH_INTERVAL` based on log volume
- Configure Prometheus retention policy
- Use Loki compactor for storage optimization
- Consider log sampling for high-traffic endpoints

### Retention
- Configure Loki retention: Default 30 days
- Configure Prometheus retention: Default 15 days
- Adjust based on compliance requirements

### Scaling
- Use Prometheus federation for multi-instance setups
- Consider Grafana Loki distributed mode for high volume
- Use remote write for long-term storage
- Implement log aggregation at edge for microservices

## Troubleshooting

### Metrics not appearing in Prometheus

1. Check metrics endpoint: `curl http://localhost:8000/metrics`
2. Verify Prometheus scrape config targets
3. Check Prometheus targets page: http://localhost:9090/targets
4. Ensure `METRICS_ENABLED=true` in `.env`

### Logs not appearing in Loki

1. Check Loki is running: `curl http://localhost:3100/ready`
2. Verify `LOKI_URL` in `.env` is correct
3. Check app logs for Loki connection errors
4. Test Loki query: `{service="identity-service"}`
5. Ensure `LOKI_ENABLED=true` in `.env`

### Dashboard shows "No data"

1. Verify data source is configured correctly
2. Check time range in dashboard (default: last 1 hour)
3. Verify label names match (case-sensitive)
4. Run queries manually in Explore view

## Support

For issues or questions:
- Check application logs for errors
- Verify environment configuration
- Review Prometheus/Loki documentation
- Ensure network connectivity between services
