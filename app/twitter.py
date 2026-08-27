import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/twitter", tags=["twitter"])

TW_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

@router.get("/health")
async def health():
    return {"status": "ok", "module": "twitter"}

@router.get("/user/{username}")
async def get_user(username: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Method 1: Twitter syndication API (public, limited)
        try:
            r = await client.get(
                f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}",
                headers=TW_HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                text = r.text
                exists = "protected" in text or f'@{username}' in text.lower() or username.lower() in text.lower()
                if exists:
                    return {
                        "platform": "twitter",
                        "username": username,
                        "found": True,
                        "profile": {
                            "username": username,
                            "url": f"https://x.com/{username}",
                            "mobile_url": f"https://mobile.twitter.com/{username}",
                        },
                        "stats": {},
                        "note": "Limited data from syndication API. Twitter/X requires auth for full API.",
                        "risk": {},
                    }
        except Exception:
            pass

        # Method 2: Try usercypher or similar public endpoints
        try:
            r = await client.get(
                f"https://twstalker.com/{username}",
                headers=TW_HEADERS,
                timeout=15,
            )
            if r.status_code == 200 and username.lower() in r.text.lower():
                return {
                    "platform": "twitter",
                    "username": username,
                    "found": True,
                    "profile": {
                        "username": username,
                        "url": f"https://x.com/{username}",
                    },
                    "stats": {},
                    "note": "Profile exists - full data requires Twitter API v2 auth",
                }
        except Exception:
            pass

        # Method 3: Nitter instances (public Twitter frontend)
        nitter_instances = [
            "https://nitter.privacydev.net",
            "https://nitter.poast.org",
            "https://nitter.cz",
        ]
        for nitter in nitter_instances:
            try:
                r = await client.get(f"{nitter}/{username}", headers=TW_HEADERS, timeout=10)
                if r.status_code == 200:
                    text = r.text
                    if "not found" not in text.lower()[:2000]:
                        # Extract what we can
                        import re
                        bio = ""
                        bio_match = re.search(r'class="profile-bio">(.*?)</p>', text, re.DOTALL)
                        if bio_match:
                            bio = bio_match.group(1).strip().replace('<span class="display-username">','').replace('</span>','').replace('<br/>','')
                        followers = ""
                        f_match = re.search(r'(\d[\d,]*)\s*Followers', text)
                        if f_match:
                            followers = f_match.group(1)
                        return {
                            "platform": "twitter",
                            "username": username,
                            "found": True,
                            "profile": {
                                "username": username,
                                "bio": bio,
                                "url": f"https://x.com/{username}",
                                "nitter_url": f"{nitter}/{username}",
                            },
                            "stats": {"followers": followers},
                            "note": f"Data via Nitter ({nitter})",
                        }
            except Exception:
                continue

        raise HTTPException(404, "Twitter/X user not found. Twitter API requires authentication for most data.")

@router.get("/search")
async def search(q: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = []
        # Try nitter search
        nitter_instances = ["https://nitter.privacydev.net", "https://nitter.cz"]
        for nitter in nitter_instances:
            try:
                r = await client.get(f"{nitter}/search", params={"f": "users", "q": q}, headers=TW_HEADERS, timeout=10)
                if r.status_code == 200:
                    import re
                    users = re.findall(r'class="username"[^>]*>@?(\w+)', r.text)
                    results = [{"username": u, "url": f"https://x.com/{u}"} for u in users[:10]]
                    if results:
                        break
            except Exception:
                continue
        return {"platform": "twitter", "query": q, "results": results, "note": "Limited - Twitter API requires auth"}
