import asyncio
import re
import socket
import httpx
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter(prefix="/api", tags=["tools"])

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ==================== EMAIL OSINT ====================
@router.get("/email/{email}")
async def email_lookup(email: str):
    if "@" not in email:
        raise HTTPException(400, "Invalid email format")
    domain = email.split("@")[1]
    results = {
        "email": email,
        "domain": domain,
        "mx_records": [],
        "dns_records": {},
        "breach_check": None,
        "disposable": False,
        "gravatar": None,
        "social_profiles": [],
    }

    async with httpx.AsyncClient() as client:
        # MX records via public DNS
        try:
            r = await client.get(f"https://dns.google/resolve?name={domain}&type=MX", timeout=10)
            if r.status_code == 200:
                data = r.json()
                results["mx_records"] = [a.get("data","") for a in data.get("Answer",[]) if a.get("type")==15]
        except: pass

        # A record
        try:
            r = await client.get(f"https://dns.google/resolve?name={domain}&type=A", timeout=10)
            if r.status_code == 200:
                data = r.json()
                results["dns_records"]["A"] = [a.get("data","") for a in data.get("Answer",[])]
        except: pass

        # SPF record
        try:
            r = await client.get(f"https://dns.google/resolve?name={domain}&type=TXT", timeout=10)
            if r.status_code == 200:
                data = r.json()
                spf = [a.get("data","") for a in data.get("Answer",[]) if "spf" in a.get("data","").lower()]
                results["dns_records"]["SPF"] = spf
        except: pass

        # DMARC
        try:
            r = await client.get(f"https://dns.google/resolve?name=_dmarc.{domain}&type=TXT", timeout=10)
            if r.status_code == 200:
                data = r.json()
                results["dns_records"]["DMARC"] = [a.get("data","") for a in data.get("Answer",[])]
        except: pass

        # Gravatar
        import hashlib
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        try:
            r = await client.get(f"https://www.gravatar.com/avatar/{email_hash}?d=404", timeout=10)
            if r.status_code == 200:
                results["gravatar"] = f"https://www.gravatar.com/avatar/{email_hash}"
        except: pass

        # Check disposable domains
        disposable_domains = ["tempmail.com","throwaway.email","guerrillamail.com","mailinator.com","yopmail.com","10minutemail.com","trashmail.com","fakeinbox.com","sharklasers.com","guerrillamailblock.com","grr.la","dispostable.com","tempail.com","temp-mail.org","mohmal.com","burnermail.io","getnada.com","emailondeck.com","33mail.com","mytemp.email","tmpmail.net"]
        results["disposable"] = domain.lower() in disposable_domains

        # Have I Been Pwned (check via breach directory - free)
        try:
            r = await client.get(f"https://haveibeenpwned.com/unifiedsearch/{email}", headers={"User-Agent":"OSINT-Hub/2.0"}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                breaches = data.get("Breaches", [])
                pastes = data.get("Pastes", [])
                results["breach_check"] = {
                    "breached": True,
                    "breach_count": len(breaches) if breaches else 0,
                    "paste_count": len(pastes) if pastes else 0,
                    "breaches": [{"name": b.get("Name"), "date": b.get("BreachDate"), "data_classes": b.get("DataClasses",[])} for b in (breaches or [])[:10]],
                }
            elif r.status_code == 404:
                results["breach_check"] = {"breached": False, "breach_count": 0}
        except: pass

    return results

# ==================== IP OSINT ====================
@router.get("/ip/{ip}")
async def ip_lookup(ip: str):
    ip = ip.strip()
    # Validate IP
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
        except:
            raise HTTPException(400, "Invalid IP address")

    results = {
        "ip": ip,
        "type": "IPv6" if ":" in ip else "IPv4",
        "geo": {},
        "asn": {},
        "abuse": {},
        "reverse_dns": None,
        "ports": [],
        "blacklists": [],
    }

    async with httpx.AsyncClient() as client:
        # ipinfo.io
        try:
            r = await client.get(f"https://ipinfo.io/{ip}/json", timeout=10)
            if r.status_code == 200:
                data = r.json()
                results["geo"] = {
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "loc": data.get("loc"),
                    "org": data.get("org"),
                    "timezone": data.get("timezone"),
                    "postal": data.get("postal"),
                }
                results["asn"] = {"org": data.get("org"), "hostname": data.get("hostname")}
        except: pass

        # Reverse DNS
        try:
            hostname = socket.gethostbyaddr(ip)
            results["reverse_dns"] = hostname[0]
        except: pass

        # ip-api.com (more geo data)
        try:
            r = await client.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting,query", timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success":
                    results["geo"].update({
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "isp": data.get("isp"),
                        "mobile": data.get("mobile"),
                        "proxy": data.get("proxy"),
                        "hosting": data.get("hosting"),
                    })
                    results["abuse"] = {
                        "proxy": data.get("proxy", False),
                        "hosting": data.get("hosting", False),
                        "mobile": data.get("mobile", False),
                    }
        except: pass

        # Blacklist check via dnsbl
        dnsbls = ["zen.spamhaus.org","bl.spamcop.net","b.barracudacentral.org","dnsbl-1.unicrypt.com","dnsbl.sorbs.net"]
        ip_rev = ".".join(reversed(ip.split(".")))
        for bl in dnsbls:
            try:
                query = f"{ip_rev}.{bl}"
                socket.gethostbyname(query)
                results["blacklists"].append({"list": bl, "listed": True})
            except:
                results["blacklists"].append({"list": bl, "listed": False})

    return results

# ==================== DOMAIN OSINT ====================
@router.get("/domain/{domain}")
async def domain_lookup(domain: str):
    domain = domain.strip().lower().replace("https://","").replace("http://","").replace("/","")
    results = {
        "domain": domain,
        "dns": {},
        "whois": {},
        "ssl": {},
        "technologies": [],
        "subdomains_found": [],
    }

    async with httpx.AsyncClient() as client:
        # DNS records
        for rtype in ["A","AAAA","MX","TXT","NS","CNAME","SOA"]:
            try:
                r = await client.get(f"https://dns.google/resolve?name={domain}&type={rtype}", timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    answers = [a.get("data","") for a in data.get("Answer",[])]
                    if answers:
                        results["dns"][rtype] = answers
            except: pass

        # SSL certificate info
        try:
            r = await client.get(f"https://crt.sh/?q={domain}&output=json", timeout=15)
            if r.status_code == 200:
                certs = r.json()
                if certs:
                    results["ssl"] = {
                        "issuer": certs[0].get("issuer_name",""),
                        "valid_from": certs[0].get("not_before",""),
                        "valid_to": certs[0].get("not_after",""),
                        "common_name": certs[0].get("common_name",""),
                        "name_count": len(certs),
                    }
                    # Extract subdomains from cert transparency
                    subs = set()
                    for c in certs[:50]:
                        name = c.get("name_value","")
                        for n in name.split("\n"):
                            n = n.strip().lower()
                            if n.endswith(domain) and n != domain:
                                subs.add(n)
                    results["subdomains_found"] = sorted(list(subs))[:30]
        except: pass

        # HTTP headers / tech detection
        try:
            r = await client.get(f"https://{domain}", headers=HEADERS, timeout=10, follow_redirects=True)
            server = r.headers.get("server","")
            powered = r.headers.get("x-powered-by","")
            results["technologies"] = [t for t in [server, powered] if t]
            results["http"] = {
                "status": r.status_code,
                "redirect_url": str(r.url),
                "headers": {k:v for k,v in r.headers.items() if k.lower() in ["server","x-powered-by","x-frame-options","content-security-policy","strict-transport-security","x-content-type-options"]},
            }
        except: pass

    return results

# ==================== GAMING OSINT ====================
@router.get("/gaming/steam/{username}")
async def steam_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://steamcommunity.com/id/{username}", headers=HEADERS, timeout=10, follow_redirects=True)
            if r.status_code == 200:
                text = r.text
                if "The specified profile could not be found" in text:
                    return {"platform":"steam","username":username,"found":False}
                import re
                name_m = re.search(r'"persona_name":"(.*?)"', text)
                level_m = re.search(r'"steam_level":(\d+)', text)
                avatar_m = re.search(r'"avatar_icon":\s*"(https://[^"]+)"', text)
                return {
                    "platform":"steam","username":username,"found":True,
                    "profile":{
                        "name":name_m.group(1) if name_m else username,
                        "level":level_m.group(1) if level_m else None,
                        "avatar":avatar_m.group(1) if avatar_m else None,
                        "url":f"https://steamcommunity.com/id/{username}",
                    }
                }
        except: pass
    return {"platform":"steam","username":username,"found":False}

@router.get("/gaming/roblox/{username}")
async def roblox_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            # Roblox API
            r = await client.get(f"https://users.roblox.com/v1/usernames/users", json={"usernames":[username]}, headers={**HEADERS,"Content-Type":"application/json"}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                users = data.get("data",[])
                if users:
                    u = users[0]
                    uid = u.get("id")
                    # Get avatar
                    avatar_r = await client.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=150x150&format=Png", timeout=10)
                    avatar_url = None
                    if avatar_r.status_code == 200:
                        ad = avatar_r.json().get("data",[])
                        if ad: avatar_url = ad[0].get("imageUrl")
                    return {
                        "platform":"roblox","username":username,"found":True,
                        "profile":{
                            "id":uid,"name":u.get("name"),
                            "display_name":u.get("displayName"),
                            "avatar":avatar_url,
                            "url":f"https://www.roblox.com/users/{uid}/profile",
                        }
                    }
        except: pass
    return {"platform":"roblox","username":username,"found":False}

@router.get("/gaming/xbox/{username}")
async def xbox_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://www.xboxgamertag.com/search/{username}", headers=HEADERS, timeout=10, follow_redirects=True)
            if r.status_code == 200:
                import re
                text = r.text
                gamertag_m = re.search(r'"gamertag":"(.*?)"', text)
                xuid_m = re.search(r'"xuid":"(.*?)"', text)
                gamerscore_m = re.search(r'"gamerscore":(\d+)', text)
                if gamertag_m or xuid_m:
                    return {
                        "platform":"xbox","username":username,"found":True,
                        "profile":{
                            "gamertag":gamertag_m.group(1) if gamertag_m else username,
                            "xuid":xuid_m.group(1) if xuid_m else None,
                            "gamerscore":gamerscore_m.group(1) if gamerscore_m else None,
                            "url":f"https://www.xboxgamertag.com/search/{username}",
                        }
                    }
        except: pass
    return {"platform":"xbox","username":username,"found":False}

@router.get("/gaming/playstation/{username}")
async def playstation_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://psnprofiles.com/{username}", headers=HEADERS, timeout=10, follow_redirects=True)
            if r.status_code == 200:
                import re
                text = r.text
                if "User not found" in text or r.url.path == "/":
                    return {"platform":"playstation","username":username,"found":False}
                name_m = re.search(r'<h1[^>]*>(.*?)</h1>', text)
                trophy_m = re.search(r'"total":(\d+)', text)
                level_m = re.search(r'"level":(\d+)', text)
                return {
                    "platform":"playstation","username":username,"found":True,
                    "profile":{
                        "psn_id":name_m.group(1).strip() if name_m else username,
                        "trophies":trophy_m.group(1) if trophy_m else None,
                        "level":level_m.group(1) if level_m else None,
                        "url":f"https://psnprofiles.com/{username}",
                    }
                }
        except: pass
    return {"platform":"playstation","username":username,"found":False}
