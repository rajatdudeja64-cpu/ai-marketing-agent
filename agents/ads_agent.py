from integrations.google_ads import create_paused_search_campaign, list_campaigns
from safety.guardrails import check_budget_guardrail, log_activity


def execute_approved_google_ads_campaign(
    business_name: str,
    google_ads_monthly_budget: float,
    max_monthly: float,
    max_daily: float,
    customer_id: str,
    login_customer_id: str,
    emergency_stop: bool = False,
) -> dict:
    """Re-verify safety guardrails, then create a real PAUSED Search campaign in Google Ads."""
    allowed, msg = check_budget_guardrail(
        requested_monthly=google_ads_monthly_budget,
        max_monthly=max_monthly,
        max_daily=max_daily,
        emergency_stop=emergency_stop,
    )
    if not allowed:
        return {"success": False, "message": msg}

    daily_budget = max(1.0, round(google_ads_monthly_budget / 30, 2))
    campaign_name = f"{business_name} - AI Search"

    result = create_paused_search_campaign(
        customer_id=customer_id.replace("-", "").strip(),
        login_customer_id=login_customer_id.replace("-", "").strip(),
        campaign_name=campaign_name,
        daily_budget_amount=daily_budget,
    )
    log_activity(
        "GOOGLE_ADS_CAMPAIGN_CREATED",
        {
            "business": business_name,
            "customer_id": customer_id,
            "campaign_resource": result["campaign_resource"],
            "daily_budget": daily_budget,
            "status": "PAUSED",
        },
        status="EXECUTED",
    )
    return {"success": True, "message": "PAUSED campaign created in Google Ads!", "data": result}


def fetch_account_campaigns(customer_id: str, login_customer_id: str) -> list[dict]:
    """Fetch live campaigns from Google Ads and format them for the dashboard."""
    rows = list_campaigns(
        customer_id=customer_id.replace("-", "").strip(),
        login_customer_id=login_customer_id.replace("-", "").strip(),
    )
    formatted = []
    for row in rows:
        camp = row.get("campaign", {})
        budget = row.get("campaignBudget", {})
        micros = int(budget.get("amountMicros", 0))
        formatted.append(
            {
                "Campaign ID": camp.get("id", ""),
                "Campaign Name": camp.get("name", ""),
                "Status": camp.get("status", ""),
                "Daily Budget": f"{micros / 1_000_000:,.2f}",
            }
        )
    return formatted
