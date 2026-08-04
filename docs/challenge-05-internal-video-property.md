# Challenge 5 — Excessive Data Exposure: Leak an internal property of a video

**OWASP API Top 10 mapping:** API3:2023 Broken Object Property Level Authorization / Excessive Data Exposure  
**crAPI category:** Excessive Data Exposure

## Goal

Find an API endpoint that exposes an internal property of the video resource — a value that should never reach the client because it describes server-side processing behavior.

## Vulnerability

The profile-video endpoint returns the full `ProfileVideo` entity, including the `conversion_params` field. This field contains the FFMPEG-style command string (`-v codec h264`) used by the server to transcode the video. It is an internal implementation detail, and exposing it helps an attacker craft later attacks (e.g., command injection against the video conversion flow).

## Exploit steps

### 1. Authenticate and get your own `video_id`

The dashboard returns the current user's video identifier:

```bash
curl -s -H "Authorization: Bearer $JWT" \
  http://127.0.0.1:8888/identity/api/v2/user/dashboard
```

Example response:

```json
{
  "id": 4,
  "name": "Test",
  "email": "test@example.com",
  "number": "9876540001",
  "picture_url": null,
  "video_url": "data:image/jpeg;base64,TenvnC+THvxYDw==",
  "video_name": "Test_video",
  "available_credit": 100.0,
  "video_id": 4,
  "role": "ROLE_USER"
}
```

> If `video_id` is `0` and `video_name` is `null`, the account has no profile video yet and the next steps will return `404`. Upload one first by logging into the crAPI web UI at `http://127.0.0.1:3001` (or `http://127.0.0.1:8888`), going to the profile section, and uploading a video. After uploading, the dashboard will show a non-zero `video_id`.

### 2. Request the video resource by ID

```bash
curl -s -H "Authorization: Bearer $JWT" \
  http://127.0.0.1:8888/identity/api/v2/user/videos/4
```

### 3. Inspect the response

```json
{
  "id": 4,
  "video_name": "Test_video",
  "conversion_params": "-v codec h264",
  "profileVideo": "data:image/jpeg;base64,TenvnC+THvxYDw=="
}
```

`conversion_params` is an internal processing directive that the API leaks to the client.

## Why this works

- The `ProfileVideo` entity is returned directly as JSON.
- `conversion_params` has no `@JsonIgnore` annotation and no DTO masks it.
- The client has no legitimate need for this value; it is used later by the server-side `convertVideo` endpoint.

## Impact

- Information disclosure about backend command structure.
- Enables follow-up attacks such as command injection in the video-conversion workflow.
- Reveals that the application constructs shell commands from user-influenced input.

## Mitigation

- Use a dedicated response DTO for API clients that excludes internal fields like `conversion_params`.
- Keep processing commands server-side; never store shell fragments in fields that can be returned to users.
- Apply `@JsonIgnore` or equivalent serialization suppression to internal implementation details.
- Review all entity-to-JSON mappings for fields that leak internal state, secrets, or command templates.
