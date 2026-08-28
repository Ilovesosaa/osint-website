import asyncio
import re
import hashlib
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["doxtools"])

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ==================== TELEGRAM LOOKUP ====================
@router.get("/telegram/{username}")
async def telegram_lookup(username: str):
    username = username.strip().lstrip("@")
    if not username or len(username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")

    result = {"username": username, "found": False, "profile": None, "source": None}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Try t.me public page
        try:
            r = await client.get(f"https://t.me/{username}", timeout=10)
            if r.status_code == 200:
                text = r.text
                if "tgme_page_title" in text:
                    result["found"] = True
                    title_m = re.search(r'class="tgme_page_title[^"]*"[^>]*>(.*?)</div>', text, re.DOTALL)
                    desc_m = re.search(r'class="tgme_page_description[^"]*"[^>]*>(.*?)</div>', text, re.DOTALL)
                    photo_m = re.search(r'class="tgme_page_photo_image"[^>]*src="(.*?)"', text)
                    result["profile"] = {
                        "name": re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else username,
                        "bio": re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else None,
                        "photo": photo_m.group(1) if photo_m else None,
                        "url": f"https://t.me/{username}",
                    }
                    result["source"] = "t.me"
        except: pass

        # DuckDuckGo check
        if not result["found"]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'site:t.me "{username}"'}, timeout=10)
                if r.status_code == 200 and f"t.me/{username}" in r.text:
                    result["found"] = True
                    result["source"] = "duckduckgo"
                    result["profile"] = {"url": f"https://t.me/{username}", "name": username}
            except: pass

    return result


# ==================== DOXBIN LOOKUP ====================
@router.get("/doxbin/{query}")
async def doxbin_lookup(query: str):
    query = query.strip()
    results = {"query": query, "found": False, "results": [], "note": "Doxbin is a dark web paste site. Results are scraped from public mirrors and search engines."}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search via DuckDuckGo for doxbin entries
        try:
            r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'site:doxbin.net "{query}"'}, timeout=10)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]*doxbin[^"]*)"', r.text)
                snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                for i, link in enumerate(links[:5]):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                    results["results"].append({"url": link, "source": "doxbin.net", "snippet": snippet[:200]})
                if links:
                    results["found"] = True
        except: pass

        # Also check alternative mirrors
        try:
            r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'doxbin "{query}" leak OR dox'}, timeout=10)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]+)"', r.text)
                snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                for i, link in enumerate(links[:3]):
                    if "doxbin" in link or "leak" in link or "paste" in link:
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        results["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
                        results["found"] = True
        except: pass

    results["count"] = len(results["results"])
    return results


# ==================== DOX SEARCH ====================
@router.get("/doxsearch/{query}")
async def dox_search(query: str):
    query = query.strip()
    results = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search across multiple dox/paste/leak sites
        search_sites = [
            ("site:doxbin.net", "doxbin.net"),
            ("site:pastebin.com leak OR dox OR exposed", "pastebin.com"),
            ("site:ghostbin.com", "ghostbin.com"),
            ("\"dox\" OR \"exposed\" OR \"leaked\"", "web"),
        ]
        for dork, source in search_sites:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'"{query}" {dork}'}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        results["results"].append({"url": link, "source": source, "snippet": snippet[:200]})
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


