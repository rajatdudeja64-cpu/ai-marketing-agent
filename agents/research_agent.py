from agents.llm import ask_gemini_json
from safety.guardrails import log_activity


def run_research_agent(business: dict, strategy: dict) -> dict:
    """Research high-intent Google Ads keywords, negative keywords, and target locations."""
    prompt = f"""
You are the Research Agent in an autonomous marketing platform.
Based on the business and strategy below, return ONLY valid JSON with these exact keys:
- "high_intent_keywords": list of 8 objects, each with "keyword" (string) and "match_type" ("Exact" or "Phrase")
- "negative_keywords": list of 5 strings (irrelevant searches to block)
- "target_locations": list of 3 specific locations to target
- "audience_interests": list of 5 Instagram audience interests

Business: {business['name']} — {business['product']}
Audience: {business['audience']}
Positioning: {strategy['positioning']}
Target Persona: {strategy['target_persona']}
"""
    result = ask_gemini_json(prompt)
    log_activity("RESEARCH_AGENT", {"business": business["name"]}, status="COMPLETED")
    return result
