"""Enable ``python -m mcp_studio``.

The fleet launcher runs ``python -m mcp_studio``. Without this file Python refuses
with "'mcp_studio' is a package and cannot be directly executed", and because the
backend starts in a hidden window that failure was silent -- the dashboard loaded
and every API call returned 404.

Mirrors the run block already at the bottom of mcp_studio/main.py rather than
inventing a second way to start the server.
"""

from __future__ import annotations

import sys


def _run() -> int:
    import uvicorn

    from mcp_studio.main import settings

    uvicorn.run(
        "mcp_studio.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
    return 0


if __name__ == "__main__":
    sys.exit(_run())
