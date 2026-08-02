# Phase 5 — API Gateway / WAAP and Traffic Analysis

**Goal:** Put a gateway with protective rules in front of crAPI and observe the traffic through Prometheus + Grafana.

## Stack

| Component | Role | URL |
|-----------|------|-----|
| Kong | API gateway (DB-less mode) | `http://127.0.0.1:8088` |
| Kong metrics endpoint | Prometheus target | `http://127.0.0.1:18001/metrics` |
| Prometheus | Metric storage | `http://127.0.0.1:19090` |
| Grafana | Dashboard | `http://127.0.0.1:13000` (admin/admin) |

Kong is configured in `gateway/kong.yml`.

## Protections enabled

1. **Rate limiting** — 10 requests per minute per IP on the catch-all route.
2. **Request size limiting** — 128 KB payload cap.
3. **Path-based WAF block** — `POST /workshop/api/merchant/contact_mechanic` returns `403`. This closes the SSRF / layer-7 DoS primitive used in Challenges 6 and 11.
4. **Prometheus metrics** — status codes, latency, and bandwidth per service/route.

## How to start

```bash
docker compose up -d kong prometheus grafana
```

## Verification

### Normal traffic still routes

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  http://127.0.0.1:8088/identity/api/v2/vehicle/vehicles \
  -H "Authorization: Bearer invalid"
```

Result: `HTTP 401` — the request reached crAPI and was rejected by identity.

### Rate limiting

```bash
for i in {1..12}; do
  curl -s -o /dev/null -w "%{http_code} " \
    http://127.0.0.1:8088/identity/api/auth/jwks.json
done
echo
```

Result:

```
200 200 200 200 200 200 200 200 200 200 429 429
```

### WAF block

```bash
curl -s -X POST http://127.0.0.1:8088/workshop/api/merchant/contact_mechanic \
  -H 'Content-Type: application/json' \
  -d '{"mechanic_api":"http://www.google.com/"}' \
  -w "HTTP %{http_code}\n" -o /dev/null
```

Result: `HTTP 403`.

Direct crAPI still answers the same call:

```bash
curl -s -X POST http://127.0.0.1:8888/workshop/api/merchant/contact_mechanic \
  -H 'Content-Type: application/json' \
  -d '{"mechanic_api":"http://www.google.com/"}' \
  -w "HTTP %{http_code}\n" -o /dev/null
```

Result: `HTTP 200`.

This proves the gateway is acting as a control point while direct service ports remain open.

### Prometheus query

Blocked requests:

```bash
curl -sG 'http://127.0.0.1:19090/api/v1/query' \
  --data-urlencode 'query=sum(kong_http_requests_total{code="403"})'
```

Rate-limited requests:

```bash
curl -sG 'http://127.0.0.1:19090/api/v1/query' \
  --data-urlencode 'query=sum(kong_http_requests_total{code="429"})'
```

Example output:

```json
{
  "status": "success",
  "data": {
    "result": [
      {
        "metric": {},
        "value": [1785648639, "3"]
      }
    ]
  }
}
```

### Grafana dashboard

Open `http://127.0.0.1:13000` and log in with `admin` / `admin`. The pre-loaded **crAPI Gateway Metrics** dashboard shows request rate by status, blocked count, and rate-limited count.

## Attack replay

The SSRF/DoS attack from Challenge 11 is now blocked at the gateway:

```bash
for i in {1..3}; do
  curl -s -X POST http://127.0.0.1:8088/workshop/api/merchant/contact_mechanic \
    -H 'Content-Type: application/json' \
    -d '{"mechanic_api":"http://www.google.com/"}' \
    -o /dev/null -w "%{http_code} "
done
echo
```

Result: `403 403 403`.

The block events appear in the Grafana dashboard and can be queried in Prometheus as `kong_http_requests_total{code="403"}`.

## Why this matters

- A gateway can enforce global policy (rate limits, payload limits, path blocks) without touching every microservice.
- Metrics make it possible to detect attack patterns (spikes in `429`, `403`, or unusual route activity).
- In a production deployment, this stack could be extended with:
  - JWT validation at the gateway using crAPI's JWKS endpoint.
  - A real WAAP such as ModSecurity/CRS or open-appsec.
  - Loki or Vector for centralized log analysis.

## Limitations in this lab

- Direct crAPI service ports are still exposed so individual phases can still be reproduced.
- Rate limiting uses Kong's `local` policy; for multi-node Kong, switch to Redis.
- JWT validation is intentionally left as a future hardening step.
