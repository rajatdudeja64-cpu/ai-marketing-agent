import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

from agents import ads_agent, content_agent, research_agent, strategy_agent
from agents.strategy_presets import MARKETING_STRATEGIES
from safety import guardrails

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


class StreamlitAppTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmp.name) / "activity_log.jsonl"
        self._patcher = mock.patch.object(guardrails, "LOG_FILE", self.log_path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def test_initial_render_and_strategy_switching(self):
        at = AppTest.from_file(APP_PATH, default_timeout=10)
        at.run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["strategy_choice"], MARKETING_STRATEGIES[0]["name"])
        self.assertEqual(at.session_state["cfg_google_share"], MARKETING_STRATEGIES[0]["google_ads_share"])

        # Switch to a different preset and verify sidebar inputs update cleanly
        target = MARKETING_STRATEGIES[2]
        at.sidebar.radio[0].set_value(target["name"]).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["cfg_google_share"], target["google_ads_share"])
        self.assertEqual(at.session_state["cfg_offer"], target["offer"])

    def test_workflow_submission_renders_all_tabs(self):
        def fake_ask(prompt):
            if "Strategy Agent" in prompt:
                return {
                    "strategy_name": "Morning Habit Acquisition",
                    "positioning": "Fresh milk by 7 AM.",
                    "target_persona": "Working households in Delhi NCR",
                    "offer": "Free 7-day delivery",
                    "tone": "Direct",
                    "primary_channel": "Google Search",
                    "google_ads_monthly_budget": 14000,
                    "instagram_monthly_budget": 6000,
                    "core_steps": ["Bid on search", "Run 7-day trial", "Retarget day 5"],
                }
            if "Research Agent" in prompt:
                return {
                    "high_intent_keywords": [
                        {"keyword": "daily milk delivery", "match_type": "Exact"},
                        {"keyword": "milk subscription delhi", "match_type": "Phrase"},
                    ],
                    "negative_keywords": ["dairy jobs", "milk recipe"],
                    "target_locations": ["Gurugram", "Noida"],
                    "audience_interests": ["Fresh groceries"],
                }
            return {
                "google_ads_headlines": ["Fresh 7 AM Milk", "Free 7-Day Trial", "Order By Midnight"],
                "google_ads_descriptions": [
                    "Order fresh milk by midnight and get doorstep delivery before 7 AM.",
                    "Subscribe once and skip daily reorders across Delhi NCR.",
                ],
                "instagram_posts": [
                    {
                        "format": "Reel",
                        "visual_idea": "7 AM doorstep crate",
                        "caption": "Fresh milk before breakfast.",
                        "hashtags": ["#Milkbasket", "#DelhiNCR"],
                    }
                ],
            }

        at = AppTest.from_file(APP_PATH, default_timeout=10)
        at.run()
        with mock.patch.object(strategy_agent, "ask_gemini_json", side_effect=fake_ask), \
             mock.patch.object(research_agent, "ask_gemini_json", side_effect=fake_ask), \
             mock.patch.object(content_agent, "ask_gemini_json", side_effect=fake_ask):
            at.button[0].click().run()

        self.assertEqual(len(at.exception), 0)
        self.assertFalse(at.session_state["last_result"]["blocked"])
        self.assertEqual(len(at.tabs), 4)
        self.assertEqual(len(at.error), 0)

    def test_emergency_stop_blocks_workflow(self):
        at = AppTest.from_file(APP_PATH, default_timeout=10)
        at.run()
        at.sidebar.toggle[0].set_value(True).run()
        at.button[0].click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(at.session_state["last_result"]["blocked"])
        self.assertTrue(any("Emergency Stop" in e.value for e in at.error))

    def test_refresh_live_campaigns_renders_dataframe(self):
        sample_rows = [
            {
                "Campaign ID": "24554585401",
                "Campaign Name": "Milkbasket - Morning Habit - AI Search",
                "Status": "PAUSED",
                "Channel": "SEARCH",
                "Daily Budget": "466.67",
                "Impressions (30d)": 0,
                "Clicks (30d)": 0,
                "Cost (30d)": "0.00",
            }
        ]
        at = AppTest.from_file(APP_PATH, default_timeout=10)
        at.run()
        with mock.patch.object(ads_agent, "list_campaigns", return_value=[]):
            pass
        at.session_state["live_campaigns"] = sample_rows
        at.run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.dataframe), 1)


if __name__ == "__main__":
    unittest.main()
