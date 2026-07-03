# Axion Frontend — Phase 1 (Auth Flow)

React + Vite + Tailwind CSS v4 + React Router.

## What's in this phase

The 6 authentication screens, matching the Figma designs (dark navy branding
panel + white form panel), fully wired with routing and accessibility
features mapped to `Accessibility_Guidelines_Rules_v2`:

- `/signup` — Create your account
- `/login` — Log in
- `/forgot-password` — Forgot your password?
- `/verify-code` — 6-digit email verification (OTP)
- `/set-password` — Set a new password
- `/reset-success` — Password reset confirmation

`/dashboard`, `/upload`, and `/report` are placeholder routes — they'll be
built in the next phases.

## How to run it

You need Node.js installed (v18 or newer) — download from nodejs.org.

```bash
cd frontend
npm install
npm run dev
```

Then open the URL it prints (usually http://localhost:5173) in your
browser. It auto-reloads whenever you save a file.

To build a production version:

```bash
npm run build
```

This outputs static files to `dist/`, which you can deploy anywhere.

## Folder structure

```
src/
  components/
    ui/            Reusable pieces: Button, TextField, PasswordField,
                    OtpInput, FooterLink, Logo
    layout/        AuthLayout.jsx - shared two-panel layout for all auth screens
  pages/
    auth/           One file per auth screen
    main/           Placeholder.jsx for not-yet-built routes
  App.jsx           Route definitions (React Router)
  main.jsx          App entry point, wraps App in BrowserRouter
  index.css         Tailwind import + Axion color tokens (--color-*)
```

## Colors

All hex values from your Figma color doc are defined as CSS variables in
src/index.css under @theme, e.g. --color-navy: #0f1422,
--color-green: #1D9E75. Use them anywhere with
text-[var(--color-navy)], bg-[var(--color-green)], etc. - keeps every
screen consistent and makes future palette tweaks a one-line change.

## Accessibility features already implemented

Mapped from Accessibility_Guidelines_Rules_v2.docx:

| Guideline | How it's implemented |
| --- | --- |
| G01/G05 - labels | Every input has a real <label>, not just a placeholder |
| G04/G17 - touch targets | All buttons/inputs/toggle icons are >=48px tall |
| G21 - clear errors | Errors name the field and the fix, role="alert", aria-describedby |
| G22 - password toggle | Show/hide button on every password field, aria-pressed |
| G23 - nav controls | Back links have aria-label |
| G24 - screen titles | Every screen has a visible <h1> |
| Focus visibility | Global :focus-visible outline (not removed anywhere) |
| Color-only info | Errors always paired with icon + text, never color alone |

## Next steps

1. Review these 6 screens against Figma pixel-by-pixel and tell me any
   spacing/copy fixes.
2. I'll build Upload (5 states), Dashboard (+ issue detail), and Report
   (Audit History, Generate Report, PDF view) the same way.
3. Wire up real state management once Intern 1's XML parsing API and
   Intern 3's report JSON schema are ready - right now forms just navigate
   on submit with mock validation.
