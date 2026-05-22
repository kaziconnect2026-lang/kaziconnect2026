"""
Resend email service for transactional emails (password reset, notifications).
"""
import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)


def _configure():
    """Set the Resend API key from env at call-time so .env updates take effect."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    resend.api_key = api_key
    return bool(api_key)


def _sender() -> str:
    return os.environ.get("SENDER_EMAIL") or "onboarding@resend.dev"


async def send_email(to: str, subject: str, html: str) -> dict:
    """Send a transactional email via Resend. Returns Resend response or raises."""
    if not _configure():
        raise RuntimeError("RESEND_API_KEY is not configured")

    params = {
        "from": _sender(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    return await asyncio.to_thread(resend.Emails.send, params)


def password_reset_html(name: str, reset_link: str) -> str:
    safe_name = (name or "there").split()[0] if name else "there"
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,Segoe UI,Roboto,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f4f4f5;padding:32px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellspacing="0" cellpadding="0" border="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e4e4e7;">
          <tr>
            <td style="padding:32px 32px 16px 32px;">
              <div style="font-size:24px;font-weight:700;color:#16a34a;letter-spacing:-0.4px;">Kazi Links</div>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 32px 0 32px;">
              <h1 style="font-size:22px;margin:0 0 12px 0;color:#0a0a0a;">Reset your password</h1>
              <p style="font-size:15px;line-height:1.55;color:#3f3f46;margin:0 0 20px 0;">
                Hi {safe_name}, we received a request to reset your Kazi Links password.
                Click the button below to choose a new one. This link expires in 30 minutes.
              </p>
              <div style="text-align:center;padding:8px 0 24px 0;">
                <a href="{reset_link}" style="display:inline-block;background:#16a34a;color:#ffffff;text-decoration:none;font-weight:600;padding:14px 28px;border-radius:10px;font-size:15px;">Reset Password</a>
              </div>
              <p style="font-size:13px;line-height:1.55;color:#71717a;margin:0 0 8px 0;">
                If the button doesn't work, copy and paste this link into your browser:
              </p>
              <p style="font-size:13px;line-height:1.55;color:#16a34a;word-break:break-all;margin:0 0 24px 0;">
                {reset_link}
              </p>
              <p style="font-size:13px;line-height:1.55;color:#71717a;margin:0 0 8px 0;">
                Didn't request this? You can safely ignore this email — your password won't change.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 32px;border-top:1px solid #e4e4e7;background:#fafafa;">
              <p style="font-size:12px;color:#a1a1aa;margin:0;">
                Kazi Links — Find skilled professionals near you.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
