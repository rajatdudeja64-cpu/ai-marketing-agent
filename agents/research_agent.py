from agents.llm import ask_gemini_json
from safety.guardrails import log_activity


def run_research_agent(business: dict, strategy: dict, live_campaign_context: str = "") -> dict:
    """Research high-intent Google Ads keywords, negative keywords, and target locations."""
    prompt = f"""
You are the Research Agent in an autonomous marketing platform.
Follow the selected strategy. Return ONLY valid JSON with these exact keys:
- "high_intent_keywords": list of 12 objects, each with "keyword" (string) and "match_type" ("Exact" or "Phrase")
- "negative_keywords": list of 8 strings (irrelevant searches to block)
- "target_locations": list of 5 specific locations to target
- "audience_interests": list of 6 Instagram audience interests

Business: {business['name']} — {business['product']}
Audience: {business['audience']}
Strategy: {strategy.get('strategy_name', '')}
Positioning: {strategy.get('positioning', '')}
Target Persona: {strategy.get('target_persona', '')}
Offer: {strategy.get('offer', '')}
Keyword focus: {strategy.get('keyword_focus', '')}
Extra instructions: {strategy.get('agent_notes') or 'None'}

Live campaigns already running. Prefer keywords those campaigns are not already built around:
{live_campaign_context or "None loaded."}
"""
    result = ask_gemini_json(prompt)
    log_activity(
        "RESEARCH_AGENT",
        {
            "business": business["name"],
            "strategy": strategy.get("strategy_name", ""),
            "keywords": len(result.get("high_intent_keywords", [])),
        },
        status="COMPLETED",
    )
    return result
