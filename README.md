# OSINT Hub

Multi-platform OSINT dashboard. Search usernames across 100+ platforms, check emails for registrations, look up IPs, domains, phone numbers, crypto wallets, and more.

**No API keys required.** All lookups use public endpoints.

## Features

- **Username Search** — 100+ platforms (GitHub, Twitter, Instagram, TikTok, Discord, Steam, Roblox, etc.)
- **Email → Accounts** — Holehe-style: find where an email is registered
- **Email Lookup** — MX records, DNS security, disposable check, Gravatar
- **Breach Check** — Check if email appears in known data breaches
- **IP Lookup** — Geolocation, ASN, blacklist checks, abuse flags
- **Domain Lookup** — DNS records, SSL certs, subdomain enumeration, tech detection
- **Phone Lookup** — Carrier, location, line type
- **Crypto Wallet** — Balance lookup for ETH, BTC, TRX
- **Wayback Machine** — Historical snapshots
- **URL Unfurl** — Metadata extraction (title, description, OG tags, tech stack)
- **Gaming** — Steam, Roblox, Xbox, PlayStation profiles

## Deploy to Railway

1. Push this repo to GitHub
2. Railway → New Project → Deploy from GitHub
3. Auto-detects Dockerfile
4. Done

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# http://localhost:8000
```

## Tech

- Python 3.11 + FastAPI
- httpx for async HTTP
- Vanilla JS frontend (no framework)
- Tailwind-free dark UI
- Docker + Railway ready
