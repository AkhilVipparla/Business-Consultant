"""Standard API response envelope — see anchor.md/ARCHITECTURE.md > API STRUCTURE.

Every /api/v1 JSON response (success or error) uses one of these two shapes,
except the /validate SSE stream, which is exempt by design.
"""

from typing import Any


def success(data: Any = None, message: str | None = None) -> dict:
    return {"success": True, "data": data, "error": None, "message": message}


def error(message: str, code: str) -> dict:
    return {"success": False, "data": None, "error": message, "code": code}
