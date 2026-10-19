# Security Audit Report — Internal Portal

Application path: `/app`  
Audit date: 2026-05-21

## Summary

A comprehensive security review of the Flask internal portal identified multiple classes of web security vulnerabilities across the application's routes, middleware, session management, and output rendering. The application included a `sanitize_input()` function that provided inadequate XSS protection (only stripped `<script>` tags while leaving other vectors intact), a CSP that appeared semi-restrictive but contained `unsafe-inline` and `unsafe-eval`, completely unvalidated redirects, insecure session cookie defaults, and missing HTTP security headers. All issues were remediated while preserving existing functionality.

---

## 1. Reflected Cross-Site Scripting (XSS) via Inadequate Sanitization

**Severity:** High

**Root cause:** The `/search` route used a `sanitize_input()` function that only removed `<script>` tags. This failed to prevent XSS through other vectors such as `<img onerror=...>`, `<svg onload=...>`, event handlers, and many other HTML injection techniques. The sanitized output was embedded directly in HTML responses and in the `value` attribute of the search input field.

**Remediation:** Replaced the ineffective tag-stripping function with proper context-aware output escaping using `markupsafe.escape()`. All user-controlled values are now escaped before inclusion in HTML output. The flawed `sanitize_input()` function was removed entirely.

---

## 2. Stored Cross-Site Scripting (XSS) via Session Data

**Severity:** High

**Root cause:** User-supplied usernames stored in the Flask session were rendered without escaping across multiple routes: the dashboard (`/dashboard`), the home page index greeting (`/`), and the account settings page (`/settings`). An attacker who set a malicious username at login would have it rendered as raw HTML whenever the session data was displayed. The settings page compounded this by allowing the display name to be changed, creating an additional stored XSS path.

**Remediation:** Applied `markupsafe.escape()` to all session-derived values before HTML rendering in the dashboard, index, and settings views.

---

## 3. Unsafe Content Security Policy

**Severity:** Medium

**Root cause:** The CSP header appeared semi-restrictive with `default-src 'self'` but included `'unsafe-inline'` and `'unsafe-eval'` in `script-src`, and `'unsafe-inline'` in `style-src`. This largely negated XSS mitigation because injected inline scripts and eval-based payloads would still execute. The policy also referenced an external CDN domain that was not actually used by the application.

**Remediation:** Replaced with a strict CSP: `default-src 'self'`, `script-src 'self'` (no unsafe directives), `style-src 'self'`, limited `img-src`, `frame-ancestors 'none'`, and explicit `base-uri` / `form-action` restrictions. All unsafe directives and unnecessary external domains were removed.

---

## 4. Open Redirect

**Severity:** High

**Root cause:** The `/redirect` endpoint forwarded users to any URL passed in the `next` parameter without any validation, enabling phishing attacks via external URLs, protocol-relative URLs (`//evil.example/...`), and `javascript:` URIs.

**Remediation:** Implemented `is_safe_redirect()` with an allowlist approach: relative paths starting with a single `/` (rejecting `//`) are permitted, and absolute URLs must use `http` or `https` with a hostname in `TRUSTED_REDIRECT_HOSTS` (containing `example.com`). All other targets return HTTP 400.

---

## 5. Insecure Session Cookies

**Severity:** Medium

**Root cause:** `SESSION_COOKIE_HTTPONLY` was explicitly set to `False` and `SESSION_COOKIE_SAMESITE` was set to `None`, exposing session identifiers to JavaScript theft via XSS and leaving the application vulnerable to cross-site request forgery.

**Remediation:** Set `SESSION_COOKIE_HTTPONLY=True` and `SESSION_COOKIE_SAMESITE='Lax'`. Login responses now emit cookies with `HttpOnly` and `SameSite` attributes.

---

## 6. Missing HTTP Security Headers

**Severity:** Medium

**Root cause:** The application's `add_headers` middleware only set `Content-Security-Policy` and `X-Content-Type-Options`. It was missing standard hardening headers for clickjacking protection, referrer information control, and browser feature restrictions. The partial coverage gave a false impression of security.

**Remediation:** Centralized all security headers in the `@app.after_request` hook: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Permissions-Policy: geolocation=(), microphone=(), camera=()`.

---

## 7. Reflected Path in 404 Error Handler

**Severity:** Low

**Root cause:** The custom 404 error handler reflected the requested path (`request.path`) directly into the HTML response without escaping. While Flask's built-in routing limits what characters reach this handler, it could still expose the application to XSS if a crafted URL bypassed those limits.

**Remediation:** Applied `markupsafe.escape()` to the reflected path in the error handler output.

---

## Verification

Automated tests under `/app/tests` verify escaped search output, escaped session data in dashboard/settings/index, redirect rejection and allowance, cookie flags, CSP restrictiveness, and presence of all security headers. Harbor verifier tests in `/tests/test_outputs.py` provide additional integration checks.
