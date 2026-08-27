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
