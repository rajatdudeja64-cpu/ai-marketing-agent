from datetime import datetime
import json
import os
from pathlib import Path
import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from safety.guardrails import validate_landing_url

API_VERSION = "v26"
BASE_URL = f"https://googleads.googleapis.com/{API_VERSION}"
SCOPES = ["https://www.googleapis.com/auth/adwords"]


def _load_service_account_credentials(credentials_path: str = "credentials.json"):
    if credentials_path and Path(credentials_path).exists():
        return service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )

    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw_json:
        return service_account.Credentials.from_service_account_info(
            json.loads(raw_json), scopes=SCOPES
        )

    try:
        import streamlit as st
        if "google_service_account" in st.secrets:
            info = dict(st.secrets["google_service_account"])
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        if "GOOGLE_SERVICE_ACCOUNT_JSON" in st.secrets:
            return service_account.Credentials.from_service_account_info(
                json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]), scopes=SCOPES
            )
    except Exception:
        pass

    raise FileNotFoundError(
        f"Google service account credentials not found at '{credentials_path}', "
        "in GOOGLE_SERVICE_ACCOUNT_JSON, or in Streamlit secrets [google_service_account]."
    )


def get_access_token(credentials_path: str = "credentials.json") -> str:
    """Authenticate with your Google Cloud Service Account and return an OAuth token."""
    creds = _load_service_account_credentials(credentials_path)
    creds.refresh(Request())
    return creds.token


def _headers(login_customer_id: str, credentials_path: str = "credentials.json") -> dict:
    return {
        "Authorization": f"Bearer {get_access_token(credentials_path)}",
        "login-customer-id": login_customer_id,
        "Content-Type": "application/json",
    }


def _post_mutate(url: str, headers: dict, payload: dict, label: str) -> dict:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"{label} failed ({resp.status_code}): {resp.text}")
    return resp.json()


