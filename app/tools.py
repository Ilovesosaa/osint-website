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

        # DNS security — SPF
        try:
            r = await client.get(f"https://dns.google/resolve?name={domain}&type=TXT", timeout=10)
            if r.status_code == 200:
                data = r.json()
                answers = [a.get("data","") for a in data.get("Answer",[])]
                results["dns_security"]["SPF"] = [a for a in answers if "spf" in a.lower()]
        except: pass

        # DMARC
        try:
            r = await client.get(f"https://dns.google/resolve?name=_dmarc.{domain}&type=TXT", timeout=10)
            if r.status_code == 200:
                data = r.json()
                answers = [a.get("data","") for a in data.get("Answer",[])]
                results["dns_security"]["DMARC"] = answers
                # Parse DMARC policy
                for ans in answers:
                    if "p=reject" in ans.lower():
                        results["dns_security"]["dmarc_policy"] = "reject"
                    elif "p=quarantine" in ans.lower():
                        results["dns_security"]["dmarc_policy"] = "quarantine"
                    elif "p=none" in ans.lower():
                        results["dns_security"]["dmarc_policy"] = "none"
        except: pass

        # DKIM (common selectors)
        dkim_selectors = ["default","google","selector1","selector2","k1","mandrill","s1","s2","smoke","protonmail","everlytickey1","dkim","mail"]
        results["dns_security"]["DKIM"] = []
        for sel in dkim_selectors:
            try:
                r = await client.get(f"https://dns.google/resolve?name={sel}._domainkey.{domain}&type=TXT", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("Answer"):
                        results["dns_security"]["DKIM"].append({"selector": sel, "records": [a.get("data","") for a in data["Answer"]]})
            except: pass

        # BIMI
        try:
            r = await client.get(f"https://dns.google/resolve?name=default._bimi.{domain}&type=TXT", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("Answer"):
                    results["dns_security"]["BIMI"] = [a.get("data","") for a in data["Answer"]]
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
        blacklists = [
            ("zen.spamhaus.org", "Spamhaus"),
            ("bl.spamcop.net", "SpamCop"),
            ("b.barracudacentral.org", "Barracuda"),
            ("dnsbl-1.uceprotect.net", "UCEPROTECT L1"),
            ("dnsbl-2.uceprotect.net", "UCEPROTECT L2"),
            ("dnsbl-3.uceprotect.net", "UCEPROTECT L3"),
            ("cbl.abuseat.org", "AbuseAt CBL"),
            ("dnsbl.sorbs.net", "SORBS"),
            ("spam.dnsbl.sorbs.net", "SORBS Spam"),
            ("dul.dnsbl.sorbs.net", "SORBS DUL"),
            ("dyna.spamrats.com", "SpamRats Dyna"),
            ("noptr.spamrats.com", "SpamRats NoPtr"),
            ("spam.spamrats.com", "SpamRats Spam"),
            ("bl.deadbeef.com", "DeadBeef"),
            ("db.wpbl.info", "WPBL"),
            ("dnsbl.dronebl.org", "DroneBL"),
            ("rbl.interserver.net", "InterServer"),
            ("ipspamlist.com", "IPSpamList"),
            ("netscan.rbl.com.au", "NetScan RBL"),
            ("all.s5h.net", "S5H"),
            ("rbl.interserver.net", "InterServer"),
        ]
        for bl_url, bl_name in blacklists:
            try:
                socket.gethostbyname(f"{ip_rev}.{bl_url}")
                results["blacklists"].append({"list": bl_name, "listed": True})
            except:
                results["blacklists"].append({"list": bl_name, "listed": False})

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
            body = r.text[:10000].lower()
            server = r.headers.get("server","")
            powered = r.headers.get("x-powered-by","")
            results["technologies"] = list(set([t for t in [server, powered] if t]))

            # Technology detection from body
            tech_signatures = {
                "WordPress": ["wp-content", "wp-includes", "wordpress"],
                "React": ["react", "_next", "reactroot"],
                "Next.js": ["_next/static", "__next"],
                "Vue.js": ["vue", "vuejs", "vue-router"],
                "Angular": ["ng-version", "ng-app", "angular"],
                "Svelte": ["svelte", "__svelte"],
                "Django": ["csrfmiddlewaretoken", "django"],
                "Flask": ["werkzeug", "flask"],
                "Laravel": ["laravel", "csrf-token"],
                "Express": ["x-powered-by: express"],
                "Ruby on Rails": ["csrf-token", "ruby"],
                "ASP.NET": ["asp.net", "viewstate"],
                "PHP": ["php", "x-powered-by: php"],
                "nginx": ["nginx"],
                "Apache": ["apache"],
                "IIS": ["microsoft-iis"],
                "Caddy": ["caddy"],
                "LiteSpeed": ["litespeed"],
                "Cloudflare": ["cloudflare"],
                "Vercel": ["vercel"],
                "Netlify": ["netlify"],
                "Firebase": ["firebase", "firebaseapp"],
                "AWS": ["amazonaws", "aws"],
                "Google Analytics": ["google-analytics", "gtag", "ga.js"],
                "Google Tag Manager": ["googletagmanager", "gtm.js"],
                "Sentry": ["sentry", "sentry-cdn"],
                "Stripe": ["stripe.com"],
                "Tailwind CSS": ["tailwindcss", "tailwind"],
                "Bootstrap": ["bootstrap"],
                "jQuery": ["jquery"],
                "Font Awesome": ["font-awesome", "fontawesome"],
                "Material UI": ["material-ui", "mui"],
                "Chakra UI": ["chakra-ui"],
                "Webpack": ["webpack"],
                "Vite": ["vite", "@vitejs"],
            }
            for tech, sigs in tech_signatures.items():
                for sig in sigs:
                    if sig in body or sig.lower() in str(r.headers).lower():
                        if tech not in results["technologies"]:
                            results["technologies"].append(tech)

            # Security headers
            security_headers = {}
            for h in ["strict-transport-security","content-security-policy","x-frame-options","x-content-type-options","x-xss-protection","referrer-policy","permissions-policy","x-permitted-cross-domain-policies"]:
                val = r.headers.get(h)
                if val:
                    security_headers[h] = val

            results["http"] = {
                "status": r.status_code,
                "url": str(r.url),
                "headers": {k:v for k,v in r.headers.items() if k.lower() in ["server","x-powered-by","x-aspnet-version","x-aspnetmvc-version","x-runtime","x-request-id","x-varnish"]},
                "security_headers": security_headers,
                "redirect_chain": [{"url": str(r.url), "status": r.status_code}],
            }
        except: pass

    return results


# ==================== PHONE OSINT ====================
import phonenumbers as pn
from phonenumbers import carrier as pn_carrier
from phonenumbers import timezone as pn_tz
from phonenumbers import geocoder as pn_geo

@router.get("/phone/{phone}")
async def phone_lookup(phone: str):
    phone = phone.strip().replace(" ","").replace("-","").replace("(","").replace(")","")
    results = {"phone": phone, "valid": False, "format": {}, "carrier": None, "location": None, "country": None, "country_code": None, "type": None, "line_type": None, "timezones": []}

    # Parse with phonenumbers library
    try:
        if phone.startswith("+"):
            parsed = pn.parse(phone)
        else:
            parsed = pn.parse(phone, None)

        if not pn.is_valid_number(parsed):
            # Try with US default
            parsed = pn.parse(phone, "US")
            if not pn.is_valid_number(parsed):
                parsed = pn.parse(phone, None)

        results["valid"] = pn.is_valid_number(parsed)
        results["possible"] = pn.is_possible_number(parsed)

        # Format variants
        try:
            results["format"]["e164"] = pn.format_number(parsed, pn.PhoneNumberFormat.E164)
        except: pass
        try:
            results["format"]["international"] = pn.format_number(parsed, pn.PhoneNumberFormat.INTERNATIONAL)
        except: pass
        try:
            results["format"]["national"] = pn.format_number(parsed, pn.PhoneNumberFormat.NATIONAL)
        except: pass
        try:
            results["format"]["rfc3966"] = pn.format_number(parsed, pn.PhoneNumberFormat.RFC3966)
        except: pass

        # Country
        region = pn.region_code_for_number(parsed)
        results["country_code"] = region
        country_name = pn.region_code_for_number(parsed)
        # Get full country name
        import pycountry
        try:
            results["country"] = pycountry.countries.get(alpha_2=region).name
        except:
            results["country"] = region

        # Carrier
        try:
            carrier_name = pn_carrier.name_for_number(parsed, "en")
            if carrier_name:
                results["carrier"] = carrier_name
        except: pass

        # Location / description
        try:
            location = pn_geo.description_for_number(parsed, "en")
            if location:
                results["location"] = location
        except: pass

        # Timezones
        try:
            tz_list = pn_tz.time_zones_for_number(parsed)
            results["timezones"] = list(tz_list)
        except: pass

        # Number type
        num_type = pn.number_type(parsed)
        type_map = {
            pn.PhoneNumberType.FIXED_LINE: "Fixed Line",
            pn.PhoneNumberType.MOBILE: "Mobile",
            pn.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
            pn.PhoneNumberType.TOLL_FREE: "Toll Free",
            pn.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            pn.PhoneNumberType.SHARED_COST: "Shared Cost",
            pn.PhoneNumberType.VOIP: "VoIP",
            pn.PhoneNumberType.PERSONAL_NUMBER: "Personal",
            pn.PhoneNumberType.PAGER: "Pager",
            pn.PhoneNumberType.UAN: "UAN",
            pn.PhoneNumberType.VOICEMAIL: "Voicemail",
            pn.PhoneNumberType.UNKNOWN: "Unknown",
        }
        results["line_type"] = type_map.get(num_type, "Unknown")
        results["type"] = type_map.get(num_type, "Unknown")

    except pn.NumberParseException:
        # Fallback: basic prefix detection
        prefix_map = {"1":"United States","44":"United Kingdom","33":"France","49":"Germany","34":"Spain","39":"Italy","81":"Japan","86":"China","91":"India","61":"Australia","55":"Brazil","7":"Russia","82":"South Korea","31":"Netherlands","46":"Sweden","47":"Norway","45":"Denmark","358":"Finland","48":"Poland","351":"Portugal","353":"Ireland","43":"Austria","41":"Switzerland","32":"Belgium","30":"Greece","90":"Turkey","972":"Israel","971":"United Arab Emirates","966":"Saudi Arabia"}
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

        # Direct paste site queries for the Discord ID
        paste_sites = [
            ("https://pastebin.com/search", {"q": discord_id}, "pastebin.com"),
            ("https://api.github.com/search/gists", {"q": discord_id, "per_page": 3}, "gist.github.com"),
            ("https://dpaste.org/search/", {"q": discord_id}, "dpaste.org"),
        ]

        for url, params, source in paste_sites:
            try:
                r = await client.get(url, params=params, timeout=10)
                if r.status_code == 200:
                    if source == "pastebin.com":
                        paste_ids = re.findall(r'href="/([a-zA-Z0-9]{6,})"', r.text)
                        for pid in paste_ids[:2]:
                            try:
                                pr = await client.get(f"https://pastebin.com/raw/{pid}", timeout=8)
                                if pr.status_code == 200 and discord_id in pr.text:
                                    breach_results.append({
                                        "source": source,
                                        "url": f"https://pastebin.com/{pid}",
                                        "snippet": pr.text[:200],
                                        "type": "breach_found",
                                    })
                            except: pass
                    elif source == "gist.github.com":
                        data = r.json()
                        for gist in data.get("items", [])[:2]:
                            breach_results.append({
                                "source": source,
                                "url": gist.get("html_url", ""),
                                "snippet": (gist.get("description", "") or "")[:200],
                                "type": "breach_found",
                                "owner": gist.get("owner", {}).get("login", ""),
                            })
                    elif source == "dpaste.org":
                        paste_ids = re.findall(r'href="/(\d+)"', r.text)
                        for pid in paste_ids[:2]:
                            breach_results.append({
                                "source": source,
                                "url": f"https://dpaste.org/{pid}/",
                                "snippet": f"Paste containing Discord ID",
                                "type": "breach_found",
                            })
            except: pass

        # DuckDuckGo dork for broader breach detection
        dorks = [
            f'"{discord_id}" "discord" breach OR leaked OR credentials OR dump',
            f'"{discord_id}" site:pastebin.com OR site:paste.ee OR site:dpaste.org',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        if any(s in link for s in ["pastebin","ghostbin","hastebin","leak","breach","dump","paste.ee","dpaste","rentry"]):
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
                scam_links = r.text.strip().split("\n")
                # Check if any scam links contain this ID
                id_in_scams = any(discord_id in link for link in scam_links[:5000])
                scam_results.append({
                    "database": "Discord-AntiScam/scam-links",
                    "total_tracked": scam_count,
                    "id_in_database": id_in_scams,
                    "status": "compromised" if id_in_scams else "clean",
                })
        except: pass

        # Check GitHub for leaked Discord tokens/IDs
        try:
            r = await client.get(
                "https://api.github.com/search/code",
                params={"q": f"{discord_id} token", "per_page": 3},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                for item in data.get("items", [])[:3]:
                    breach_results.append({
                        "source": "github.com",
                        "url": item.get("html_url", ""),
                        "snippet": f"Code match in {item.get('repository',{}).get('full_name','')} — {item.get('name','')}",
                        "type": "code_leak",
                    })
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
    results = {"query": query, "results": [], "count": 0, "sources_checked": []}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # 1. Pastebin search (scrape search page)
        try:
            r = await client.get(f"https://pastebin.com/search", params={"q": query}, timeout=10)
            if r.status_code == 200:
                paste_links = re.findall(r'href="/([a-zA-Z0-9]+)"', r.text)
                seen_pastes = set()
                for paste_id in paste_links[:5]:
                    if paste_id not in seen_pastes and len(paste_id) >= 6 and paste_id not in ("search","archive","tools","api","login","signup","faq","privacy","dmca","contact"):
                        seen_pastes.add(paste_id)
                        # Fetch paste content preview
                        try:
                            pr = await client.get(f"https://pastebin.com/raw/{paste_id}", timeout=8)
                            if pr.status_code == 200:
                                content = pr.text[:500]
                                if query.lower() in content.lower():
                                    results["results"].append({
                                        "source": "pastebin.com",
                                        "url": f"https://pastebin.com/{paste_id}",
                                        "snippet": content[:200],
                                        "matched": True,
                                    })
                        except: pass
            results["sources_checked"].append("pastebin.com")
        except: pass

        # 2. GitHub Gists search
        try:
            r = await client.get(
                "https://api.github.com/search/gists",
                params={"q": query, "per_page": 5},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                for gist in data.get("items", [])[:5]:
                    desc = gist.get("description", "") or ""
                    files = list(gist.get("files", {}).keys())[:3]
                    results["results"].append({
                        "source": "gist.github.com",
                        "url": gist.get("html_url", ""),
                        "snippet": f"{desc[:100]} | Files: {', '.join(files)}",
                        "owner": gist.get("owner", {}).get("login", ""),
                        "created": gist.get("created_at", ""),
                    })
            results["sources_checked"].append("gist.github.com")
        except: pass

        # 3. Paste.ee search
        try:
            r = await client.get(f"https://paste.ee/search", params={"q": query}, timeout=10)
            if r.status_code == 200:
                paste_links = re.findall(r'href="/p/([a-zA-Z0-9]+)"', r.text)
                for pid in paste_links[:3]:
                    results["results"].append({
                        "source": "paste.ee",
                        "url": f"https://paste.ee/p/{pid}",
                        "snippet": f"Paste ID: {pid}",
                    })
            results["sources_checked"].append("paste.ee")
        except: pass

        # 4. DPaste search
        try:
            r = await client.get(f"https://dpaste.org/search/", params={"q": query}, timeout=10)
            if r.status_code == 200:
                paste_links = re.findall(r'href="/(\d+)"', r.text)
                for pid in paste_links[:3]:
                    results["results"].append({
                        "source": "dpaste.org",
                        "url": f"https://dpaste.org/{pid}/",
                        "snippet": f"Paste ID: {pid}",
                    })
            results["sources_checked"].append("dpaste.org")
        except: pass

        # 5. Rentry.co search
        try:
            r = await client.get(f"https://rentry.co/search", params={"query": query}, timeout=10)
            if r.status_code == 200:
                paste_links = re.findall(r'href="/([a-zA-Z0-9-]+)"', r.text)
                seen_rentry = set()
                for slug in paste_links[:5]:
                    if slug not in seen_rentry and slug not in ("search","api","docs","about","terms","privacy"):
                        seen_rentry.add(slug)
                        results["results"].append({
                            "source": "rentry.co",
                            "url": f"https://rentry.co/{slug}",
                            "snippet": f"Page: {slug}",
                        })
            results["sources_checked"].append("rentry.co")
        except: pass

        # 6. DuckDuckGo dorks for broader coverage
        dorks = [f'"{query}" site:pastebin.com', f'"{query}" site:paste.ee', f'"{query}" site:dpaste.org']
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        if any(s in link for s in ["pastebin","paste.ee","dpaste","rentry"]):
                            snippet_text = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                            results["results"].append({
                                "source": link.split("/")[2],
                                "url": link,
                                "snippet": snippet_text[:200],
                            })
            except: pass

    # Deduplicate
    seen = set()
    unique = []
    for r in results["results"]:
        key = r.get("url", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    results["results"] = unique[:30]
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


# === BREACH CHECKER — find leaked/hacked data across paste sites & breach DBs ===
import json as _json

BREACH_SOURCES = [
    {"name": "Pastebin", "domain": "pastebin.com", "search_url": "https://pastebin.com/search?q={q}"},
    {"name": "GitHub Gists", "domain": "gist.github.com", "api": "https://api.github.com/search/gists?q={q}"},
    {"name": "paste.ee", "domain": "paste.ee", "search_url": "https://paste.ee/search?q={q}"},
    {"name": "dpaste", "domain": "dpaste.org", "search_url": "https://dpaste.org/search/?q={q}"},
    {"name": "rentry", "domain": "rentry.co", "search_url": "https://rentry.co/search?q={q}"},
]

HACKED_PLATFORMS = {
    "facebook": {"breached": True, "date": "2021-04", "records": "533M", "severity": "critical", "data_types": ["email","phone","name","password"], "source": "Facebook Leak"},
    "instagram": {"breached": True, "date": "2022-08", "records": "3.3B", "severity": "critical", "data_types": ["email","phone","username"], "source": "Instagram Scrape"},
    "twitter": {"breached": True, "date": "2023-01", "records": "5.4M", "severity": "high", "data_types": ["email","phone","name"], "source": "Twitter API Exploit"},
    "linkedin": {"breached": True, "date": "2021-06", "records": "700M", "severity": "critical", "data_types": ["email","phone","name"], "source": "LinkedIn Scrape"},
    "tiktok": {"breached": True, "date": "2022-09", "records": "2B", "severity": "critical", "data_types": ["email","phone","name"], "source": "TikTok Scrape"},
    "twitch": {"breached": True, "date": "2021-10", "records": "7.5M", "severity": "critical", "data_types": ["email","password","payment"], "source": "Twitch Source Leak"},
    "discord": {"breached": True, "date": "2023-05", "records": "Unknown", "severity": "high", "data_types": ["email","password","token"], "source": "Discord Phishing"},
    "snapchat": {"breached": True, "date": "2013-12", "records": "4.6M", "severity": "high", "data_types": ["phone","username"], "source": "Snapchat Scrape"},
    "yahoo": {"breached": True, "date": "2013-07", "records": "3B", "severity": "critical", "data_types": ["email","password","security_questions"], "source": "Yahoo Hack"},
    "adobe": {"breached": True, "date": "2013-10", "records": "153M", "severity": "critical", "data_types": ["email","password","password_hint"], "source": "Adobe Breach"},
    "dropbox": {"breached": True, "date": "2012-06", "records": "68M", "severity": "high", "data_types": ["email","password"], "source": "Dropbox Hack"},
    "spotify": {"breached": True, "date": "2020-09", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Spotify Credentials"},
    "reddit": {"breached": True, "date": "2023-01", "records": "Unknown", "severity": "high", "data_types": ["email","password"], "source": "Reddit Source Code"},
    "github": {"breached": True, "date": "2022-04", "records": "Unknown", "severity": "high", "data_types": ["email","token"], "source": "GitHub Token Leak"},
    "netflix": {"breached": True, "date": "2021-07", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Netflix Credentials"},
    "roblox": {"breached": True, "date": "2021-08", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Roblox Credential Stuffing"},
    "steam": {"breached": True, "date": "2011-11", "records": "35M", "severity": "high", "data_types": ["email","password","payment"], "source": "Steam Breach"},
    "playstation": {"breached": True, "date": "2011-04", "records": "77M", "severity": "critical", "data_types": ["email","password","payment","dob"], "source": "PSN Hack"},
    "paypal": {"breached": True, "date": "2022-12", "records": "35K", "severity": "high", "data_types": ["email","name","phone","address"], "source": "PayPal Credentials"},
    "ebay": {"breached": True, "date": "2014-05", "records": "145M", "severity": "critical", "data_types": ["email","password","phone","address"], "source": "eBay Hack"},
    "tumblr": {"breached": True, "date": "2013-02", "records": "65M", "severity": "high", "data_types": ["email","password"], "source": "Tumblr Hack"},
    "myspace": {"breached": True, "date": "2013-06", "records": "360M", "severity": "critical", "data_types": ["email","password"], "source": "MySpace Hack"},
    "quora": {"breached": True, "date": "2018-12", "records": "100M", "severity": "critical", "data_types": ["email","password","content"], "source": "Quora Breach"},
    "wattpad": {"breached": True, "date": "2020-07", "records": "270M", "severity": "critical", "data_types": ["email","password","name"], "source": "Wattpad Leak"},
    "canva": {"breached": True, "date": "2019-05", "records": "137M", "severity": "high", "data_types": ["email","password","name"], "source": "Canva Breach"},
    "pinterest": {"breached": True, "date": "2019-01", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Pinterest Credentials"},
    "patreon": {"breached": True, "date": "2015-09", "records": "15M", "severity": "high", "data_types": ["email","password","payment","address"], "source": "Patreon SQL Injection"},
    "venmo": {"breached": True, "date": "2016-07", "records": "Unknown", "severity": "high", "data_types": ["email","phone","transactions"], "source": "Venmo API Exploit"},
    "strava": {"breached": True, "date": "2020-05", "records": "Unknown", "severity": "high", "data_types": ["email","location"], "source": "Strava Location Leak"},
    "lastfm": {"breached": True, "date": "2012-09", "records": "43M", "severity": "high", "data_types": ["email","password"], "source": "Last.fm Hack"},
    "soundcloud": {"breached": True, "date": "2016-09", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "SoundCloud Credentials"},
    "deviantart": {"breached": True, "date": "2012-08", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "DeviantArt Breach"},
    "flickr": {"breached": True, "date": "2012-06", "records": "6.4M", "severity": "high", "data_types": ["email","password"], "source": "Flickr (via Yahoo)"},
    "weibo": {"breached": True, "date": "2019-05", "records": "500M", "severity": "critical", "data_types": ["phone","email","username"], "source": "Weibo Leak"},
    "bilibili": {"breached": True, "date": "2019-04", "records": "Unknown", "severity": "medium", "data_types": ["email","phone"], "source": "Bilibili Leak"},
    "zhihu": {"breached": True, "date": "2018-07", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Zhihu Credentials"},
    "etsy": {"breached": True, "date": "2019-08", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Etsy Credentials"},
    "duolingo": {"breached": True, "date": "2023-08", "records": "2.6M", "severity": "medium", "data_types": ["email","name"], "source": "Duolingo Scrape"},
    "hackthebox": {"breached": True, "date": "2022-11", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "HTB Credentials"},
    "tryhackme": {"breached": True, "date": "2023-03", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "THM Credentials"},
    "npm": {"breached": True, "date": "2021-03", "records": "Unknown", "severity": "high", "data_types": ["email","token"], "source": "NPM Token Leak"},
    "dockerhub": {"breached": True, "date": "2019-04", "records": "190K", "severity": "medium", "data_types": ["email","password"], "source": "DockerHub Leak"},
    "zoho": {"breached": True, "date": "2021-03", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Zoho Credentials"},
    "aboutme": {"breached": True, "date": "2019-03", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "About.me Credentials"},
    "behance": {"breached": True, "date": "2014-05", "records": "8M", "severity": "medium", "data_types": ["email","password"], "source": "Behance (via Adobe)"},
    "goodreads": {"breached": True, "date": "2013-12", "records": "Unknown", "severity": "medium", "data_types": ["email","password"], "source": "Goodreads Credentials"},
    "onlyfans": {"breached": True, "date": "2023-01", "records": "Unknown", "severity": "high", "data_types": ["email","password"], "source": "OnlyFans Credentials"},
    "protonmail": {"breached": False, "date": None, "records": None, "severity": "none", "data_types": [], "source": "No Known Breach"},
    "virustotal": {"breached": False, "date": None, "records": None, "severity": "none", "data_types": [], "source": "No Known Breach"},
    "replit": {"breached": False, "date": None, "records": None, "severity": "none", "data_types": [], "source": "No Known Breach"},
}


@router.get("/breach/{query}")
async def breach_check(query: str):
    query = query.strip().lstrip("@")
    if not query or len(query) < 2:
        raise HTTPException(400, "Query must be at least 2 characters")

    is_email = "@" in query
    is_username = not is_email

    results = {
        "query": query,
        "type": "email" if is_email else "username",
        "leaks": [],
        "hacked_platforms": [],
        "paste_results": [],
        "total_leaks": 0,
    }

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search paste sites
        for source in BREACH_SOURCES:
            q_encoded = query.replace("@", "%40")
            if source.get("api"):
                url = source["api"].format(q=q_encoded)
            elif source.get("search_url"):
                url = source["search_url"].format(q=q_encoded)
            else:
                continue
            try:
                r = await client.get(url, timeout=10)
                if r.status_code == 200:
                    text = r.text[:8000]
                    query_lower = query.lower()
                    snippets = []
                    for line in text.split("\n"):
                        if query_lower in line.lower():
                            clean = re.sub(r'<[^>]+>', '', line).strip()
                            if clean and len(clean) > 5:
                                snippets.append(clean[:200])
                    for snippet in snippets[:3]:
                        email_match = re.search(r'[\w.+-]+@[\w.-]+\.\w+', snippet)
                        pass_match = re.search(r'(?:pass|password|pwd|pw)[:\s=]+([^\s;,<>"]{3,30})', snippet, re.IGNORECASE)
                        user_match = re.search(r'(?:user|username|login)[:\s=]+([^\s;,<>"]{3,30})', snippet, re.IGNORECASE)
                        results["leaks"].append({
                            "source": source["name"],
                            "host": source["domain"],
                            "snippet": snippet[:150],
                            "leak_url": url,
                            "email": email_match.group(0) if email_match else (query if is_email else ""),
                            "username": user_match.group(1) if user_match else (query if is_username else ""),
                            "password": pass_match.group(1) if pass_match else "",
                            "has_password": bool(pass_match),
                        })
            except: pass

        # Search GitHub code
        try:
            r = await client.get(f"https://api.github.com/search/code?q={query}+password+OR+token+OR+credentials", timeout=10)
            if r.status_code == 200:
                for item in (r.json().get("items") or [])[:5]:
                    repo = item.get("repository", {}).get("full_name", "")
                    path = item.get("path", "")
                    results["leaks"].append({
                        "source": "GitHub",
                        "host": "github.com",
                        "snippet": f"Found in {repo}/{path}",
                        "leak_url": item.get("html_url", ""),
                        "email": query if is_email else "",
                        "username": query if is_username else "",
                        "password": "",
                        "has_password": False,
                    })
        except: pass

        # DuckDuckGo breach searches
        for dq in [f'"{query}" password leaked', f'"{query}" credentials breach']:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dq}, timeout=10)
                if r.status_code == 200:
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    for i, snippet in enumerate(snippets[:2]):
                        clean = re.sub(r'<[^>]+>', '', snippet).strip()
                        link = links[i] if i < len(links) else ""
                        if clean and len(clean) > 10:
                            email_in = re.search(r'[\w.+-]+@[\w.-]+\.\w+', clean)
                            pass_in = re.search(r'(?:pass|password|pwd)[:\s=]+([^\s;,<>"]{3,30})', clean, re.IGNORECASE)
                            results["leaks"].append({
                                "source": "DuckDuckGo",
                                "host": link.split("/")[2] if link else "web",
                                "snippet": clean[:150],
                                "leak_url": link,
                                "email": email_in.group(0) if email_in else "",
                                "username": query if is_username else "",
                                "password": pass_in.group(1) if pass_in else "",
                                "has_password": bool(pass_in),
                            })
            except: pass

        # Add known hacked platforms
        for platform, info in HACKED_PLATFORMS.items():
            if info["breached"]:
                results["hacked_platforms"].append({
                    "platform": platform,
                    "date": info["date"],
                    "records": info["records"],
                    "severity": info["severity"],
                    "data_types": info["data_types"],
                    "source": info["source"],
                })

    # Deduplicate leaks
    seen = set()
    unique = []
    for leak in results["leaks"]:
        key = (leak["source"], leak["email"], leak["password"], leak["username"])
        if key not in seen:
            seen.add(key)
            unique.append(leak)
    results["leaks"] = unique[:20]
    results["total_leaks"] = len(unique)
    results["total_hacked"] = len(results["hacked_platforms"])

    return results
