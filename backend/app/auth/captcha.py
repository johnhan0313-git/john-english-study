from __future__ import annotations

import random
import secrets
import string
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class CaptchaChallenge:
    answer: str
    expires_at: float


_lock = threading.Lock()
_captchas: dict[str, CaptchaChallenge] = {}


def _purge_expired(now: float) -> None:
    expired = [key for key, item in _captchas.items() if item.expires_at <= now]
    for key in expired:
        _captchas.pop(key, None)


def create_captcha(*, ttl_seconds: int = 300) -> tuple[str, str, str]:
    answer = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    captcha_id = secrets.token_urlsafe(16)
    now = time.time()
    with _lock:
        _purge_expired(now)
        _captchas[captcha_id] = CaptchaChallenge(answer=answer.upper(), expires_at=now + ttl_seconds)

    svg = _render_svg(answer)
    return captcha_id, svg, answer


def verify_captcha(captcha_id: str, user_input: str) -> bool:
    now = time.time()
    with _lock:
        _purge_expired(now)
        challenge = _captchas.pop(captcha_id, None)
    if not challenge or challenge.expires_at <= now:
        return False
    return challenge.answer == user_input.strip().upper()


def _render_svg(text: str) -> str:
    chars = []
    for index, ch in enumerate(text):
        x = 18 + index * 22
        y = 28 + random.randint(-4, 4)
        rotate = random.randint(-25, 25)
        color = f"rgb({random.randint(30, 120)},{random.randint(30, 120)},{random.randint(30, 120)})"
        chars.append(
            f'<text x="{x}" y="{y}" font-size="22" font-family="monospace" fill="{color}" '
            f'transform="rotate({rotate} {x} {y})">{ch}</text>'
        )
    noise = "".join(
        f'<line x1="{random.randint(0,120)}" y1="{random.randint(0,40)}" '
        f'x2="{random.randint(0,120)}" y2="{random.randint(0,40)}" stroke="#cbd5e1" stroke-width="1"/>'
        for _ in range(6)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40" viewBox="0 0 120 40">'
        f'<rect width="120" height="40" fill="#f8fafc"/>'
        f"{noise}{''.join(chars)}"
        "</svg>"
    )
