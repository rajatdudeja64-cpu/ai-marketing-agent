import json
from pathlib import Path
import streamlit as st
from agents.orchestrator import run_marketing_workflow
from agents.ads_agent import execute_approved_google_ads_campaign, fetch_account_campaigns
from agents.strategy_presets import MARKETING_STRATEGIES
from safety.guardrails import log_activity, validate_landing_url

st.set_page_config(page_title="AI Marketing Agent", layout="wide")
st.title("Autonomous AI Marketing Agent — Control Center")
st.caption("Stage 3: Strategy Presets, Multi-Agent Planning & Live Google Ads API (v26) with Hard Safety Controls")

STRATEGY_BY_NAME = {preset["name"]: preset for preset in MARKETING_STRATEGIES}


def _apply_selected_strategy():
    preset = STRATEGY_BY_NAME[st.session_state["strategy_choice"]]
    st.session_state["cfg_positioning"] = preset["positioning"]
    st.session_state["cfg_persona"] = preset["target_persona"]
    st.session_state["cfg_offer"] = preset["offer"]
    st.session_state["cfg_tone"] = preset["tone"]
    st.session_state["cfg_channel"] = preset["primary_channel"]
    st.session_state["cfg_google_share"] = int(preset["google_ads_share"])
    st.session_state["cfg_keyword_focus"] = preset["keyword_focus"]
    st.session_state["cfg_steps"] = "\n".join(preset["core_steps"])
    st.session_state["cfg_notes"] = ""


def current_strategy_config() -> dict:
    steps = [line.strip() for line in st.session_state["cfg_steps"].splitlines() if line.strip()]
    return {
        "name": st.session_state["strategy_choice"],
        "positioning": st.session_state["cfg_positioning"].strip(),
        "target_persona": st.session_state["cfg_persona"].strip(),
        "offer": st.session_state["cfg_offer"].strip(),
        "tone": st.session_state["cfg_tone"].strip(),
        "primary_channel": st.session_state["cfg_channel"].strip(),
        "google_ads_share": int(st.session_state["cfg_google_share"]),
        "keyword_focus": st.session_state["cfg_keyword_focus"].strip(),
        "core_steps": steps,
        "agent_notes": st.session_state.get("cfg_notes", "").strip(),
        "sample_limit": int(st.session_state.get("sample_limit", 50)),
    }


if "cfg_positioning" not in st.session_state:
    st.session_state["strategy_choice"] = MARKETING_STRATEGIES[0]["name"]
    _apply_selected_strategy()
if "sample_limit" not in st.session_state:
    st.session_state["sample_limit"] = 50
if "include_live_samples" not in st.session_state:
    st.session_state["include_live_samples"] = True

with st.sidebar:
    st.header("Safety & Budget Controls")
    emergency_stop = st.toggle("Emergency Stop (Pause All Actions)", value=False)
    max_monthly = st.number_input("Hard Monthly Budget Limit", min_value=1000, value=25000, step=1000)
    max_daily = st.number_input("Hard Daily Spend Cap", min_value=100, value=1000, step=100)
    if emergency_stop:
        st.error("EMERGENCY STOP ACTIVE — All campaign actions are blocked.")

    st.divider()
    st.header("Marketing Strategy")
    st.radio(
        "Select a strategy",
        list(STRATEGY_BY_NAME),
        key="strategy_choice",
        on_change=_apply_selected_strategy,
    )
    st.caption(STRATEGY_BY_NAME[st.session_state["strategy_choice"]]["summary"])
    st.slider(
        "Google Ads share of monthly budget (%)",
        min_value=10,
        max_value=90,
        step=5,
        key="cfg_google_share",
    )
    instagram_share = 100 - int(st.session_state["cfg_google_share"])
    st.caption(f"Instagram receives the other {instagram_share}%. The agent cannot change this split.")

    with st.expander("Agent inputs", expanded=True):
        st.caption("These fields are sent to the strategy, research, and content agents on the next run.")
        st.text_area("Positioning", key="cfg_positioning", height=90)
        st.text_input("Ideal buyer", key="cfg_persona")
        st.text_area("Offer", key="cfg_offer", height=70)
        st.text_input("Tone", key="cfg_tone")
        st.text_input("Primary channel", key="cfg_channel")
        st.text_area("Keyword focus", key="cfg_keyword_focus", height=70)
        st.text_area("Core steps (one per line)", key="cfg_steps", height=120)
        st.text_area(
            "Extra instructions",
            key="cfg_notes",
            height=70,
            placeholder="Example: stay inside Gurugram, and do not mention discounts",
        )

    st.checkbox("Send live campaign samples to the agent", key="include_live_samples")
    st.number_input(
        "Live campaign samples",
        min_value=5,
        max_value=100,
        step=5,
        key="sample_limit",
        help="How many existing Google Ads campaigns to load and pass to the agent (default 50).",
    )

    st.divider()
    st.header("Google Ads Connection")
    login_customer_id = st.text_input("Manager Account ID", value="5201301135")
    customer_id = st.text_input("Client Account ID", value="7315795729")

