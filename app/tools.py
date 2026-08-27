import asyncio
import re
import socket
import hashlib
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["tools"])

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ==================== HOLEHE-STYLE EMAIL OSINT ====================
# Checks register/forgot-password endpoints to find where email is registered

HOLEHE_MODULES = {
    "github": {"url": "https://github.com/join", "check": "text", "exists_text": "already associated", "method": "register"},
    "twitter": {"url": "https://api.twitter.com/1.1/account/get_prerender_qubit.json", "check": "status", "method": "register"},
    "instagram": {"url": "https://www.instagram.com/accounts/web/usersetup/", "check": "status", "method": "register"},
    "spotify": {"url": "https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email=", "check": "status", "method": "register"},
    "pinterest": {"url": "https://www.pinterest.com/resource/EmailExistsResource/get/?data={\"options\":{\"email\":\"EMAIL\"}}", "check": "text", "exists_text": "\"data\":true", "method": "register"},
    "reddit": {"url": "https://www.reddit.com/register/", "check": "status", "method": "register"},
    "tumblr": {"url": "https://www.tumblr.com/register", "check": "status", "method": "register"},
    "snapchat": {"url": "https://accounts.snapchat.com/accounts/signup", "check": "status", "method": "register"},
    "medium": {"url": "https://medium.com/_/api/1.1/users/validate?", "check": "status", "method": "register"},
    "npm": {"url": "https://www.npmjs.com/signup", "check": "status", "method": "register"},
    "gitlab": {"url": "https://gitlab.com/users/sign_up", "check": "status", "method": "register"},
    "bitbucket": {"url": "https://bitbucket.org/account/signup/", "check": "status", "method": "register"},
    "dockerhub": {"url": "https://hub.docker.com/signup", "check": "status", "method": "register"},
    "twitch": {"url": "https://passport.twitch.tv/register", "check": "status", "method": "register"},
    "discord": {"url": "https://discord.com/api/v9/auth/register", "check": "status", "method": "register"},
    "roblox": {"url": "https://auth.roblox.com/v2/signup", "check": "status", "method": "register"},
    "steam": {"url": "https://store.steampowered.com/join", "check": "status", "method": "register"},
    "xbox": {"url": "https://signup.live.com/", "check": "status", "method": "register"},
    "playstation": {"url": "https://id.sonyentertainmentnetwork.com/signin/create_account", "check": "status", "method": "register"},
    "apple": {"url": "https://appleid.apple.com/account", "check": "status", "method": "register"},
    "google": {"url": "https://accounts.google.com/signup", "check": "status", "method": "register"},
    "yahoo": {"url": "https://login.yahoo.com/account/create", "check": "status", "method": "register"},
    "protonmail": {"url": "https://mail.proton.me/signup", "check": "status", "method": "register"},
    "zoho": {"url": "https://www.zoho.com/accounts/signup", "check": "status", "method": "register"},
    "adobe": {"url": "https://auth.services.adobe.com/en_US/index.html?callback=https%3A%2F%2Fims-na1.adobelogin.com%2Fims%2Fadobeid%2Fcc-web-key%2FAdobeID%2Ftoken", "check": "status", "method": "register"},
    "amazon": {"url": "https://www.amazon.com/ap/register?openid.pape.max_auth_age=0", "check": "status", "method": "register"},
    "ebay": {"url": "https://signin.ebay.com/ws/eBayISAPI.dll?JoinRenter", "check": "status", "method": "register"},
    "netflix": {"url": "https://www.netflix.com/signup/registration", "check": "status", "method": "register"},
    "dropbox": {"url": "https://www.dropbox.com/register", "check": "status", "method": "register"},
    "samsung": {"url": "https://account.samsung.com/membership/pp/signup", "check": "status", "method": "register"},
    "nike": {"url": "https://www.nikereg.com/", "check": "status", "method": "register"},
    "flickr": {"url": "https://www.flickr.com/register", "check": "status", "method": "register"},
    "strava": {"url": "https://www.strava.com/register", "check": "status", "method": "register"},
    "myanimelist": {"url": "https://myanimelist.net/register.php", "check": "status", "method": "register"},
    "behance": {"url": "https://www.behance.net/login?redirect=/register", "check": "status", "method": "register"},
    "dribbble": {"url": "https://dribbble.com/signup", "check": "status", "method": "register"},
    "producthunt": {"url": "https://www.producthunt.com/users/sign_up", "check": "status", "method": "register"},
    "deviantart": {"url": "https://www.deviantart.com/users/register", "check": "status", "method": "register"},
    "soundcloud": {"url": "https://soundcloud.com/discover", "check": "status", "method": "register"},
    "replit": {"url": "https://replit.com/signup", "check": "status", "method": "register"},
    "codepen": {"url": "https://codepen.io/signup", "check": "status", "method": "register"},
    "kaggle": {"url": "https://www.kaggle.com/account/register", "check": "status", "method": "register"},
    "aboutme": {"url": "https://about.me/signup", "check": "status", "method": "register"},
    "keybase": {"url": "https://keybase.io/_/api/1.0/username/available.json?username=", "check": "status", "method": "register"},
    "venmo": {"url": "https://venmo.com/signup", "check": "status", "method": "register"},
    "patreon": {"url": "https://www.patreon.com/register", "check": "status", "method": "register"},
    "buymeacoffee": {"url": "https://www.buymeacoffee.com/signup", "check": "status", "method": "register"},
    "evernote": {"url": "https://www.evernote.com/Registration.action", "check": "status", "method": "register"},
    "quora": {"url": "https://www.quora.com/", "check": "status", "method": "register"},
    "wattpad": {"url": "https://www.wattpad.com/register", "check": "status", "method": "register"},
    "lastfm": {"url": "https://www.last.fm/join", "check": "status", "method": "register"},
    "smule": {"url": "https://www.smule.com/signup", "check": "status", "method": "register"},
    "blablacar": {"url": "https://www.blablacar.com/", "check": "status", "method": "register"},
    "strava": {"url": "https://www.strava.com/register", "check": "status", "method": "register"},
    "vivino": {"url": "https://www.vivino.com/signup", "check": "status", "method": "register"},
    "vsco": {"url": "https://vsco.co/subscriptions", "check": "status", "method": "register"},
    "mercadolibre": {"url": "https://www.mercadolibre.com/jms/mla/lgz/login", "check": "status", "method": "register"},
    "pipedrive": {"url": "https://www.pipedrive.com/en/register", "check": "status", "method": "register"},
    "canva": {"url": "https://www.canva.com/signup", "check": "status", "method": "register"},
    "monzo": {"url": "https://monzo.com/", "check": "status", "method": "register"},
    "revolut": {"url": "https://www.revolut.com/", "check": "status", "method": "register"},
    "tandem": {"url": "https://www.tandem.net/", "check": "status", "method": "register"},
    "tineye": {"url": "https://tineye.com/", "check": "status", "method": "register"},
    "archiveorg": {"url": "https://archive.org/account/signup", "check": "status", "method": "register"},
}

