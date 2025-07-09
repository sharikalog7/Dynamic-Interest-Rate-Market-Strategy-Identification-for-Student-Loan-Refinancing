import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from io import BytesIO
import base64

st.set_page_config(page_title="Student Loan Navigator", layout="wide", page_icon="🎓", initial_sidebar_state="expanded")

# Helper to download figures
def fig_to_download_link(fig, filename="chart.png"):
    try:
        buf = BytesIO()
        fig.write_image(buf, format="png", width=800, height=500, scale=2)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"[Download Chart as PNG](data:image/png;base64,{b64})"
    except Exception as e:
        st.warning("Unable to generate PNG download link (Kaleido may not be supported in this environment).")
        return ""

# --- Loan Calculator Tab ---
tab1, tab2 = st.tabs(["💸 Loan Calculator", "🔄 Refinance Comparison"])

with tab1:
    st.header("🎓 Student Loan Calculator", anchor=False)

    # Inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        principal = st.number_input("Loan Amount ($)", 1000, 500_000, 20_000, step=500)
    with col2:
        annual_rate = st.slider("Annual Interest Rate (%)", 0.0, 20.0, 5.0, step=0.1)
    with col3:
        years = st.slider("Loan Term (Years)", 1, 30, 10)

    # Calculate payments
    r = annual_rate / 100 / 12
    n = years * 12
    if r == 0:
        monthly_payment = principal / n
    else:
        monthly_payment = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)

    # Build amortization
    df = []
    balance = principal
    for m in range(1, int(n) + 1):
        interest = balance * r
        principal_paid = monthly_payment - interest
        balance -= principal_paid
        df.append({
            "Month": m,
            "Principal Paid": principal_paid,
            "Interest Paid": interest,
            "Remaining Balance": max(balance, 0)
        })
        if balance <= 0:
            break
    schedule = pd.DataFrame(df)
    total_interest = schedule["Interest Paid"].sum()
    total_payment = schedule["Principal Paid"].sum() + total_interest

    # Metrics
    st.subheader("📊 Loan Summary")
    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly Payment", f"${monthly_payment:,.2f}")
    m2.metric("Total Interest Paid", f"${total_interest:,.2f}")
    m3.metric("Total Payment", f"${total_payment:,.2f}")

    # Charts
    st.subheader("📈 Principal vs. Interest Over Time")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=schedule["Month"], y=schedule["Principal Paid"].cumsum(),
        mode="lines", name="Cumulative Principal",
        hovertemplate="%{y:$,.0f}"
    ))
    fig1.add_trace(go.Scatter(
        x=schedule["Month"], y=schedule["Interest Paid"].cumsum(),
        mode="lines", name="Cumulative Interest",
        hovertemplate="%{y:$,.0f}"
    ))
    fig1.update_layout(template="plotly_white", legend=dict(x=0, y=1))
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown(fig_to_download_link(fig1), unsafe_allow_html=True)

    st.subheader("📊 Remaining Balance Over Time")
    fig2 = go.Figure(go.Scatter(
        x=schedule["Month"], y=schedule["Remaining Balance"], fill="tozeroy",
        mode="lines", name="Balance", hovertemplate="%{y:$,.0f}"
    ))
    fig2.update_layout(template="plotly_white", yaxis_title="Balance ($)")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown(fig_to_download_link(fig2), unsafe_allow_html=True)

    # Amortization Table Toggle
    if st.checkbox("Show Amortization Table"):
        st.dataframe(schedule, use_container_width=True)
        csv = schedule.to_csv(index=False).encode()
        st.download_button("Download Schedule CSV", csv, "amortization.csv", "text/csv")

# --- Refinance Comparison Tab ---
with tab2:
    st.header("🔄 Refinance Comparison & Savings Timeline")

    # Allow up to 3 scenarios
    scenarios = []
    for i in range(1, 4):
        with st.expander(f"Refinance Scenario {i}"):
            p = st.number_input(f"Principal ($) - Scenario {i}", 1000.0, 500_000.0, key=f"p{i}")
            rate = st.number_input(f"APR (%) - Scenario {i}", 0.0, 20.0, key=f"r{i}")
            term = st.slider(f"Term (Years) - Scenario {i}", 1.0, 30.0, key=f"t{i}")
            scenarios.append((p, rate, term))

    # Compute each
    all_schedules = {}
    for idx, (p, rate, term) in enumerate(scenarios, start=1):
        if p and rate:
            r = rate / 100 / 12
            n = int(term * 12)
            mp = p * r * (1 + r) ** n / ((1 + r) ** n - 1) if r else p / n
            df2 = []
            bal = p
            for m in range(1, n + 1):
                i_paid = bal * r
                pr_paid = mp - i_paid
                bal -= pr_paid
                df2.append({"Month": m, "Remaining Balance": bal, "Total Paid": mp * m})
                if bal <= 0:
                    break
            all_schedules[f"Scenario {idx}"] = pd.DataFrame(df2)

    # Plot all on same axes
    st.subheader("📈 Balance Comparison")
    fig3 = go.Figure()
    for name, df3 in all_schedules.items():
        fig3.add_trace(go.Scatter(
            x=df3["Month"], y=df3["Remaining Balance"],
            name=name, mode="lines"
        ))
    fig3.update_layout(template="plotly_white", yaxis_title="Balance ($)")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown(fig_to_download_link(fig3), unsafe_allow_html=True)

    # Savings Timeline
    st.subheader("💰 Cumulative Savings Over Time")
    base = list(all_schedules.values())[0]
    fig4 = go.Figure()
    for name, df4 in list(all_schedules.items())[1:]:
        savings = base["Total Paid"].values[:len(df4)] - df4["Total Paid"]
        fig4.add_trace(go.Scatter(x=df4["Month"], y=savings, name=name))
    fig4.update_layout(template="plotly_white", yaxis_title="Savings ($)")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown(fig_to_download_link(fig4), unsafe_allow_html=True)

    # Download combined CSV
    if st.button("Download All Scenarios Data"):
        combined = pd.concat(all_schedules.values(), keys=all_schedules.keys(), names=["Scenario", "Row"])
        csv2 = combined.reset_index().to_csv(index=False).encode()
        st.download_button("Download Scenarios CSV", csv2, "refinance_comparison.csv", "text/csv")

st.markdown("---\n*This app is for educational/demo purposes only.*", unsafe_allow_html=True)
