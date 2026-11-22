from agents.llm import ask_gemini_json
from safety.guardrails import log_activity


def run_strategy_agent(business: dict) -> dict:
    """Create a structured marketing strategy and channel budget split."""
    prompt = f"""
You are the Strategy Agent in an autonomous marketing platform.
Analyze this business and return ONLY valid JSON with these exact keys:
- "positioning": string (one clear sentence explaining why customers should buy)
- "target_persona": string (concise description of the ideal buyer)
- "google_ads_monthly_budget": number (portion of monthly budget for Google Ads)
- "instagram_monthly_budget": number (portion of monthly budget for Instagram)
- "core_steps": list of 3 short, actionable strategy steps

Business details:
- Name: {business['name']}
- Product/Service: {business['product']}
- Target Audience & Location: {business['audience']}
- Goal: {business['goal']}
- Total Monthly Budget: {business['monthly_budget']} {business['currency']}
"""
    result = ask_gemini_json(prompt)
    log_activity("STRATEGY_AGENT", {"business": business["name"]}, status="COMPLETED")
    return result
