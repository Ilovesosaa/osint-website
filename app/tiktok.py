import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/tiktok", tags=["tiktok"])

TIKTOK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tiktok.com/",
}

async def tt_get(client, url, params=None):
    r = await client.get(url, headers=TIKTOK_HEADERS, params=params, timeout=15)
    if r.status_code == 404:
        raise HTTPException(404, "TikTok user not found")
    if r.status_code != 200:
        raise HTTPException(r.status_code, f"TikTok error {r.status_code}: {r.text[:300]}")
    return r.json() if r.headers.get("content-type","").startswith("application/json") else r.text

@router.get("/health")
async def health():
    return {"status": "ok", "module": "tiktok"}

@router.get("/user/{username}")
async def get_user(username: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            data = await tt_get(client, f"https://www.tiktok.com/api/user/detail/", {"uniqueId": username, "aid": "1988"})
            user = data.get("userInfo", {}).get("user", {})
            stats = data.get("userInfo", {}).get("stats", {})
            return {
                "platform": "tiktok",
                "username": username,
                "found": bool(user),
                "profile": {
                    "id": user.get("id"),
                    "unique_id": user.get("uniqueId"),
                    "nickname": user.get("nickname"),
                    "avatar": user.get("avatarThumb"),
                    "signature": user.get("signature"),
                    "verified": user.get("verified"),
                    "private": user.get("privateAccount"),
                    "language": user.get("language"),
                    "created": user.get("createTime"),
                    "sec_uid": user.get("secUid"),
                    "url": f"https://www.tiktok.com/@{username}",
                },
                "stats": stats,
                "risk": {
                    "private_account": user.get("privateAccount", False),
                    "verified": user.get("verified", False),
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            # fallback: try scraping the page
            try:
                r = await client.get(f"https://www.tiktok.com/@{username}", headers=TIKTOK_HEADERS)
                if r.status_code == 200 and "uniqueId" in r.text:
                    return {"platform": "tiktok", "username": username, "found": True, "profile": {"url": f"https://www.tiktok.com/@{username}"}, "stats": {}, "note": "Limited data - API blocked, page exists", "risk": {}}
                raise HTTPException(404, "TikTok user not found")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(502, f"TikTok lookup failed: {str(e)}")

@router.get("/search")
async def search_users(q: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        data = await tt_get(client, f"https://www.tiktok.com/api/search/user/full/", {"keyword": q, "aid": "1988", "count": 10})
        users = data.get("user_list", [])
        return {
            "platform": "tiktok",
            "query": q,
            "results": [
                {
                    "username": u.get("user_info",{}).get("uniqueId"),
                    "nickname": u.get("user_info",{}).get("nickname"),
                    "avatar": u.get("user_info",{}).get("avatarThumb"),
                    "followers": u.get("user_info",{}).get("followerCount"),
                    "verified": u.get("user_info",{}).get("verified"),
                    "url": f"https://www.tiktok.com/@{u.get('user_info',{}).get('uniqueId')}"
                } for u in users
            ]
        }
