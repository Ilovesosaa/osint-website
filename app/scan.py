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

# 160+ platforms pulled from Sherlock, Blackbird, NExfil, OSINTsweep, NebulaOSINT
PLATFORMS = {
    # === SOCIAL MEDIA ===
    "twitter": {"url": "https://x.com/{u}"},
    "instagram": {"url": "https://www.instagram.com/{u}/"},
    "facebook": {"url": "https://www.facebook.com/{u}"},
    "tiktok": {"url": "https://www.tiktok.com/@{u}"},
    "snapchat": {"url": "https://www.snapchat.com/add/{u}"},
    "pinterest": {"url": "https://www.pinterest.com/{u}/"},
    "tumblr": {"url": "https://{u}.tumblr.com"},
    "reddit": {"url": "https://www.reddit.com/user/{u}"},
    "discord": {"url": "https://www.discord.com/users/{u}"},
    "linkedin": {"url": "https://www.linkedin.com/in/{u}"},
    "mastodon": {"url": "https://mastodon.social/@{u}"},
    "bluesky": {"url": "https://bsky.app/profile/{u}"},
    "threads": {"url": "https://www.threads.net/@{u}"},
    "truthsocial": {"url": "https://truthsocial.com/@{u}"},
    "parler": {"url": "https://parler.com/profile/{u}"},
    "gab": {"url": "https://gab.com/{u}"},
    "gettr": {"url": "https://www.gettr.com/user/{u}"},
    "minds": {"url": "https://www.minds.com/{u}"},
    "diaspora": {"url": "https://diasp.org/u/{u}"},
    "weverse": {"url": "https://weverse.onelink.me/weverse/deeplink"},
    "substack": {"url": "https://{u}.substack.com"},
    "medium": {"url": "https://medium.com/@{u}"},
    "quora": {"url": "https://www.quora.com/profile/{u}"},
    "facebook_pages": {"url": "https://www.facebook.com/pages/{u}"},

    # === VIDEO / STREAMING ===
    "youtube": {"url": "https://www.youtube.com/@{u}"},
    "twitch": {"url": "https://www.twitch.tv/{u}"},
    "vimeo": {"url": "https://vimeo.com/{u}"},
    "dailymotion": {"url": "https://www.dailymotion.com/{u}"},
    "rumble": {"url": "https://rumble.com/c/{u}"},
    "odysee": {"url": "https://odysee.com/@{u}"},
    "bitchute": {"url": "https://www.bitchute.com/channel/{u}"},
    "newgrounds": {"url": "https://{u}.newgrounds.com"},
    "dailymotion": {"url": "https://www.dailymotion.com/{u}"},

    # === MUSIC ===
    "spotify": {"url": "https://open.spotify.com/user/{u}"},
    "soundcloud": {"url": "https://soundcloud.com/{u}"},
    "lastfm": {"url": "https://www.last.fm/user/{u}"},
    "bandcamp": {"url": "{u}.bandcamp.com"},
    "mixcloud": {"url": "https://www.mixcloud.com/{u}/"},
    "reverbnation": {"url": "https://www.reverbnation.com/{u}"},

    # === DEVELOPMENT ===
    "github": {"url": "https://github.com/{u}"},
    "gitlab": {"url": "https://gitlab.com/{u}"},
    "bitbucket": {"url": "https://bitbucket.org/{u}/"},
    "codeberg": {"url": "https://codeberg.org/{u}"},
    "npm": {"url": "https://www.npmjs.com/~{u}"},
    "pypi": {"url": "https://pypi.org/user/{u}/"},
    "dockerhub": {"url": "https://hub.docker.com/u/{u}"},
    "crates.io": {"url": "https://crates.io/users/{u}"},
    "rubygems": {"url": "https://rubygems.org/profiles/{u}"},
    "packagist": {"url": "https://packagist.org/@{u}"},
    "replit": {"url": "https://replit.com/@{u}"},
    "codepen": {"url": "https://codepen.io/{u}"},
    "codesandbox": {"url": "https://codesandbox.io/u/{u}"},
    "jsfiddle": {"url": "https://jsfiddle.net/user/{u}/"},
    "glitch": {"url": "https://glitch.com/@{u}"},
    "observable": {"url": "https://observablehq.com/@{u}"},
    "devto": {"url": "https://dev.to/{u}"},
    "hashnode": {"url": "https://hashnode.com/@{u}"},
    "stackoverflow": {"url": "https://stackoverflow.com/users/?tab=Accounts"},
    "stackexchange": {"url": "https://stackexchange.com/users/{u}"},
    "hackerrank": {"url": "https://www.hackerrank.com/{u}"},
    "leetcode": {"url": "https://leetcode.com/{u}/"},
    "codewars": {"url": "https://www.codewars.com/users/{u}"},
    "codeforces": {"url": "https://codeforces.com/profile/{u}"},
    "kaggle": {"url": "https://www.kaggle.com/{u}"},
    "topcoder": {"url": "https://www.topcoder.com/members/profile/{u}"},
    "exercism": {"url": "https://exercism.org/profiles/{u}"},
    "huggingface": {"url": "https://huggingface.co/{u}"},

    # === GAMING ===
    "steam": {"url": "https://steamcommunity.com/id/{u}"},
    "roblox": {"url": "https://www.roblox.com/user.aspx?username={u}"},
    "xbox": {"url": "https://www.xboxgamertag.com/search/{u}"},
    "playstation": {"url": "https://psnprofiles.com/{u}"},
    "epicgames": {"url": "https://www.epicgames.com/site/en-US/home"},
    "nintendo": {"url": "https://www.nintendo.com/us/search/#q={u}"},
    "chess.com": {"url": "https://www.chess.com/member/{u}"},
    "lichess": {"url": "https://lichess.org/@/{u}"},
    "scratch": {"url": "https://scratch.mit.edu/users/{u}"},
    "itch.io": {"url": "https://{u}.itch.io"},
    "faceit": {"url": "https://www.faceit.com/en/players/{u}"},
    "op.gg": {"url": "https://www.op.gg/summoners/kr/{u}"},
    "valorant": {"url": "https://tracker.gg/valorant/profile/riot/{u}/overview"},
    "fortnite": {"url": "https://fortnitetracker.com/profile/all/{u}"},
    "apexlegends": {"url": "https://apex.tracker.gg/profile/pc/{u}"},
    "warzone": {"url": "https://tracker.gg/warzone/profile/atvi/{u}/overview"},
    "minecraft": {"url": "https://namemc.com/profile/{u}"},

    # === CREATIVE ===
    "behance": {"url": "https://www.behance.net/{u}"},
    "dribbble": {"url": "https://dribbble.com/{u}"},
    "deviantart": {"url": "https://www.deviantart.com/{u}"},
    "artstation": {"url": "https://www.artstation.com/{u}"},
    "flickr": {"url": "https://www.flickr.com/people/{u}"},
    "500px": {"url": "https://500px.com/p/{u}"},
    "unsplash": {"url": "https://unsplash.com/@{u}"},
    "canva": {"url": "https://www.canva.com/{u}"},
    "redbubble": {"url": "https://www.redbubble.com/people/{u}"},
    "furaffinity": {"url": "https://www.furaffinity.net/user/{u}"},
    "newgrounds": {"url": "https://{u}.newgrounds.com"},

    # === BLOGGING / WRITING ===
    "wordpress": {"url": "https://{u}.wordpress.com"},
    "ghost": {"url": "https://{u}.ghost.io"},
    "blogger": {"url": "https://{u}.blogspot.com"},
    "livejournal": {"url": "https://{u}.livejournal.com"},
    "wattpad": {"url": "https://www.wattpad.com/user/{u}"},
    "archiveofourown": {"url": "https://archiveofourown.org/users/{u}"},
    "fanfiction": {"url": "https://www.fanfiction.net/u/{u}"},
    "royalroad": {"url": "https://www.royalroad.com/profile/{u}"},

    # === PROFESSIONAL ===
    "aboutme": {"url": "https://about.me/{u}"},
    "keybase": {"url": "https://keybase.io/{u}"},
    "gravatar": {"url": "https://en.gravatar.com/{u}"},
    "producthunt": {"url": "https://www.producthunt.com/@{u}"},
    "angelist": {"url": "https://angel.co/u/{u}"},
    "wellfound": {"url": "https://wellfound.com/u/{u}"},

    # === FINANCE / CRYPTO ===
    "patreon": {"url": "https://www.patreon.com/{u}"},
    "buymeacoffee": {"url": "https://www.buymeacoffee.com/{u}"},
    "kofi": {"url": "https://ko-fi.com/{u}"},
    "liberapay": {"url": "https://liberapay.com/{u}"},
    "venmo": {"url": "https://venmo.com/{u}"},
    "cashapp": {"url": "https://cash.app/${u}"},
    "onlyfans": {"url": "https://onlyfans.com/{u}"},
    "fansly": {"url": "https://fansly.com/{u}"},

    # === FITNESS / LIFESTYLE ===
    "strava": {"url": "https://www.strava.com/athletes/{u}"},
    "myfitnesspal": {"url": "https://www.myfitnesspal.com/profile/{u}"},
    "goodreads": {"url": "https://www.goodreads.com/user/show/{u}"},
    "letterboxd": {"url": "https://letterboxd.com/{u}"},
    "trakt": {"url": "https://trakt.tv/users/{u}"},
    "imdb": {"url": "https://www.imdb.com/user/{u}"},
    "duolingo": {"url": "https://www.duolingo.com/profile/{u}"},
    "myanimelist": {"url": "https://myanimelist.net/profile/{u}"},
    "anilist": {"url": "https://anilist.co/user/{u}"},
    "mal": {"url": "https://myanimelist.net/profile/{u}"},
    "trakt": {"url": "https://trakt.tv/users/{u}"},

    # === SHOPPING / MARKETPLACE ===
    "etsy": {"url": "https://www.etsy.com/people/{u}"},
    "ebay": {"url": "https://www.ebay.com/usr/{u}"},
    "amazon_wishlist": {"url": "https://www.amazon.com/hz/wishlist/ls/{u}"},
    "mercartari": {"url": "https://www.mercari.com/u/{u}"},
    "poshmark": {"url": "https://poshmark.com/closet/{u}"},

    # === SECURITY ===
    "hackthebox": {"url": "https://app.hackthebox.com/profile/{u}"},
    "tryhackme": {"url": "https://tryhackme.com/p/{u}"},
    "hackerone": {"url": "https://hackerone.com/{u}"},
    "bugcrowd": {"url": "https://bugcrowd.com/{u}"},
    "rootme": {"url": "https://www.root-me.org/{u}"},
    "hackforums": {"url": "https://hackforums.net/member.php?username={u}"},
    "cracked.io": {"url": "https://cracked.io/{u}"},
    "virusbay": {"url": "https://virusbay.io/user/{u}"},
    "virustotal": {"url": "https://www.virustotal.com/gui/user/{u}"},
    "urlscan": {"url": "https://urlscan.io/user/{u}/"},
    "anyrun": {"url": "https://app.any.run/profile/{u}"},

    # === CLOUD / HOSTING ===
    "vercel": {"url": "https://vercel.com/{u}"},
    "netlify": {"url": "https://app.netlify.com/teams/{u}"},
    "heroku": {"url": "https://dashboard.heroku.com/apps/{u}"},
    "digitalocean": {"url": "https://www.digitalocean.com/community/users/{u}"},
    "vultr": {"url": "https://www.vultr.com/user/{u}"},

    # === FORUMS / COMMUNITY ===
    "hackernews": {"url": "https://news.ycombinator.com/user?id={u}"},
    "4chan": {"url": "https://boards.4chan.org/u/{u}"},
    "420chan": {"url": "https://www.420chan.org/u/{u}"},
    "reddit": {"url": "https://www.reddit.com/user/{u}"},
    "steemit": {"url": "https://steemit.com/@{u}"},
    "lobste.rs": {"url": "https://lobste.rs/u/{u}"},
    "discourse": {"url": "https://discourse.org/u/{u}"},
    "xda": {"url": "https://forum.xda-developers.com/member.php?u={u}"},

    # === CHINESE PLATFORMS ===
    "zhihu": {"url": "https://www.zhihu.com/people/{u}"},
    "juejin": {"url": "https://juejin.cn/user/{u}"},
    "douban": {"url": "https://www.douban.com/people/{u}"},
    "bilibili": {"url": "https://space.bilibili.com/{u}"},
    "weibo": {"url": "https://weibo.com/{u}"},
    "nga": {"url": "https://nga.178.com/threads.php?fid={u}"},

    # === MISC ===
    "gravatar": {"url": "https://en.gravatar.com/{u}"},
    "bitly": {"url": "https://bit.ly/{u}"},
    "kalshi": {"url": "https://kalshi.com/profile/{u}"},
    "notion": {"url": "https://www.notion.so/{u}"},
    "airtable": {"url": "https://airtable.com/{u}"},
    "trello": {"url": "https://trello.com/{u}"},
    "zapier": {"url": "https://zapier.com/app/profile/{u}"},
}

