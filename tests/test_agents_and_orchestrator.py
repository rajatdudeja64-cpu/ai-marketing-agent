import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from agents import content_agent, llm, orchestrator, research_agent, strategy_agent
from agents.strategy_presets import MARKETING_STRATEGIES
from safety import guardrails


class LlmTests(unittest.TestCase):
    def test_parse_json_object_strips_code_fences(self):
        raw = '```json\n{"ok": true, "count": 2}\n```'
        self.assertEqual(llm._parse_json_object(raw), {"ok": True, "count": 2})

    def test_parse_json_object_rejects_non_dict(self):
        with self.assertRaises(ValueError):
            llm._parse_json_object("[1, 2, 3]")

    def test_ask_gemini_json_retries_and_falls_back(self):
        calls = []

        def fake_generate(model, contents, config):
            calls.append(model)
            if model == llm.MODELS[0]:
                raise RuntimeError("503 Service Unavailable")
            return SimpleNamespace(text='{"status": "ok"}')

        fake_client = SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate))
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), \
             mock.patch("agents.llm.genai.Client", return_value=fake_client), \
             mock.patch("agents.llm.time.sleep"):
            result = llm.ask_gemini_json("hello")

        self.assertEqual(result, {"status": "ok"})
        self.assertEqual(calls[:3], [llm.MODELS[0]] * 3)
        self.assertEqual(calls[3], llm.MODELS[1])

    def test_ask_gemini_json_missing_key_raises(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                llm.ask_gemini_json("hello")


class AgentsAndOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmp.name) / "activity_log.jsonl"
        self._patcher = mock.patch.object(guardrails, "LOG_FILE", self.log_path)
        self._patcher.start()
        self.business = {
            "name": "Milkbasket",
            "product": "Early-morning doorstep delivery of milk and groceries",
            "audience": "Urban households in Delhi NCR",
            "goal": "Get More Sales",
            "monthly_budget": 20000.0,
            "currency": "INR",
        }
        preset = MARKETING_STRATEGIES[0]
        self.strategy_config = {
            **preset,
            "agent_notes": "Focus on Gurugram societies",
            "sample_limit": 50,
        }

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def test_strategy_agent_enforces_user_budget_split_and_fallbacks(self):
        fake_llm_output = {
            "strategy_name": "Something Else",
            "positioning": "",
            "target_persona": "Busy families",
            "google_ads_monthly_budget": 99999,
            "instagram_monthly_budget": 1,
            "core_steps": "not-a-list",
        }
        with mock.patch.object(strategy_agent, "ask_gemini_json", return_value=fake_llm_output):
            res = strategy_agent.run_strategy_agent(self.business, self.strategy_config, "- Camp A | PAUSED")

        self.assertEqual(res["strategy_name"], self.strategy_config["name"])
        self.assertEqual(res["google_ads_monthly_budget"], 14000.0)
        self.assertEqual(res["instagram_monthly_budget"], 6000.0)
        self.assertEqual(res["positioning"], self.strategy_config["positioning"])
        self.assertEqual(res["core_steps"], self.strategy_config["core_steps"])

    def test_orchestrator_blocks_on_guardrail_without_calling_agents(self):
        with mock.patch.object(orchestrator, "run_strategy_agent") as m_strat:
            res = orchestrator.run_marketing_workflow(
                business=self.business,
                max_monthly=10000.0,
                max_daily=1000.0,
                strategy_config=self.strategy_config,
            )
        self.assertTrue(res["blocked"])
        m_strat.assert_not_called()

    def test_orchestrator_end_to_end_propagates_live_samples(self):
        captured_prompts = []

        def fake_ask(prompt):
            captured_prompts.append(prompt)
            if "Strategy Agent" in prompt:
                return {
                    "strategy_name": "Morning Habit Acquisition",
                    "positioning": "7 AM fresh milk delivery.",
                    "target_persona": "Delhi NCR working families",
                    "offer": "Free 7-day delivery",
                    "tone": "Direct",
                    "primary_channel": "Google Search",
                    "google_ads_monthly_budget": 14000,
                    "instagram_monthly_budget": 6000,
                    "core_steps": ["Step 1", "Step 2", "Step 3"],
                }
            if "Research Agent" in prompt:
                return {
                    "high_intent_keywords": [
                        {"keyword": "milk delivery delhi", "match_type": "Exact"},
                        {"keyword": "morning milk subscription", "match_type": "Phrase"},
                    ],
                    "negative_keywords": ["free milk", "dairy jobs"],
                    "target_locations": ["Gurugram", "Noida"],
                    "audience_interests": ["Organic groceries"],
                }
            return {
                "google_ads_headlines": ["Fresh 7 AM Milk", "Free 7-Day Trial", "Daily Milk Delivery"],
                "google_ads_descriptions": [
                    "Order fresh milk by midnight and get doorstep delivery before 7 AM.",
                    "Start a 7-day free delivery trial across Delhi NCR. Cancel anytime.",
                ],
                "instagram_posts": [
                    {"format": "Reel", "visual_idea": "Doorstep crate", "caption": "7 AM fresh", "hashtags": ["#Milkbasket"]}
                ],
            }

        live_rows = [
            {
                "Campaign ID": "101",
                "Campaign Name": "Existing Milk Campaign",
                "Status": "PAUSED",
                "Channel": "SEARCH",
                "Daily Budget": "500.00",
                "Impressions (30d)": 0,
                "Clicks (30d)": 0,
                "Cost (30d)": "0.00",
            }
        ]
        progress = []
        with mock.patch.object(strategy_agent, "ask_gemini_json", side_effect=fake_ask), \
             mock.patch.object(research_agent, "ask_gemini_json", side_effect=fake_ask), \
             mock.patch.object(content_agent, "ask_gemini_json", side_effect=fake_ask):
            res = orchestrator.run_marketing_workflow(
                business=self.business,
                max_monthly=25000.0,
                max_daily=1000.0,
                strategy_config=self.strategy_config,
                live_campaigns=live_rows,
                progress_callback=progress.append,
            )

        self.assertFalse(res["blocked"])
        self.assertEqual(res["status"], "AWAITING_APPROVAL")
        self.assertEqual(res["content"]["validation_issues"], [])
        self.assertEqual(len(progress), 4)
        self.assertEqual(len(captured_prompts), 3)
        for p in captured_prompts:
            self.assertIn("Existing Milk Campaign", p)
            self.assertIn("30d impressions 0 | clicks 0 | cost 0.00", p)

        logs = [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines()]
        research_log = next(e for e in logs if e["action"] == "RESEARCH_AGENT")
        self.assertEqual(research_log["details"]["keywords"], 2)


if __name__ == "__main__":
    unittest.main()
