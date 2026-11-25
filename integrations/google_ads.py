from datetime import datetime
import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

API_VERSION = "v26"
BASE_URL = f"https://googleads.googleapis.com/{API_VERSION}"
SCOPES = ["https://www.googleapis.com/auth/adwords"]


def get_access_token(credentials_path: str = "credentials.json") -> str:
    """Authenticate with your Google Cloud Service Account and return an OAuth token."""
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
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
    credentials_path: str = "credentials.json",
) -> dict:
    """Create a PAUSED Search campaign with Budget, Ad Group, Keywords, and Responsive Search Ad."""
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

    # 5. Responsive Search Ad (deduplicated & safely trimmed to 30/90 chars)
    clean_headlines = []
    for h in headlines:
        h_clean = h.strip()[:30]
        if h_clean and h_clean not in clean_headlines:
            clean_headlines.append(h_clean)
    clean_descriptions = []
    for d in descriptions:
        d_clean = d.strip()[:90]
        if d_clean and d_clean not in clean_descriptions:
            clean_descriptions.append(d_clean)

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
                            "finalUrls": [final_url],
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
        "status": "PAUSED",
        "daily_budget": daily_budget_amount,
    }


def list_campaigns(
    customer_id: str,
    login_customer_id: str,
    credentials_path: str = "credentials.json",
) -> list[dict]:
    """List existing campaigns and their daily budgets in the account."""
    query = """
        SELECT campaign.id, campaign.name, campaign.status, campaign_budget.amount_micros
        FROM campaign
        ORDER BY campaign.id DESC
    """
    return query_google_ads(customer_id, login_customer_id, query, credentials_path)