# ==================== FISCAL CODE (Italian CF) ====================
@router.get("/fiscalcode/{cf}")
async def fiscal_code_lookup(cf: str):
    cf = cf.strip().upper()
    result = {"input": cf, "valid": False, "decoded": {}, "breach_results": []}

    # Validate Italian Fiscal Code format (16 chars)
    if len(cf) != 16:
        result["error"] = f"Invalid length: {len(cf)} (expected 16)"
        return result

    # Basic format check
    pattern = r'^[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$'
    if not re.match(pattern, cf):
        result["error"] = "Invalid format — does not match Italian CF pattern"
        return result

    result["valid"] = True

    # Decode what we can
    # Surname (chars 1-3): odd-position chars from first 6
    # Name (chars 4-6): odd-position chars from chars 7-12... simplified
    result["decoded"] = {
        "surname_consonants": cf[0:6:2],
        "surname_vowels": cf[1:6:2],
        "year_digits": cf[6:8],
        "month_code": cf[8],
        "day": cf[9:11],
        "municipality": cf[11:15],
        "check_char": cf[15],
        "birth_year": f"19{cf[6:8]}" if int(cf[6:8]) > 40 else f"20{cf[6:8]}" if int(cf[6:8]) < 40 else f"19{cf[6:8]}",
    }

    month_codes = {"A":"January","B":"February","C":"March","D":"April","E":"May","H":"June","L":"July","M":"August","P":"September","R":"October","S":"November","T":"December"}
    result["decoded"]["birth_month"] = month_codes.get(cf[8], "Unknown")

    # Gender: even day = F, odd day = M
    day_num = int(cf[9:11])
    if day_num > 40:
        day_num -= 40
        result["decoded"]["gender"] = "Female"
    else:
        result["decoded"]["gender"] = "Male"
    result["decoded"]["birth_day"] = day_num

    # Check CF in breach databases
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        try:
            r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'"{cf}" "codice fiscale" OR "fiscal code" OR "breach" OR "leaked"'}, timeout=10)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]+)"', r.text)
                snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                for i, link in enumerate(links[:3]):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                    result["breach_results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
        except: pass

    return result


# ==================== VAT SEARCH (EU VIES) ====================
@router.get("/vat/{vat_number}")
async def vat_lookup(vat_number: str):
    vat = vat_number.strip().upper()
    result = {"input": vat, "valid": False, "country": None, "number": None, "company": None, "vies_valid": None, "source": "EU VIES"}

    # Extract country code (first 2 chars)
    if len(vat) < 4 or not vat[:2].isalpha():
        result["error"] = "Invalid VAT format — must start with 2-letter country code"
        return result

    result["country"] = vat[:2]
    result["number"] = vat[2:]

    # Validate via EU VIES
    async with httpx.AsyncClient(headers=HEADERS) as client:
        try:
            r = await client.get(f"https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{vat[:2]}/vat/{vat[2:]}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                result["vies_valid"] = data.get("isValid", False)
                result["valid"] = data.get("isValid", False)
                result["company"] = data.get("name")
                result["address"] = data.get("address")
                result["request_id"] = data.get("requestIdentifier")
        except: pass

        # Fallback: search for VAT info
        if not result["company"]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'"{vat}" VAT company registration'}, timeout=10)
                if r.status_code == 200:
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    if snippets:
                        result["note"] = re.sub(r'<[^>]+>', '', snippets[0]).strip()[:200]
            except: pass

    return result


