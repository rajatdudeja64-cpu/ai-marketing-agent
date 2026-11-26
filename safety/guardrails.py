import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

LOG_FILE = Path("activity_log.jsonl")


def log_activity(action: str, details: dict, status: str = "INFO") -> None:
    """Save every agent action and approval decision to a local audit log."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "action": action,
        "details": details,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_budget_guardrail(
    requested_monthly: float,
    max_monthly: float,
    max_daily: float,
    emergency_stop: bool = False,
) -> tuple[bool, str]:
    """Block any campaign if Emergency Stop is active or budget exceeds caps."""
    if emergency_stop:
        log_activity("BUDGET_CHECK", {"reason": "Emergency stop active"}, status="BLOCKED")
        return False, "BLOCKED: Emergency Stop is active. All campaign actions are paused."

    if requested_monthly <= 0:
        return False, "BLOCKED: Monthly budget must be greater than 0."

    if requested_monthly > max_monthly:
        msg = f"BLOCKED: Requested monthly budget ({requested_monthly:,.0f}) exceeds your hard limit ({max_monthly:,.0f})."
        log_activity("BUDGET_CHECK", {"requested": requested_monthly, "max_monthly": max_monthly}, status="BLOCKED")
        return False, msg

    estimated_daily = requested_monthly / 30
    if estimated_daily > max_daily:
        msg = f"BLOCKED: Estimated daily spend ({estimated_daily:,.0f}/day) exceeds your daily cap ({max_daily:,.0f}/day)."
        log_activity("BUDGET_CHECK", {"estimated_daily": estimated_daily, "max_daily": max_daily}, status="BLOCKED")
        return False, msg

    log_activity("BUDGET_CHECK", {"requested": requested_monthly, "estimated_daily": round(estimated_daily, 2)}, status="APPROVED")
    return True, f"PASSED: Budget within limits (~{estimated_daily:,.0f}/day)."


def validate_landing_url(url: str) -> tuple[bool, str]:
    """Validate that a Google Ads landing page URL uses http(s) and includes a host."""
    cleaned = (url or "").strip()
    if not cleaned:
        return False, "BLOCKED: Landing Page URL is required."
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False, "BLOCKED: Landing Page URL must start with http:// or https:// and include a valid domain."
    if "." not in parsed.netloc and parsed.hostname != "localhost":
        return False, "BLOCKED: Landing Page URL must include a valid domain name (e.g., https://www.milkbasket.com)."
    return True, cleaned


def validate_google_ads_copy(headlines: list[str], descriptions: list[str]) -> list[str]:
    """Return a list of Google Ads RSA copy issues (30/90 char rule and minimum asset counts)."""
    issues = []
    unique_headlines = set()
    for h in headlines:
        text = str(h).strip()
        if not text:
            issues.append("Empty headline found.")
            continue
        unique_headlines.add(text)
        if len(text) > 30:
            issues.append(f"Headline too long ({len(text)}/30 chars): '{text}'")

    unique_descriptions = set()
    for d in descriptions:
        text = str(d).strip()
        if not text:
            issues.append("Empty description found.")
            continue
        unique_descriptions.add(text)
        if len(text) > 90:
            issues.append(f"Description too long ({len(text)}/90 chars): '{text}'")

    if len(unique_headlines) < 3:
        issues.append(f"Google Ads requires at least 3 unique headlines (found {len(unique_headlines)}).")
    if len(unique_descriptions) < 2:
        issues.append(f"Google Ads requires at least 2 unique descriptions (found {len(unique_descriptions)}).")
    return issues
