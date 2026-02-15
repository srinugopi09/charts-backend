"""Authentication dependencies.

Placeholder implementation that reads user identity from the X-User-Id
header.  Replace the body of ``get_current_user_id`` with real auth
(JWT / OAuth / SSO) when ready — every endpoint that needs a user ID
already depends on this single function.
"""

from fastapi import Request


def get_current_user_id(request: Request) -> str:
    """Return the authenticated user ID from the request.

    Current implementation: reads the ``X-User-Id`` header and falls
    back to ``"anonymous"``.
    """
    return request.headers.get("x-user-id", "anonymous")
