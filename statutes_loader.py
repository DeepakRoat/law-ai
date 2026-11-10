import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

KB_FILE_PATH = Path(__file__).parent / "data" / "statutes_kb.json"
API_CACHE_PATH = Path(__file__).parent / "data" / "api_statutes_cache.json"


def load_statutes_from_file(filepath: Path = KB_FILE_PATH) -> Dict[str, Any]:
    """Loads verified Indian statutes from the local JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Statutes knowledge base file not found at: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_laws_via_api(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Fetches live statutory provisions / judgments from:
    1. Official Indian Kanoon API (https://api.indiankanoon.org/search/) if INDIAN_KANOON_API_TOKEN is set.
    2. Open Kanoon Pilot API (https://api.kanoon.dev/v1/search) if no token is required/present.
    Also caches results to data/api_statutes_cache.json for offline auditability.
    """
    ik_token = os.environ.get("INDIAN_KANOON_API_TOKEN", "").strip()
    results_list: List[Dict[str, str]] = []
    source_used = "local_file_only"

    # Path A: Official Indian Kanoon API (POST /search/ with Token Auth)
    if ik_token:
        try:
            url = "https://api.indiankanoon.org/search/"
            headers = {
                "Authorization": f"Token {ik_token}",
                "Accept": "application/json"
            }
            params = {"formInput": query, "pagenum": 0}
            resp = requests.post(url, headers=headers, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                source_used = "api.indiankanoon.org"
                for doc in data.get("docs", [])[:max_results]:
                    clean_headline = re.sub(r"<[^>]+>", "", doc.get("headline", ""))
                    results_list.append({
                        "doc_id": str(doc.get("tid", "")),
                        "title": re.sub(r"<[^>]+>", "", doc.get("title", "")),
                        "source": doc.get("docsource", "Indian Kanoon"),
                        "snippet": clean_headline,
                        "url": f"https://indiankanoon.org/doc/{doc.get('tid', '')}/"
                    })
        except Exception as e:
            source_used = f"indiankanoon_error ({str(e)})"

    # Path B: Keyless Kanoon REST API (GET https://api.kanoon.dev/v1/search)
    if not results_list:
        try:
            url = "https://api.kanoon.dev/v1/search"
            params = {"q": query, "limit": max_results}
            resp = requests.get(url, params=params, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("results", data.get("items", []))
                if items:
                    source_used = "api.kanoon.dev"
                    for item in items[:max_results]:
                        results_list.append({
                            "doc_id": str(item.get("id", item.get("document_id", "N/A"))),
                            "title": item.get("title", item.get("court", "Verified Legal Record")),
                            "source": item.get("court", "Indian Court Record"),
                            "snippet": item.get("snippet", item.get("text", ""))[:350],
                            "url": item.get("source_url", item.get("document_url", "https://docs.kanoon.dev"))
                        })
        except Exception:
            pass

    payload = {
        "query": query,
        "api_source": source_used,
        "live_records": results_list
    }

    # Cache API response to local file for traceability
    try:
        API_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {}
        if API_CACHE_PATH.exists():
            with open(API_CACHE_PATH, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        cache_data[query] = payload
        with open(API_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return payload


def get_domain_context(domain: str, use_live_api: bool = True) -> Dict[str, Any]:
    """
    Loads the domain's statutory ground truth from `data/statutes_kb.json`
    and optionally enriches it with live API lookups.
    """
    statutes_db = load_statutes_from_file()
    if domain not in statutes_db:
        return {
            "prompt_context": "NO VERIFIED STATUTES AVAILABLE. ESCALATE TO REAL LAWYER.",
            "api_data": {"api_source": "none", "live_records": []},
            "allowed_sections": {}
        }

    info = statutes_db[domain]
    lines = [
        f"DOMAIN: {info['domain_name']} (Loaded from data/statutes_kb.json)",
        f"PRIMARY STATUTE: {info['primary_act']}",
        "ALLOWED STATUTE SECTIONS (CITE ONLY FROM THIS VERIFIED LIST):"
    ]
    for sec, desc in info["allowed_sections"].items():
        lines.append(f"- {sec}: {desc}")

    lines.append("\nSTANDARD REMEDY STEPS:")
    lines.extend(info["remedy_steps"])

    api_data = {"api_source": "disabled", "live_records": []}
    if use_live_api:
        search_q = info.get("api_search_query", info["primary_act"])
        api_data = fetch_laws_via_api(search_q)
        if api_data["live_records"]:
            lines.append(f"\nLIVE API SUPPLEMENTAL RECORDS (Fetched via {api_data['api_source']}):")
            for rec in api_data["live_records"]:
                lines.append(f"- [{rec['title']} ({rec['source']})]: {rec['snippet']} (Ref: {rec['url']})")

    return {
        "prompt_context": "\n".join(lines),
        "api_data": api_data,
        "allowed_sections": info["allowed_sections"]
    }


def validate_citations(text: str, domain: str) -> Dict[str, Any]:
    """
    Deterministic Anti-Hallucination Guardrail.
    Scans output text for any 'Section X', 'Order X', 'Rule X', or 'Article X'
    and verifies them against `data/statutes_kb.json` for the active domain.
    """
    statutes_db = load_statutes_from_file()
    if domain not in statutes_db:
        return {"passed": True, "flagged_citations": [], "cleaned_text": text}

    allowed_keys = list(statutes_db[domain]["allowed_sections"].keys())
    allowed_tokens = set()
    for k in allowed_keys:
        tokens = re.findall(r"(?:Section|Rule|Order|Article)\s+([A-Za-z0-9\(\)]+)", k, re.IGNORECASE)
        for t in tokens:
            allowed_tokens.add(t.upper())
            base = re.sub(r"\(.*?\)", "", t).upper()
            allowed_tokens.add(base)

    pattern = r"\b(Section|Rule|Order|Article)\s+([0-9A-Za-z\(\)]+)"
    matches = re.findall(pattern, text, re.IGNORECASE)

    flagged: List[str] = []
    cleaned_text = text

    for prefix, sec_id in matches:
        clean_id = sec_id.upper().rstrip(".,;:")
        base_id = re.sub(r"\(.*?\)", "", clean_id)
        if clean_id not in allowed_tokens and base_id not in allowed_tokens:
            citation_str = f"{prefix} {sec_id}"
            flagged.append(citation_str)
            cleaned_text = re.sub(
                rf"\b{re.escape(prefix)}\s+{re.escape(sec_id)}\b",
                "[UNVERIFIED CITATION BLOCKED BY GUARDRAIL]",
                cleaned_text,
                flags=re.IGNORECASE
            )

    return {
        "passed": len(flagged) == 0,
        "flagged_citations": flagged,
        "cleaned_text": cleaned_text,
        "allowed_sections_checked": allowed_keys
    }