# ==================== IBAN INTEL ====================
@router.get("/iban/{iban}")
async def iban_lookup(iban: str):
    iban_clean = iban.strip().replace(" ", "").replace("-", "").upper()
    result = {"input": iban_clean, "valid": False, "country": None, "bank_code": None, "account": None, "length": len(iban_clean)}

    # Country IBAN lengths
    country_lengths = {
        "AL":28,"AD":24,"AT":20,"AZ":28,"BH":22,"BY":28,"BE":16,"BA":20,
        "BR":29,"BG":22,"CR":22,"HR":21,"CY":28,"CZ":24,"DK":18,"DO":28,
        "TL":23,"EE":20,"FO":18,"FI":18,"FR":27,"GE":22,"DE":22,"GI":23,
        "GR":27,"GL":18,"GT":28,"HU":28,"IS":26,"IQ":23,"IE":22,"IL":23,
        "IT":27,"JO":30,"KZ":20,"XK":20,"KW":30,"LV":21,"LB":28,"LI":21,
        "LT":20,"LU":20,"MK":19,"MT":31,"MR":27,"MU":30,"MC":27,"MD":24,
        "ME":22,"NL":18,"NO":15,"PK":24,"PS":29,"PL":28,"PT":25,"QA":29,
        "RO":24,"LC":32,"SM":27,"ST":25,"SA":24,"RS":22,"SC":31,"SK":24,
        "SI":19,"ES":24,"SE":24,"CH":21,"TN":24,"TR":26,"UA":29,"AE":23,
        "GB":22,"VA":22,"VG":24",
    }

    if len(iban_clean) < 4:
        result["error"] = "Too short"
        return result

    result["country"] = iban_clean[:2]

    # Check length
    expected = country_lengths.get(iban_clean[:2])
    if expected and len(iban_clean) != expected:
        result["error"] = f"Invalid length for {iban_clean[:2]}: {len(iban_clean)} (expected {expected})"
        return result

    # MOD-97 validation (ISO 13616)
    moved = iban_clean[4:] + iban_clean[:4]
    numeric = ""
    for ch in moved:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - ord("A") + 10)

    try:
        remainder = int(numeric) % 97
        result["valid"] = remainder == 1
    except:
        result["valid"] = False

    if not result["valid"]:
        result["error"] = "Failed MOD-97 checksum validation"
        return result

    # Extract bank code and account
    if iban_clean[:2] == "IT":
        result["bank_code"] = iban_clean[5:10]
        result["account"] = iban_clean[15:27]
        result["check_digits"] = iban_clean[2:4]
        result["cin"] = iban_clean[4]
        result["abi"] = iban_clean[5:10]
        result["cab"] = iban_clean[10:15]
    elif iban_clean[:2] == "GB":
        result["bank_code"] = iban_clean[4:8]
        result["account"] = iban_clean[14:22]
    elif iban_clean[:2] == "DE":
        result["bank_code"] = iban_clean[4:12]
        result["account"] = iban_clean[12:22]
    else:
        result["bank_code"] = iban_clean[4:8]
        result["account"] = iban_clean[8:]

    # Check IBAN in breach databases
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        try:
            r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'"{iban_clean[:8]}..." IBAN leak OR breach OR stolen'}, timeout=10)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]+)"', r.text)
                result["breach_results"] = [{"url": l, "source": l.split("/")[2]} for l in links[:3]]
        except: pass

    return result


# ==================== VIN LOOKUP ====================
@router.get("/vin/{vin}")
async def vin_lookup(vin: str):
    vin = vin.strip().upper()
    result = {"input": vin, "valid": False, "decoded": {}, "api_data": None}

    # Basic VIN validation (17 chars, no I/O/Q)
    if len(vin) != 17:
        result["error"] = f"Invalid length: {len(vin)} (expected 17)"
        return result

    if re.search(r'[IOQ]', vin):
        result["error"] = "VIN contains invalid characters (I, O, Q not allowed)"
        return result

    if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
        result["error"] = "Invalid VIN format"
        return result

    result["valid"] = True

    # Decode basic info
    wm_world = {
        "1":"United States","2":"Canada","3":"Mexico","J":"Japan","K":"South Korea",
        "L":"China","M":"India","S":"United Kingdom","T":"Switzerland","V":"France",
        "W":"Germany","X":"Russia","Y":"Sweden/Finland","Z":"Italy",
    }
    result["decoded"] = {
        "wmi": vin[:3],
        "country": wm_world.get(vin[0], "Unknown"),
        "manufacturer_region": vin[0],
        "model_year_code": vin[9],
        "plant_code": vin[10],
        "vds": vin[3:9],
        "vis": vin[9:17],
    }

    # Model year decoding
    year_codes = "ABCDEFGHJKLMNPRSTVWXY123456789"
    year_map = {}
    for i, c in enumerate(year_codes):
        y = 2010 + i if i < 22 else 1980 + (i - 22)
        if y <= 2026:
            year_map[c] = y
    code = vin[9]
    if code in year_map:
        result["decoded"]["model_year"] = year_map[code]

    # NHTSA vPIC API (free, US vehicles)
    async with httpx.AsyncClient(headers=HEADERS) as client:
        try:
            r = await client.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json", timeout=15)
            if r.status_code == 200:
                data = r.json()
                results_list = data.get("Results", [{}])
                if results_list:
                    d = results_list[0]
                    result["api_data"] = {
                        "make": d.get("Make"),
                        "model": d.get("Model"),
                        "model_year": d.get("ModelYear"),
                        "body_class": d.get("BodyClass"),
                        "engine_cylinders": d.get("EngineCylinders"),
                        "engine_displacement": d.get("DisplacementL"),
                        "fuel_type": d.get("FuelTypePrimary"),
                        "transmission": d.get("TransmissionStyle"),
                        "manufacturer": d.get("Manufacturer"),
                        "plant_city": d.get("PlantCity"),
                        "plant_country": d.get("PlantCountry"),
                        "trim": d.get("Trim"),
                        "vehicle_type": d.get("VehicleType"),
                        "error_code": d.get("ErrorCode"),
                        "error_text": d.get("ErrorText"),
                    }
        except: pass

    return result