def query_google_ads(
    customer_id: str,
    login_customer_id: str,
    gaql_query: str,
    credentials_path: str = "credentials.json",
) -> list[dict]:
    """Run a GAQL query via the official Google Ads REST API (v26)."""
    url = f"{BASE_URL}/customers/{customer_id}/googleAds:searchStream"
    resp = requests.post(
        url,
        headers=_headers(login_customer_id, credentials_path),
        json={"query": gaql_query},
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Google Ads API error {resp.status_code}: {resp.text}")

    rows = []
    for batch in resp.json():
        rows.extend(batch.get("results", []))
    return rows


def create_full_paused_search_campaign(
    customer_id: str,
    login_customer_id: str,
    campaign_name: str,
    daily_budget_amount: float,
    keywords: list[dict],
    headlines: list[str],
    descriptions: list[str],
    final_url: str,
    negative_keywords: list[str] | None = None,
    credentials_path: str = "credentials.json",
) -> dict:
    """Create a PAUSED Search campaign with Budget, Ad Group, Keywords, Negative Keywords, and RSA."""
    url_ok, url_or_err = validate_landing_url(final_url)
    if not url_ok:
        raise ValueError(url_or_err)
    validated_url = url_or_err

    # Pre-validate and sanitize RSA copy before creating any resources in Google Ads
    clean_headlines = []
    for h in headlines:
        h_clean = str(h).strip()[:30]
        if h_clean and h_clean not in clean_headlines:
            clean_headlines.append(h_clean)
    clean_descriptions = []
    for d in descriptions:
        d_clean = str(d).strip()[:90]
        if d_clean and d_clean not in clean_descriptions:
            clean_descriptions.append(d_clean)

    if len(clean_headlines) < 3:
        raise ValueError(f"Google Ads Responsive Search Ad requires at least 3 unique headlines (got {len(clean_headlines)}).")
    if len(clean_descriptions) < 2:
        raise ValueError(f"Google Ads Responsive Search Ad requires at least 2 unique descriptions (got {len(clean_descriptions)}).")

    headers = _headers(login_customer_id, credentials_path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # 1. Daily Campaign Budget (micros: 1 unit = 1,000,000 micros)
    budget_res = _post_mutate(
        f"{BASE_URL}/customers/{customer_id}/campaignBudgets:mutate",
        headers,
        {
            "operations": [
                {
                    "create": {
                        "name": f"{campaign_name} Budget {stamp}",
                        "amountMicros": str(int(daily_budget_amount * 1_000_000)),
                        "deliveryMethod": "STANDARD",
                        "explicitlyShared": False,
                    }
                }
            ]
        },
        "Budget creation",
    )
    budget_resource = budget_res["results"][0]["resourceName"]

    # 2. PAUSED Search Campaign
    camp_res = _post_mutate(
        f"{BASE_URL}/customers/{customer_id}/campaigns:mutate",
        headers,
        {
            "operations": [
                {
                    "create": {
                        "name": f"{campaign_name} ({stamp})",
                        "advertisingChannelType": "SEARCH",
                        "status": "PAUSED",
                        "manualCpc": {},
                        "campaignBudget": budget_resource,
                        "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING",
                        "networkSettings": {
                            "targetGoogleSearch": True,
                            "targetSearchNetwork": False,
                            "targetContentNetwork": False,
                        },
                    }
                }
            ]
        },
        "Campaign creation",
    )
    campaign_resource = camp_res["results"][0]["resourceName"]

    # 3. Ad Group
    ag_res = _post_mutate(
        f"{BASE_URL}/customers/{customer_id}/adGroups:mutate",
        headers,
        {
            "operations": [
                {
                    "create": {
                        "name": f"{campaign_name} - Main Ad Group",
                        "campaign": campaign_resource,
                        "type": "SEARCH_STANDARD",
                        "status": "ENABLED",
                        "cpcBidMicros": "10000000",
                    }
                }
            ]
        },
        "Ad Group creation",
    )
    ad_group_resource = ag_res["results"][0]["resourceName"]

    # 4. High-Intent Keywords (Exact / Phrase)
    kw_ops = []
    seen_kw = set()
    for item in keywords:
        text = str(item.get("keyword", "")).strip()
        match_raw = str(item.get("match_type", "PHRASE")).upper()
        match_type = "EXACT" if "EXACT" in match_raw else "PHRASE"
        key = (text.lower(), match_type)
        if text and key not in seen_kw:
            seen_kw.add(key)
            kw_ops.append(
                {
                    "create": {
                        "adGroup": ad_group_resource,
                        "status": "ENABLED",
                        "keyword": {"text": text, "matchType": match_type},
                    }
                }
            )
    kw_count = 0
    if kw_ops:
        kw_res = _post_mutate(
            f"{BASE_URL}/customers/{customer_id}/adGroupCriteria:mutate",
            headers,
            {"operations": kw_ops},
            "Keywords creation",
        )
        kw_count = len(kw_res.get("results", []))

    # 4b. Campaign-Level Negative Keywords (Phrase match to block irrelevant spend)
    neg_ops = []
    seen_neg = set()
    for neg in negative_keywords or []:
        text = str(neg).strip()
        key = text.lower()
        if text and key not in seen_neg:
            seen_neg.add(key)
            neg_ops.append(
                {
                    "create": {
                        "campaign": campaign_resource,
                        "negative": True,
                        "keyword": {"text": text, "matchType": "PHRASE"},
                    }
                }
            )
    neg_kw_count = 0
    if neg_ops:
        neg_res = _post_mutate(
            f"{BASE_URL}/customers/{customer_id}/campaignCriteria:mutate",
            headers,
            {"operations": neg_ops},
            "Negative keywords creation",
        )
        neg_kw_count = len(neg_res.get("results", []))

    # 5. Responsive Search Ad (already deduplicated & safely trimmed to 30/90 chars)
    ad_res = _post_mutate(
        f"{BASE_URL}/customers/{customer_id}/adGroupAds:mutate",
        headers,
        {
            "operations": [
                {
                    "create": {
                        "adGroup": ad_group_resource,
                        "status": "ENABLED",
                        "ad": {
                            "finalUrls": [validated_url],
                            "responsiveSearchAd": {
                                "headlines": [{"text": h} for h in clean_headlines[:15]],
                                "descriptions": [{"text": d} for d in clean_descriptions[:4]],
                            },
                        },
                    }
                }
            ]
        },
        "Responsive Search Ad creation",
    )
    ad_resource = ad_res["results"][0]["resourceName"]

    return {
        "campaign_resource": campaign_resource,
        "budget_resource": budget_resource,
        "ad_group_resource": ad_group_resource,
        "ad_resource": ad_resource,
        "keywords_added": kw_count,
        "negative_keywords_added": neg_kw_count,
        "status": "PAUSED",
        "daily_budget": daily_budget_amount,
    }


def list_campaigns(
    customer_id: str,
    login_customer_id: str,
    credentials_path: str = "credentials.json",
    limit: int = 50,
) -> list[dict]:
    """List campaigns in the account, then attach 30-day stats when the API allows it.

    A metrics-only query hides paused campaigns with zero delivery. The base query
    is what increases the sample: newest campaigns first, up to `limit`.
    """
    limit = max(1, min(int(limit), 100))
    base_query = f"""
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          campaign.advertising_channel_type,
          campaign_budget.amount_micros
        FROM campaign
        ORDER BY campaign.id DESC
        LIMIT {limit}
    """
    rows = query_google_ads(customer_id, login_customer_id, base_query, credentials_path)
    if not rows:
        return rows

    campaign_ids = [
        str(row.get("campaign", {}).get("id", "")).strip()
        for row in rows
        if str(row.get("campaign", {}).get("id", "")).strip().isdigit()
    ]
    id_filter = f" AND campaign.id IN ({', '.join(campaign_ids)})" if campaign_ids else ""

    metrics_query = f"""
        SELECT
          campaign.id,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS{id_filter}
        ORDER BY metrics.impressions DESC
        LIMIT {limit}
    """
    try:
        metric_rows = query_google_ads(customer_id, login_customer_id, metrics_query, credentials_path)
    except RuntimeError:
        return rows

    stats_by_id = {}
    for row in metric_rows:
        campaign_id = str(row.get("campaign", {}).get("id", ""))
        if campaign_id:
            stats_by_id[campaign_id] = row.get("metrics", {})
    for row in rows:
        campaign_id = str(row.get("campaign", {}).get("id", ""))
        if campaign_id in stats_by_id:
            row["metrics"] = stats_by_id[campaign_id]
    return rows
