"""
Generate city names via Featherless AI.
"""
import json, os, re, time
import urllib.request, urllib.error

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY", "")
FEATHERLESS_BASE    = "https://api.featherless.ai/v1"
MODEL               = os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

CATEGORY_HINTS = {
    "fantasy":  "Use flowing, elvish or arcane-sounding syllables. Evoke magic, nature, ancient power.",
    "medieval": "Use Germanic, Anglo-Saxon, or Latin roots. Evoke castles, guilds, trade routes.",
    "sci-fi":   "Use technical prefixes, Greek/Latin roots, alphanumeric suffixes. Evoke colonies, stations, megacities.",
    "ancient":  "Use Sumerian, Egyptian, Greek, or Roman roots. Evoke temples, empires, river civilizations.",
    "any":      "The style should match the city description.",
}


def _call_api(prompt: str) -> str:
    if not FEATHERLESS_API_KEY:
        raise ValueError("FEATHERLESS_API_KEY is not set.")
    payload = json.dumps({
        "model": MODEL, "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85, "max_tokens": 400,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FEATHERLESS_API_KEY}",
        "User-Agent": "Mozilla/5.0 (compatible; CityNameGenerator/1.0)",
    }
    for attempt in range(8):
        req = urllib.request.Request(f"{FEATHERLESS_BASE}/chat/completions",
                                     data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 7:
                time.sleep(3); continue
            raise ConnectionError(f"Featherless API error {e.code}: {e.read().decode()}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot reach Featherless: {e}")


def _repair_json(text: str) -> str:
    result, in_string, esc = [], False, False
    for i, ch in enumerate(text):
        if esc: result.append(ch); esc = False; continue
        if ch == '\\': result.append(ch); esc = True; continue
        if ch == '"':
            if not in_string: in_string = True; result.append(ch)
            else:
                rest = text[i+1:].lstrip()
                if rest and rest[0] in (',', ']', '}', ':'): in_string = False; result.append(ch)
        else: result.append(ch)
    return ''.join(result)


def _parse(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start != -1 and end > start:
        for candidate in (raw[start:end], _repair_json(raw[start:end])):
            try:
                p = json.loads(candidate)
                names = p.get("names", [])
                if isinstance(names, list) and names:
                    seen = list(dict.fromkeys(str(n) for n in names if n))
                    explanations = p.get("explanations", [])
                    if isinstance(explanations, list) and explanations:
                        reasoning = "  ".join(f"**{n}** — {e}" for n, e in zip(seen, explanations) if e)
                    else:
                        reasoning = p.get("reasoning", "")
                    return {"names": seen, "reasoning": reasoning}
            except Exception:
                continue
    # Fallback
    names = list(dict.fromkeys(n for n in re.findall(r'"([A-Z][a-zA-Z0-9\-]{2,20})"', raw)
                               if n not in ("Name1","Name2")))[:4]
    return {"names": names or ["Unnamed"], "reasoning": raw[:300]}


def generate_city_names(description: str, category: str = "any", count: int = 2) -> dict:
    hint = CATEGORY_HINTS.get(category.lower(), CATEGORY_HINTS["any"])
    prompt = (
        f"You are a master world-builder and city naming expert.\n"
        f"{hint}\n\n"
        f"Reply with ONLY this JSON, no extra text, no quotation marks inside the text fields:\n"
        f'{{"names":["CityName1","CityName2"],"explanations":["2-3 sentences about CityName1 - its linguistic roots, what it evokes, and why it fits this city","same for CityName2"]}}\n\n'
        f"City description: {description}\n"
        f"Generate exactly {count} city names. IMPORTANT: do not use quotation marks inside the explanation text."
    )
    raw = _call_api(prompt)
    return _parse(raw)


def check_api_connection() -> bool:
    if not FEATHERLESS_API_KEY:
        return False
    try:
        req = urllib.request.Request(f"{FEATHERLESS_BASE}/models",
            headers={"Authorization": f"Bearer {FEATHERLESS_API_KEY}", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False
