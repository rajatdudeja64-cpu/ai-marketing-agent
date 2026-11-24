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


def create_paused_search_campaign(
    customer_id: str,
    login_customer_id: str,
    campaign_name: str,
    daily_budget_amount: float,
    credentials_path: str = "credentials.json",
) -> dict:
    """Create a real PAUSED Search campaign with a daily budget in Google Ads."""
    headers = _headers(login_customer_id, credentials_path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # 1. Create the daily Campaign Budget (Google Ads stores amounts in micros: 1 INR = 1,000,000 micros)
    budget_url = f"{BASE_URL}/customers/{customer_id}/campaignBudgets:mutate"
    budget_payload = {
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
    }
    b_resp = requests.post(budget_url, headers=headers, json=budget_payload, timeout=30)
    if not b_resp.ok:
        raise RuntimeError(f"Budget creation failed {b_resp.status_code}: {b_resp.text}")
    budget_resource = b_resp.json()["results"][0]["resourceName"]

    # 2. Create the Search Campaign (strictly PAUSED by default for safety)
    camp_url = f"{BASE_URL}/customers/{customer_id}/campaigns:mutate"
    camp_payload = {
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
    }
    c_resp = requests.post(camp_url, headers=headers, json=camp_payload, timeout=30)
    if not c_resp.ok:
        raise RuntimeError(f"Campaign creation failed {c_resp.status_code}: {c_resp.text}")
    campaign_resource = c_resp.json()["results"][0]["resourceName"]

    return {
        "campaign_resource": campaign_resource,
        "budget_resource": budget_resource,
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
