#!/usr/bin/env bash
# Demo: trigger Kong rate limiting on the gateway proxy path.
# Expects the gateway to be reachable at http://127.0.0.1:8088
set -euo pipefail

URL="${GATEWAY_URL:-http://127.0.0.1:8088/identity/api/auth/jwks.json}"

for i in $(seq 1 12); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  echo "request $i: HTTP $code"
done
