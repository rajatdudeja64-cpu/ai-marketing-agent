from agents.llm import ask_gemini_json
from safety.guardrails import log_activity, validate_google_ads_copy


def run_content_agent(business: dict, strategy: dict, research: dict, live_campaign_context: str = "") -> dict:
    """Create Google Ads headlines/descriptions and Instagram posts, then validate ad limits."""
    top_keywords = [
        k.get("keyword", "") if isinstance(k, dict) else str(k)
        for k in research.get("high_intent_keywords", [])[:8]
    ]
    top_keywords = [kw for kw in top_keywords if kw]
    prompt = f"""
You are the Content Agent in an autonomous marketing platform.
Write copy for the selected strategy. Return ONLY valid JSON with these exact keys:
- "google_ads_headlines": list of 8 headlines, STRICTLY 30 characters or fewer each
- "google_ads_descriptions": list of 4 descriptions, STRICTLY 90 characters or fewer each
- "instagram_posts": list of 5 objects, each with "format" ("Reel", "Carousel", or "Single Image"), "visual_idea" (string), "caption" (string), and "hashtags" (list of 5 strings)

Business: {business['name']} — {business['product']}
Strategy: {strategy.get('strategy_name', '')}
Positioning: {strategy.get('positioning', '')}
Offer: {strategy.get('offer', '')}
Tone: {strategy.get('tone', '')}
Primary channel: {strategy.get('primary_channel', '')}
Top Keywords: {', '.join(top_keywords)}
Extra instructions: {strategy.get('agent_notes') or 'None'}

Do not repeat the angle of these live campaigns:
{live_campaign_context or "None loaded."}
"""
    result = ask_gemini_json(prompt)
    issues = validate_google_ads_copy(
        result.get("google_ads_headlines", []),
        result.get("google_ads_descriptions", []),
    )
    result["validation_issues"] = issues
    log_activity(
        "CONTENT_AGENT",
        {
            "business": business["name"],
            "strategy": strategy.get("strategy_name", ""),
            "validation_issues": len(issues),
        },
        status="COMPLETED",
    )
    return result
