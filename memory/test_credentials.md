# Test Credentials

## App Auth
- Admin: `admin@test.com` / `password`
- Client: `client@test.com` / `password`
- Professional: `pro@test.com` / `password`

## M-Pesa Daraja Sandbox
- Environment: `sandbox`
- Shortcode: `174379`
- Test phone (auto-cancel): `254708374149`
- Test phone (any number works in sandbox): `2547XXXXXXXX`
- Sandbox Passkey: `bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919`
- Consumer Key/Secret: stored in `/app/backend/.env` (do not commit)
- Callback URL: `{REACT_APP_BACKEND_URL}/api/mpesa/callback/{MPESA_CALLBACK_SECRET}`
