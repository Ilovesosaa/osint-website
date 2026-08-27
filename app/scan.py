import asyncio
import re
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["scan"])

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

PLATFORMS = {
    "github": {"check": "status", "url": "https://github.com/{u}", "err": [404]},
    "twitter": {"check": "status", "url": "https://x.com/{u}", "err": [404]},
    "instagram": {"check": "status", "url": "https://www.instagram.com/{u}/", "err": [404]},
    "tiktok": {"check": "status", "url": "https://www.tiktok.com/@{u}", "err": [404]},
    "youtube": {"check": "status", "url": "https://www.youtube.com/@{u}", "err": [404]},
    "discord": {"check": "text", "url": "https://www.discord.com/users/{u}", "err": [], "exists_text": "Discord"},
    "reddit": {"check": "status", "url": "https://www.reddit.com/user/{u}", "err": [404]},
    "twitch": {"check": "status", "url": "https://www.twitch.tv/{u}", "err": [404]},
    "linkedin": {"check": "status", "url": "https://www.linkedin.com/in/{u}", "err": [404, 999]},
    "snapchat": {"check": "status", "url": "https://www.snapchat.com/add/{u}", "err": [404]},
    "pinterest": {"check": "status", "url": "https://www.pinterest.com/{u}/", "err": [404]},
    "tumblr": {"check": "status", "url": "https://{u}.tumblr.com", "err": [404]},
    "spotify": {"check": "status", "url": "https://open.spotify.com/user/{u}", "err": [404]},
    "soundcloud": {"check": "status", "url": "https://soundcloud.com/{u}", "err": [404]},
    "deviantart": {"check": "status", "url": "https://www.deviantart.com/{u}", "err": [404]},
    "flickr": {"check": "status", "url": "https://www.flickr.com/people/{u}", "err": [404]},
    "medium": {"check": "status", "url": "https://medium.com/@{u}", "err": [404]},
    "substack": {"check": "status", "url": "https://{u}.substack.com", "err": [404]},
    "npm": {"check": "status", "url": "https://www.npmjs.com/~{u}", "err": [404]},
    "dockerhub": {"check": "status", "url": "https://hub.docker.com/u/{u}", "err": [404]},
    "steam": {"check": "status", "url": "https://steamcommunity.com/id/{u}", "err": [404]},
    "roblox": {"check": "status", "url": "https://www.roblox.com/user.aspx?username={u}", "err": [404]},
    "xbox": {"check": "status", "url": "https://www.xbox.com/en-US/play/user/{u}", "err": [404]},
    "playstation": {"check": "status", "url": "https://psnprofiles.com/{u}", "err": [404]},
    "keybase": {"check": "status", "url": "https://keybase.io/{u}", "err": [404]},
    "aboutme": {"check": "status", "url": "https://about.me/{u}", "err": [404]},
    "gravatar": {"check": "status", "url": "https://en.gravatar.com/{u}", "err": [404]},
    "bitbucket": {"check": "status", "url": "https://bitbucket.org/{u}/", "err": [404]},
    "gitlab": {"check": "status", "url": "https://gitlab.com/{u}", "err": [404]},
    "codeberg": {"check": "status", "url": "https://codeberg.org/{u}", "err": [404]},
    "hackthebox": {"check": "status", "url": "https://app.hackthebox.com/profile/{u}", "err": [404]},
    "tryhackme": {"check": "status", "url": "https://tryhackme.com/p/{u}", "err": [404]},
    "hackerone": {"check": "status", "url": "https://hackerone.com/{u}", "err": [404]},
    "producthunt": {"check": "status", "url": "https://www.producthunt.com/@{u}", "err": [404]},
    "behance": {"check": "status", "url": "https://www.behance.net/{u}", "err": [404]},
    "dribbble": {"check": "status", "url": "https://dribbble.com/{u}", "err": [404]},
    "etsy": {"check": "status", "url": "https://www.etsy.com/people/{u}", "err": [404]},
    "ebay": {"check": "status", "url": "https://www.ebay.com/usr/{u}", "err": [404]},
    "goodreads": {"check": "status", "url": "https://www.goodreads.com/user/show/{u}", "err": [404]},
    "strava": {"check": "status", "url": "https://www.strava.com/athletes/{u}", "err": [404]},
    "kalshi": {"check": "status", "url": "https://kalshi.com/profile/{u}", "err": [404]},
    "myanimelist": {"check": "status", "url": "https://myanimelist.net/profile/{u}", "err": [404]},
    "letterboxd": {"check": "status", "url": "https://letterboxd.com/{u}", "err": [404]},
    "duolingo": {"check": "status", "url": "https://www.duolingo.com/profile/{u}", "err": [404]},
    "replit": {"check": "status", "url": "https://replit.com/@{u}", "err": [404]},
    "itch.io": {"check": "status", "url": "https://{u}.itch.io", "err": [404]},
    "chess.com": {"check": "status", "url": "https://www.chess.com/member/{u}", "err": [404]},
    "scratch": {"check": "status", "url": "https://scratch.mit.edu/users/{u}", "err": [404]},
    "archlinux": {"check": "status", "url": "https://bbs.archlinux.org/viewforum.php?id=57", "err": [404]},
    "kaggle": {"check": "status", "url": "https://www.kaggle.com/{u}", "err": [404]},
    "hackernews": {"check": "status", "url": "https://news.ycombinator.com/user?id={u}", "err": [404]},
    "4chan": {"check": "text", "url": "https://boards.4chan.org/u/{u}", "err": [], "exists_text": "No such user"},
}

