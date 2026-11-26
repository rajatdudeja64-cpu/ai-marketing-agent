import json

from agents.llm import ask_gemini_json
from safety.guardrails import log_activity


def run_strategy_agent(business: dict, strategy_config: dict, live_campaign_context: str = "") -> dict:
    """Shape the selected strategy around the business. Budget split stays under user control."""
    monthly = float(business["monthly_budget"])
    share = max(0.0, min(float(strategy_config["google_ads_share"]), 100.0)) / 100.0
    google_budget = round(monthly * share, 2)
    instagram_budget = round(monthly - google_budget, 2)
    steps = strategy_config.get("core_steps") or []
    prompt = f"""
You are the Strategy Agent in an autonomous marketing platform.
The user has already selected the strategy. Do not switch to a different strategy.
Keep the selected angle, offer, tone, and channel. You may sharpen wording so it fits the business.
Return ONLY valid JSON with these exact keys:
- "strategy_name": string
- "positioning": string (one clear sentence)
- "target_persona": string
- "offer": string
- "tone": string
- "primary_channel": string
- "google_ads_monthly_budget": number (must be {google_budget})
- "instagram_monthly_budget": number (must be {instagram_budget})
- "core_steps": list of exactly 3 short actionable steps

Selected strategy and editable agent inputs:
{json.dumps(strategy_config, ensure_ascii=False)}

Live Google Ads campaigns already in the account. Do not reuse these campaign names. If a similar offer is already running, say how this plan differs:
{live_campaign_context or "None loaded."}

Business details:
- Name: {business['name']}
- Product/Service: {business['product']}
- Target Audience & Location: {business['audience']}
- Goal: {business['goal']}
- Total Monthly Budget: {monthly} {business['currency']}
- Extra instructions: {strategy_config.get('agent_notes') or 'None'}
"""
    result = ask_gemini_json(prompt)
    result["strategy_name"] = strategy_config["name"]
    result["google_ads_monthly_budget"] = google_budget
    result["instagram_monthly_budget"] = instagram_budget
    result["offer"] = result.get("offer") or strategy_config.get("offer", "")
    result["tone"] = result.get("tone") or strategy_config.get("tone", "")
    result["primary_channel"] = result.get("primary_channel") or strategy_config.get("primary_channel", "")
    result["keyword_focus"] = strategy_config.get("keyword_focus", "")
    result["agent_notes"] = strategy_config.get("agent_notes", "")
    if not result.get("positioning"):
        result["positioning"] = strategy_config.get("positioning", "")
    if not result.get("target_persona"):
        result["target_persona"] = strategy_config.get("target_persona", "")
    if not isinstance(result.get("core_steps"), list) or not result.get("core_steps"):
        result["core_steps"] = steps
    log_activity(
        "STRATEGY_AGENT",
        {"business": business["name"], "strategy": strategy_config["name"]},
        status="COMPLETED",
    )
    return result