strategy_config = current_strategy_config()
share = strategy_config["google_ads_share"]
st.info(
    f"**Selected strategy:** {strategy_config['name']}  \n"
    f"**Offer:** {strategy_config['offer']}  \n"
    f"**Channel:** {strategy_config['primary_channel']}  \n"
    f"**Budget split:** {share}% Google Ads / {100 - share}% Instagram"
)

with st.form("business_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(
            "Business Name",
            value="Milkbasket",
            placeholder="Milkbasket",
        )
        audience = st.text_input(
            "Target Audience & Location",
            value="Urban households and working families in Delhi NCR who reorder milk and daily essentials",
            placeholder="Urban households and working families in Delhi NCR",
        )
        goal = st.selectbox("Primary Marketing Goal", ["Get More Sales", "Generate Leads", "Build Brand Awareness"])
    with col2:
        product = st.text_area(
            "What do you sell?",
            value="Early-morning doorstep delivery of fresh milk, bread, eggs, fruits, and daily groceries. Order by midnight, delivered before 7 AM on a repeat subscription.",
            placeholder="Early-morning milk and daily grocery delivery on subscription",
        )
        c1, c2 = st.columns([2, 1])
        with c1:
            monthly_budget = st.number_input("Requested Monthly Ad Budget", min_value=0, value=20000, step=1000)
        with c2:
            currency = st.selectbox("Currency", ["INR", "USD", "GBP", "EUR"])
    submitted = st.form_submit_button("Run Multi-Agent Workflow", type="primary")

if submitted:
    if not name.strip() or not product.strip():
        st.error("Please enter both a Business Name and a description of what you sell.")
    else:
        business = {
            "name": name.strip(),
            "product": product.strip(),
            "audience": audience.strip(),
            "goal": goal,
            "monthly_budget": float(monthly_budget),
            "currency": currency,
        }
        live_rows = []
        if st.session_state.get("include_live_samples"):
            live_rows = (st.session_state.get("live_campaigns") or [])[: strategy_config["sample_limit"]]
            if not live_rows:
                st.warning("No live campaigns are loaded yet. Refresh the list at the bottom to include them in the next run.")
        with st.status("Running AI Marketing Agents...", expanded=True) as status_box:
            try:
                result = run_marketing_workflow(
                    business=business,
                    max_monthly=float(max_monthly),
                    max_daily=float(max_daily),
                    strategy_config=strategy_config,
                    live_campaigns=live_rows,
                    emergency_stop=emergency_stop,
                    progress_callback=lambda msg: st.write(msg),
                )
                st.session_state["last_result"] = result
                st.session_state["last_business"] = business
                st.session_state["last_strategy_config"] = strategy_config
                st.session_state["ads_launch_result"] = None
                if result["blocked"]:
                    status_box.update(label="Blocked by Safety Guardrails", state="error")
                else:
                    status_box.update(label="All 3 Agents Finished — Ready for Approval & Google Ads Launch", state="complete")
            except Exception as e:
                status_box.update(label="Agent Error", state="error")
                st.error(f"Something went wrong: {e}")

