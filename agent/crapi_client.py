"""Small HTTP client for the crAPI endpoints used by the demo agent."""
import json
import uuid
from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8888"


def _req(method: str, path: str, *, jwt: str | None = None, json_data: dict | None = None, params: dict | None = None) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    try:
        resp = requests.request(method, url, headers=headers, json=json_data, params=params, timeout=30)
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text, "status": resp.status_code}
        if isinstance(body, dict):
            body.setdefault("http_status", resp.status_code)
        else:
            body = {"data": body, "http_status": resp.status_code}
        return body
    except Exception as exc:
        return {"error": str(exc)}


def sign_up(name: str, email: str, number: str, password: str) -> dict[str, Any]:
    return _req("POST", "/identity/api/auth/signup", json_data={
        "name": name,
        "email": email,
        "number": number,
        "password": password,
    })


def log_in(email: str, password: str) -> dict[str, Any]:
    return _req("POST", "/identity/api/auth/login", json_data={
        "email": email,
        "password": password,
    })


def get_dashboard(jwt: str) -> dict[str, Any]:
    return _req("GET", "/identity/api/v2/user/dashboard", jwt=jwt)


def list_vehicles(jwt: str) -> dict[str, Any]:
    return _req("GET", "/identity/api/v2/vehicle/vehicles", jwt=jwt)


def get_vehicle_location(jwt: str, car_id: str) -> dict[str, Any]:
    return _req("GET", f"/identity/api/v2/vehicle/{car_id}/location", jwt=jwt)


def list_products(jwt: str) -> dict[str, Any]:
    return _req("GET", "/workshop/api/shop/products", jwt=jwt, params={"offset": 0, "limit": 10})


def place_order(jwt: str, product_id: int, quantity: int) -> dict[str, Any]:
    return _req("POST", "/workshop/api/shop/orders", jwt=jwt, json_data={
        "product_id": product_id,
        "quantity": quantity,
    })


def apply_coupon(jwt: str, coupon_code: str, amount: int) -> dict[str, Any]:
    return _req("POST", "/workshop/api/shop/apply_coupon", jwt=jwt, json_data={
        "coupon_code": coupon_code,
        "amount": amount,
    })


def contact_mechanic(jwt: str, mechanic_api: str, repeat_request_if_failed: bool = False, number_of_repeats: int = 1) -> dict[str, Any]:
    return _req("POST", "/workshop/api/merchant/contact_mechanic", jwt=jwt, json_data={
        "mechanic_api": mechanic_api,
        "repeat_request_if_failed": repeat_request_if_failed,
        "number_of_repeats": number_of_repeats,
    })


def get_recent_community_posts(jwt: str, offset: int = 0, limit: int = 10) -> dict[str, Any]:
    return _req("GET", "/community/api/v2/community/posts/recent", jwt=jwt, params={"offset": offset, "limit": limit})
