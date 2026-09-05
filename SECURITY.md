# HARSH TRADER AI — Security Architecture & Prompt Protection

## 1. Secrets & Credentials Policy
- Zero secrets committed to source control. `.env` is listed in `.gitignore`.
- Production API keys (OpenAI, Anthropic, Gemini, Market Data, WhatsApp) are resolved strictly via environment variables.

## 2. News Prompt Injection Defense
News stories are retrieved as raw untrusted external data. The `NewsAgent` cleans all news input:
- Sanitizes prompt injection patterns (e.g. "ignore previous instructions", "system prompt override").
- Restricts credibility scope to verified sources (`HIGH` / `MEDIUM`).
- External news content CANNOT override system instructions or hard rejection rules.

## 3. Signal Fingerprinting & Idempotency
- Trade signals generate a SHA-256 fingerprint hash based on symbol, mode, direction, setup, entry price, and trading session date.
- Duplicate alerts and WhatsApp messages are automatically blocked via idempotency keys.
