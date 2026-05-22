# Test Credentials

## App Auth
- Admin: `admin@kazilinks.com` / `password` (legacy admins also exist: admin023219@test.com)
- Client: `client@test.com` / `password`
- Professional: `pro@test.com` / `password`

## M-Pesa Daraja Sandbox
- Environment: `sandbox`
- Shortcode: `174379`
- Test phone (auto-cancel): `254708374149`
- Sandbox Passkey: `bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919`
- Consumer Key/Secret: stored in `/app/backend/.env` (do not commit)
- Callback URL: `{REACT_APP_BACKEND_URL}/api/mpesa/callback/{MPESA_CALLBACK_SECRET}`

## Resend (Forgot Password Emails)
- API key not yet provided by user — set via `RESEND_API_KEY` in `/app/backend/.env`
- Sender: `onboarding@resend.dev` (Resend's sandbox sender — only sends to your own verified email until you add a custom domain)
- While unconfigured, the reset link is logged to `/var/log/supervisor/backend.err.log` (DEV-only fallback) and the user gets a generic success message.

## Object Storage
- Auto-initialized at startup using `EMERGENT_LLM_KEY`
- Chat attachments path: `kazi-links/chat/{user_id}/{uuid}.{ext}`