# ==================== TAX ID SEARCH (auto-detect) ====================
@router.get("/taxid/{taxid}")
async def taxid_search(taxid: str):
    taxid = taxid.strip()
    result = {"input": taxid, "detected_type": None, "valid": False, "data": {}}

    # Auto-detect type
    if re.match(r'^[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$', taxid.upper()):
        result["detected_type"] = "Italian Fiscal Code (Codice Fiscale)"
        cf_result = await fiscal_code_lookup(taxid.upper())
        result["data"] = cf_result
        result["valid"] = cf_result.get("valid", False)
    elif re.match(r'^[A-Z]{2}\d{10,12}$', taxid.upper()):
        result["detected_type"] = "VAT Number"
        vat_result = await vat_lookup(taxid.upper())
        result["data"] = vat_result
        result["valid"] = vat_result.get("valid", False)
    elif re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$', taxid.upper()):
        result["detected_type"] = "IBAN"
        iban_result = await iban_lookup(taxid.upper())
        result["data"] = iban_result
        result["valid"] = iban_result.get("valid", False)
    elif re.match(r'^\d{2}-\d{7}$', taxid):
        result["detected_type"] = "US EIN"
        result["data"] = {"ein": taxid, "note": "EIN format detected. Use IRS SS-4 for formal verification."}
        result["valid"] = True
    else:
        result["detected_type"] = "Unknown"
        result["data"] = {"note": "Could not auto-detect tax ID type. Try Italian CF, VAT, IBAN, or EIN format."}

    return result


# ==================== PARTIAL RECOVERY ====================
@router.get("/partialrecovery/{query}")
async def partial_recovery(query: str):
    query = query.strip()
    is_email = "@" in query

    result = {"query": query, "type": "email" if is_email else "phone", "platforms": []}

    platforms = [
        {"name": "Instagram", "check_url": "https://www.instagram.com/accounts/web/login/", "method": "password_reset"},
        {"name": "Battle.net", "check_url": "https://account.battle.net/password/recovery", "method": "password_reset"},
        {"name": "Epic Games", "check_url": "https://www.epicgames.com/id/logout", "method": "password_reset"},
        {"name": "EA", "check_url": "https://help.ea.com/en", "method": "password_reset"},
        {"name": "Apple", "check_url": "https://iforgot.apple.com", "method": "password_reset"},
        {"name": "Google", "check_url": "https://accounts.google.com/signin/recovery", "method": "password_reset"},
        {"name": "PayPal", "check_url": "https://www.paypal.com/signin?intent=PASSWORD_RESET", "method": "password_reset"},
        {"name": "Uber", "check_url": "https://auth.uber.com/v1/reset-password", "method": "password_reset"},
        {"name": "Twitter/X", "check_url": "https://twitter.com/account/begin_password_reset", "method": "password_reset"},
    ]

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        for p in platforms:
            status = "unknown"
            try:
                if is_email:
                    r = await client.get(f"https://html.duckduckgo.com/html/", params={"q": f'"{query}" site:{p["check_url"].split("/")[2]}'}, timeout=8)
                    if r.status_code == 200 and query.lower() in r.text.lower():
                        status = "possible_match"
                    else:
                        status = "no_direct_match"
                else:
                    status = "phone_recovery_available"
            except:
                status = "check_manually"
            result["platforms"].append({"name": p["name"], "status": status, "method": p["method"], "recovery_url": p["check_url"]})

    return result


