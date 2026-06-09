from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx

from app.config import Settings


class WeChatNotConfiguredError(RuntimeError):
    pass


def wechat_configured(settings: Settings) -> bool:
    return bool(settings.wechat_app_id and settings.wechat_app_secret and settings.wechat_redirect_uri)


def build_wechat_authorize_url(settings: Settings, *, state: str | None = None) -> str:
    if not wechat_configured(settings):
        raise WeChatNotConfiguredError("WeChat OAuth is not configured")
    state_value = state or secrets.token_urlsafe(16)
    params = urlencode(
        {
            "appid": settings.wechat_app_id,
            "redirect_uri": settings.wechat_redirect_uri,
            "response_type": "code",
            "scope": "snsapi_login",
            "state": state_value,
        }
    )
    return f"https://open.weixin.qq.com/connect/qrconnect?{params}#wechat_redirect"


async def exchange_wechat_code(settings: Settings, code: str) -> dict:
    if not wechat_configured(settings):
        raise WeChatNotConfiguredError("WeChat OAuth is not configured")

    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    params = {
        "appid": settings.wechat_app_id,
        "secret": settings.wechat_app_secret,
        "code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.get(token_url, params=params)
        token_resp.raise_for_status()
        token_data = token_resp.json()
        if token_data.get("errcode"):
            raise RuntimeError(token_data.get("errmsg", "WeChat token exchange failed"))

        access_token = token_data["access_token"]
        openid = token_data["openid"]
        user_resp = await client.get(
            "https://api.weixin.qq.com/sns/userinfo",
            params={"access_token": access_token, "openid": openid},
        )
        user_resp.raise_for_status()
        profile = user_resp.json()
        if profile.get("errcode"):
            raise RuntimeError(profile.get("errmsg", "WeChat userinfo failed"))

    return {
        "openid": openid,
        "nickname": profile.get("nickname"),
        "avatar_url": profile.get("headimgurl"),
    }


def frontend_callback_url(settings: Settings, token: str, *, next_path: str = "/") -> str:
    base = settings.frontend_base_url.rstrip("/")
    query = urlencode({"token": token, "next": next_path})
    return f"{base}/auth/callback?{query}"