result = st.session_state.get("last_result")
if result:
    if result["blocked"]:
        st.error(result["guardrail_message"])
    else:
        st.success(result["guardrail_message"])
        business = st.session_state["last_business"]
        cur = business["currency"]
        strategy = result["strategy"]
        research = result["research"]
        content = result["content"]

        tab1, tab2, tab3, tab4 = st.tabs(["1. Strategy", "2. Keywords & Audience", "3. Ads & Instagram", "4. Launch to Google Ads"])

        with tab1:
            st.subheader(strategy.get("strategy_name") or "Positioning & Target Persona")
            st.write(f"**Positioning:** {strategy['positioning']}")
            st.write(f"**Ideal Buyer:** {strategy['target_persona']}")
            st.write(f"**Offer:** {strategy.get('offer', '')}")
            st.write(f"**Tone:** {strategy.get('tone', '')}  ·  **Channel:** {strategy.get('primary_channel', '')}")
            m1, m2 = st.columns(2)
            m1.metric("Google Ads Monthly Budget", f"{cur} {strategy['google_ads_monthly_budget']:,.0f}")
            m2.metric("Instagram Monthly Budget", f"{cur} {strategy['instagram_monthly_budget']:,.0f}")
            st.subheader("Core Action Steps")
            for i, step in enumerate(strategy.get("core_steps", []), 1):
                st.write(f"{i}. {step}")

        with tab2:
            st.subheader("High-Intent Google Ads Keywords")
            st.table(research.get("high_intent_keywords", []))
            c1, c2, c3 = st.columns(3)
            c1.write("**Negative Keywords (Blocked)**")
            for kw in research.get("negative_keywords", []):
                c1.write(f"- {kw}")
            c2.write("**Target Locations**")
            for loc in research.get("target_locations", []):
                c2.write(f"- {loc}")
            c3.write("**Instagram Interests**")
            for interest in research.get("audience_interests", []):
                c3.write(f"- {interest}")

        with tab3:
            issues = content.get("validation_issues", [])
            if issues:
                st.warning("Guardrail Character-Limit Warnings:\n" + "\n".join(f"- {x}" for x in issues))
            else:
                st.success("All Google Ads headlines (<=30 chars) and descriptions (<=90 chars) passed validation!")
            st.subheader("Google Ads Headlines")
            for h in content.get("google_ads_headlines", []):
                st.write(f"- {h} `({len(h)}/30 chars)`")
            st.subheader("Google Ads Descriptions")
            for d in content.get("google_ads_descriptions", []):
                st.write(f"- {d} `({len(d)}/90 chars)`")
            st.subheader("Instagram Content Plan")
            for i, post in enumerate(content.get("instagram_posts", []), 1):
                with st.expander(f"Post {i}: {post.get('format', 'Post')}", expanded=True):
                    st.write(f"**Visual Idea:** {post.get('visual_idea', '')}")
                    st.write(f"**Caption:** {post.get('caption', '')}")
                    st.write("**Hashtags:** " + " ".join(post.get("hashtags", [])))

        with tab4:
            st.subheader("Google Ads Campaign Preview & Approval Gate")
            gads_monthly = float(strategy["google_ads_monthly_budget"])
            daily_preview = max(1.0, round(gads_monthly / 30, 2)) if gads_monthly > 0 else 0.0
            strategy_name = strategy.get("strategy_name", "")
            preview_campaign_name = (
                f"{business['name']} - {strategy_name} - AI Search"
                if strategy_name
                else f"{business['name']} - AI Search"
            )
            neg_keywords = research.get("negative_keywords", [])
            st.info(
                f"**Campaign Name:** {preview_campaign_name}  \n"
                f"**Target Account:** {customer_id} (Test Sandbox)  \n"
                f"**Daily Budget:** {cur} {daily_preview:,.2f}/day  \n"
                f"**Keywords:** {len(research.get('high_intent_keywords', []))} positive · {len(neg_keywords)} negative  \n"
                f"**Initial Status:** PAUSED (safe — no ads will serve automatically)"
            )

            final_url = st.text_input(
                "Landing Page URL (required by Google Ads)",
                value="https://www.milkbasket.com",
                placeholder="https://www.milkbasket.com",
            )
            if st.button("Approve & Launch Full PAUSED Campaign (Ad Group + Keywords + Ad)", type="primary", disabled=emergency_stop):
                url_ok, url_msg = validate_landing_url(final_url)
                if not url_ok:
                    st.error(url_msg)
                else:
                    with st.spinner("Sending approved campaign to Google Ads API (v26)..."):
                        try:
                            log_activity("HUMAN_APPROVAL", {"business": business["name"], "daily_budget": daily_preview, "strategy": strategy_name}, status="APPROVED")
                            launch = execute_approved_google_ads_campaign(
                                business_name=business["name"],
                                google_ads_monthly_budget=gads_monthly,
                                max_monthly=float(max_monthly),
                                max_daily=float(max_daily),
                                customer_id=customer_id,
                                login_customer_id=login_customer_id,
                                keywords=research.get("high_intent_keywords", []),
                                headlines=content.get("google_ads_headlines", []),
                                descriptions=content.get("google_ads_descriptions", []),
                                final_url=url_msg,
                                strategy_name=strategy_name,
                                negative_keywords=neg_keywords,
                                emergency_stop=emergency_stop,
                            )
                            st.session_state["ads_launch_result"] = launch
                        except Exception as e:
                            st.error(f"Google Ads API Error: {e}")

            launch = st.session_state.get("ads_launch_result")
            if launch:
                if launch["success"]:
                    st.success(f"{launch['message']} Resource: `{launch['data']['campaign_resource']}`")
                else:
                    st.error(launch["message"])

