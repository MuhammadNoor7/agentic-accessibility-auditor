# Free setup: SMTP OTP mail + Google Sign-In

Guide for teammates on branch `noor`. All steps below use **free** Google accounts (no paid Cloud billing required for this prototype).

Copy `.env.example` → `.env` at the repo root, then fill the values from this guide.  
**Never commit `.env`.** Only placeholders belong in `.env.example`.

---

## What you need

| Feature | Free service | Env vars |
|---------|--------------|----------|
| OTP / forgot-password email | Gmail + **App Password** | `SMTP_*` |
| Continue with Google | Google Cloud **OAuth Web client ID** | `GOOGLE_CLIENT_ID` |
| JWT sessions | Local secret string | `JWT_SECRET` |

Recipients can use **any email domain** (Yahoo, Outlook, university `.edu`, etc.).  
Only the **sending** account must be Gmail SMTP.

---

## 1. Gmail SMTP (OTP emails) — free

### 1.1 Use a Gmail account

1. Sign in at [https://mail.google.com](https://mail.google.com) (personal Gmail is fine).
2. You will send OTPs **from** this address.

### 1.2 Turn on 2-Step Verification

1. Open [Google Account → Security](https://myaccount.google.com/security).
2. Under **How you sign in to Google**, enable **2-Step Verification**.
3. Complete the setup (phone / prompt).

App Passwords only appear after 2-Step Verification is on.

### 1.3 Create a free App Password

1. Go to [App passwords](https://myaccount.google.com/apppasswords)  
   (or Security → 2-Step Verification → **App passwords**).
2. App name: e.g. `Axion Auditor SMTP`.
3. Click **Create**.
4. Google shows a **16-character password** (often shown in 4 groups).  
   Copy it once — you will not see it again.

This is **not** your normal Gmail login password. It is free and meant for apps like this.

### 1.4 Put values in `.env`

```env
SMTP_PROVIDER=gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=1
SMTP_USER=your-gmail@gmail.com
SMTP_FROM=your-gmail@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
AUTH_DEV_SHOW_OTP=0
```

| Variable | What to put |
|----------|-------------|
| `SMTP_USER` / `SMTP_FROM` | The same Gmail address |
| `SMTP_PASSWORD` | The 16-char App Password (spaces OK) |
| `AUTH_DEV_SHOW_OTP` | `0` once mail works (hides on-screen debug OTP). Use `1` only for local debugging without SMTP |

### 1.5 Restart the API

From repo root:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

`backend/main.py` loads `.env` with `override=True`, so restart (or rely on reload) after editing `.env`.

### 1.6 Quick test

1. Open Axion → **Forgot password** (or sign-up OTP flow).
2. Enter an email you can open (Yahoo / edu / Gmail all fine).
3. Check inbox (and spam) for the 6-digit code.
4. Optional local helper (repo): `python scripts/dev/_smtp_test_send.py` (uses your `.env`; do not commit secrets).

**Common errors**

| Symptom | Fix |
|---------|-----|
| `535 BadCredentials` | Wrong App Password, or 2-Step Verification off; create a **new** App Password |
| No email, but API returns OTP on screen | SMTP failed; set `AUTH_DEV_SHOW_OTP=1` only to debug, then fix SMTP and set back to `0` |
| Stale settings | Kill old uvicorn processes; confirm `.env` is in **repo root** |

---

## 2. Google Client ID (Sign-In) — free

Google Sign-In uses an **OAuth 2.0 Web client ID**. Creating one on Google Cloud is free for this student/demo usage.

### 2.1 Create / select a project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (e.g. `axion-auditor`) or select an existing one.  
   You do **not** need to enable billing for OAuth client IDs used this way.

### 2.2 Configure OAuth consent screen

1. **APIs & Services** → **OAuth consent screen**.
2. User type: **External** (for personal Gmail testing) → Create.
3. App name: e.g. `Axion Accessibility Auditor`.
4. User support email: your Gmail.
5. Developer contact: your Gmail.
6. Save. For local demo, **Testing** mode is enough; add your Google account under **Test users** if required.

### 2.3 Create OAuth Web Client ID

1. **APIs & Services** → **Credentials** → **Create credentials** → **OAuth client ID**.
2. Application type: **Web application**.
3. Name: e.g. `Axion Web`.
4. **Authorized JavaScript origins** (add what you use locally), for example:
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
5. **Authorized redirect URIs** (if asked; GIS often works with origins alone):
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
6. Create → copy the **Client ID**  
   (looks like `123456789-xxxx.apps.googleusercontent.com`).

You do **not** need the Client Secret for the GIS button + `POST /auth/google` ID-token flow used in this project.

### 2.4 Put Client ID in `.env`

```env
GOOGLE_CLIENT_ID=123456789-xxxx.apps.googleusercontent.com
```

Frontend reads config from the API (`GET /auth/config`) / env wiring used by `frontend/src/utils/googleAuth.js`.

Restart backend (and refresh the Vite app) after changing this.

### 2.5 Test Google Sign-In

1. `npm run dev` in `frontend/` → open Log In / Sign Up.
2. Click **Continue with Google**.
3. Pick a Google account (must be a test user if consent screen is in Testing).
4. You should land in the app with a JWT session.

**Common errors**

| Symptom | Fix |
|---------|-----|
| `origin_mismatch` / blocked | Add exact origin (`http://localhost:5173`) under Authorized JavaScript origins |
| Button missing / not configured | `GOOGLE_CLIENT_ID` empty → set it and restart API |
| Access blocked for other people | Consent screen Testing → add their Google email as test user, or publish the app later |

---

## 3. JWT secret

```env
JWT_SECRET=some-long-random-string-for-local-dev
```

Any long random string is fine for local/demo. Change it for any shared deployment.

---

## 4. Minimal `.env` checklist

```env
JWT_SECRET=change-me-in-production
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com

SMTP_PROVIDER=gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=1
SMTP_USER=your-gmail@gmail.com
SMTP_FROM=your-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
AUTH_DEV_SHOW_OTP=0
```

Optional frontend:

```env
# in frontend/.env if used
VITE_API_BASE=http://127.0.0.1:8000
```

---

## 5. Security (important)

- **Do** keep real App Passwords and secrets in **local `.env` only**.
- **Do not** paste App Passwords into Slack, commits, or `.env.example`.
- If an App Password was ever pushed to GitHub, **revoke it** in Google Account → App passwords and create a new one.
- `.env.example` in the repo is placeholders only — that is correct.

---

## 6. Related code / docs

| Path | Role |
|------|------|
| `backend/email_service.py` | Sends OTP via SMTP |
| `backend/otp_store.py` | Stores OTP codes + TTL |
| `backend/routers/auth_router.py` | `/auth/forgot-password`, `/auth/verify-otp`, `/auth/google`, … |
| `frontend/src/utils/googleAuth.js` | Google Identity Services button |
| `frontend/src/pages/auth/*` | Sign Up, Log In, Forgot, OTP, Reset |
| `scripts/dev/` | Optional local SMTP/auth smoke helpers |
| `README.md` | Project-wide quick start |

---

## 7. Cost summary

| Item | Cost |
|------|------|
| Gmail account | Free |
| App Password | Free |
| Google Cloud project + OAuth Web client ID | Free for this use |
| Sending OTP to Yahoo / edu / etc. | Free (normal Gmail send limits apply for demos) |

You do **not** need SendGrid, Mailgun, or a paid Google Workspace account for the internship prototype.
