import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agents.strategy_presets import MARKETING_STRATEGIES
from safety import guardrails


class GuardrailsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmp.name) / "activity_log.jsonl"
        self._patcher = mock.patch.object(guardrails, "LOG_FILE", self.log_path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def test_emergency_stop_blocks(self):
        allowed, msg = guardrails.check_budget_guardrail(10000, 25000, 1000, emergency_stop=True)
        self.assertFalse(allowed)
        self.assertIn("Emergency Stop", msg)

    def test_zero_or_negative_budget_blocks(self):
        for amount in (0, -500):
            allowed, msg = guardrails.check_budget_guardrail(amount, 25000, 1000)
            self.assertFalse(allowed)
            self.assertIn("greater than 0", msg)

    def test_monthly_limit_blocks(self):
        allowed, msg = guardrails.check_budget_guardrail(30000, 25000, 2000)
        self.assertFalse(allowed)
        self.assertIn("hard limit", msg)

    def test_daily_cap_blocks(self):
        allowed, msg = guardrails.check_budget_guardrail(24000, 25000, 500)
        self.assertFalse(allowed)
        self.assertIn("daily cap", msg)

    def test_valid_budget_passes_and_logs(self):
        allowed, msg = guardrails.check_budget_guardrail(18000, 25000, 1000)
        self.assertTrue(allowed)
        self.assertIn("PASSED", msg)
        entries = [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["status"], "APPROVED")

    def test_validate_google_ads_copy_passes(self):
        headlines = ["Fresh 7 AM Milk", "Free 7-Day Trial", "Order By Midnight"]
        descriptions = [
            "Fresh milk delivered to your doorstep before 7 AM every morning.",
            "Subscribe once and skip daily reorders. Cancel anytime in the app.",
        ]
        self.assertEqual(guardrails.validate_google_ads_copy(headlines, descriptions), [])

    def test_validate_google_ads_copy_catches_length_and_counts(self):
        issues = guardrails.validate_google_ads_copy(
            ["This headline is definitely way longer than thirty characters", ""],
            ["Short description only"],
        )
        self.assertTrue(any("Headline too long" in i for i in issues))
        self.assertTrue(any("Empty headline" in i for i in issues))
        self.assertTrue(any("at least 3 unique headlines" in i for i in issues))
        self.assertTrue(any("at least 2 unique descriptions" in i for i in issues))

    def test_validate_landing_url(self):
        ok, cleaned = guardrails.validate_landing_url("  https://www.milkbasket.com/trial  ")
        self.assertTrue(ok)
        self.assertEqual(cleaned, "https://www.milkbasket.com/trial")

        for bad in ("", "   ", "www.milkbasket.com", "ftp://milkbasket.com", "https://notadomain"):
            ok, msg = guardrails.validate_landing_url(bad)
            self.assertFalse(ok, f"Expected invalid URL: {bad!r}")
            self.assertIn("BLOCKED", msg)


class StrategyPresetsTests(unittest.TestCase):
    def test_presets_have_complete_valid_schema(self):
        required_keys = {
            "name",
            "summary",
            "positioning",
            "target_persona",
            "offer",
            "tone",
            "primary_channel",
            "google_ads_share",
            "keyword_focus",
            "core_steps",
        }
        self.assertGreaterEqual(len(MARKETING_STRATEGIES), 3)
        names = set()
        for preset in MARKETING_STRATEGIES:
            self.assertTrue(required_keys.issubset(preset.keys()))
            self.assertNotIn(preset["name"], names)
            names.add(preset["name"])
            self.assertGreaterEqual(preset["google_ads_share"], 10)
            self.assertLessEqual(preset["google_ads_share"], 90)
            self.assertEqual(len(preset["core_steps"]), 3)


if __name__ == "__main__":
    unittest.main()