# === NAME SEARCH - Google/Bing dorking for real names ===
async def name_search(client, name):
    results = []
    queries = [
        f'"{name}" site:linkedin.com/in',
        f'"{name}" site:twitter.com OR site:x.com',
        f'"{name}" site:facebook.com',
        f'"{name}" site:instagram.com',
        f'"{name}" site:github.com',
        f'"{name}" site:youtube.com',
    ]
    for q in queries[:3]:
        try:
            r = await client.get(
                f"https://html.duckduckgo.com/html/",
                params={"q": q},
                headers=HEADERS,
                timeout=10,
            )
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]+)"', r.text)
                for link in links[:5]:
                    if any(s in link for s in ["linkedin","twitter","x.com","facebook","instagram","github","youtube"]):
                        results.append({"url": link, "query": q})
        except:
            pass
    return results

# === PERSON SEARCH - combined email + phone + username ===
@router.get("/person/{query}")
async def person_search(query: str):
    query = query.strip()
    results = {"query": query, "type": None, "email_results": None, "username_results": None, "phone_results": None}

    if "@" in query and "." in query.split("@")[1]:
        results["type"] = "email"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"http://localhost:8000/api/email/{query}", timeout=30)
                if r.status_code == 200:
                    results["email_results"] = r.json()
        except:
            pass
    elif query.startswith("+") or (query.replace(" ","").replace("-","").isdigit() and len(query.replace(" ","").replace("-","")) > 7):
        results["type"] = "phone"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"http://localhost:8000/api/phone/{query}", timeout=15)
                if r.status_code == 200:
                    results["phone_results"] = r.json()
        except:
            pass
    else:
        results["type"] = "username"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"http://localhost:8000/api/scan/{query}", timeout=60)
                if r.status_code == 200:
                    results["username_results"] = r.json()
        except:
            pass

    return results


