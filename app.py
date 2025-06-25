import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from interest_rate_model import predict_interest_rate
from refinance_recommender import recommend_refinance_options
from payoff_simulator import simulate_payoff
from resources import get_resource_links, get_video_links

st.set_page_config(page_title="Student Loan Refinance & Payoff Navigator", layout="wide")

# ---- TABS ----
tab1, tab2 = st.tabs(["💸 Loan Calculator", "🔄 Refinance Comparison"])

with tab1:
    st.markdown("<h1 style='font-size: 2.8em; color: #800000; margin-bottom: 0.2em;'>🎓 STUDENT LOAN CALCULATOR</h1>", unsafe_allow_html=True)

    # --- Input Section ---
    st.markdown("<h2 style='color: #800000;'>Enter Your Loan Details</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        principal = st.number_input("Loan Amount ($)", min_value=1000, step=500, value=20000)
    with col2:
        annual_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=20.0, step=0.1, value=5.0)
    with col3:
        years = st.slider("Loan Term (Years)", 1, 30, 10)

    # --- Calculation Functions ---
    def calc_monthly_payment(P, r, n):
        if r == 0:
            return P / n
        return P * r * (1 + r) ** n / ((1 + r) ** n - 1)

    def amortization_schedule(P, annual_rate, years, monthly_payment):
        r = annual_rate / 100 / 12
        n = int(years * 12)
        schedule = []
        balance = P
        for i in range(1, n + 1):
            interest = balance * r
            principal_paid = monthly_payment - interest
            balance -= principal_paid
            balance = max(balance, 0)
            schedule.append({
                "Month": i,
                "Payment": round(monthly_payment, 2),
                "Principal Paid": round(principal_paid, 2),
                "Interest Paid": round(interest, 2),
                "Remaining Principal": round(balance, 2)
            })
            if balance == 0:
                break
        return pd.DataFrame(schedule)

    # --- Calculate on Button ---
    if st.button("Calculate Loan Schedule"):
        r = annual_rate / 100 / 12
        n = int(years * 12)
        monthly_payment = calc_monthly_payment(principal, r, n)
        schedule_df = amortization_schedule(principal, annual_rate, years, monthly_payment)
        total_interest = schedule_df["Interest Paid"].sum()
        total_payment = schedule_df["Payment"].sum()

        # --- Metrics ---
        st.markdown("<h2 style='color: #800000;'>📊 Loan Metrics</h2>", unsafe_allow_html=True)
        colA, colB, colC = st.columns(3)
        colA.metric("Monthly Payment", f"${monthly_payment:,.2f}")
        colB.metric("Total Interest Paid", f"${total_interest:,.2f}")
        colC.metric("Total Payment", f"${total_payment:,.2f}")

        # --- Filter for Amortization Table ---
        st.markdown("<h2 style='color: #800000;'>📅 Amortization Table</h2>", unsafe_allow_html=True)
        filter_option = st.selectbox(
            "Show amortization for:",
            ("First 12 months", "First 3 years", "Full term")
        )
        if filter_option == "First 12 months":
            display_df = schedule_df.head(12)
        elif filter_option == "First 3 years":
            display_df = schedule_df.head(36)
        else:
            display_df = schedule_df
        st.dataframe(display_df, use_container_width=True)
        st.download_button(
            "Download Full Amortization Table (CSV)",
            data=schedule_df.to_csv(index=False),
            file_name="student_loan_amortization.csv"
        )

        # --- Trend Charts ---
        st.markdown("<h2 style='color: #800000;'>📈 Loan Trends</h2>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=schedule_df["Month"],
            y=schedule_df["Remaining Principal"],
            mode='lines+markers',
            name="Principal Balance",
            line=dict(color="#800000", width=3),
            marker=dict(size=5),
            text=[f"${p:,.0f}" if i % 12 == 0 or i == len(schedule_df)-1 else "" for i, p in enumerate(schedule_df["Remaining Principal"])],
            textposition="top right"
        ))
        fig.add_trace(go.Scatter(
            x=schedule_df["Month"],
            y=schedule_df["Interest Paid"].cumsum(),
            mode='lines+markers',
            name="Cumulative Interest Paid",
            line=dict(color="royalblue", width=3, dash='dot'),
            marker=dict(size=5),
            text=[f"${ip:,.0f}" if i % 12 == 0 or i == len(schedule_df)-1 else "" for i, ip in enumerate(schedule_df["Interest Paid"].cumsum())],
            textposition="top right"
        ))
        fig.update_layout(
            title="Principal & Interest Reduction Over Loan Term",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.5)', bordercolor='gray'),
            font=dict(size=14),
            plot_bgcolor="#fafafa"
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Payment Breakdown Pie Chart ---
        st.markdown("<h2 style='color: #800000;'>💡 Payment Breakdown</h2>", unsafe_allow_html=True)
        pie_fig = go.Figure(data=[go.Pie(
            labels=["Principal", "Interest"],
            values=[principal, total_interest],
            marker=dict(colors=["#800000", "royalblue"]),
            hole=0.4,
            textinfo='label+percent+value'
        )])
        pie_fig.update_layout(
            title="Total Payments: Principal vs. Interest",
            font=dict(size=14)
        )
        st.plotly_chart(pie_fig, use_container_width=True)

        # --- Resources ---
        st.markdown("<h2 style='color: #800000;'>🔗 Useful Student Loan Resources</h2>", unsafe_allow_html=True)
        st.markdown("""
        ### [NerdWallet: Student Loan Calculator](https://www.nerdwallet.com/article/loans/student-loans/student-loan-calculator)
        ### [Federal Student Aid: Repayment Estimator](https://studentaid.gov/loan-simulator/)
        ### [YouTube: Student Loan Amortization Explained](https://www.youtube.com/watch?v=FvZl7F0gG8w)
        """)

    st.markdown("---")
    st.caption("This calculator is for educational purposes only. For personalized advice, consult a financial professional.")

