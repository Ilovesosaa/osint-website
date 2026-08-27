import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/instagram", tags=["instagram"])

IG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-IG-App-ID": "936619743392459",
}

@router.get("/health")
async def health():
    return {"status": "ok", "module": "instagram"}

@router.get("/user/{username}")
async def get_user(username: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Method 1: Try i.instagram.com API (mobile API, sometimes works)
        try:
            r = await client.get(
                f"https://i.instagram.com/api/v1/users/web_profile_info/",
                headers={**IG_HEADERS, "X-IG-App-ID": "936619743392459"},
                params={"username": username},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                user = data.get("data", {}).get("user", {})
                if user:
                    return {
                        "platform": "instagram",
                        "username": username,
                        "found": True,
                        "profile": {
                            "id": user.get("id"),
                            "username": user.get("username"),
                            "full_name": user.get("full_name"),
                            "biography": user.get("biography"),
                            "external_url": user.get("external_url"),
                            "profile_pic_url": user.get("profile_pic_url"),
                            "is_private": user.get("is_private"),
                            "is_verified": user.get("is_verified"),
                            "category": user.get("category_name"),
                            "url": f"https://www.instagram.com/{username}/",
                        },
                        "stats": {
                            "followers": user.get("edge_followed_by", {}).get("count"),
                            "following": user.get("edge_follow", {}).get("count"),
                            "posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
                            "highlights_count": user.get("highlight_reel_count"),
                        },
                        "risk": {
                            "private_account": user.get("is_private", False),
                            "verified": user.get("is_verified", False),
                            "has_external_link": bool(user.get("external_url")),
                            "category": user.get("category_name"),
                            "business_category": user.get("business_category_name"),
                        },
                        "recent_posts": [
                            {
                                "shortcode": m.get("shortcode"),
                                "caption": (m.get("edge_media_to_caption",{}).get("edges",[{}])[0].get("node",{}).get("text",""))[:200] if m.get("edge_media_to_caption",{}).get("edges") else "",
                                "likes": m.get("edge_liked_by", {}).get("count"),
                                "comments": m.get("edge_media_to_comment", {}).get("count"),
                                "timestamp": m.get("taken_at_timestamp"),
                            }
                            for m in user.get("edge_owner_to_timeline_media", {}).get("edges", [])[:5]
                        ] if not user.get("is_private") else [],
                    }
        except Exception:
            pass

        # Method 2: Try the web profile (limited data)
        try:
            r = await client.get(
                f"https://www.instagram.com/{username}/",
                headers=IG_HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                text = r.text
                if '"is_private":true' in text or '"is_private": true' in text:
                    return {
                        "platform": "instagram",
                        "username": username,
                        "found": True,
                        "profile": {"username": username, "url": f"https://www.instagram.com/{username}/"},
                        "stats": {},
                        "risk": {"private_account": True, "note": "Private account - limited data"},
                    }
                if "login" not in text.lower()[:500] and username.lower() in text.lower():
                    return {
                        "platform": "instagram",
                        "username": username,
                        "found": True,
                        "profile": {"username": username, "url": f"https://www.instagram.com/{username}/"},
                        "stats": {},
                        "note": "Profile exists but API blocked - use manual inspection",
                    }
        except Exception:
            pass

        raise HTTPException(404, "Instagram user not found or API blocked. Instagram heavily restricts automated access.")

@router.get("/search")
async def search(q: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            r = await client.get(
                f"https://www.instagram.com/web/search/topsearch/",
                headers={**IG_HEADERS, "X-ASBD-ID": "198387"},
                params={"query": q, "context": "user"},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                users = data.get("users", [])
                return {
                    "platform": "instagram",
                    "query": q,
                    "results": [
                        {
                            "username": u.get("user", {}).get("username"),
                            "full_name": u.get("user", {}).get("full_name"),
                            "avatar": u.get("user", {}).get("profile_pic_url"),
                            "followers": u.get("user", {}).get("follower_count"),
                            "verified": u.get("user", {}).get("is_verified"),
                            "url": f"https://www.instagram.com/{u.get('user',{}).get('username')}/",
                        }
                        for u in users[:10]
                    ]
                }
        except Exception:
            pass
        return {"platform": "instagram", "query": q, "results": [], "note": "Search blocked by Instagram"}