PLATFORM_CATEGORIES = {
    "social": ["twitter","instagram","facebook","tiktok","reddit","tumblr","snapchat","pinterest","discord","linkedin","mastodon","bluesky","threads","truthsocial","parler","gab","gettr","minds","diaspora"],
    "video": ["youtube","twitch","vimeo","dailymotion","rumble","odysee","bitchute"],
    "dev": ["github","gitlab","bitbucket","codeberg","npm","pypi","dockerhub","crates.io","rubygems","packagist","replit","codepen","codesandbox","jsfiddle","glitch","observable","devto","hashnode","stackoverflow","hackerrank","leetcode","codewars","codeforces","kaggle","topcoder","exercism","huggingface"],
    "gaming": ["steam","roblox","xbox","playstation","epicgames","chess.com","lichess","scratch","itch.io","faceit","op.gg","valorant","fortnite","apexlegends","minecraft"],
    "creative": ["behance","dribbble","deviantart","artstation","flickr","500px","unsplash","redbubble","furaffinity"],
    "music": ["spotify","soundcloud","lastfm","bandcamp","mixcloud","reverbnation"],
    "blog": ["medium","substack","wordpress","ghost","blogger","livejournal","wattpad","archiveofourown","royalroad"],
    "professional": ["aboutme","keybase","gravatar","producthunt","wellfound"],
    "finance": ["patreon","buymeacoffee","kofi","liberapay","venmo","cashapp","onlyfans","fansly"],
    "fitness": ["strava","goodreads","letterboxd","duolingo","myanimelist","anilist"],
    "security": ["hackthebox","tryhackme","hackerone","bugcrowd","rootme","hackforums","cracked.io","virustotal"],
    "cloud": ["vercel","netlify","heroku","digitalocean"],
    "community": ["hackernews","reddit","steemit","lobste.rs"],
    "chinese": ["zhihu","juejin","douban","bilibili","weibo","nga"],
    "shopping": ["etsy","ebay","poshmark"],
}