PLATFORM_CATEGORIES = {
    "social": ["twitter", "instagram", "tiktok", "reddit", "tumblr", "snapchat", "pinterest", "discord"],
    "dev": ["github", "gitlab", "bitbucket", "codeberg", "npm", "dockerhub", "replit", "gitlab"],
    "gaming": ["steam", "roblox", "xbox", "playstation", "chess.com", "scratch", "itch.io"],
    "creative": ["youtube", "twitch", "deviantart", "behance", "dribbble", "flickr", "soundcloud", "medium", "substack", "letterboxd"],
    "professional": ["linkedin", "producthunt", "keybase", "aboutme", "gravatar", "kaggle", "hackernews"],
    "fitness": ["strava", "duolingo"],
    "music": ["spotify", "soundcloud"],
    "security": ["hackthebox", "tryhackme", "hackerone"],
}

async def check_platform(client: httpx.AsyncClient, username: str, platform: str, config: dict):
    url = config["url"].replace("{u}", username)
    try:
        r = await client.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        exists = False
        if config["check"] == "status":
            exists = r.status_code == 200
        elif config["check"] == "text":
            exists = config.get("exists_text", "") not in r.text[:5000]
        
        return {
            "platform": platform,
            "url": url,
            "status": "found" if exists else "not_found",
            "http_status": r.status_code,
        }
    except httpx.TimeoutException:
        return {"platform": platform, "url": url, "status": "timeout", "http_status": 0}
    except Exception as e:
        return {"platform": platform, "url": url, "status": "error", "http_status": 0, "error": str(e)[:100]}

@router.get("/scan/{username}")
async def scan_username(username: str):
    username = username.strip().lstrip("@")
    if not username or len(username) < 2:
        raise HTTPException(400, "Username must be at least 2 characters")

    async with httpx.AsyncClient() as client:
        tasks = [check_platform(client, username, name, cfg) for name, cfg in PLATFORMS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    found = []
    not_found = []
    errors = []
    for r in results:
        if isinstance(r, Exception):
            errors.append({"platform": "unknown", "status": "error", "error": str(r)[:100]})
        elif r["status"] == "found":
            found.append(r)
        elif r["status"] in ("timeout", "error"):
            errors.append(r)
        else:
            not_found.append(r)

    # Categorize found results
    categories = {}
    for cat, platforms_list in PLATFORM_CATEGORIES.items():
        cat_found = [r for r in found if r["platform"] in platforms_list]
        if cat_found:
            categories[cat] = cat_found

    return {
        "username": username,
        "total_platforms": len(PLATFORMS),
        "found_count": len(found),
        "not_found_count": len(not_found),
        "error_count": len(errors),
        "found": sorted(found, key=lambda x: x["platform"]),
        "not_found": sorted(not_found, key=lambda x: x["platform"]),
        "errors": errors,
        "categories": categories,
    }

@router.get("/platforms")
async def list_platforms():
    return {
        "total": len(PLATFORMS),
        "platforms": list(PLATFORMS.keys()),
        "categories": {k: v for k, v in PLATFORM_CATEGORIES.items()},
    }

@router.get("/health")
async def health():
    return {"status": "ok", "platforms": len(PLATFORMS)}
