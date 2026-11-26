import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agents import ads_agent
from integrations import google_ads
from safety import guardrails


class GoogleAdsIntegrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmp.name) / "activity_log.jsonl"
        self._patcher = mock.patch.object(guardrails, "LOG_FILE", self.log_path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def test_list_campaigns_filters_metrics_by_fetched_ids_and_preserves_zero_metrics(self):
        base_rows = [
            {
                "campaign": {"id": "111", "name": "New Campaign", "status": "PAUSED", "advertisingChannelType": "SEARCH"},
                "campaignBudget": {"amountMicros": "500000000"},
            },
            {
                "campaign": {"id": "110", "name": "Active Campaign", "status": "ENABLED", "advertisingChannelType": "SEARCH"},
                "campaignBudget": {"amountMicros": "300000000"},
            },
        ]
        metric_rows = [
            {"campaign": {"id": "111"}, "metrics": {"impressions": "0", "clicks": "0", "costMicros": "0"}},
            {"campaign": {"id": "110"}, "metrics": {"impressions": "450", "clicks": "12", "costMicros": "125000000"}},
        ]
        queries = []

        def fake_query(cid, lcid, gaql, creds):
            queries.append(gaql)
            return base_rows if len(queries) == 1 else metric_rows

        with mock.patch.object(google_ads, "query_google_ads", side_effect=fake_query):
            formatted = ads_agent.fetch_account_campaigns("731-579-5729", "520-130-1135", sample_limit=50)

        self.assertEqual(len(queries), 2)
        self.assertIn("LIMIT 50", queries[0])
        self.assertIn("campaign.id IN (111, 110)", queries[1])
        self.assertEqual(formatted[0]["Impressions (30d)"], 0)
        self.assertEqual(formatted[0]["Clicks (30d)"], 0)
        self.assertEqual(formatted[0]["Cost (30d)"], "0.00")
        self.assertEqual(formatted[1]["Impressions (30d)"], 450)
        self.assertEqual(formatted[1]["Cost (30d)"], "125.00")

        summary = ads_agent.summarize_live_campaigns(formatted, limit=50)
        self.assertIn("30d impressions 0 | clicks 0 | cost 0.00", summary)
        self.assertIn("30d impressions 450 | clicks 12 | cost 125.00", summary)

    def test_summarize_live_campaigns_respects_sample_limit_up_to_100(self):
        rows = [
            {
                "Campaign Name": f"Camp {i}",
                "Status": "PAUSED",
                "Channel": "SEARCH",
                "Daily Budget": "100.00",
                "Impressions (30d)": "",
                "Clicks (30d)": "",
                "Cost (30d)": "",
            }
            for i in range(60)
        ]
        summary_50 = ads_agent.summarize_live_campaigns(rows, limit=50)
        self.assertEqual(len(summary_50.splitlines()), 50)
        summary_60 = ads_agent.summarize_live_campaigns(rows, limit=100)
        self.assertEqual(len(summary_60.splitlines()), 60)

    def test_list_campaigns_skips_metrics_query_when_empty(self):
        with mock.patch.object(google_ads, "query_google_ads", return_value=[]) as m_query:
            rows = google_ads.list_campaigns("7315795729", "5201301135")
        self.assertEqual(rows, [])
        self.assertEqual(m_query.call_count, 1)

    def test_create_full_campaign_validates_before_mutating(self):
        with mock.patch.object(google_ads, "_headers") as m_headers:
            with self.assertRaises(ValueError):
                google_ads.create_full_paused_search_campaign(
                    customer_id="7315795729",
                    login_customer_id="5201301135",
                    campaign_name="Test",
                    daily_budget_amount=100.0,
                    keywords=[],
                    headlines=["One", "Two"],
                    descriptions=["Desc 1", "Desc 2"],
                    final_url="https://www.milkbasket.com",
                )
        m_headers.assert_not_called()

    def test_execute_approved_campaign_creates_paused_campaign_with_negatives(self):
        mutate_calls = []

        def fake_post(url, headers, payload, label):
            mutate_calls.append((url, payload, label))
            if "campaignBudgets" in url:
                return {"results": [{"resourceName": "customers/1/campaignBudgets/10"}]}
            if "campaigns:mutate" in url:
                return {"results": [{"resourceName": "customers/1/campaigns/20"}]}
            if "adGroups:mutate" in url:
                return {"results": [{"resourceName": "customers/1/adGroups/30"}]}
            if "adGroupCriteria:mutate" in url:
                return {"results": [{"resourceName": f"kw/{i}"} for i in range(len(payload["operations"]))]}
            if "campaignCriteria:mutate" in url:
                return {"results": [{"resourceName": f"neg/{i}"} for i in range(len(payload["operations"]))]}
            if "adGroupAds:mutate" in url:
                return {"results": [{"resourceName": "customers/1/adGroupAds/30~40"}]}
            raise AssertionError(f"Unexpected URL: {url}")

        with mock.patch.object(google_ads, "_headers", return_value={"Authorization": "Bearer x"}), \
             mock.patch.object(google_ads, "_post_mutate", side_effect=fake_post):
            res = ads_agent.execute_approved_google_ads_campaign(
                business_name="Milkbasket",
                google_ads_monthly_budget=14000.0,
                max_monthly=25000.0,
                max_daily=1000.0,
                customer_id="731-579-5729",
                login_customer_id="520-130-1135",
                keywords=[
                    {"keyword": "daily milk delivery", "match_type": "Exact"},
                    {"keyword": "daily milk delivery", "match_type": "Exact"},
                    {"keyword": "milk subscription", "match_type": "Phrase"},
                ],
                headlines=["Fresh 7 AM Milk", "Free 7-Day Delivery", "Order By Midnight"],
                descriptions=[
                    "Fresh milk at your doorstep before 7 AM every day.",
                    "Start your 7-day free trial with Milkbasket today.",
                ],
                final_url="https://www.milkbasket.com",
                strategy_name="Morning Habit Acquisition",
                negative_keywords=["dairy jobs", "Dairy Jobs", "milk recipes"],
            )

        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["status"], "PAUSED")
        self.assertEqual(res["data"]["keywords_added"], 2)
        self.assertEqual(res["data"]["negative_keywords_added"], 2)
        labels = [c[2] for c in mutate_calls]
        self.assertIn("Negative keywords creation", labels)
        camp_payload = next(c[1] for c in mutate_calls if c[2] == "Campaign creation")
        self.assertEqual(camp_payload["operations"][0]["create"]["status"], "PAUSED")

    def test_execute_approved_campaign_rejects_bad_url(self):
        res = ads_agent.execute_approved_google_ads_campaign(
            business_name="Milkbasket",
            google_ads_monthly_budget=14000.0,
            max_monthly=25000.0,
            max_daily=1000.0,
            customer_id="7315795729",
            login_customer_id="5201301135",
            keywords=[],
            headlines=["H1", "H2", "H3"],
            descriptions=["D1", "D2"],
            final_url="not-a-url",
        )
        self.assertFalse(res["success"])
        self.assertIn("BLOCKED", res["message"])

    def test_load_service_account_credentials_supports_env_json(self):
        fake_info = {"type": "service_account", "client_email": "bot@example.iam.gserviceaccount.com"}
        with mock.patch.dict("os.environ", {"GOOGLE_SERVICE_ACCOUNT_JSON": '{"type":"service_account","client_email":"bot@example.iam.gserviceaccount.com"}'}), \
             mock.patch.object(google_ads.service_account.Credentials, "from_service_account_info", return_value="CREDS") as m_info:
            creds = google_ads._load_service_account_credentials("nonexistent_credentials.json")
        self.assertEqual(creds, "CREDS")
        m_info.assert_called_once_with(fake_info, scopes=google_ads.SCOPES)


if __name__ == "__main__":
    unittest.main()
