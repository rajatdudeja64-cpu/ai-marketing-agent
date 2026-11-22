import json
from datetime import datetime, timezone
from pathlib import Path

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


def validate_google_ads_copy(headlines: list[str], descriptions: list[str]) -> list[str]:
    """Return a list of any Google Ads character-limit violations (30/90 rule)."""
    issues = []
    for h in headlines:
        if len(h) > 30:
            issues.append(f"Headline too long ({len(h)}/30 chars): '{h}'")
    for d in descriptions:
        if len(d) > 90:
            issues.append(f"Description too long ({len(d)}/90 chars): '{d}'")
    return issues
