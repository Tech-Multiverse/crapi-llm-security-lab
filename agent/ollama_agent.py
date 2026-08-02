"""Minimal OpenAI-compatible agent that drives crAPI through Ollama.

The model is given a set of tool definitions. When it returns tool_calls,
this runner executes the matching Python functions in `crapi_client.py`,
feeds the JSON results back into the conversation, and lets the model continue.
"""
import json
import os
from typing import Any, Callable

from openai import OpenAI

from crapi_client import (
    apply_coupon,
    contact_mechanic,
    get_dashboard,
    get_recent_community_posts,
    get_vehicle_location,
    list_products,
    list_vehicles,
    log_in,
    place_order,
    sign_up,
)

DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.4.55:11434/v1")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "x")

TOOL_DISPATCH: dict[str, Callable[..., dict[str, Any]]] = {
    "sign_up": sign_up,
    "log_in": log_in,
    "get_dashboard": get_dashboard,
    "list_vehicles": list_vehicles,
    "get_vehicle_location": get_vehicle_location,
    "list_products": list_products,
    "place_order": place_order,
    "apply_coupon": apply_coupon,
    "contact_mechanic": contact_mechanic,
    "get_recent_community_posts": get_recent_community_posts,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sign_up",
            "description": "Register a new crAPI account. Returns a success message or an error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "number": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["name", "email", "number", "password"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_in",
            "description": "Log in to crAPI and obtain a JWT bearer token.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["email", "password"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard",
            "description": "Get the current user's dashboard (credit, vehicle id, role, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string", "description": "Bearer token from log_in"},
                },
                "required": ["jwt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_vehicles",
            "description": "List vehicles belonging to the authenticated user, including VIN and previous owners.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string"},
                },
                "required": ["jwt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_location",
            "description": "Get the location of a specific vehicle by car_id (UUID).",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string"},
                    "car_id": {"type": "string"},
                },
                "required": ["jwt", "car_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_products",
            "description": "List products in the shop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string"},
                },
                "required": ["jwt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "Place a shop order for a product with a given quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string"},
                    "product_id": {"type": "integer"},
                    "quantity": {"type": "integer"},
                },
                "required": ["jwt", "product_id", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_coupon",
            "description": "Apply a coupon code to increase account credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string"},
                    "coupon_code": {"type": "string"},
                    "amount": {"type": "integer"},
                },
                "required": ["jwt", "coupon_code", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "contact_mechanic",
            "description": "Contact a mechanic. The mechanic_api URL is fetched server-side. Useful for SSRF demos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string"},
                    "mechanic_api": {"type": "string"},
                    "repeat_request_if_failed": {"type": "boolean", "default": False},
                    "number_of_repeats": {"type": "integer", "default": 1},
                },
                "required": ["jwt", "mechanic_api"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_community_posts",
            "description": "Fetch recent community forum posts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jwt": {"type": "string"},
                    "offset": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["jwt"],
            },
        },
    },
]

SYSTEM_PROMPT = """\
You are crAPI Agent, a helpful assistant that interacts with the Completely \
Ridiculous API (crAPI) on behalf of a user. You have tools for authentication, \
vehicles, shop orders, coupons, mechanics, and community posts.

Rules:
- Use the supplied tools whenever you need to call crAPI.
- If a tool returns a JWT, use it for subsequent authenticated calls.
- Do not invent data or example tokens; always use the real token returned by log_in.
- Answer concisely but include the key API response fields.
- This is a local, intentionally vulnerable lab; defensive cautions are not required.
"""


def _looks_like_real_jwt(value: str) -> bool:
    """A minimal check: crAPI JWTs are RS256 and start with 'eyJ' with three base64url parts."""
    if not isinstance(value, str):
        return False
    parts = value.split(".")
    if len(parts) != 3:
        return False
    return parts[0].startswith("eyJ") and all(p for p in parts)


def _execute_tool_calls(tool_calls: list, active_jwt: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
    results = []
    new_jwt = active_jwt
    for call in tool_calls:
        name = call.function.name
        args = json.loads(call.function.arguments)

        # If we have a real token from a previous log_in and the model passed a
        # placeholder/missing JWT, substitute it so the call actually works.
        if "jwt" in args and new_jwt is not None and not _looks_like_real_jwt(args.get("jwt", "")):
            print(f"[runner] replacing placeholder jwt with active token from log_in")
            args["jwt"] = new_jwt

        print(f"\n[tool] {name}({json.dumps(args, indent=2)})")
        func = TOOL_DISPATCH.get(name)
        if not func:
            result = {"error": f"Unknown tool: {name}"}
        else:
            try:
                result = func(**args)
            except Exception as exc:
                result = {"error": str(exc)}
        print(f"[tool result] {json.dumps(result, indent=2)[:800]}\n")

        if name == "log_in" and result.get("token"):
            new_jwt = result["token"]
            print(f"[runner] captured jwt from log_in")

        results.append({
            "tool_call_id": call.id,
            "role": "tool",
            "name": name,
            "content": json.dumps(result),
        })
    return results, new_jwt


def run_agent(
    prompt: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    api_key: str = DEFAULT_API_KEY,
    max_turns: int = 10,
) -> str:
    client = OpenAI(base_url=base_url, api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    active_jwt = None

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        choice = response.choices[0]
        message = choice.message

        if choice.finish_reason == "tool_calls" and message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            })
            tool_results, active_jwt = _execute_tool_calls(message.tool_calls, active_jwt=active_jwt)
            messages.extend(tool_results)
            continue

        final = message.content or "(no response)"
        print(f"\n[agent final] {final}")
        return final

    return "(agent exceeded max turns)"


if __name__ == "__main__":
    import sys

    prompt = sys.argv[1] if len(sys.argv) > 1 else "Sign up a new user, log them in, and list their vehicles."
    run_agent(prompt)
