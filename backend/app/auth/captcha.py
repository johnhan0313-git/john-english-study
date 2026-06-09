from __future__ import annotations

import hashlib
import random
import secrets
import threading
import time
from dataclasses import dataclass

WIDTH = 300
HEIGHT = 150
PIECE_W = 46
PIECE_H = 46
TOLERANCE = 10


@dataclass(frozen=True)
class CaptchaChallenge:
    answer: str
    expires_at: float


@dataclass(frozen=True)
class SliderCaptchaPayload:
    captcha_id: str
    width: int
    height: int
    puzzle_y: int
    piece_width: int
    background_svg: str
    piece_svg: str
    target_x: int


_lock = threading.Lock()
_captchas: dict[str, CaptchaChallenge] = {}


def _purge_expired(now: float) -> None:
    expired = [key for key, item in _captchas.items() if item.expires_at <= now]
    for key in expired:
        _captchas.pop(key, None)


def _seed_from_id(captcha_id: str) -> int:
    digest = hashlib.sha256(captcha_id.encode()).hexdigest()
    return int(digest[:8], 16)


def _render_scene(rng: random.Random, width: int, height: int) -> str:
    parts: list[str] = []
    hue = rng.randint(200, 230)
    parts.append(
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="hsl({hue},55%,88%)"/>'
        f'<stop offset="100%" stop-color="hsl({hue + 20},45%,72%)"/>'
        f"</linearGradient></defs>"
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="url(#bg)"/>')

    for _ in range(22):
        cx = rng.randint(-10, width + 10)
        cy = rng.randint(-10, height + 10)
        r = rng.randint(6, 28)
        color = f"hsl({rng.randint(180, 260)},{rng.randint(35, 70)}%,{rng.randint(45, 65)}%)"
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.55"/>')

    for _ in range(10):
        x1, y1 = rng.randint(0, width), rng.randint(0, height)
        x2, y2 = rng.randint(0, width), rng.randint(0, height)
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#64748b" stroke-width="1.5" opacity="0.35"/>'
        )

    return "".join(parts)


def create_captcha(*, ttl_seconds: int = 300) -> SliderCaptchaPayload:
    captcha_id = secrets.token_urlsafe(16)
    target_x = random.randint(55, WIDTH - PIECE_W - 55)
    target_y = random.randint(25, HEIGHT - PIECE_H - 25)
    now = time.time()

    seed = _seed_from_id(captcha_id)
    rng = random.Random(seed)
    scene = _render_scene(rng, WIDTH, HEIGHT)

    slot = (
        f'<rect x="{target_x}" y="{target_y}" width="{PIECE_W}" height="{PIECE_H}" '
        f'fill="rgba(15,23,42,0.18)" rx="6"/>'
        f'<rect x="{target_x}" y="{target_y}" width="{PIECE_W}" height="{PIECE_H}" '
        f'fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="2" stroke-dasharray="5 4" rx="6"/>'
    )
    background_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">{scene}{slot}</svg>'
    )

    piece_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PIECE_W}" height="{PIECE_H}" '
        f'viewBox="0 0 {PIECE_W} {PIECE_H}">'
        f'<defs><clipPath id="clip"><rect width="{PIECE_W}" height="{PIECE_H}" rx="6"/></clipPath></defs>'
        f'<g clip-path="url(#clip)" transform="translate({-target_x}, {-target_y})">{scene}</g>'
        f'<rect width="{PIECE_W}" height="{PIECE_H}" fill="none" stroke="#fff" stroke-width="2" rx="6"/>'
        f"</svg>"
    )

    with _lock:
        _purge_expired(now)
        _captchas[captcha_id] = CaptchaChallenge(answer=str(target_x), expires_at=now + ttl_seconds)

    return SliderCaptchaPayload(
        captcha_id=captcha_id,
        width=WIDTH,
        height=HEIGHT,
        puzzle_y=target_y,
        piece_width=PIECE_W,
        background_svg=background_svg,
        piece_svg=piece_svg,
        target_x=target_x,
    )


def verify_captcha(captcha_id: str, user_x: int) -> bool:
    now = time.time()
    with _lock:
        _purge_expired(now)
        challenge = _captchas.get(captcha_id)
        if not challenge or challenge.expires_at <= now:
            return False
        target_x = int(challenge.answer)
        if abs(user_x - target_x) > TOLERANCE:
            return False
        _captchas.pop(captcha_id, None)
    return True
