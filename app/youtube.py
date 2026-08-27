import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/youtube", tags=["youtube"])

@router.get("/health")
async def health():
    return {"status": "ok", "module": "youtube"}

@router.get("/user/{username}")
async def get_user(username: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Method 1: Try oEmbed for channel
        try:
            r = await client.get(
                f"https://www.youtube.com/@{username}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
            )
            if r.status_code == 200:
                text = r.text
                if "This page isn't available" in text or "404" in text[:500]:
                    raise HTTPException(404, "YouTube channel not found")
                import re
                # Extract from page metadata
                title_match = re.search(r'<title>(.*?) - YouTube</title>', text)
                desc_match = re.search(r'<meta name="description" content="(.*?)"', text)
                channel_title = title_match.group(1).replace(" - YouTube", "") if title_match else username
                description = desc_match.group(1)[:300] if desc_match else ""

                # Extract subscriber count from page
                subs = ""
                subs_match = re.search(r'(\d[\d,.]*[KMB]?)\s*subscribers', text)
                if subs_match:
                    subs = subs_match.group(1)

                videos = ""
                vid_match = re.search(r'(\d[\d,.]*[KMB]?)\s*videos', text)
                if vid_match:
                    videos = vid_match.group(1)

                views = ""
                views_match = re.search(r'(\d[\d,.]*[KMB]?)\s*views', text)
                if views_match:
                    views = views_match.group(1)

                # Get channel ID
                cid_match = re.search(r'"channelId":"(UC[\w-]+)"', text)
                channel_id = cid_match.group(1) if cid_match else None

                # Get join date
                join_match = re.search(r'Joined\s+(\w+\s+\d{1,2},\s+\d{4})', text)
                join_date = join_match.group(1) if join_match else None

                # Get country
                country_match = re.search(r'"country":"(\w+)"', text)
                country = country_match.group(1) if country_match else None

                return {
                    "platform": "youtube",
                    "username": username,
                    "found": True,
                    "profile": {
                        "channel_title": channel_title,
                        "channel_id": channel_id,
                        "description": description,
                        "url": f"https://www.youtube.com/@{username}",
                        "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                        "join_date": join_date,
                        "country": country,
                    },
                    "stats": {
                        "subscribers": subs,
                        "videos": videos,
                        "total_views": views,
                    },
                    "risk": {
                        "has_description": bool(description),
                        "country": country,
                    }
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(502, f"YouTube lookup failed: {str(e)}")

@router.get("/channel/{channel_id}")
async def get_channel(channel_id: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            r = await client.get(
                f"https://www.youtube.com/channel/{channel_id}/about",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
            )
            if r.status_code == 200:
                import re
                text = r.text
                title_match = re.search(r'<title>(.*?) - YouTube</title>', text)
                channel_title = title_match.group(1).replace(" - YouTube", "") if title_match else channel_id
                return {
                    "platform": "youtube",
                    "channel_id": channel_id,
                    "found": True,
                    "profile": {"channel_title": channel_title, "url": f"https://www.youtube.com/channel/{channel_id}"},
                }
        except Exception as e:
            raise HTTPException(502, f"YouTube lookup failed: {str(e)}")

@router.get("/search")
async def search(q: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            r = await client.get(
                "https://www.youtube.com/results",
                params={"search_query": q, "sp": "EgIQAg%3D%3D"},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
            )
            if r.status_code == 200:
                import re
                text = r.text
                # Find channel results
                channels = re.findall(r'"channelRenderer":\{(.*?)\}', text)
                results = []
                for ch in channels[:10]:
                    name_m = re.search(r'"text":"(.*?)"', ch)
                    cid_m = re.search(r'"channelId":"(UC[\w-]+)"', ch)
                    if name_m and cid_m:
                        results.append({
                            "name": name_m.group(1),
                            "channel_id": cid_m.group(1),
                            "url": f"https://www.youtube.com/channel/{cid_m.group(1)}",
                        })
                return {"platform": "youtube", "query": q, "results": results}
        except Exception as e:
            pass
        return {"platform": "youtube", "query": q, "results": [], "note": "Search unavailable"}
