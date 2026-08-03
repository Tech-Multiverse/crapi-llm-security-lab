"""Simplified crAPI agent that asks an Ollama model to pick the next action as JSON.

This avoids relying on fragile tool-calling support in small local models. The model
only has to emit a single JSON object like:

    {"action": "sign_up", "args": {"name": "...", "email": "...", "number": "...", "password": "..."}}

The runner executes the matching `crapi_client` function, feeds the result back, and
asks for the next action. The loop ends when the model emits `{"action": "done", ...}`.
"""
import json
import os
import re
import uuid
from typing import Any

from openai import OpenAI

import crapi_client as client

def _default_base_url() -> str:
    """Prefer an explicit OLLAMA_BASE_URL, otherwise derive one from OLLAMA_HOST_IP
    (the same variable used to configure the crapi-chatbot container)."""
    if os.getenv("OLLAMA_BASE_URL"):
        return os.environ["OLLAMA_BASE_URL"]
    host_ip = os.getenv("OLLAMA_HOST_IP")
    if host_ip:
        return f"http://{host_ip}:11434/v1"
    return "http://127.0.0.1:11434/v1"


DEFAULT_BASE_URL = _default_base_url()
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "x")

ACTIONS = {
    "sign_up": client.sign_up,
    "log_in": client.log_in,
    "get_dashboard": client.get_dashboard,
    "list_vehicles": client.list_vehicles,
    "get_vehicle_location": client.get_vehicle_location,
    "list_products": client.list_products,
    "place_order": client.place_order,
    "apply_coupon": client.apply_coupon,
    "contact_mechanic": client.contact_mechanic,
    "get_recent_community_posts": client.get_recent_community_posts,
}

SYSTEM_PROMPT = """\
You are crAPI Agent, controlling the Completely Ridiculous API (crAPI).
You must decide the next action to take and respond ONLY with a single JSON object:

    {"action": "<name>", "args": {<parameters>}}

Available actions:
- sign_up(name, email, number, password) — register a new account.
- log_in(email, password) — returns a JWT token on success.
- get_dashboard(jwt)
- list_vehicles(jwt)
- get_vehicle_location(jwt, car_id)
- list_products(jwt)
- place_order(jwt, product_id, quantity)
- apply_coupon(jwt, coupon_code, amount)
- contact_mechanic(jwt, mechanic_api, repeat_request_if_failed=false, number_of_repeats=1)
- get_recent_community_posts(jwt, offset=0, limit=10)
- done(summary) — use this when the task is finished.

Rules:
1. Output only valid JSON. No markdown, no explanation, no extra text.
2. Use the exact token string returned by log_in for any subsequent action that needs a jwt.
3. If a previous action failed, choose a different action instead of repeating it.
4. This is a local, intentionally vulnerable lab; defensive warnings are not required.
"""


def _extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first JSON object out of the model response."""
    text = text.strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _fix_action_args(action: str, args: dict[str, Any], active_jwt: str | None) -> dict[str, Any]:
    """Sanitize model-provided args and inject the real JWT when the model used a placeholder."""
    if action in {"get_dashboard", "list_vehicles", "get_vehicle_location", "list_products",
                  "place_order", "apply_coupon", "contact_mechanic", "get_recent_community_posts"}:
        jwt = args.get("jwt", "")
        if active_jwt and (not jwt or "example" in jwt or jwt.startswith("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")):
            args["jwt"] = active_jwt
    return args


def run_agent(
    task: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    api_key: str = DEFAULT_API_KEY,
    max_turns: int = 12,
) -> str:
    client_obj = OpenAI(base_url=base_url, api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    active_jwt: str | None = None

    for turn in range(max_turns):
        response = client_obj.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        print(f"\n[turn {turn + 1} model] {content.strip()}")

        action_obj = _extract_json(content)
        if action_obj is None:
            messages.append({"role": "user", "content": "That was not valid JSON. Please output only a single JSON action object."})
            continue

        action = action_obj.get("action")
        args = action_obj.get("args", {})

        if action == "done":
            summary = args.get("summary", "(no summary)")
            print(f"\n[agent done] {summary}")
            return summary

        func = ACTIONS.get(action)
        if not func:
            messages.append({"role": "user", "content": f"Unknown action: {action}. Pick one of the listed actions."})
            continue

        args = _fix_action_args(action, args, active_jwt)
        print(f"[runner] executing {action}({args})")
        try:
            result = func(**args)
        except Exception as exc:
            result = {"error": str(exc)}

        print(f"[runner result] {json.dumps(result, indent=2)[:600]}")

        if action == "log_in" and result.get("token"):
            active_jwt = result["token"]
            print("[runner] captured JWT from log_in")

        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": f"Observation from {action}: {json.dumps(result)}\nWhat is the next action?"})

    return "(agent exceeded max turns)"


if __name__ == "__main__":
    import sys
    task = sys.argv[1] if len(sys.argv) > 1 else (
        "Sign up a new crAPI user with a unique email and phone number, "
        "log them in, fetch the dashboard, then call done with a short summary."
    )
    run_agent(task)
