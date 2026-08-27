# OSINT Hub — GitHub Module

Simple OSINT website starter focused on **GitHub**, built with **Python + FastAPI** and ready to host on **Railway.app**.

No auth required (60 req/hr via GitHub public API). Add `GITHUB_TOKEN` env var in Railway to get 5000/hr.

## Features (all requested)
- **Username lookup** — profile, bio, social links, repos, starred, followers/following, recent events + commit samples
- **Email finder** — extracts emails from git commits (real + `noreply.github.com`), across top repos
- **Repo analyzer** — stars, forks, languages, contributors, emails in commits, root file listing
- **Search** — users & repos (`/search/users`, `/search/repos`)
- **Network map** — followers / following / mutuals
- **Org lookup** — org meta + repos + members

## Quick start (local)
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# open http://localhost:8000
# docs: http://localhost:8000/docs
```

## Deploy to Railway
1. Push this folder to a GitHub repo
2. Railway → New Project → Deploy from GitHub
3. Builder: Dockerfile (auto-detected) or `railway.toml`
4. No env vars needed for MVP. Optional: `GITHUB_TOKEN=ghp_...`
5. Health check: `/api/health`

### Railway config
- `Dockerfile` + `railway.toml` + `Procfile` included.
- Uses `$PORT` automatically.

## API endpoints
```
GET /api/health
GET /api/modules
GET /api/github/user/{username}
GET /api/github/emails/{username}
GET /api/github/repo/{owner}/{repo}
GET /api/github/search/users?q=...
GET /api/github/search/repos?q=...
GET /api/github/network/{username}
GET /api/github/org/{org}
```

## Next modules (planned)
- Instagram, Domain/Whois, Email breach check — add under `/api/<module>/`

## Notes
- GitHub API without token = 60 requests/hour/IP. The frontend batches calls, so a single username lookup costs ~7-10 requests.
- To avoid noreply noise, emails are split into `real_emails` vs `noreply_emails`.