async def check_platform(client, username, platform, config):
    url = config["url"].replace("{u}", username)
    try:
        r = await client.get(url, headers=HEADERS, timeout=8, follow_redirects=True)
        exists = r.status_code == 200 and "not found" not in r.text[:3000].lower() and "doesn't exist" not in r.text[:3000].lower()
        return {"platform": platform, "url": url, "status": "found" if exists else "not_found", "http_status": r.status_code}
    except httpx.TimeoutException:
        return {"platform": platform, "url": url, "status": "timeout", "http_status": 0}
    except Exception as e:
        return {"platform": platform, "url": url, "status": "error", "http_status": 0}

@router.get("/scan/{username}")
async def scan_username(username: str):
    username = username.strip().lstrip("@")
    if not username or len(username) < 2:
        raise HTTPException(400, "Username must be at least 2 characters")

    async with httpx.AsyncClient() as client:
        tasks = [check_platform(client, username, name, cfg) for name, cfg in PLATFORMS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    found, not_found, errors = [], [], []
    for r in results:
        if isinstance(r, Exception):
            errors.append({"platform": "unknown", "status": "error"})
        elif r["status"] == "found":
            found.append(r)
        elif r["status"] in ("timeout", "error"):
            errors.append(r)
        else:
            not_found.append(r)

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

@router.get("/name/{name}")
async def name_lookup(name: str):
    name = name.strip()
    if len(name) < 2:
        raise HTTPException(400, "Name must be at least 2 characters")
    async with httpx.AsyncClient() as client:
        results = await name_search(client, name)
    return {"name": name, "results": results, "count": len(results)}

@router.get("/platforms")
async def list_platforms():
    return {"total": len(PLATFORMS), "platforms": list(PLATFORMS.keys()), "categories": PLATFORM_CATEGORIES}

@router.get("/health")
async def health():
    return {"status": "ok", "platforms": len(PLATFORMS)}
