from __future__ import annotations

import json


def format_sse(data: dict[str, object], event: str | None = None) -> str:
    """Render one Server-Sent Events frame.

    The wire format is line-based: an optional ``event:`` line, a ``data:``
    line, and a blank line that terminates the frame. We JSON-encode the
    payload so the client can parse a structured object per event.
    """
    frame = ""
    if event is not None:
        frame += f"event: {event}\n"
    frame += f"data: {json.dumps(data)}\n\n"
    return frame
