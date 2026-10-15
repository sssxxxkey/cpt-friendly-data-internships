#!/usr/bin/env python3
"""Refresh public U.S. data internship postings from ATS and community feeds."""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "sources.json"
JOBS_FILE = ROOT / "data" / "jobs.csv"
FIELDS = [
    "company", "title", "location", "workplace_type", "cycle", "job_url",
    "source_url", "cpt_status", "sponsorship_wording", "authorization_evidence",
    "first_seen_utc", "last_seen_utc", "listing_status",
]
ROLE_TERMS = re.compile(
    r"data analyst|business intelligence|business analyst|data scientist|"
    r"data science|data analytics|analytics intern|business analytics|"
    r"product analyst|decision science",
    re.I,
)
INTERNSHIP = re.compile(r"\b(intern|internship|co-?op)\b", re.I)
NON_US = re.compile(r"\b(canada|united kingdom|london,? uk|india|singapore|germany|france|australia)\b", re.I)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def classify_authorization(text: str) -> tuple[str, str, str]:
    text = re.sub(r"\s+", " ", clean_text(text))
    explicit_yes = re.search(r"\b(CPT|curricular practical training|F-?1)\b.{0,100}\b(accept|eligible|welcome|consider|authorized)\b|\b(accept|eligible|welcome|consider)\b.{0,100}\b(CPT|curricular practical training|F-?1)\b", text, re.I)
    explicit_no = re.search(r"\b(no|not|ineligible|unable to accept|do not accept|cannot accept)\b.{0,80}\b(CPT|curricular practical training|F-?1)\b|\b(CPT|curricular practical training|F-?1)\b.{0,80}\b(not accepted|not eligible|prohibited|not permitted)\b", text, re.I)
    generic = re.search(r"(will not|do not|does not|unable to|cannot)\s+(provide|offer|sponsor|support).{0,80}(visa|sponsor|work authorization)|without.{0,40}(sponsorship|visa)|no sponsorship|must not require.{0,60}(sponsorship|visa|work authorization)", text, re.I)
    evidence = ""
    if explicit_no:
        status = "explicit_cpt_no"
        evidence = explicit_no.group(0)
    elif explicit_yes:
        status = "explicit_cpt_yes"
        evidence = explicit_yes.group(0)
    elif generic:
        status = "possible_restriction"
        evidence = generic.group(0)
    else:
        status = "unknown"
    sponsorship = "generic_no_sponsorship_wording" if generic else "no_generic_restriction_detected"
    return status, sponsorship, evidence[:220]


