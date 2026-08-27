import re
import asyncio
from typing import Optional
import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/github", tags=["github"])

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "OSINT-Website/1.0"
}

# Optional token - will use if env var set later, but not required now
import os
def get_headers():
    h = HEADERS.copy()
    token = os.getenv("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"token {token}"
    return h

async def gh_get(client: httpx.AsyncClient, path: str, params=None):
    url = f"{GITHUB_API}{path}"
    r = await client.get(url, headers=get_headers(), params=params, timeout=15)
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    if r.status_code == 403:
        # rate limited
        raise HTTPException(status_code=429, detail=f"GitHub rate limited (60/hr without token). Try adding GITHUB_TOKEN. Body: {r.text[:300]}")
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text[:500])
    return r.json(), dict(r.headers)

@router.get("/health")
async def health():
    return {"status": "ok", "module": "github"}

@router.get("/user/{username}")
async def get_user(username: str):
    """Full OSINT profile for a username: profile + repos + orgs + starred + followers sample + events"""
    async with httpx.AsyncClient() as client:
        # fetch in parallel where possible
        profile, _ = await gh_get(client, f"/users/{username}")
        
        # parallel fetch others - ignore failures
        async def safe_get(path, params=None):
            try:
                data, headers = await gh_get(client, path, params)
                return data, headers
            except HTTPException as e:
                return None, {}

        repos, orgs, starred, followers, following, events = await asyncio.gather(
            safe_get(f"/users/{username}/repos", {"per_page": 100, "sort": "updated"}),
            safe_get(f"/users/{username}/orgs"),
            safe_get(f"/users/{username}/starred", {"per_page": 20}),
            safe_get(f"/users/{username}/followers", {"per_page": 30}),
            safe_get(f"/users/{username}/following", {"per_page": 30}),
            safe_get(f"/users/{username}/events/public", {"per_page": 30}),
        )
        
        # Extract emails from patch data via events -> commits
        emails = set()
        commit_samples = []
        if events[0]:
            for ev in events[0][:15]:
                if ev.get("type") == "PushEvent":
                    for c in ev.get("payload", {}).get("commits", [])[:5]:
                        # GitHub API doesn't give email in public events, but message is there
                        commit_samples.append({"repo": ev.get("repo", {}).get("name"), "message": c.get("message"), "sha": c.get("sha")})
                # also check for generic
                if ev.get("actor", {}).get("login") == username:
                    pass

        # Try to get emails via fetching patch of recent commits across top repos
        # Limit to 3 repos to stay under rate limit
        if repos[0]:
            top_repos = sorted(repos[0], key=lambda x: x.get("stargazers_count",0), reverse=True)[:3]
            for repo in top_repos:
                owner = repo["owner"]["login"]
                name = repo["name"]
                try:
                    commits, _ = await gh_get(client, f"/repos/{owner}/{name}/commits", {"per_page": 5, "author": username})
                    for commit in commits:
                        c = commit.get("commit", {})
                        author = c.get("author", {})
                        committer = c.get("committer", {})
                        for p in [author, committer]:
                            email = p.get("email")
                            if email and "noreply.github.com" not in email:
                                emails.add(email)
                            elif email and "noreply.github.com" in email:
                                # still useful: reveals GitHub username pattern
                                emails.add(email)
                        # also store commit sample
                        commit_samples.append({
                            "repo": f"{owner}/{name}",
                            "message": c.get("message","")[:120],
                            "author_email": author.get("email"),
                            "date": author.get("date")
                        })
                except:
                    continue

        # Social footprint
        social = {
            "blog": profile.get("blog"),
            "twitter": profile.get("twitter_username"),
            "company": profile.get("company"),
            "location": profile.get("location"),
            "email_public": profile.get("email"),
            "hireable": profile.get("hireable"),
        }

        return {
            "profile": profile,
            "social_footprint": social,
            "emails_found": sorted(list(emails)),
            "repos": repos[0] if repos[0] else [],
            "repos_count": len(repos[0]) if repos[0] else 0,
            "orgs": orgs[0] if orgs[0] else [],
            "starred": starred[0] if starred[0] else [],
            "followers_sample": followers[0] if followers[0] else [],
            "following_sample": following[0] if following[0] else [],
            "recent_events": events[0][:10] if events[0] else [],
            "commit_samples": commit_samples[:10],
            "osint_summary": {
                "username": profile.get("login"),
                "name": profile.get("name"),
                "created_at": profile.get("created_at"),
                "public_repos": profile.get("public_repos"),
                "followers": profile.get("followers"),
                "following": profile.get("following"),
                "is_site_admin": profile.get("site_admin"),
                "type": profile.get("type"),
            }
        }

@router.get("/search/users")
async def search_users(q: str = Query(..., description="Search query e.g. john or john location:germany"), per_page: int = 10):
    async with httpx.AsyncClient() as client:
        data, headers = await gh_get(client, "/search/users", {"q": q, "per_page": per_page})
        return data

