import httpx
import plotly.graph_objects as go
import streamlit as st

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

DECISION_COLORS = {
    "continue": "#22c55e",
    "clarify": "#f59e0b",
    "fallback": "#f97316",
    "handoff": "#ef4444",
}

STATUS_COLORS = {
    "active": "#3b82f6",
    "completed": "#22c55e",
    "handed_off": "#ef4444",
    "failed": "#6b7280",
}

EVENT_ICONS = {
    "utterance_received": "\U0001f4ac",
    "intent_predicted": "\U0001f9e0",
    "policy_checked": "\U0001f6e1\ufe0f",
    "downstream_called": "\U0001f310",
    "decision_made": "\u2696\ufe0f",
    "handoff_created": "\U0001f4de",
}

SCENARIO_DESCRIPTIONS = {
    "safe_continue": "Order status query from a verified caller \u2014 high confidence, safe intent",
    "low_confidence_clarify": "Vague utterance the AI can\u2019t parse \u2014 triggers a clarification request",
    "cancel_order_unverified": "Cancel order without identity verification \u2014 risky action blocked",
    "downstream_failure": "Valid query but the downstream Order API times out \u2014 forced handoff",
}

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def api_get(path: str) -> dict | list | None:
    try:
        r = httpx.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None


def api_post(path: str, json: dict) -> dict | None:
    try:
        r = httpx.post(f"{API_BASE}{path}", json=json, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="CallGuard Dashboard",
    page_icon="\U0001f6e1\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("\U0001f6e1\ufe0f CallGuard")
    st.caption("AI Escalation & Recovery Engine")
    st.divider()

    health = api_get("/health")
    if health:
        st.success(f"API online \u00b7 v{health['version']}")
    else:
        st.error("API offline \u2014 start the server with:\n\n`uv run uvicorn app.main:app`")
        st.stop()

    page = st.radio(
        "Navigate",
        ["\U0001f3ae Simulate", "\U0001f4cb Call Explorer", "\U0001f4ca Analytics"],
        label_visibility="collapsed",
    )

# ---------------------------------------------------------------------------
# Helpers: render a single call detail
# ---------------------------------------------------------------------------


def render_call_detail(call: dict) -> None:
    """Render the full detail view for a single call."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", call["status"].replace("_", " ").title())
    with col2:
        if call["decisions"]:
            d = call["decisions"][-1]
            st.metric("Decision", d["decision"].upper(), delta=d["reason"].replace("_", " "))
        else:
            st.metric("Decision", "Pending")
    with col3:
        if call["decisions"]:
            risk = call["decisions"][-1]["risk_score"]
            st.metric("Risk Score", f"{risk:.0%}")
        else:
            st.metric("Risk Score", "\u2014")

    # Decision detail cards
    if call["decisions"]:
        d = call["decisions"][-1]
        st.markdown("#### Decision Detail")
        dc1, dc2, dc3, dc4 = st.columns(4)
        dc1.markdown(f"**Intent:** `{d['intent']}`")
        dc2.markdown(f"**Confidence:** `{d['confidence']:.0%}`")
        dc3.markdown(f"**Risk:** `{d['risk_score']:.0%}`")
        color = DECISION_COLORS.get(d["decision"], "#6b7280")
        dc4.markdown(
            f"**Decision:** <span style='color:{color};font-weight:700'>"
            f"{d['decision'].upper()}</span>",
            unsafe_allow_html=True,
        )

    # Handoff summary
    if call["handoff_summaries"]:
        st.markdown("#### \U0001f4de Handoff Summary")
        for hs in call["handoff_summaries"]:
            st.warning(hs["summary"])

    # Event timeline
    st.markdown("#### \U0001f4c8 Event Timeline")
    render_timeline(call["events"])

    # Pipeline latency chart
    latency_events = [e for e in call["events"] if e.get("latency_ms")]
    if latency_events:
        st.markdown("#### \u23f1\ufe0f Pipeline Latency")
        render_latency_chart(latency_events)


def render_timeline(events: list[dict]) -> None:
    """Render a vertical event timeline."""
    for i, event in enumerate(events):
        icon = EVENT_ICONS.get(event["event_type"], "\u25cf")
        label = event["event_type"].replace("_", " ").title()
        latency = f" \u00b7 {event['latency_ms']:.1f}ms" if event.get("latency_ms") else ""

        with st.container():
            ecol1, ecol2 = st.columns([0.08, 0.92])
            with ecol1:
                st.markdown(
                    f"<div style='text-align:center;font-size:1.6rem;line-height:2'>{icon}</div>",
                    unsafe_allow_html=True,
                )
            with ecol2:
                st.markdown(f"**{label}**{latency}")
                render_event_payload(event["event_type"], event["payload"])

        if i < len(events) - 1:
            st.markdown(
                "<div style='border-left:2px solid #cbd5e1;height:8px;margin-left:1.6rem'></div>",
                unsafe_allow_html=True,
            )


def render_event_payload(event_type: str, payload: dict) -> None:
    """Render payload content based on event type."""
    if event_type == "utterance_received":
        verified_badge = (
            "\u2705 Verified" if payload.get("verified") else "\u274c Not verified"
        )
        st.markdown(f'> *"{payload.get("text", "")}"* \u2014 {verified_badge}')

    elif event_type == "intent_predicted":
        confidence = payload.get("confidence", 0)
        intent = payload.get("intent", "unknown")
        entities = payload.get("entities", {})
        parts = [f"`{intent}` \u00b7 confidence **{confidence:.0%}**"]
        if entities:
            ent_str = ", ".join(f"{k}=`{v}`" for k, v in entities.items())
            parts.append(f"entities: {ent_str}")
        st.markdown(" \u00b7 ".join(parts))

    elif event_type == "policy_checked":
        violations = payload.get("violations", [])
        risk = payload.get("risk_score", 0)
        if violations:
            for v in violations:
                sev_color = "#ef4444" if v["severity"] == "deny" else "#f59e0b"
                st.markdown(
                    f"<span style='color:{sev_color};font-weight:600'>"
                    f"[{v['severity'].upper()}]</span> {v['rule']} \u2014 {v['description']}",
                    unsafe_allow_html=True,
                )
            st.markdown(f"Aggregate risk score: **{risk:.0%}**")
        else:
            st.markdown("\u2705 No policy violations")

    elif event_type == "decision_made":
        decision = payload.get("decision", "")
        reason = payload.get("reason", "")
        color = DECISION_COLORS.get(decision, "#6b7280")
        st.markdown(
            f"<span style='color:{color};font-weight:700'>{decision.upper()}</span>"
            f" \u2014 {reason.replace('_', ' ')}",
            unsafe_allow_html=True,
        )

    elif event_type == "downstream_called":
        if payload.get("success"):
            st.markdown(f"\u2705 Success \u2014 `{payload.get('data', {})}`")
        else:
            st.markdown(f"\u274c **Failed** \u2014 {payload.get('error', 'unknown')}")

    elif event_type == "handoff_created":
        st.markdown(f"*{payload.get('summary', '')}*")

    else:
        st.json(payload)


def render_latency_chart(events: list[dict]) -> None:
    """Horizontal bar chart of latency per pipeline step."""
    labels = [e["event_type"].replace("_", " ").title() for e in events]
    values = [e["latency_ms"] for e in events]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color="#6366f1",
            text=[f"{v:.1f}ms" for v in values],
            textposition="auto",
        )
    )
    fig.update_layout(
        height=max(180, len(labels) * 50),
        margin=dict(l=0, r=20, t=10, b=10),
        xaxis_title="Latency (ms)",
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: Simulate
# ═══════════════════════════════════════════════════════════════════════════

if page == "\U0001f3ae Simulate":
    st.header("\U0001f3ae Scenario Simulator")
    st.markdown(
        "Run predefined scenarios to see how CallGuard processes each call "
        "through the pipeline. Each scenario demonstrates a different decision path."
    )

    scenarios = api_get("/api/v1/simulate/scenarios") or []

    tabs = st.tabs([s.replace("_", " ").title() for s in scenarios])

    for tab, scenario in zip(tabs, scenarios):
        with tab:
            desc = SCENARIO_DESCRIPTIONS.get(scenario, "")
            st.info(desc)

            if st.button(f"Run \u25b6", key=f"run_{scenario}", use_container_width=True):
                with st.spinner("Running scenario\u2026"):
                    result = api_post(
                        "/api/v1/simulate/scenario",
                        json={"scenario": scenario},
                    )
                if result:
                    render_call_detail(result["call"])
                else:
                    st.error("Simulation failed. Check the API server.")

    st.divider()
    st.subheader("\U0001f4dd Custom Utterance")
    st.markdown("Create a call and send a custom utterance through the pipeline.")

    with st.form("custom_utterance"):
        col_phone, col_text = st.columns([1, 3])
        phone = col_phone.text_input("Caller phone", value="+13105559999")
        utterance = col_text.text_input("Utterance", value="I want to cancel my order #7890")
        col_v, col_ds = st.columns(2)
        verified = col_v.checkbox("Caller is verified")
        force_fail = col_ds.checkbox("Simulate downstream failure")
        submitted = st.form_submit_button("Process", use_container_width=True)

    if submitted and utterance:
        with st.spinner("Processing\u2026"):
            call_resp = api_post("/api/v1/calls", json={"caller_phone": phone})
            if call_resp:
                call_id = call_resp["id"]
                api_post(
                    f"/api/v1/calls/{call_id}/utterances",
                    json={
                        "text": utterance,
                        "verified": verified,
                        "simulate_downstream_failure": force_fail,
                    },
                )
                call_detail = api_get(f"/api/v1/calls/{call_id}")
                if call_detail:
                    render_call_detail(call_detail)
                else:
                    st.error("Failed to fetch call details.")
            else:
                st.error("Failed to create call.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: Call Explorer
# ═══════════════════════════════════════════════════════════════════════════

elif page == "\U0001f4cb Call Explorer":
    st.header("\U0001f4cb Call Explorer")
    st.markdown("Browse all processed calls and inspect their full event timelines.")

    call_id_input = st.number_input(
        "Enter Call ID",
        min_value=1,
        step=1,
        value=1,
    )

    if st.button("Load Call", use_container_width=True):
        with st.spinner("Fetching\u2026"):
            call_detail = api_get(f"/api/v1/calls/{call_id_input}")

        if call_detail:
            st.markdown(
                f"**Call** `{call_detail['external_id']}` \u00b7 "
                f"**Phone** `{call_detail['caller_phone']}` \u00b7 "
                f"**Created** `{call_detail['created_at']}`"
            )
            render_call_detail(call_detail)
        else:
            st.warning(f"Call #{call_id_input} not found. Run a simulation first to create calls.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: Analytics
# ═══════════════════════════════════════════════════════════════════════════

elif page == "\U0001f4ca Analytics":
    st.header("\U0001f4ca Analytics")
    st.markdown(
        "Generate all 4 demo scenarios and see aggregated analytics across them."
    )

    if st.button("\U0001f504 Generate All Scenarios", use_container_width=True):
        st.session_state["analytics_calls"] = []
        scenarios = api_get("/api/v1/simulate/scenarios") or []
        progress = st.progress(0.0, text="Running scenarios\u2026")
        for i, scenario in enumerate(scenarios):
            result = api_post("/api/v1/simulate/scenario", json={"scenario": scenario})
            if result:
                st.session_state["analytics_calls"].append(result["call"])
            progress.progress((i + 1) / len(scenarios))
        progress.empty()
        st.success(f"Generated {len(st.session_state['analytics_calls'])} calls.")

    calls = st.session_state.get("analytics_calls", [])

    if not calls:
        st.info("Click the button above to generate scenario data for analytics.")
        st.stop()

    # KPI row
    total = len(calls)
    decisions_all = [d for c in calls for d in c["decisions"]]
    handoffs = sum(1 for d in decisions_all if d["decision"] == "handoff")
    continues = sum(1 for d in decisions_all if d["decision"] == "continue")
    clarifies = sum(1 for d in decisions_all if d["decision"] == "clarify")
    avg_risk = sum(d["risk_score"] for d in decisions_all) / len(decisions_all) if decisions_all else 0
    avg_conf = sum(d["confidence"] for d in decisions_all) / len(decisions_all) if decisions_all else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Calls", total)
    k2.metric("Handoffs", handoffs)
    k3.metric("Continues", continues)
    k4.metric("Avg Risk", f"{avg_risk:.0%}")
    k5.metric("Avg Confidence", f"{avg_conf:.0%}")

    st.divider()

    chart1, chart2 = st.columns(2)

    # Decision distribution donut
    with chart1:
        st.subheader("Decision Distribution")
        decision_counts: dict[str, int] = {}
        for d in decisions_all:
            decision_counts[d["decision"]] = decision_counts.get(d["decision"], 0) + 1

        labels = list(decision_counts.keys())
        values = list(decision_counts.values())
        colors = [DECISION_COLORS.get(l, "#6b7280") for l in labels]

        fig = go.Figure(
            go.Pie(
                labels=[l.upper() for l in labels],
                values=values,
                hole=0.5,
                marker=dict(colors=colors),
                textinfo="label+value",
                textfont_size=14,
            )
        )
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Confidence vs Risk scatter
    with chart2:
        st.subheader("Confidence vs Risk")
        fig = go.Figure()
        for decision_type, color in DECISION_COLORS.items():
            subset = [d for d in decisions_all if d["decision"] == decision_type]
            if subset:
                fig.add_trace(
                    go.Scatter(
                        x=[d["confidence"] for d in subset],
                        y=[d["risk_score"] for d in subset],
                        mode="markers",
                        name=decision_type.upper(),
                        marker=dict(color=color, size=14, line=dict(width=1, color="white")),
                        text=[d["reason"].replace("_", " ") for d in subset],
                        hovertemplate="Confidence: %{x:.0%}<br>Risk: %{y:.0%}<br>%{text}<extra></extra>",
                    )
                )

        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(title="Confidence", range=[-0.05, 1.05], tickformat=".0%"),
            yaxis=dict(title="Risk Score", range=[-0.05, 1.05], tickformat=".0%"),
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Pipeline latency comparison
    st.subheader("\u23f1\ufe0f Pipeline Latency by Call")
    all_events = [(c["external_id"], e) for c in calls for e in c["events"] if e.get("latency_ms")]

    if all_events:
        fig = go.Figure()
        call_ids_seen: list[str] = []
        for call in calls:
            cid = call["external_id"][:16]
            latency_events = [e for e in call["events"] if e.get("latency_ms")]
            if latency_events:
                call_ids_seen.append(cid)
                fig.add_trace(
                    go.Bar(
                        name=cid,
                        x=[e["event_type"].replace("_", " ").title() for e in latency_events],
                        y=[e["latency_ms"] for e in latency_events],
                        text=[f"{e['latency_ms']:.1f}ms" for e in latency_events],
                        textposition="auto",
                    )
                )

        fig.update_layout(
            barmode="group",
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis_title="Latency (ms)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Per-call summary table
    st.subheader("Call Summary")
    table_data = []
    for c in calls:
        d = c["decisions"][-1] if c["decisions"] else {}
        table_data.append(
            {
                "Call ID": c["external_id"][:16],
                "Phone": c["caller_phone"],
                "Status": c["status"].replace("_", " ").title(),
                "Intent": d.get("intent", "\u2014"),
                "Confidence": f"{d['confidence']:.0%}" if d.get("confidence") else "\u2014",
                "Risk": f"{d['risk_score']:.0%}" if d.get("risk_score") is not None else "\u2014",
                "Decision": d.get("decision", "\u2014").upper(),
                "Reason": d.get("reason", "\u2014").replace("_", " "),
                "Events": len(c["events"]),
            }
        )
    st.dataframe(table_data, use_container_width=True, hide_index=True)
