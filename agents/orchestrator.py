from agents.ads_agent import summarize_live_campaigns
from agents.strategy_agent import run_strategy_agent
from agents.research_agent import run_research_agent
from agents.content_agent import run_content_agent
from safety.guardrails import check_budget_guardrail, log_activity


def run_marketing_workflow(
    business: dict,
    max_monthly: float,
    max_daily: float,
    strategy_config: dict,
    live_campaigns=None,
    emergency_stop: bool = False,
    progress_callback=None,
) -> dict:
    """Coordinate all agents behind hard safety guardrails."""
    if progress_callback:
        progress_callback("1/4 Checking budget limits & safety guardrails...")

    allowed, guardrail_msg = check_budget_guardrail(
        requested_monthly=business["monthly_budget"],
        max_monthly=max_monthly,
        max_daily=max_daily,
        emergency_stop=emergency_stop,
    )
    if not allowed:
        return {"blocked": True, "guardrail_message": guardrail_msg}

    live_context = summarize_live_campaigns(live_campaigns or [], limit=strategy_config.get("sample_limit", 50))

    if progress_callback:
        progress_callback(f"2/4 Strategy Agent is applying “{strategy_config['name']}”...")
    strategy = run_strategy_agent(business, strategy_config, live_context)

    if progress_callback:
        progress_callback("3/4 Research Agent is finding high-intent keywords & audiences...")
    research = run_research_agent(business, strategy, live_context)

    if progress_callback:
        progress_callback("4/4 Content Agent is writing & validating Google Ads + Instagram copy...")
    content = run_content_agent(business, strategy, research, live_context)

    log_activity(
        "WORKFLOW_COMPLETE",
        {"business": business["name"], "strategy": strategy_config["name"]},
        status="AWAITING_APPROVAL",
    )
    return {
        "blocked": False,
        "guardrail_message": guardrail_msg,
        "status": "AWAITING_APPROVAL",
        "strategy": strategy,
        "research": research,
        "content": content,
    }
