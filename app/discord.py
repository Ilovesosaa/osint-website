import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/discord", tags=["discord"])

DISCORD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

@router.get("/health")
async def health():
    return {"status": "ok", "module": "discord"}

@router.get("/user/{username}")
async def get_user(username: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Method 1: Try Discord's public user lookup
        try:
            r = await client.get(
                f"https://discordlookup.mesavirep.xyz/user/{username}",
                headers=DISCORD_HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("id"):
                    return {
                        "platform": "discord",
                        "username": username,
                        "found": True,
                        "profile": {
                            "id": data.get("id"),
                            "username": data.get("username"),
                            "discriminator": data.get("discriminator"),
                            "global_name": data.get("global_name"),
                            "avatar": data.get("avatar", {}).get("id") if isinstance(data.get("avatar"), dict) else None,
                            "banner": data.get("banner"),
                            "accent_color": data.get("accent_color"),
                            "created_at": data.get("created_at"),
                            "url": f"https://discord.com/users/{data.get('id')}",
                        },
                        "risk": {
                            "account_age": data.get("created_at"),
                        }
                    }
        except Exception:
            pass

        # Method 2: Try weeb.dev lookup
        try:
            r = await client.get(
                f"https://weeb.dev/api/users/{username}",
                headers=DISCORD_HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("id"):
                    return {
                        "platform": "discord",
                        "username": username,
                        "found": True,
                        "profile": {
                            "id": data.get("id"),
                            "username": data.get("username"),
                            "discriminator": data.get("discriminator"),
                            "avatar": data.get("avatar"),
                            "url": f"https://discord.com/users/{data.get('id')}",
                        },
                        "stats": {},
                    }
        except Exception:
            pass

        # Method 3: Try discord.id public lookup
        try:
            r = await client.get(
                f"https://discord.id/api/users/{username}",
                headers=DISCORD_HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("id"):
                    return {
                        "platform": "discord",
                        "username": username,
                        "found": True,
                        "profile": {
                            "id": data.get("id"),
                            "username": data.get("username"),
                            "discriminator": data.get("discriminator"),
                            "avatar": data.get("avatar"),
                            "banner": data.get("banner"),
                            "created_at": data.get("created_at"),
                            "url": f"https://discord.com/users/{data.get('id')}",
                        },
                    }
        except Exception:
            pass

        return {
            "platform": "discord",
            "username": username,
            "found": False,
            "note": "Discord does not expose user lookup via public API. Use a Discord bot or manual inspection.",
            "profile": {
                "username": username,
                "url": f"https://discord.com",
            }
        }

@router.get("/user/{user_id}/avatar")
async def get_avatar(user_id: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            r = await client.get(
                f"https://discordlookup.mesavirep.xyz/user/{user_id}",
                headers=DISCORD_HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                avatar = data.get("avatar", {})
                if avatar.get("id"):
                    ext = "gif" if avatar.get("animated") else "png"
                    return {
                        "avatar_url": f"https://cdn.discordapp.com/avatars/{user_id}/{avatar['id']}.{ext}",
                        "animated": avatar.get("animated"),
                        "id": avatar.get("id"),
                    }
        except Exception:
            pass
        raise HTTPException(404, "Avatar not found")

@router.get("/servers")
async def known_servers_note():
    return {
        "note": "Discord server lists are not publicly accessible. Use Discord bots (e.g., MEE6, Dyno) or Discord API with bot token for server discovery.",
        "tip": "To find a user's servers: Use a mutual servers checker bot or the Discord API with proper OAuth2 scopes."
    }
