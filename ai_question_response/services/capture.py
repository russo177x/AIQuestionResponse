from __future__ import annotations

import io

import mss
from PIL import Image


def capture_screen_png(monitor_index: int = 1) -> bytes:
    """Captura uma tela local autorizada e devolve PNG em memória."""
    with mss.mss() as screen:
        monitors = screen.monitors
        if monitor_index >= len(monitors):
            monitor_index = 1 if len(monitors) > 1 else 0
        shot = screen.grab(monitors[monitor_index])
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