async def holehe_check(client, email, site, config):
    url = config["url"]
    if "EMAIL" in url:
        url = url.replace("EMAIL", email)
    elif url.endswith("=") or url.endswith("?"):
        url = url + email
    try:
        if config["method"] == "register":
            r = await client.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        else:
            r = await client.get(url, headers=HEADERS, timeout=10)
        
        exists = False
        if config.get("check") == "status":
            exists = r.status_code == 200
        elif config.get("check") == "text":
            exists = config.get("exists_text", "") in r.text[:5000]
        
        return {"site": site, "exists": exists, "status": r.status_code}
    except:
        return {"site": site, "exists": False, "status": 0, "error": True}

@router.get("/email/{email}")
async def email_lookup(email: str):
    if "@" not in email or "." not in email.split("@")[1]:
        raise HTTPException(400, "Invalid email format")
    domain = email.split("@")[1]

    results = {
        "email": email,
        "domain": domain,
        "registered_on": [],
        "not_registered_on": [],
        "mx_records": [],
        "dns_security": {},
        "disposable": False,
        "gravatar": None,
        "breach_check": None,
    }

    async with httpx.AsyncClient() as client:
        # Holehe-style: check all sites in parallel
        tasks = [holehe_check(client, email, site, cfg) for site, cfg in HOLEHE_MODULES.items()]
        holehe_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for r in holehe_results:
            if isinstance(r, dict):
                if r.get("exists"):
                    results["registered_on"].append(r["site"])
                else:
                    results["not_registered_on"].append(r["site"])

        # MX records
        try:
            r = await client.get(f"https://dns.google/resolve?name={domain}&type=MX", timeout=10)
            if r.status_code == 200:
                data = r.json()
                results["mx_records"] = [a.get("data","") for a in data.get("Answer",[]) if a.get("type")==15]
        except: pass

        # DNS security
        for rtype in ["TXT","DMARC"]:
            try:
                q = f"_dmarc.{domain}" if rtype == "DMARC" else domain
                r = await client.get(f"https://dns.google/resolve?name={q}&type=TXT", timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    answers = [a.get("data","") for a in data.get("Answer",[])]
                    if rtype == "TXT":
                        results["dns_security"]["SPF"] = [a for a in answers if "spf" in a.lower()]
                    else:
                        results["dns_security"]["DMARC"] = answers
            except: pass

        # Disposable check
        disposable_domains = ["tempmail.com","throwaway.email","guerrillamail.com","mailinator.com","yopmail.com","10minutemail.com","trashmail.com","fakeinbox.com","sharklasers.com","guerrillamailblock.com","grr.la","dispostable.com","tempail.com","temp-mail.org","mohmal.com","burnermail.io","getnada.com","emailondeck.com","33mail.com","mytemp.email","tmpmail.net","discard.email","maildrop.cc","harakirimail.com","tmail.io","tmpmail.org"]
        results["disposable"] = domain.lower() in disposable_domains

        # Gravatar
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        try:
            r = await client.get(f"https://www.gravatar.com/avatar/{email_hash}?d=404", timeout=10)
            if r.status_code == 200:
                results["gravatar"] = f"https://www.gravatar.com/avatar/{email_hash}"
        except: pass

    results["registered_count"] = len(results["registered_on"])
    return results


# ==================== IP OSINT ====================
@router.get("/ip/{ip}")
async def ip_lookup(ip: str):
    ip = ip.strip()
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
        except:
            raise HTTPException(400, "Invalid IP")

    results = {"ip": ip, "type": "IPv6" if ":" in ip else "IPv4", "geo": {}, "asn": {}, "abuse": {}, "reverse_dns": None, "blacklists": []}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://ipinfo.io/{ip}/json", timeout=10)
            if r.status_code == 200:
                d = r.json()
                results["geo"] = {k: d.get(k) for k in ["city","region","country","loc","org","timezone","postal"]}
                results["asn"] = {"org": d.get("org"), "hostname": d.get("hostname")}
        except: pass

        try:
            r = await client.get(f"http://ip-api.com/json/{ip}?fields=lat,lon,isp,mobile,proxy,hosting", timeout=10)
            if r.status_code == 200:
                d = r.json()
                results["geo"].update({"lat": d.get("lat"), "lon": d.get("lon"), "isp": d.get("isp")})
                results["abuse"] = {"proxy": d.get("proxy",False), "hosting": d.get("hosting",False), "mobile": d.get("mobile",False)}
        except: pass

        try:
            results["reverse_dns"] = socket.gethostbyaddr(ip)[0]
        except: pass

        ip_rev = ".".join(reversed(ip.split(".")))
        for bl in ["zen.spamhaus.org","bl.spamcop.net","b.barracudacentral.org"]:
            try:
                socket.gethostbyname(f"{ip_rev}.{bl}")
                results["blacklists"].append({"list": bl, "listed": True})
            except:
                results["blacklists"].append({"list": bl, "listed": False})

    return results


# ==================== DOMAIN OSINT ====================
@router.get("/domain/{domain}")
async def domain_lookup(domain: str):
    domain = domain.strip().lower().replace("https://","").replace("http://","").rstrip("/")
    results = {"domain": domain, "dns": {}, "ssl": {}, "technologies": [], "subdomains": [], "http": {}}

    async with httpx.AsyncClient() as client:
        for rtype in ["A","AAAA","MX","TXT","NS","CNAME"]:
            try:
                r = await client.get(f"https://dns.google/resolve?name={domain}&type={rtype}", timeout=10)
                if r.status_code == 200:
                    answers = [a.get("data","") for a in r.json().get("Answer",[])]
                    if answers: results["dns"][rtype] = answers
            except: pass

        try:
            r = await client.get(f"https://crt.sh/?q={domain}&output=json", timeout=15)
            if r.status_code == 200:
                certs = r.json()
                if certs:
                    results["ssl"] = {"issuer": certs[0].get("issuer_name",""), "from": certs[0].get("not_before",""), "to": certs[0].get("not_after","")}
                    subs = set()
                    for c in certs[:50]:
                        for n in c.get("name_value","").split("\n"):
                            n = n.strip().lower()
                            if n.endswith(domain) and n != domain: subs.add(n)
                    results["subdomains"] = sorted(list(subs))[:30]
        except: pass

        try:
            r = await client.get(f"https://{domain}", headers=HEADERS, timeout=10, follow_redirects=True)
            results["technologies"] = [t for t in [r.headers.get("server",""), r.headers.get("x-powered-by","")] if t]
            results["http"] = {"status": r.status_code, "url": str(r.url), "headers": {k:v for k,v in r.headers.items() if k.lower() in ["server","x-powered-by","strict-transport-security","content-security-policy"]}}
        except: pass

    return results


# ==================== PHONE OSINT ====================
@router.get("/phone/{phone}")
async def phone_lookup(phone: str):
    phone = phone.strip().replace(" ","").replace("-","").replace("(","").replace(")","")
    results = {"phone": phone, "format": {}, "carrier": None, "location": None, "country": None, "type": None, "line_type": None}

    # Parse phone
    if phone.startswith("+"):
        results["format"]["e164"] = phone
        results["format"]["international"] = phone
        country_code = phone[1:3] if len(phone) > 3 else phone[1:]
        results["country"] = country_code
    else:
        results["format"]["local"] = phone

    async with httpx.AsyncClient() as client:
        # NumVerify / abstract API style lookup via numverify
        try:
            r = await client.get(f"http://apilayer.net/api/validate?access_key=demo&number={phone}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get("valid") is not None:
                    results["valid"] = d.get("valid")
                    results["carrier"] = d.get("carrier")
                    results["line_type"] = d.get("line_type")
                    results["location"] = d.get("location")
                    results["country"] = d.get("country_name")
                    results["format"]["national"] = d.get("local_format")
                    results["format"]["international"] = d.get("international_format")
        except: pass

        # Fallback: parse country from number
        if not results.get("country"):
            prefix_map = {"1":"US/CA","44":"UK","33":"FR","49":"DE","34":"ES","39":"IT","81":"JP","86":"CN","91":"IN","61":"AU","55":"BR","7":"RU","82":"KR","31":"NL","46":"SE","47":"NO","45":"DK","358":"FI","48":"PL","351":"PT","352":"LU","353":"IE","43":"AT","41":"CH","32":"BE","30":"GR","90":"TR","972":"IL","971":"AE","966":"SA"}
            for code, country in sorted(prefix_map.items(), key=lambda x: -len(x[0])):
                if phone.startswith("+"+code) or phone.startswith(code):
                    results["country"] = country
                    break

    return results


# ==================== CRYPTO WALLET OSINT ====================
@router.get("/crypto/{address}")
async def crypto_lookup(address: str):
    address = address.strip()
    results = {"address": address, "type": None, "balance": None, "transactions": None, "first_seen": None, "last_seen": None, "chain": None}

    # Detect chain
    if address.startswith("0x") and len(address) == 42:
        results["chain"] = "Ethereum (ERC-20)"
        results["type"] = "ETH"
    elif address.startswith("1") or address.startswith("3") or address.startswith("bc1"):
        results["chain"] = "Bitcoin"
        results["type"] = "BTC"
    elif address.startswith("T"):
        results["chain"] = "Tron (TRC-20)"
        results["type"] = "TRX"
    elif address.startswith("addr1"):
        results["chain"] = "Cardano"
        results["type"] = "ADA"
    elif address.startswith("r"):
        results["chain"] = "XRP Ledger"
        results["type"] = "XRP"
    else:
        results["chain"] = "Unknown"
        results["type"] = "Unknown"

    async with httpx.AsyncClient() as client:
        if results["type"] == "ETH":
            try:
                r = await client.get(f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken", timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    if d.get("result"):
                        balance_wei = int(d["result"])
                        results["balance"] = f"{balance_wei / 10**18:.6f} ETH"
            except: pass
        elif results["type"] == "BTC":
            try:
                r = await client.get(f"https://blockchain.info/rawaddr/{address}?limit=5", timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    results["balance"] = f"{d.get('final_balance',0) / 10**8:.8f} BTC"
                    results["transactions"] = d.get("n_tx", 0)
                    results["total_received"] = f"{d.get('total_received',0) / 10**8:.8f} BTC"
                    if d.get("txs"):
                        results["last_seen"] = d["txs"][0].get("time")
                        results["first_seen"] = d["txs"][-1].get("time") if len(d["txs"]) > 1 else None
            except: pass
        elif results["type"] == "TRX":
            try:
                r = await client.get(f"https://api.trongrid.io/v1/accounts/{address}", timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    accounts = d.get("data",[])
                    if accounts:
                        balance = accounts[0].get("balance",0)
                        results["balance"] = f"{balance / 10**6:.6f} TRX"
            except: pass

    return results


# ==================== WAYBACK MACHINE ====================
@router.get("/wayback/{url:path}")
async def wayback_lookup(url: str):
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    results = {"url": url, "snapshots": [], "total_snapshots": 0, "first_snapshot": None, "last_snapshot": None}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=10&fl=timestamp,statuscode,mimetype", timeout=15)
            if r.status_code == 200:
                data = r.json()
                if len(data) > 1:
                    results["total_snapshots"] = len(data) - 1
                    for row in data[1:]:
                        ts = row[0]
                        results["snapshots"].append({
                            "timestamp": ts,
                            "date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[8:10]}:{ts[10:12]}",
                            "status": row[1],
                            "mimetype": row[2],
                            "url": f"https://web.archive.org/web/{ts}/{url}"
                        })
                    if results["snapshots"]:
                        results["first_snapshot"] = results["snapshots"][-1]["date"]
                        results["last_snapshot"] = results["snapshots"][0]["date"]
        except: pass

    return results


# ==================== URL UNFURL ====================
@router.get("/url/{url:path}")
async def url_unfurl(url: str):
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    results = {"url": url, "title": None, "description": None, "og_image": None, "og_site_name": None, "favicon": None, "headers": {}, "technologies": [], "redirects": []}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
            text = r.text[:50000]
            results["status"] = r.status_code
            results["final_url"] = str(r.url)
            results["headers"] = {k:v for k,v in r.headers.items() if k.lower() in ["server","content-type","x-powered-by","set-cookie","x-frame-options"]}

            # Extract meta tags
            title_m = re.search(r"<title[^>]*>(.*?)</title>", text, re.DOTALL|re.IGNORECASE)
            results["title"] = title_m.group(1).strip()[:200] if title_m else None

            desc_m = re.search(r'<meta\s+(?:name|property)="(?:description|og:description)"\s+content="(.*?)"', text, re.IGNORECASE)
            if not desc_m:
                desc_m = re.search(r'content="(.*?)"\s+(?:name|property)="(?:description|og:description)"', text, re.IGNORECASE)
            results["description"] = desc_m.group(1).strip()[:300] if desc_m else None

            og_img = re.search(r'<meta\s+property="og:image"\s+content="(.*?)"', text, re.IGNORECASE)
            results["og_image"] = og_img.group(1) if og_img else None

            og_site = re.search(r'<meta\s+property="og:site_name"\s+content="(.*?)"', text, re.IGNORECASE)
            results["og_site_name"] = og_site.group(1) if og_site else None

            # Favicon
            from urllib.parse import urljoin
            fav_m = re.search(r'<link[^>]+rel="(?:shortcut )?icon"[^>]+href="(.*?)"', text, re.IGNORECASE)
            if fav_m:
                results["favicon"] = urljoin(url, fav_m.group(1))

            # Simple tech detection
            tech_hints = {"react":"React","vue":"Vue.js","angular":"Angular","next":"Next.js","nuxt":"Nuxt.js","wordpress":"WordPress","shopify":"Shopify","wix":"Wix","squarespace":"Squarespace","cloudflare":"Cloudflare","vercel":"Vercel","netlify":"Netlify","jquery":"jQuery","bootstrap":"Bootstrap","tailwind":"Tailwind CSS"}
            for hint, name in tech_hints.items():
                if hint.lower() in text.lower() or hint.lower() in str(r.headers).lower():
                    results["technologies"].append(name)

            # Track redirects
            for resp in r.history:
                results["redirects"].append({"url": str(resp.url), "status": resp.status_code})
        except Exception as e:
            results["error"] = str(e)[:200]

    return results


# ==================== GAMING ====================
@router.get("/gaming/steam/{username}")
async def steam_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://steamcommunity.com/id/{username}", headers=HEADERS, timeout=10, follow_redirects=True)
            if r.status_code == 200 and "The specified profile could not be found" not in r.text:
                import re
                name_m = re.search(r'"persona_name":"(.*?)"', r.text)
                level_m = re.search(r'"steam_level":(\d+)', r.text)
                return {"platform":"steam","username":username,"found":True,"profile":{"name":name_m.group(1) if name_m else username,"level":level_m.group(1) if level_m else None,"url":f"https://steamcommunity.com/id/{username}"}}
        except: pass
    return {"platform":"steam","username":username,"found":False}

@router.get("/gaming/roblox/{username}")
async def roblox_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post("https://users.roblox.com/v1/usernames/users", json={"usernames":[username]}, headers={**HEADERS,"Content-Type":"application/json"}, timeout=10)
            if r.status_code == 200:
                users = r.json().get("data",[])
                if users:
                    u = users[0]
                    return {"platform":"roblox","username":username,"found":True,"profile":{"id":u.get("id"),"name":u.get("name"),"display_name":u.get("displayName"),"url":f"https://www.roblox.com/users/{u.get('id')}/profile"}}
        except: pass
    return {"platform":"roblox","username":username,"found":False}

@router.get("/gaming/xbox/{username}")
async def xbox_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://www.xboxgamertag.com/search/{username}", headers=HEADERS, timeout=10, follow_redirects=True)
            if r.status_code == 200:
                import re
                gamertag_m = re.search(r'"gamertag":"(.*?)"', r.text)
                xuid_m = re.search(r'"xuid":"(.*?)"', r.text)
                if gamertag_m or xuid_m:
                    return {"platform":"xbox","username":username,"found":True,"profile":{"gamertag":gamertag_m.group(1) if gamertag_m else username,"xuid":xuid_m.group(1) if xuid_m else None,"url":f"https://www.xboxgamertag.com/search/{username}"}}
        except: pass
    return {"platform":"xbox","username":username,"found":False}

@router.get("/gaming/playstation/{username}")
async def playstation_lookup(username: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"https://psnprofiles.com/{username}", headers=HEADERS, timeout=10, follow_redirects=True)
            if r.status_code == 200 and "User not found" not in r.text:
                import re
                name_m = re.search(r'<h1[^>]*>(.*?)</h1>', r.text)
                trophy_m = re.search(r'"total":(\d+)', r.text)
                return {"platform":"playstation","username":username,"found":True,"profile":{"psn_id":name_m.group(1).strip() if name_m else username,"trophies":trophy_m.group(1) if trophy_m else None,"url":f"https://psnprofiles.com/{username}"}}
        except: pass
    return {"platform":"playstation","username":username,"found":False}

# === Discord ID Snowflake Decoder ===
DISCORD_EPOCH = 1420070400000  # Discord epoch in ms (2015-01-01T00:00:00Z)

def decode_discord_id(discord_id: str):
    discord_id = discord_id.strip().replace(" ", "")
    if not discord_id.isdigit():
        return None
    snowflake = int(discord_id)
    timestamp_ms = ((snowflake >> 22) + DISCORD_EPOCH)
    from datetime import datetime, timezone
    created_at = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    internal_worker_id = (snowflake & 0x3E0000) >> 17
    internal_process_id = (snowflake & 0x1F000) >> 12
    internal_increment = snowflake & 0xFFF
    now = datetime.now(tz=timezone.utc)
    age = now - created_at
    return {
        "id": discord_id,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "created_at_unix": int(timestamp_ms / 1000),
        "age_days": age.days,
        "age_human": f"{age.days // 365}y {(age.days % 365) // 30}mo {age.days % 30}d",
        "internal_worker_id": internal_worker_id,
        "internal_process_id": internal_process_id,
        "internal_increment": internal_increment,
    }

@router.get("/discord/{discord_id}")
async def discord_lookup(discord_id: str):
    info = decode_discord_id(discord_id)
    if not info:
        raise HTTPException(400, "Invalid Discord ID — must be a numeric snowflake")

    avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/avatar.png"
    banner_url = f"https://cdn.discordapp.com/banners/{discord_id}/banner.png"

    avatar_exists = False
    banner_exists = False
    profile_data = None
    breach_results = []
    scam_results = []
    associated_accounts = []

    async with httpx.AsyncClient(headers=HEADERS) as client:
        # Avatar & Banner check
        try:
            r = await client.head(avatar_url, timeout=5)
            avatar_exists = r.status_code == 200
        except: pass
        try:
            r = await client.head(banner_url, timeout=5)
            banner_exists = r.status_code == 200
        except: pass

        # DiscordLookup profile
        try:
            r = await client.get(f"https://discordlookup.mesavirep.xyz/user/{discord_id}", timeout=8)
            if r.status_code == 200:
                profile_data = r.json()
        except: pass

        # Check public breach paste sites for the Discord ID
        breach_checks = [
            ("https://haveibeenpwned.com/api/v3/breachedaccount/", "HIBP (requires key, checking pattern)"),
            ("https://psbdmp.ws/api/v3/search", "Pastebin Dumps"),
            ("https://leaked.site/api/v2/check", "Leaked.site"),
        ]

        # Google dork for breaches — search for ID in known paste/breach sites
        google_dorks = [
            f'"{discord_id}" site:pastebin.com',
            f'"{discord_id}" site:ghostbin.co',
            f'"{discord_id}" site:hastebin.com',
            f'"{discord_id}" "discord" "breach"',
            f'"{discord_id}" "discord" "leaked"',
            f'"{discord_id}" "discord" "credentials"',
        ]

        for dork in google_dorks[:3]:
            try:
                r = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": dork},
                    timeout=10,
                )
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        if any(s in link for s in ["pastebin","ghostbin","hastebin","leak","breach","dump"]):
                            snippet_text = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                            breach_results.append({
                                "source": link.split("/")[2],
                                "url": link,
                                "snippet": snippet_text[:200],
                                "type": "breach_found",
                            })
            except: pass

        # Check Discord scam links DB
        try:
            r = await client.get(
                "https://raw.githubusercontent.com/Discord-AntiScam/scam-links/main/plus/scam-links-raw.txt",
                timeout=10,
            )
            if r.status_code == 200:
                scam_count = len(r.text.strip().split("\n"))
                scam_results.append({"database": "Discord-AntiScam/scam-links", "total_tracked": scam_count, "status": "checked"})
        except: pass

        # Check if ID appears in public breach databases
        for db_url in [
            f"https://api.pwnedpasswords.com/breaches",
        ]:
            try:
                r = await client.get(db_url, timeout=5)
            except: pass

        # Associated accounts — search for username patterns
        if profile_data and profile_data.get("global_name"):
            search_name = profile_data["global_name"]
            try:
                r = await client.get(f"http://localhost:8000/api/scan/{search_name}", timeout=60)
                if r.status_code == 200:
                    scan_data = r.json()
                    if scan_data.get("found_count", 0) > 0:
                        associated_accounts = scan_data.get("found", [])[:10]
            except: pass

    # Risk analysis
    risk_flags = []
    age_days = info.get("age_days", 0)
    if age_days < 30:
        risk_flags.append({"flag": "New Account", "severity": "high", "detail": f"Only {age_days} days old — possible throwaway"})
    elif age_days < 180:
        risk_flags.append({"flag": "Young Account", "severity": "medium", "detail": f"{age_days} days old — less than 6 months"})
    else:
        risk_flags.append({"flag": "Mature Account", "severity": "low", "detail": f"{age_days} days old — established account"})

    if breach_results:
        risk_flags.append({"flag": "Breach Exposure", "severity": "high", "detail": f"ID found in {len(breach_results)} breach/paste sources"})

    if not avatar_exists:
        risk_flags.append({"flag": "No Avatar", "severity": "low", "detail": "Default avatar — may indicate alt or inactive account"})
    else:
        risk_flags.append({"flag": "Custom Avatar", "severity": "low", "detail": "Has uploaded a profile picture"})

    if banner_exists:
        risk_flags.append({"flag": "Nitro Banner", "severity": "info", "detail": "Has banner — likely has Discord Nitro"})

    if profile_data:
        if profile_data.get("badge"):
            risk_flags.append({"flag": "Badges", "severity": "info", "detail": f"Has badges: {profile_data['badge']}"})
        if profile_data.get("special"):
            risk_flags.append({"flag": "Special Account", "severity": "info", "detail": "Has special flags set"})

    # Additional intel
    creation_year = info["created_at"][:4]
    creation_month = info["created_at"][5:7]
    era = "pre-2019" if int(creation_year) < 2019 else "2019-2021" if int(creation_year) < 2022 else "2022-2024" if int(creation_year) < 2025 else "2025+"
    risk_flags.append({"flag": "Creation Era", "severity": "info", "detail": f"Created in {era} ({creation_year}-{creation_month})"})

    return {
        "discord_id": discord_id,
        "info": info,
        "avatar": avatar_url if avatar_exists else None,
        "banner": banner_url if banner_exists else None,
        "profile": profile_data,
        "breaches": breach_results,
        "breach_count": len(breach_results),
        "scam_databases_checked": scam_results,
        "associated_accounts": associated_accounts,
        "risk_flags": risk_flags,
        "risk_summary": {
            "high": len([r for r in risk_flags if r["severity"] == "high"]),
            "medium": len([r for r in risk_flags if r["severity"] == "medium"]),
            "low": len([r for r in risk_flags if r["severity"] == "low"]),
            "info": len([r for r in risk_flags if r["severity"] == "info"]),
        },
    }


# === Reverse IP Lookup ===
@router.get("/reverseip/{ip}")
async def reverse_ip(ip: str):
    ip = ip.strip()
    results = {"ip": ip, "reverse_dns": None, "same_server_domains": [], "geo": None}

    # Reverse DNS
    try:
        hostname = socket.gethostbyaddr(ip)
        results["reverse_dns"] = hostname[0]
    except: pass

    async with httpx.AsyncClient(headers=HEADERS) as client:
        # ipinfo.io for geo
        try:
            r = await client.get(f"https://ipinfo.io/{ip}/json", timeout=8)
            if r.status_code == 200:
                results["geo"] = r.json()
        except: pass

        # Find domains on same IP via DNS lookup
        try:
            r = await client.get(f"https://api.hackertarget.com/reverseiplookup/?q={ip}", timeout=10)
            if r.status_code == 200 and "error" not in r.text.lower():
                domains = [line.strip() for line in r.text.strip().split("\n") if line.strip() and not line.startswith("API")]
                results["same_server_domains"] = domains[:20]
        except: pass

    return results


# === SSL/TLS Certificate Analysis ===
@router.get("/ssl/{domain}")
async def ssl_check(domain: str):
    domain = domain.strip().replace("https://", "").replace("http://", "").split("/")[0]
    result = {"domain": domain, "certificates": [], "issuer": None, "subject": None, "valid_from": None, "valid_to": None, "days_left": None, "san": [], "protocols": [], "cipher": None}

    import ssl
    import datetime
    context = ssl.create_default_context()
    try:
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                cipher_info = ssock.cipher()
                protocol = ssock.version()

                result["subject"] = dict(x[0] for x in cert.get("subject", []))
                result["issuer"] = dict(x[0] for x in cert.get("issuer", []))
                result["valid_from"] = cert.get("notBefore")
                result["valid_to"] = cert.get("notAfter")
                result["san"] = [entry[1] for entry in cert.get("subjectAltName", [])]
                result["protocols"] = [protocol]
                result["cipher"] = cipher_info[0] if cipher_info else None

                # Calculate days left
                if result["valid_to"]:
                    expire = datetime.datetime.strptime(result["valid_to"], "%b %d %H:%M:%S %Y %Z")
                    result["days_left"] = (expire - datetime.datetime.utcnow()).days
    except Exception as e:
        result["error"] = str(e)

    return result


# === WAF / CDN Detection ===
WAF_SIGNATURES = {
    "Cloudflare": ["cf-ray", "cf-cache-status", "cloudflare"],
    "AWS CloudFront": ["x-amz-cf-id", "x-amz-cf-pop", "cloudfront"],
    "Akamai": ["x-akamai-transformed", "akamai"],
    "Fastly": ["x-fastly-request-id", "fastly"],
    "Sucuri": ["x-sucuri-id", "sucuri"],
    "Imperva": ["x-iinfo", "imperva"],
    "Incapsula": ["x-incap-ses", "incapsula"],
    "F5 BIG-IP": ["bigip"],
    "Barracuda": ["barracounter_session"],
    "Vercel": ["x-vercel-id", "vercel"],
    "Netlify": ["x-nf-request-id", "netlify"],
    "Firebase": ["firebase"],
}

@router.get("/waf/{domain}")
async def waf_detect(domain: str):
    domain = domain.strip().replace("https://", "").replace("http://", "").split("/")[0]
    result = {"domain": domain, "detected": [], "headers": {}, "server": None, "technologies": []}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        try:
            r = await client.get(f"https://{domain}", timeout=10)
            headers_lower = {k.lower(): v for k, v in r.headers.items()}
            result["headers"] = dict(r.headers)
            result["server"] = r.headers.get("Server") or r.headers.get("server")
            result["status"] = r.status_code

            # WAF detection
            for waf, signatures in WAF_SIGNATURES.items():
                for sig in signatures:
                    if any(sig in str(v).lower() for v in headers_lower.values()) or sig in str(headers_lower):
                        result["detected"].append(waf)

            # Technology detection from headers and body
            body_preview = r.text[:5000].lower()
            tech_map = {
                "WordPress": ["wp-content", "wp-includes"],
                "nginx": ["nginx"],
                "Apache": ["apache"],
                "Express": ["x-powered-by: express"],
                "PHP": ["x-powered-by: php"],
                "ASP.NET": ["x-powered-by: asp.net", "x-aspnet-version"],
                "Vercel": ["vercel"],
                "Netlify": ["netlify"],
                "React": ["react", "_next"],
                "Next.js": ["_next/static"],
                "Vue.js": ["vue"],
                "Angular": ["ng-version"],
                "Cloudflare": ["cloudflare"],
                "Google Analytics": ["google-analytics.com", "gtag"],
                "Sentry": ["sentry"],
                "Bootstrap": ["bootstrap"],
                "jQuery": ["jquery"],
                "Tailwind CSS": ["tailwindcss"],
            }
            for tech, patterns in tech_map.items():
                for pat in patterns:
                    if pat in body_preview or pat in str(headers_lower):
                        if tech not in result["technologies"]:
                            result["technologies"].append(tech)
        except Exception as e:
            result["error"] = str(e)

    return result


# === Google Dork Generator ===
@router.get("/dorks/{target}")
async def generate_dorks(target: str):
    target = target.strip()
    dorks = {
        "site_pages": f'site:{target}',
        "filetype_pdf": f'site:{target} filetype:pdf',
        "filetype_doc": f'site:{target} filetype:doc OR filetype:docx',
        "filetype_xls": f'site:{target} filetype:xls OR filetype:xlsx',
        "filetype_ppt": f'site:{target} filetype:ppt OR filetype:pptx',
        "filetype_sql": f'site:{target} filetype:sql',
        "filetype_log": f'site:{target} filetype:log',
        "filetype_config": f'site:{target} filetype:yml OR filetype:yaml OR filetype:conf',
        "filetype_env": f'site:{target} filetype:env',
        "filetype_key": f'site:{target} filetype:key OR filetype:pem',
        "login_pages": f'site:{target} inurl:login OR inurl:signin OR inurl:admin',
        "api_endpoints": f'site:{target} inurl:api OR inurl:v1 OR inurl:v2',
        "error_pages": f'site:{target} intitle:"error" OR intitle:"exception"',
        "backup_files": f'site:{target} filetype:bak OR filetype:old OR filetype:backup',
        "directory_listing": f'site:{target} intitle:"index of"',
        "emails": f'site:{target} "@{target}" email OR contact',
        "phone_numbers": f'site:{target} phone OR tel OR mobile',
        "employees": f'site:{target} "team" OR "staff" OR "employee" OR "about"',
        "github_secrets": f'site:github.com "{target}" password OR secret OR token OR api_key',
        "pastebin_leaks": f'site:pastebin.com "{target}"',
        "job_listings": f'site:{target} inurl:jobs OR inurl:careers OR "hiring"',
        "subdomains": f'site:*.{target}',
        "sitemap": f'site:{target} filetype:xml',
        "robots": f'site:{target} robots.txt',
        "exposed_data": f'site:{target} filetype:csv OR filetype:json OR filetype:xml',
        "swagger_api": f'site:{target} inurl:swagger OR inurl:docs OR inurl:openapi',
    }
    return {"target": target, "dorks": dorks, "count": len(dorks)}


# === Port Scanner ===
@router.get("/ports/{ip}")
async def port_scan(ip: str):
    ip = ip.strip()
    common_ports = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 111: "RPCBind", 135: "MSRPC",
        139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
        993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3306: "MySQL",
        3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
        8080: "HTTP-Alt", 8443: "HTTPS-Alt", 8888: "HTTP-Proxy",
        9090: "HTTP-Mgmt", 27017: "MongoDB",
    }

    open_ports = []
    banners = {}

    async def check_port(port):
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=1.5
            )
            writer.close()
            await writer.wait_closed()
            open_ports.append(port)
            # Try to grab banner
            try:
                reader2, writer2 = await asyncio.wait_for(
                    asyncio.open_connection(ip, port), timeout=1.5
                )
                banner_data = await asyncio.wait_for(reader2.read(256), timeout=1.5)
                banners[port] = banner_data.decode(errors="ignore").strip()
                writer2.close()
                await writer2.wait_closed()
            except: pass
        except: pass

    tasks = [check_port(port) for port in common_ports.keys()]
    await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "ip": ip,
        "open_ports": sorted(open_ports),
        "closed_ports": [p for p in common_ports.keys() if p not in open_ports],
        "services": {p: {"port": p, "service": common_ports[p], "banner": banners.get(p)} for p in open_ports},
        "total_open": len(open_ports),
    }


# === Paste / Pastebin Search ===
@router.get("/pastes/{query}")
async def paste_search(query: str):
    query = query.strip()
    results = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS) as client:
        # Search for the query in known paste/breach sites via Google dork
        dorks = [
            f'"{query}" site:pastebin.com',
            f'"{query}" site:ghostbin.co',
            f'"{query}" site:hastebin.com',
            f'"{query}" site:paste.ee',
            f'"{query}" site:dpaste.org',
            f'"{query}" site:rentry.co',
        ]

        for dork in dorks[:4]:
            try:
                r = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": dork},
                    timeout=10,
                )
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        snippet_text = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        source = link.split("/")[2] if "/" in link else link
                        results["results"].append({
                            "source": source,
                            "url": link,
                            "snippet": snippet_text[:200],
                            "query": dork,
                        })
            except: pass

    # Deduplicate
    seen = set()
    unique = []
    for r in results["results"]:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    results["results"] = unique[:20]
    results["count"] = len(results["results"])

    return results