# ---- TAB 2: Refinance Comparison ----
with tab2:
    st.title("Refinance Comparison & Savings Calculator")
    with st.form("refi_comp"):
        st.header("Current Loan Details", divider="gray")
        curr_principal = st.number_input("Current Principal ($)", min_value=1000.0, step=500.0, key="curr_principal")
        curr_rate = st.number_input("Current APR (%)", min_value=0.0, max_value=20.0, step=0.1, key="curr_rate")
        curr_years_left = st.number_input("Years Remaining", min_value=1.0, max_value=30.0, step=0.5, key="curr_years_left")

        st.header("Refinance Offer", divider="gray")
        new_rate = st.number_input("New APR (%)", min_value=0.0, max_value=20.0, step=0.1, key="new_rate")
        new_term = st.number_input("New Loan Term (Years)", min_value=1.0, max_value=30.0, step=0.5, key="new_term")
        submitted = st.form_submit_button("Compare & Visualize")

    def calculate_monthly_payment(principal, annual_rate, years):
        n = int(years * 12)
        r = (annual_rate / 100) / 12
        if r == 0:
            return principal / n
        return (r * principal * (1 + r) ** n) / ((1 + r) ** n - 1)

    def amortization_schedule(principal, annual_rate, years, monthly_payment):
        n = int(years * 12)
        r = (annual_rate / 100) / 12
        schedule = []
        balance = principal
        for i in range(1, n + 1):
            interest = balance * r
            principal_paid = monthly_payment - interest
            balance -= principal_paid
            balance = max(balance, 0)
            schedule.append({
                "Month": i,
                "Payment": round(monthly_payment, 2),
                "Principal Paid": round(principal_paid, 2),
                "Interest Paid": round(interest, 2),
                "Remaining Balance": round(balance, 2)
            })
            if balance == 0:
                break
        return schedule

    if submitted:
        curr_monthly = calculate_monthly_payment(curr_principal, curr_rate, curr_years_left)
        new_monthly = calculate_monthly_payment(curr_principal, new_rate, new_term)
        curr_amort = amortization_schedule(curr_principal, curr_rate, curr_years_left, curr_monthly)
        new_amort = amortization_schedule(curr_principal, new_rate, new_term, new_monthly)
        curr_total_paid = sum([x["Payment"] for x in curr_amort])
        curr_total_interest = sum([x["Interest Paid"] for x in curr_amort])
        new_total_paid = sum([x["Payment"] for x in new_amort])
        new_total_interest = sum([x["Interest Paid"] for x in new_amort])
        savings = curr_total_paid - new_total_paid
        interest_savings = curr_total_interest - new_total_interest

        st.header("💡 Results", divider="gray")
        colA, colB, colC = st.columns(3)
        colA.metric("Current Monthly Payment", f"${curr_monthly:,.2f}")
        colB.metric("Refinanced Monthly Payment", f"${new_monthly:,.2f}")
        colC.metric("Total Savings", f"${savings:,.2f}")

        st.metric("Current Total Interest", f"${curr_total_interest:,.2f}")
        st.metric("Refinanced Total Interest", f"${new_total_interest:,.2f}")
        st.metric("Interest Savings", f"${interest_savings:,.2f}")

        # Plot balance trends
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=[x["Remaining Balance"] for x in curr_amort],
            x=[x["Month"] for x in curr_amort],
            mode='lines+markers+text',
            name='Current Loan Balance',
            text=[f"${x['Remaining Balance']:,.0f}" if x['Month']%12==0 or x['Month']==len(curr_amort) else "" for x in curr_amort],
            textposition="top right"
        ))
        fig.add_trace(go.Scatter(
            y=[x["Remaining Balance"] for x in new_amort],
            x=[x["Month"] for x in new_amort],
            mode='lines+markers+text',
            name='Refinanced Loan Balance',
            text=[f"${x['Remaining Balance']:,.0f}" if x['Month']%12==0 or x['Month']==len(new_amort) else "" for x in new_amort],
            textposition="top right"
        ))
        fig.update_layout(title="Loan Balance Trend Over Time",
                          xaxis_title="Month",
                          yaxis_title="Balance ($)")
        st.plotly_chart(fig, use_container_width=True)

        # Plot interest vs. principal
        fig2 = go.Figure(data=[
            go.Bar(name='Current Loan', x=['Principal', 'Interest'],
                   y=[curr_principal, curr_total_interest],
                   text=[f"${curr_principal:,.0f}", f"${curr_total_interest:,.0f}"],
                   textposition='auto'),
            go.Bar(name='Refinanced Loan', x=['Principal', 'Interest'],
                   y=[curr_principal, new_total_interest],
                   text=[f"${curr_principal:,.0f}", f"${new_total_interest:,.0f}"],
                   textposition='auto')
        ])
        fig2.update_layout(barmode='group', title='Principal vs. Interest Paid')
        st.plotly_chart(fig2, use_container_width=True)

        # Show amortization table (first 12 months)
        st.header("Amortization Table (First 12 Months)", divider="gray")
        table_df = pd.DataFrame(new_amort[:12])
        st.dataframe(table_df)

        # Download full amortization as CSV
        st.download_button("Download Full Amortization Table (CSV)",
                           data=pd.DataFrame(new_amort).to_csv(index=False),
                           file_name="amortization_table.csv")

        st.header("📚 Learn More About Refinancing", divider="gray")
        st.markdown("### [NerdWallet: How to Refinance Student Loans](https://www.nerdwallet.com/article/loans/student-loans/how-to-refinance-student-loans)")
        st.markdown("### [ELFI Student Loan Refinance Calculator](https://www.elfi.com/refinance-student-loans/student-loan-refinance-calculator/)")
        st.markdown("### [YouTube: Student Loan Refinancing Explained](https://www.youtube.com/watch?v=6k4bVdKJv2Y)")

st.markdown("---")
st.caption("This tool is for educational purposes. Always compare offers and consult a financial advisor before refinancing.")
st