# Challenge 4 — Excessive Data Exposure: Leak sensitive information of other users

**OWASP API Top 10 mapping:** API3:2023 Broken Object Property Level Authorization / Excessive Data Exposure  
**crAPI category:** Excessive Data Exposure

## Goal

Find an API endpoint that returns more sensitive information about other users than the UI needs or the user is authorized to see.

## Vulnerability

The community forum endpoint returns the full author object for every post, including the author's **email address** and **vehicle ID**. These values are not required to display a forum post and can be used to mount further attacks (e.g., BOLA against vehicle location or password-reset attempts).

## Exploit steps

### 1. Authenticate as any crAPI user

You can sign up a new account or use a seeded user. Any valid JWT works because the response is returned to every authenticated user.

### 2. Request the recent community posts

```bash
curl -s -H "Authorization: Bearer $JWT" \
  'http://127.0.0.1:8888/community/api/v2/community/posts/recent?offset=0&limit=10'
```

### 3. Inspect the response

The API returns an array of posts. Each post contains an `author` block similar to:

```json
{
  "id": "hVVGBmxKgTKp6ia7kr4Bwh",
  "title": "Classic Car Restoration",
  "content": "Working on restoring a 1969 muscle car...",
  "author": {
    "nickname": "Adam",
    "email": "adam007@example.com",
    "vehicleid": "f89b5f21-7829-45cb-a650-299a61090378",
    "profile_pic_url": "",
    "created_at": "2026-07-31T23:35:10.946Z"
  },
  "comments": [],
  "authorid": 1,
  "CreatedAt": "2026-07-31T23:35:10.946Z"
}
```

The same endpoint returns other users' real email addresses and GUID vehicle identifiers for every seeded user who has posted in the forum.

## Why this works

- The backend returns the entire `Author` model as JSON instead of a public-facing DTO.
- `Author.email` and `Author.vehicleid` are sensitive properties that the forum UI does not need.
- The endpoint only checks that the caller is authenticated; it does not filter object properties per caller or per use case.

## Mitigation

- Return **public DTOs** from public endpoints. The forum author object should contain only `nickname` and `profile_pic_url`.
- Keep PII, internal IDs, and vehicle identifiers in internal models and expose them only when the business logic explicitly requires them.
- Apply the **principle of least privilege** at the property level, not just the endpoint level.
- Classify API response fields by sensitivity and review them regularly for over-exposure.

## Related challenges

- The leaked `vehicleid` is reused in **Challenge 1** to access another user's vehicle location via `/identity/api/v2/vehicle/<vehicleid>/location`.
