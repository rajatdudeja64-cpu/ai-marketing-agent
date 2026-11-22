import json
from pathlib import Path
import streamlit as st
from agents.orchestrator import run_marketing_workflow
from safety.guardrails import log_activity

st.set_page_config(page_title="AI Marketing Agent", layout="wide")
st.title("Autonomous AI Marketing Agent — Control Center")
st.caption("Stage 1 Multi-Agent Architecture: Strategy → Research → Content → Safety & Approval Gate")

with st.sidebar:
    st.header("Safety & Budget Controls")
    emergency_stop = st.toggle("Emergency Stop (Pause All Actions)", value=False)
    max_monthly = st.number_input("Hard Monthly Budget Limit", min_value=1000, value=25000, step=1000)
    max_daily = st.number_input("Hard Daily Spend Cap", min_value=100, value=1000, step=100)
    if emergency_stop:
        st.error("EMERGENCY STOP ACTIVE — All campaign actions are blocked.")

with st.form("business_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Business Name", value="Urban Roast Coffee")
        audience = st.text_input("Target Audience & Location", value="Working professionals 24-40 in Gurugram & Delhi NCR")
        goal = st.selectbox("Primary Marketing Goal", ["Get More Sales", "Generate Leads", "Build Brand Awareness"])
    with col2:
        product = st.text_area("What do you sell?", value="Freshly roasted specialty coffee beans, cold brew packs, and pour-over kits delivered in 24 hours.")
        c1, c2 = st.columns([2, 1])
        with c1:
            monthly_budget = st.number_input("Requested Monthly Ad Budget", min_value=0, value=20000, step=1000)
        with c2:
            currency = st.selectbox("Currency", ["INR", "USD", "GBP", "EUR"])
    submitted = st.form_submit_button("Run Multi-Agent Workflow", type="primary")

if submitted:
    business = {
        "name": name,
        "product": product,
        "audience": audience,
        "goal": goal,
        "monthly_budget": float(monthly_budget),
        "currency": currency,
    }
    with st.status("Running AI Marketing Agents...", expanded=True) as status_box:
        try:
            result = run_marketing_workflow(
                business=business,
                max_monthly=float(max_monthly),
                max_daily=float(max_daily),
                emergency_stop=emergency_stop,
                progress_callback=lambda msg: st.write(msg),
            )
            st.session_state["last_result"] = result
            st.session_state["last_business"] = business
            st.session_state["approved"] = False
            if result["blocked"]:
                status_box.update(label="Blocked by Safety Guardrails", state="error")
            else:
                status_box.update(label="All 3 Agents Finished — Ready for Your Approval", state="complete")
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

        tab1, tab2, tab3, tab4 = st.tabs(["1. Strategy", "2. Keywords & Audience", "3. Ads & Instagram", "4. Approve & Audit Log"])

        with tab1:
            st.subheader("Positioning & Target Persona")
            st.write(f"**Positioning:** {strategy['positioning']}")
            st.write(f"**Ideal Buyer:** {strategy['target_persona']}")
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
            st.subheader("Human Approval Gate")
            if st.session_state.get("approved"):
                st.success("Campaign plan APPROVED and recorded in activity_log.jsonl (ready for Stage 2 Google Ads test execution).")
            else:
                st.info("No money will be spent and no ads will be created until you explicitly approve this plan.")
                if st.button("Approve Campaign Plan", type="primary"):
                    log_activity("HUMAN_APPROVAL", {"business": business["name"], "budget": business["monthly_budget"]}, status="APPROVED")
                    st.session_state["approved"] = True
                    st.rerun()

            st.subheader("Recent Activity Audit Log")
            log_path = Path("activity_log.jsonl")
            if log_path.exists():
                lines = log_path.read_text(encoding="utf-8").strip().splitlines()[-8:]
                st.json([json.loads(line) for line in reversed(lines)])