# === WHOIS Lookup ===
@router.get("/whois/{domain}")
async def whois_lookup(domain: str):
    domain = domain.strip().replace("https://", "").replace("http://", "").split("/")[0]
    result = {"domain": domain, "registrar": None, "creation_date": None, "expiration_date": None, "name_servers": [], "registrant": None, "status": []}

    # Use RDAP (free, no API key)
    rdap_urls = [
        f"https://rdap.verisign.com/com/v1/domain/{domain}",
        f"https://rdap.org/domain/{domain}",
    ]

    async with httpx.AsyncClient(headers=HEADERS) as client:
        for url in rdap_urls:
            try:
                r = await client.get(url, timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    result["ldh_name"] = data.get("ldhName")
                    result["status"] = data.get("status", [])

                    # Events
                    for ev in data.get("events", []):
                        if ev.get("eventAction") == "registration":
                            result["creation_date"] = ev.get("eventDate")
                        elif ev.get("eventAction") == "expiration":
                            result["expiration_date"] = ev.get("eventDate")

                    # Nameservers
                    for ns in data.get("nameservers", []):
                        if ns.get("ldhName"):
                            result["name_servers"].append(ns["ldhName"])

                    # Entities
                    for ent in data.get("entities", []):
                        roles = ent.get("roles", [])
                        if "registrar" in roles:
                            vcards = ent.get("vcardArray", [None, []])[1] if ent.get("vcardArray") else []
                            for v in vcards:
                                if len(v) > 3 and v[0] == "fn":
                                    result["registrar"] = v[3]
                        if "registrant" in roles or "technical" in roles:
                            vcards = ent.get("vcardArray", [None, []])[1] if ent.get("vcardArray") else []
                            for v in vcards:
                                if len(v) > 3 and v[0] == "fn":
                                    result["registrant"] = v[3]

                    if result["creation_date"] or result["name_servers"]:
                        break
            except: pass

    return result


# === Subdomain Finder (via crt.sh Certificate Transparency) ===
@router.get("/subdomains/{domain}")
async def subdomain_finder(domain: str):
    domain = domain.strip().replace("https://", "").replace("http://", "").split("/")[0]
    subdomains = set()

    async with httpx.AsyncClient(headers=HEADERS) as client:
        # crt.sh Certificate Transparency
        try:
            r = await client.get(
                f"https://crt.sh/?q=%.{domain}&output=json",
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                for entry in data:
                    name = entry.get("name_value", "")
                    for sub in name.split("\n"):
                        sub = sub.strip().lower()
                        if sub.endswith(domain) and "*" not in sub:
                            subdomains.add(sub)
        except: pass

        # Also try DNS resolution on common subdomains
        common_subs = ["www","mail","ftp","smtp","pop","ns1","ns2","dns","mx","webmail","cpanel","api","dev","staging","test","admin","portal","vpn","remote","blog","shop","store","cdn","media","static","img","images","app","dashboard","panel"]
        for sub in common_subs:
            try:
                full = f"{sub}.{domain}"
                socket.getaddrinfo(full, None)
                subdomains.add(full)
            except: pass

    return {
        "domain": domain,
        "subdomains": sorted(subdomains),
        "count": len(subdomains),
        "sources": ["crt.sh Certificate Transparency", "Common subdomain DNS probe"],
    }


# === Shodan-style (IP Info + Services) via public APIs ===
@router.get("/shodan/{ip}")
async def shodan_lookup(ip: str):
    ip = ip.strip()
    result = {"ip": ip, "ports": [], "vulns": [], "hostnames": [], "org": None, "os": None, "isp": None}

    async with httpx.AsyncClient(headers=HEADERS) as client:
        # Use ipinfo.io + ip-api for free data
        try:
            r = await client.get(f"https://ipinfo.io/{ip}/json", timeout=8)
            if r.status_code == 200:
                data = r.json()
                result["hostnames"] = [data.get("hostname", "")]
                result["org"] = data.get("org")
                result["isp"] = data.get("org")
                result["city"] = data.get("city")
                result["region"] = data.get("region")
                result["country"] = data.get("country")
                result["loc"] = data.get("loc")
        except: pass

        # IP-API for more details
        try:
            r = await client.get(f"http://ip-api.com/json/{ip}?fields=status,message,isp,org,as,mobile,proxy,hosting", timeout=8)
            if r.status_code == 200:
                data = r.json()
                result["isp"] = result["isp"] or data.get("isp")
                result["org"] = result["org"] or data.get("org")
                result["as"] = data.get("as")
                result["mobile"] = data.get("mobile")
                result["proxy"] = data.get("proxy")
                result["hosting"] = data.get("hosting")
        except: pass

        # Try to get open ports from common ports
        common_ports = [21,22,23,25,53,80,110,143,443,993,995,1723,3306,3389,5432,5900,6379,8080,8443,8888,9090,27017]
        open_ports = []
        async def check(port):
            try:
                _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=1)
                w.close()
                await w.wait_closed()
                open_ports.append(port)
            except: pass
        await asyncio.gather(*[check(p) for p in common_ports], return_exceptions=True)
        result["ports"] = sorted(open_ports)

    return result