st.divider()
st.subheader("Live Campaigns in Google Ads Account")
st.markdown(
    "Refresh **reads** campaigns that already exist in the client account. It does not create a campaign and it does not spend. "
    "The app calls Google Ads API v26 `googleAds:searchStream` with the manager account as `login-customer-id`. "
    "The query returns the newest campaigns first, up to the sample size in the sidebar, including channel and daily budget. "
    "A second query adds 30-day impressions, clicks, and cost when the account has them. "
    "Paused campaigns with no delivery stay in the list, because a metrics-only query would hide them. "
    "**Approve & Launch** is a different action: it creates one new PAUSED search campaign only after you confirm."
)
sample_limit = int(st.session_state.get("sample_limit", 50))
loaded = st.session_state.get("live_campaigns") or []
st.caption(
    f"Sample size is {sample_limit}. {len(loaded)} campaigns are loaded. "
    "With “Send live campaign samples to the agent” on, the next workflow receives these rows."
)
if st.button("Refresh Live Campaigns from Google Ads"):
    with st.spinner(f"Fetching up to {sample_limit} campaigns from Google Ads API..."):
        try:
            st.session_state["live_campaigns"] = fetch_account_campaigns(
                customer_id,
                login_customer_id,
                sample_limit=sample_limit,
            )
            loaded = st.session_state["live_campaigns"]
        except Exception as e:
            st.error(f"Could not fetch campaigns: {e}")

if loaded:
    st.caption(f"{len(loaded)} campaigns in this sample.")
    st.dataframe(loaded, width="stretch")

with st.expander("Recent Activity Audit Log"):
    log_path = Path("activity_log.jsonl")
    if log_path.exists():
        raw_lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()][-10:]
        entries = []
        for line in reversed(raw_lines):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if entries:
            st.json(entries)
