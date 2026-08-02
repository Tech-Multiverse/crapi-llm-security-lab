# crAPI API Gateway & WAAP

This directory holds a Kong-based gateway that sits in front of crAPI, plus a Prometheus + Grafana observability stack.

## What is included

| Component | Purpose | Local URL |
|-----------|---------|-----------|
| Kong | API gateway with rate limiting, request-size limits, path-based WAF block, and Prometheus metrics | `http://127.0.0.1:8088` |
| Kong Admin / metrics | Prometheus metrics endpoint | `http://127.0.0.1:18001/metrics` |
| Prometheus | Scrapes Kong metrics | `http://127.0.0.1:19090` |
| Grafana | Preloaded dashboard for gateway traffic | `http://127.0.0.1:13000` |

Ports are offset from the standard ones to avoid collisions with crAPI's existing services (e.g., crAPI-workshop already uses 8000).

## Start the gateway stack

From the repo root:

```bash
docker compose up -d kong prometheus grafana
```

Kong will wait for `crapi-web` to be healthy before starting. Prometheus and Grafana then start after Kong.

## Kong configuration

The declarative config is in `gateway/kong.yml`:

- **Upstream**: all routes forward to `http://crapi-web:80` (the crAPI web proxy).
- **Rate limiting**: 10 requests per minute per client IP on the catch-all route.
- **Request size limiting**: 128 KB payload cap.
- **WAF-style block**: `POST /workshop/api/merchant/contact_mechanic` is terminated with `403 Blocked by gateway WAF rule`. This endpoint is the SSRF / layer-7 DoS primitive used in Challenge 6 and Challenge 11.
- **Prometheus plugin**: enabled globally with status-code, latency, and bandwidth metrics.

## Quick verification

### 1. Normal routing

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  http://127.0.0.1:8088/identity/api/v2/vehicle/vehicles \
  -H "Authorization: Bearer invalid"
```

Expected: `HTTP 401` — the request reached crAPI identity service and was rejected.

### 2. Rate limiting

```bash
for i in {1..12}; do
  curl -s -o /dev/null -w "%{http_code} " \
    http://127.0.0.1:8088/identity/api/auth/jwks.json
done
echo
```

Expected: ten `200`s followed by two `429`s.

### 3. WAF block

```bash
curl -s -X POST http://127.0.0.1:8088/workshop/api/merchant/contact_mechanic \
  -H 'Content-Type: application/json' \
  -d '{"mechanic_api":"http://www.google.com/"}' \
  -w "HTTP %{http_code}\n" -o /dev/null
```

Expected: `HTTP 403`.

The same call directly to crAPI (`http://127.0.0.1:8888/...`) still succeeds, showing that the gateway is a control point, not a full perimeter, while direct service ports remain open.

### 4. Prometheus metrics

```bash
curl -s http://127.0.0.1:18001/metrics | grep kong_http_requests_total
```

You should see counters like:

```
kong_http_requests_total{service="crapi-web",route="crapi-catch-all",code="200",source="service",workspace="default",consumer=""} 10
kong_http_requests_total{service="crapi-web",route="crapi-catch-all",code="429",source="kong",workspace="default",consumer=""} 2
kong_http_requests_total{service="waf-block-contact-mechanic",route="contact-mechanic-block",code="403",source="kong",workspace="default",consumer=""} 1
```

### 5. Grafana dashboard

Log in at `http://127.0.0.1:13000` with:

- Username: `admin`
- Password: `admin`

The pre-provisioned dashboard **crAPI Gateway Metrics** shows:

- Request rate by HTTP status code
- Rate-limited request count (`429`)
- Blocked request count (`403`)

## Attack replay through the gateway

The SSRF / DoS primitive is now blocked at the gateway:

```bash
for i in {1..3}; do
  curl -s -X POST http://127.0.0.1:8088/workshop/api/merchant/contact_mechanic \
    -H 'Content-Type: application/json' \
    -d '{"mechanic_api":"http://www.google.com/"}' \
    -o /dev/null -w "%{http_code} "
done
echo
```

Then query Prometheus:

```bash
curl -sG 'http://127.0.0.1:19090/api/v1/query' \
  --data-urlencode 'query=sum(kong_http_requests_total{code="403"})'
```

The result will show the number of blocked requests. The same value appears in the Grafana dashboard.

## Files

- `gateway/kong.yml` — Kong DB-less declarative configuration
- `gateway/prometheus.yml` — Prometheus scrape config
- `gateway/grafana/provisioning/` — Grafana datasource and dashboard provider config
- `gateway/grafana/dashboards/crapi-gateway.json` — Sample dashboard

## Notes & limitations

- Direct crAPI ports (`8888`, `8080`, `8000`, etc.) are still exposed in this lab. The gateway is an *in-line* choke point, not a closed perimeter.
- JWT validation at the gateway is not configured here; crAPI still validates tokens internally. In a production deployment, JWT validation could be added with Kong's `jwt` or `openid-connect` plugin and the JWKS endpoint from `/identity/api/auth/jwks.json`.
- Kong's rate-limiting plugin uses the `local` policy, which is fine for a single Kong container. For a multi-node deployment, use `redis`.