# ==================== PHONE → EMAIL ====================
@router.get("/phonetoemail/{phone}")
async def phone_to_email(phone: str):
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    result = {"phone": phone, "emails_found": [], "methods_checked": []}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search for phone number in public data
        dorks = [
            f'"{phone}" email',
            f'"{phone}" "@gmail.com" OR "@outlook.com" OR "@yahoo.com"',
            f'"{phone}" site:pastebin.com OR site:ghostbin.com',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    emails = re.findall(r'[\w.+-]+@[\w.-]+\.\w{2,}', r.text)
                    for email in emails:
                        if email not in result["emails_found"] and len(email) < 60:
                            result["emails_found"].append(email)
                    result["methods_checked"].append("duckduckgo")
            except: pass

        # Check paste sites
        try:
            r = await client.get("https://pastebin.com/search", params={"q": phone}, timeout=10)
            if r.status_code == 200:
                emails = re.findall(r'[\w.+-]+@[\w.-]+\.\w{2,}', r.text)
                for email in emails:
                    if email not in result["emails_found"] and len(email) < 60:
                        result["emails_found"].append(email)
                result["methods_checked"].append("pastebin")
        except: pass

    result["count"] = len(result["emails_found"])
    return result


# ==================== EMAIL → PHONE ====================
@router.get("/emailtophone/{email}")
async def email_to_phone(email: str):
    email = email.strip().lower()
    result = {"email": email, "phones_found": [], "methods_checked": []}

    if "@" not in email:
        raise HTTPException(400, "Invalid email format")

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        dorks = [
            f'"{email}" phone OR telephone OR mobile OR cell',
            f'"{email}" "+1" OR "+44" OR "+39" OR "+49" OR "+33"',
            f'"{email}" site:pastebin.com',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    phones = re.findall(r'[\+]?[\d\-\(\)\s]{8,20}', r.text)
                    for phone in phones:
                        clean = re.sub(r'[^\d+]', '', phone)
                        if len(clean) >= 8 and clean not in result["phones_found"]:
                            result["phones_found"].append(clean)
                    result["methods_checked"].append("duckduckgo")
            except: pass

        try:
            r = await client.get("https://pastebin.com/search", params={"q": email}, timeout=10)
            if r.status_code == 200:
                phones = re.findall(r'[\+]?[\d\-\(\)\s]{8,20}', r.text)
                for phone in phones:
                    clean = re.sub(r'[^\d+]', '', phone)
                    if len(clean) >= 8 and clean not in result["phones_found"]:
                        result["phones_found"].append(clean)
                result["methods_checked"].append("pastebin")
        except: pass

    result["count"] = len(result["phones_found"])
    return result


# ==================== SHADOW LEAK ====================
@router.get("/shadowleak/{query}")
async def shadow_leak(query: str):
    query = query.strip()
    result = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search for partial matches in public breach databases
        dorks = [
            f'"{query}" "shadow" leak OR breach OR dump',
            f'"{query}" site:pastebin.com "shadow"',
            f'"{query}" "partial" breach OR leaked',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        result["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
            except: pass

    seen = set()
    unique = []
    for r in result["results"]:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    result["results"] = unique[:15]
    result["count"] = len(result["results"])
    return result


# ==================== FIVEM HUNTER ====================
@router.get("/fivemhunter/{query}")
async def fivem_hunter(query: str):
    query = query.strip()
    result = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search FiveM related databases
        dorks = [
            f'site:fivem.com "{query}"',
            f'"FiveM" "{query}" player OR identifier OR license',
            f'"cfx.re" "{query}"',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        result["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
            except: pass

    seen = set()
    unique = []
    for r in result["results"]:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    result["results"] = unique[:10]
    result["count"] = len(result["results"])
    return result


# ==================== DISCORD GRAVE ====================
@router.get("/discordgrave/{query}")
async def discord_grave(query: str):
    query = query.strip()
    result = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        dorks = [
            f'"discord" "{query}" "deleted" OR "banned" OR "grave" OR "removed"',
            f'site:discord.scrape "{query}"',
            f'"discord id" "{query}" breach OR leaked OR deleted',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        result["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
            except: pass

    seen = set()
    unique = []
    for r in result["results"]:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    result["results"] = unique[:10]
    result["count"] = len(result["results"])
    return result


# ==================== PAYPAL TRACE ====================
@router.get("/paypaltrace/{query}")
async def paypal_trace(query: str):
    query = query.strip()
    result = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        dorks = [
            f'"paypal" "{query}" log OR transaction OR credentials',
            f'site:buycraft.com OR site:tebex.com "{query}"',
            f'"paypal" "{query}" "payment" OR "receipt"',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        result["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
            except: pass

    seen = set()
    unique = []
    for r in result["results"]:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    result["results"] = unique[:10]
    result["count"] = len(result["results"])
    return result


# ==================== GITHUB OSINT ====================
@router.get("/github/{query}")
async def github_osint(query: str):
    query = query.strip()
    result = {"query": query, "user": None, "repos": [], "gists": [], "events": []}

    async with httpx.AsyncClient(headers=HEADERS) as client:
        # User profile
        try:
            r = await client.get(f"https://api.github.com/users/{query}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                result["user"] = {
                    "login": d.get("login"),
                    "name": d.get("name"),
                    "bio": d.get("bio"),
                    "blog": d.get("blog"),
                    "location": d.get("location"),
                    "email": d.get("email"),
                    "company": d.get("company"),
                    "public_repos": d.get("public_repos"),
                    "followers": d.get("followers"),
                    "following": d.get("following"),
                    "created_at": d.get("created_at"),
                    "avatar_url": d.get("avatar_url"),
                    "html_url": d.get("html_url"),
                }
        except: pass

        # Recent repos
        try:
            r = await client.get(f"https://api.github.com/users/{query}/repos?sort=updated&per_page=5", timeout=10)
            if r.status_code == 200:
                for repo in r.json()[:5]:
                    result["repos"].append({
                        "name": repo.get("name"),
                        "description": repo.get("description"),
                        "language": repo.get("language"),
                        "stars": repo.get("stargazers_count"),
                        "url": repo.get("html_url"),
                    })
        except: pass

        # Recent gists
        try:
            r = await client.get(f"https://api.github.com/users/{query}/gists?per_page=3", timeout=10)
            if r.status_code == 200:
                for gist in r.json()[:3]:
                    files = list(gist.get("files", {}).keys())
                    result["gists"].append({
                        "description": gist.get("description"),
                        "files": files[:3],
                        "url": gist.get("html_url"),
                        "created": gist.get("created_at"),
                    })
        except: pass

        # Recent events
        try:
            r = await client.get(f"https://api.github.com/users/{query}/events/public?per_page=5", timeout=10)
            if r.status_code == 200:
                for ev in r.json()[:5]:
                    result["events"].append({
                        "type": ev.get("type"),
                        "repo": ev.get("repo", {}).get("name"),
                        "created": ev.get("created_at"),
                    })
        except: pass

    return result


# ==================== MINECRAFT LOOKUP ====================
@router.get("/minecraft/{username}")
async def minecraft_lookup(username: str):
    username = username.strip()
    result = {"username": username, "found": False, "profiles": [], "name_history": []}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Mojang API
        try:
            r = await client.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                result["found"] = True
                result["uuid"] = d.get("id")
                result["display_name"] = d.get("name")

                # Skin texture
                if d.get("id"):
                    try:
                        r2 = await client.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{d['id']}", timeout=10)
                        if r2.status_code == 200:
                            profile = r2.json()
                            for prop in profile.get("properties", []):
                                if prop.get("name") == "textures":
                                    import base64
                                    tex = base64.b64decode(prop["value"])
                                    tex_data = __import__("json").loads(tex)
                                    skin_url = tex_data.get("textures", {}).get("SKIN", {}).get("url")
                                    cape_url = tex_data.get("textures", {}).get("CAPE", {}).get("url")
                                    result["skin_url"] = skin_url
                                    result["cape_url"] = cape_url
                    except: pass
        except: pass

        # NameMC
        try:
            r = await client.get(f"https://namemc.com/profile/{username}", timeout=10, follow_redirects=True)
            if r.status_code == 200:
                # Extract name history from NameMC page
                names = re.findall(r'class="text-body"[^>]*>(.*?)</a>', r.text)
                result["name_history"] = [n.strip() for n in names if n.strip() and len(n.strip()) < 20][:10]
        except: pass

    return result


# ==================== FIVEM LOOKUP ====================
@router.get("/fivem/{query}")
async def fivem_lookup(query: str):
    query = query.strip()
    result = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search FiveM forums and resources
        try:
            r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'site:fivem.com OR site:cfx.re "{query}"'}, timeout=10)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]+)"', r.text)
                snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                for i, link in enumerate(links[:5]):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                    result["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
        except: pass

        # CFX Dumps search
        try:
            r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'"cfx.re" OR "FiveM" "{query}" license OR server OR player'}, timeout=10)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]+)"', r.text)
                snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                for i, link in enumerate(links[:3]):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                    result["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
        except: pass

    seen = set()
    unique = []
    for r in result["results"]:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    result["results"] = unique[:10]
    result["count"] = len(result["results"])
    return result


# ==================== BUSINESS SEARCH ====================
@router.get("/business/{query}")
async def business_search(query: str):
    query = query.strip()
    result = {"query": query, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # OpenCorporates
        try:
            r = await client.get(f"https://api.opencorporates.com/v0.4/companies/search?q={query}&per_page=5", timeout=10)
            if r.status_code == 200:
                data = r.json()
                companies = data.get("results", {}).get("companies", [])
                for c in companies:
                    co = c.get("company", {})
                    result["results"].append({
                        "name": co.get("name"),
                        "number": co.get("company_number"),
                        "jurisdiction": co.get("jurisdiction_code"),
                        "status": co.get("current_status"),
                        "incorporated": co.get("incorporation_date"),
                        "url": co.get("opencorporates_url"),
                        "source": "OpenCorporates",
                    })
        except: pass

        # Companies House (UK)
        try:
            r = await client.get(f"https://api.company-information.service.gov.uk/search/companies?q={query}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("items", [])[:3]:
                    result["results"].append({
                        "name": item.get("title"),
                        "number": item.get("company_number"),
                        "status": item.get("company_status"),
                        "address": item.get("address_snippet"),
                        "source": "Companies House",
                    })
        except: pass

    seen = set()
    unique = []
    for r in result["results"]:
        key = r.get("name", "") + r.get("number", "")
        if key not in seen:
            seen.add(key)
            unique.append(r)
    result["results"] = unique[:10]
    result["count"] = len(result["results"])
    return result


# ==================== INTELX SEARCH ====================
@router.get("/intelx/{query}")
async def intelx_search(query: str):
    query = query.strip()
    result = {"query": query, "results": [], "count": 0, "note": "Results from public Intelligence X search"}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        try:
            r = await client.get("https://html.duckduckgo.com/html/", params={"q": f'site:intelx.io "{query}" OR "intelx" "{query}"'}, timeout=10)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://[^"]+)"', r.text)
                snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                for i, link in enumerate(links[:5]):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                    result["results"].append({"url": link, "source": "intelx.io", "snippet": snippet[:200]})
        except: pass

    result["count"] = len(result["results"])
    return result


# ==================== FOLDER INTEL ====================
@router.get("/folder/{path:path}")
async def folder_intel(path: str):
    path = path.strip("/")
    result = {"path": path, "results": [], "count": 0}

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Search for folder/directory leaks
        dorks = [
            f'"folder" OR "directory" "{path}" leak OR dump OR breach',
            f'site:pastebin.com OR site:ghostbin.com "{path}"',
            f'"{path}" "backup" OR "database" OR "sql"',
        ]
        for dork in dorks[:2]:
            try:
                r = await client.get("https://html.duckduckgo.com/html/", params={"q": dork}, timeout=10)
                if r.status_code == 200:
                    links = re.findall(r'href="(https?://[^"]+)"', r.text)
                    snippets = re.findall(r'class="result__snippet">(.*?)</a>', r.text, re.DOTALL)
                    for i, link in enumerate(links[:3]):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                        result["results"].append({"url": link, "source": link.split("/")[2], "snippet": snippet[:200]})
            except: pass

    seen = set()
    unique = []
    for r in result["results"]:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    result["results"] = unique[:10]
    result["count"] = len(result["results"])
    return result