@router.get("/search/repos")
async def search_repos(q: str = Query(..., description="Search repos e.g. osint language:python"), per_page: int = 10, sort: str = "stars"):
    async with httpx.AsyncClient() as client:
        data, headers = await gh_get(client, "/search/repositories", {"q": q, "per_page": per_page, "sort": sort})
        return data

@router.get("/repo/{owner}/{repo}")
async def repo_analyzer(owner: str, repo: str):
    """Deep repo OSINT: metadata + contributors + languages + commits + forks"""
    async with httpx.AsyncClient() as client:
        meta, _ = await gh_get(client, f"/repos/{owner}/{repo}")
        
        async def safe(path, params=None):
            try:
                d,_ = await gh_get(client, path, params)
                return d
            except:
                return None

        contributors, languages, commits, forks, readme = await asyncio.gather(
            safe(f"/repos/{owner}/{repo}/contributors", {"per_page": 20}),
            safe(f"/repos/{owner}/{repo}/languages"),
            safe(f"/repos/{owner}/{repo}/commits", {"per_page": 10}),
            safe(f"/repos/{owner}/{repo}/forks", {"per_page": 10}),
            safe(f"/repos/{owner}/{repo}/readme"),
        )

        # email extraction from commits
        emails = set()
        if commits:
            for c in commits:
                commit = c.get("commit", {})
                for field in [commit.get("author", {}), commit.get("committer", {})]:
                    email = field.get("email")
                    if email:
                        emails.add(email)

        # detect leaked secrets patterns in filenames? quick check via file list
        # fetch contents root
        contents = await safe(f"/repos/{owner}/{repo}/contents", {"per_page": 100})

        return {
            "meta": meta,
            "contributors": contributors,
            "languages": languages,
            "commit_samples": commits[:5] if commits else [],
            "emails_in_commits": sorted(list(emails)),
            "forks_sample": forks,
            "contents_sample": contents[:20] if isinstance(contents, list) else contents,
            "readme_truncated": readme.get("content", "")[:500] if readme and isinstance(readme, dict) else None,
        }

@router.get("/emails/{username}")
async def email_finder(username: str):
    """Dedicated email finder: aggregates emails from commit patches across user's repos"""
    async with httpx.AsyncClient() as client:
        # get repos
        try:
            repos, _ = await gh_get(client, f"/users/{username}/repos", {"per_page": 30, "sort": "updated"})
        except HTTPException as e:
            raise e
        
        emails = set()
        noreply = set()
        details = []
        
        # check up to 5 repos
        for repo in repos[:5]:
            owner = repo["owner"]["login"]
            name = repo["name"]
            try:
                commits, _ = await gh_get(client, f"/repos/{owner}/{name}/commits", {"per_page": 10, "author": username})
                for c in commits:
                    commit_data = c.get("commit", {})
                    author = commit_data.get("author", {})
                    committer = commit_data.get("committer", {})
                    for p in [author, committer]:
                        email = p.get("email", "")
                        if email:
                            if "noreply.github.com" in email:
                                noreply.add(email)
                            else:
                                emails.add(email)
                            details.append({
                                "repo": f"{owner}/{name}",
                                "sha": c.get("sha","")[:7],
                                "email": email,
                                "name": p.get("name"),
                                "date": p.get("date"),
                                "message": commit_data.get("message","")[:100]
                            })
            except:
                continue
        
        # also try patch via events as fallback
        return {
            "username": username,
            "real_emails": sorted(list(emails)),
            "noreply_emails": sorted(list(noreply)),
            "all_emails": sorted(list(emails | noreply)),
            "details": details[:20],
            "note": "noreply.github.com emails are anonymized but still leak username pattern. Real emails only appear if user didn't hide email in git config."
        }

@router.get("/network/{username}")
async def network_map(username: str):
    """Follower / following graph for OSINT pivoting"""
    async with httpx.AsyncClient() as client:
        profile, _ = await gh_get(client, f"/users/{username}")
        followers, _ = await gh_get(client, f"/users/{username}/followers", {"per_page": 50})
        following, _ = await gh_get(client, f"/users/{username}/following", {"per_page": 50})
        
        # mutuals
        follower_logins = set(f["login"] for f in followers)
        following_logins = set(f["login"] for f in following)
        mutuals = list(follower_logins & following_logins)
        
        return {
            "profile": {"login": profile["login"], "followers": profile["followers"], "following": profile["following"]},
            "followers": followers,
            "following": following,
            "mutuals": mutuals,
            "mutuals_count": len(mutuals),
            "followers_count": len(followers),
            "following_count": len(following),
        }

@router.get("/org/{org}")
async def org_lookup(org: str):
    async with httpx.AsyncClient() as client:
        meta, _ = await gh_get(client, f"/orgs/{org}")
        repos, _ = await gh_get(client, f"/orgs/{org}/repos", {"per_page": 20})
        members = None
        try:
            members, _ = await gh_get(client, f"/orgs/{org}/members", {"per_page": 20})
        except:
            members = {"note": "members hidden or requires auth"}
        return {"org": meta, "repos": repos, "members": members}