def fetch_json(url: str) -> object:
    request = urllib.request.Request(url, headers={"User-Agent": "cpt-friendly-data-internships/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_source(source: dict) -> list[dict]:
    if source["platform"] == "community_json":
        payload = fetch_json(source["feed_url"])
        return payload if isinstance(payload, list) else payload.get("listings", [])
    platform, board = source["platform"], urllib.parse.quote(source["board"], safe="")
    if platform == "greenhouse":
        payload = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
        return payload.get("jobs", [])
    if platform == "lever":
        return fetch_json(f"https://api.lever.co/v0/postings/{board}?mode=json")
    if platform == "ashby":
        payload = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
        return payload.get("jobs", [])
    raise ValueError(f"Unsupported platform: {platform}")


def normalize(source: dict, raw: dict, seen: str) -> dict | None:
    if source["platform"] == "community_json":
        if not raw.get("active", True) or not raw.get("is_visible", True):
            return None
        title = raw.get("title") or ""
        location_values = raw.get("locations") or []
        location = "; ".join(str(item) for item in location_values) or "Location not stated"
        terms = raw.get("terms") or []
        cycle_text = " ".join([title, *[str(term) for term in terms]])
        if not re.search(r"\bSummer\s+2027\b", cycle_text, re.I):
            return None
        # Filter by title to avoid pulling unrelated roles whose descriptions mention analytics.
        if not INTERNSHIP.search(title) or not ROLE_TERMS.search(title):
            return None
        if NON_US.search(location):
            return None
        sponsorship_meta = str(raw.get("sponsorship") or "").strip().lower()
        if sponsorship_meta == "does not offer sponsorship":
            return None
        job_url = raw.get("url", "")
        if not job_url:
            return None
        cpt, sponsorship, evidence = classify_authorization("")
        return {
            "company": raw.get("company_name") or source["company"],
            "title": clean_text(title), "location": location,
            "workplace_type": "remote" if re.search(r"\bremote\b", location, re.I) else "not stated",
            "cycle": "Summer 2027", "job_url": job_url,
            "source_url": source["careers_url"], "cpt_status": cpt,
            "sponsorship_wording": "not_stated_in_community_feed" if not sponsorship_meta else sponsorship_meta,
            "authorization_evidence": evidence,
            "first_seen_utc": "", "last_seen_utc": seen, "listing_status": "listed",
        }

    title = raw.get("title") or raw.get("text") or ""
    description = raw.get("content") or raw.get("description") or raw.get("descriptionPlain") or ""
    categories = raw.get("categories") or {}
    location_obj = raw.get("location") or categories.get("location") or ""
    if isinstance(location_obj, dict):
        location = location_obj.get("name", "")
    else:
        location = str(location_obj)
    plain = clean_text(description)
    # Filter by title, not description: otherwise general operations roles that
    # merely mention analytics in their copy get pulled into a data-role tracker.
    if not INTERNSHIP.search(title) or not ROLE_TERMS.search(title):
        return None
    if NON_US.search(location):
        return None

    if source["platform"] == "greenhouse":
        job_url = raw.get("absolute_url", "")
    elif source["platform"] == "lever":
        job_url = raw.get("hostedUrl", "")
    else:
        job_url = raw.get("jobUrl", "")
    if not job_url:
        return None

    low = (title + " " + plain).lower()
    workplace = "remote" if "remote" in low else ("hybrid" if "hybrid" in low else ("on-site" if "on-site" in low or "onsite" in low else "not stated"))
    cycle_match = re.search(r"(?:summer|fall|spring|winter)\s+20\d{2}", title + " " + plain, re.I)
    cycle = cycle_match.group(0).title() if cycle_match else "not stated"
    cpt, sponsorship, evidence = classify_authorization(plain)
    if cpt == "explicit_cpt_no" or sponsorship == "generic_no_sponsorship_wording":
        return None
    return {
        "company": source["company"], "title": clean_text(title), "location": location,
        "workplace_type": workplace, "cycle": cycle, "job_url": job_url,
        "source_url": source["careers_url"], "cpt_status": cpt,
        "sponsorship_wording": sponsorship, "authorization_evidence": evidence,
        "first_seen_utc": "", "last_seen_utc": seen, "listing_status": "listed",
    }


def load_rows() -> dict[str, dict]:
    if not JOBS_FILE.exists():
        return {}
    with JOBS_FILE.open(newline="", encoding="utf-8") as stream:
        return {row["job_url"]: row for row in csv.DictReader(stream) if row.get("job_url")}


def update() -> int:
    config = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    rows = load_rows()
    timestamp = now_utc()
    refreshed_urls: set[str] = set()
    successful_source_urls: set[str] = set()
    successful_sources = 0
    failures: list[str] = []

    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue
        try:
            postings = fetch_source(source)
            successful_sources += 1
            successful_source_urls.add(source["careers_url"])
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            failures.append(f"{source.get('company', 'unknown')}: {error}")
            continue
        for raw in postings:
            row = normalize(source, raw, timestamp)
            if row is None:
                continue
            key = row["job_url"]
            refreshed_urls.add(key)
            if key in rows:
                existing = rows[key]
                row["first_seen_utc"] = existing.get("first_seen_utc") or timestamp
                official_source_urls = {item.get("careers_url") for item in config.get("sources", []) if item.get("platform") in {"greenhouse", "lever", "ashby"}}
                if source["platform"] == "community_json" and existing.get("source_url") in official_source_urls:
                    row = existing
                    row["last_seen_utc"] = timestamp
                    row["listing_status"] = "listed"
            else:
                row["first_seen_utc"] = timestamp
            rows[key] = row

    if successful_sources == 0:
        print("No sources refreshed successfully; leaving CSV unchanged.", file=sys.stderr)
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    # Only close records from sources that successfully responded. Other sources may have failed.
    for key, row in rows.items():
        if row.get("source_url") in successful_source_urls and key not in refreshed_urls:
            row["listing_status"] = "not_seen"

    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with JOBS_FILE.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows.values(), key=lambda item: (item["cpt_status"], item["company"].lower(), item["title"].lower())))
    print(f"Refreshed {successful_sources} sources; {len(rows)} matching listings retained.")
    for failure in failures:
        print(f"Source warning: {failure}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(update())
