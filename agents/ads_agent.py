from integrations.google_ads import create_full_paused_search_campaign, list_campaigns
from safety.guardrails import check_budget_guardrail, log_activity, validate_landing_url


def execute_approved_google_ads_campaign(
    business_name: str,
    google_ads_monthly_budget: float,
    max_monthly: float,
    max_daily: float,
    customer_id: str,
    login_customer_id: str,
    keywords: list[dict],
    headlines: list[str],
    descriptions: list[str],
    final_url: str,
    strategy_name: str = "",
    negative_keywords: list[str] | None = None,
    emergency_stop: bool = False,
) -> dict:
    """Re-verify safety guardrails, then create a complete PAUSED Search campaign in Google Ads."""
    allowed, msg = check_budget_guardrail(
        requested_monthly=google_ads_monthly_budget,
        max_monthly=max_monthly,
        max_daily=max_daily,
        emergency_stop=emergency_stop,
    )
    if not allowed:
        return {"success": False, "message": msg}

    url_ok, url_or_err = validate_landing_url(final_url)
    if not url_ok:
        log_activity("URL_CHECK", {"business": business_name, "final_url": final_url}, status="BLOCKED")
        return {"success": False, "message": url_or_err}

    daily_budget = max(1.0, round(google_ads_monthly_budget / 30, 2))
    campaign_name = f"{business_name} - {strategy_name} - AI Search" if strategy_name else f"{business_name} - AI Search"

    result = create_full_paused_search_campaign(
        customer_id=customer_id.replace("-", "").strip(),
        login_customer_id=login_customer_id.replace("-", "").strip(),
        campaign_name=campaign_name,
        daily_budget_amount=daily_budget,
        keywords=keywords,
        headlines=headlines,
        descriptions=descriptions,
        final_url=url_or_err,
        negative_keywords=negative_keywords,
    )
    neg_count = result.get("negative_keywords_added", 0)
    log_activity(
        "GOOGLE_ADS_FULL_CAMPAIGN_CREATED",
        {
            "business": business_name,
            "strategy": strategy_name,
            "customer_id": customer_id,
            "campaign_resource": result["campaign_resource"],
            "ad_group_resource": result["ad_group_resource"],
            "ad_resource": result["ad_resource"],
            "keywords_added": result["keywords_added"],
            "negative_keywords_added": neg_count,
            "daily_budget": daily_budget,
            "status": "PAUSED",
        },
        status="EXECUTED",
    )
    neg_part = f", {neg_count} negative keywords" if neg_count else ""
    return {
        "success": True,
        "message": (
            f"PAUSED campaign created with Ad Group, {result['keywords_added']} keywords"
            f"{neg_part}, and Responsive Search Ad!"
        ),
        "data": result,
    }


def _metric_number(metrics: dict, key: str):
    raw = metrics.get(key)
    if raw in (None, ""):
        return ""
    return int(float(raw))


def _display_metric(value) -> str:
    if value in (None, ""):
        return "n/a"
    return str(value)


def fetch_account_campaigns(customer_id: str, login_customer_id: str, sample_limit: int = 50) -> list[dict]:
    """Fetch live campaigns from Google Ads and format them for the dashboard."""
    rows = list_campaigns(
        customer_id=customer_id.replace("-", "").strip(),
        login_customer_id=login_customer_id.replace("-", "").strip(),
        limit=sample_limit,
    )
    formatted = []
    for row in rows:
        camp = row.get("campaign", {})
        budget = row.get("campaignBudget", {})
        metrics = row.get("metrics") or {}
        micros = int(float(budget.get("amountMicros", 0) or 0))
        cost_micros = metrics.get("costMicros")
        formatted.append(
            {
                "Campaign ID": camp.get("id", ""),
                "Campaign Name": camp.get("name", ""),
                "Status": camp.get("status", ""),
                "Channel": camp.get("advertisingChannelType", ""),
                "Daily Budget": f"{micros / 1_000_000:,.2f}",
                "Impressions (30d)": _metric_number(metrics, "impressions"),
                "Clicks (30d)": _metric_number(metrics, "clicks"),
                "Cost (30d)": f"{int(float(cost_micros)) / 1_000_000:,.2f}" if cost_micros not in (None, "") else "",
            }
        )
    return formatted


def summarize_live_campaigns(rows, limit: int = 50) -> str:
    """Compact live-campaign sample passed into the strategy, research, and content agents."""
    if not rows:
        return ""
    limit = max(1, min(int(limit), 100))
    lines = []
    for row in rows[:limit]:
        lines.append(
            "- {name} | {status} | {channel} | daily budget {budget} | "
            "30d impressions {impressions} | clicks {clicks} | cost {cost}".format(
                name=row.get("Campaign Name", ""),
                status=row.get("Status", ""),
                channel=row.get("Channel", ""),
                budget=row.get("Daily Budget", ""),
                impressions=_display_metric(row.get("Impressions (30d)")),
                clicks=_display_metric(row.get("Clicks (30d)")),
                cost=_display_metric(row.get("Cost (30d)")),
            )
        )
    return "\n".join(lines)
