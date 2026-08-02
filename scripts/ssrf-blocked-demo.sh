#!/usr/bin/env bash
# Demo: the gateway WAF rule blocks SSRF via /workshop/api/merchant/contact_mechanic,
# while the same request directly to crAPI (with a valid JWT) still succeeds.
set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:8088/workshop/api/merchant/contact_mechanic}"
DIRECT_URL="${DIRECT_URL:-http://127.0.0.1:8888/workshop/api/merchant/contact_mechanic}"
IDENTITY_URL="${IDENTITY_URL:-http://127.0.0.1:8888/identity/api/auth/login}"
PAYLOAD='{"mechanic_api":"http://www.google.com/"}'

echo "=== Logging in as admin to get a JWT ==="
TOKEN=$(curl -s -X POST "$IDENTITY_URL" -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"Admin!123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))')

if [ -z "$TOKEN" ]; then
  echo "Failed to obtain JWT; make sure crAPI identity service is running."
  exit 1
fi

echo ""
echo "=== Through gateway (should be 403, no JWT needed to be blocked) ==="
curl -s -X POST "$GATEWAY_URL" -H 'Content-Type: application/json' -d "$PAYLOAD" -w "\nHTTP %{http_code}\n"

echo ""
echo "=== Direct to crAPI with JWT (should be 200) ==="
curl -s -X POST "$DIRECT_URL" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d "$PAYLOAD" -w "\nHTTP %{http_code}\n"
