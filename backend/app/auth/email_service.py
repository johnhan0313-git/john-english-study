from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import Settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    pass


def _use_ssl(settings: Settings) -> bool:
    return settings.smtp_use_ssl or settings.smtp_port == 465


def send_login_code(settings: Settings, email: str, code: str) -> None:
    subject = f"{settings.app_name} 登录验证码"
    body = (
        f"您的登录验证码是：{code}\n\n"
        f"验证码 {settings.email_code_expire_minutes} 分钟内有效，请勿泄露给他人。\n"
        f"如非本人操作，请忽略此邮件。"
    )

    if not settings.smtp_configured:
        if settings.testing or settings.debug or settings.auth_expose_codes:
            logger.warning("[dev-email] to=%s code=%s (SMTP 未配置，验证码仅写入日志)", email, code)
            return
        raise EmailDeliveryError("邮件服务未配置，请联系管理员")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = email
    message.set_content(body)

    try:
        if _use_ssl(settings):
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        logger.exception("Failed to send login code email to %s", email)
        raise EmailDeliveryError(
            "邮件发送失败，请检查 SMTP 配置（163 邮箱建议使用端口 465 + SSL）"
        ) from exc

    logger.info("Login code email sent to %s", email)


def send_email_change_code(settings: Settings, email: str, code: str) -> None:
    subject = f"{settings.app_name} 邮箱变更验证码"
    body = (
        f"您正在变更账号绑定邮箱，验证码是：{code}\n\n"
        f"验证码 {settings.email_code_expire_minutes} 分钟内有效，请勿泄露给他人。\n"
        f"如非本人操作，请忽略此邮件。"
    )

    if not settings.smtp_configured:
        if settings.testing or settings.debug or settings.auth_expose_codes:
            logger.warning("[dev-email] change-email to=%s code=%s (SMTP 未配置)", email, code)
            return
        raise EmailDeliveryError("邮件服务未配置，请联系管理员")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = email
    message.set_content(body)

    try:
        if _use_ssl(settings):
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        logger.exception("Failed to send email change code to %s", email)
        raise EmailDeliveryError(
            "邮件发送失败，请检查 SMTP 配置（163 邮箱建议使用端口 465 + SSL）"
        ) from exc

    logger.info("Email change code sent to %s", email)
