import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# ---------------------------
# Helper Functions
# ---------------------------
def calculate_roi(subscribers, take_rate, max_customers, install_cost,
                  cost_per_customer, monthly_revenue, years, project_cost, discount_rate):
    total_possible = min(int(subscribers * take_rate), max_customers)

    # Ramp up Y1
    y1_q = [int(total_possible * pct) for pct in [0.25, 0.50, 0.75, 1.0]]
    subs_pattern = y1_q + [total_possible] * ((years-1) * 4)

    quarters = [f"Y{y}-{q}" for y in range(1, years + 1) for q in ["Q1","Q2","Q3","Q4"]]
    install_total = total_possible * install_cost

    quarterly_costs, quarterly_revenue = [], []
    for i, subs in enumerate(subs_pattern):
        cost = subs * cost_per_customer * 3
        if i == 0:
            cost += project_cost + install_total
        quarterly_costs.append(cost)
        quarterly_revenue.append(subs * monthly_revenue * 3)

    total_costs = np.cumsum(quarterly_costs).tolist()
    total_revenue = np.cumsum(quarterly_revenue).tolist()
    roi = [r - c for r, c in zip(total_revenue, total_costs)]
    cash_flow = [rev - cost for rev, cost in zip(quarterly_revenue, quarterly_costs)]

    # KPIs
    payback_quarter = next((i for i, val in enumerate(roi) if val >= 0), None)
    payback_text = f"{quarters[payback_quarter]} (~{(payback_quarter+1)*3} months)" if payback_quarter else "Not achieved"
    net_profit = roi[-1]
    roi_pct = (net_profit / total_costs[-1]) * 100 if total_costs[-1] > 0 else 0

    # NPV & IRR
    periods = np.arange(1, len(cash_flow)+1)
    discount_factors = [(1+discount_rate)**(p/4) for p in periods]
    npv = sum(cf/df for cf, df in zip(cash_flow, discount_factors))
    try:
        irr = np.irr(cash_flow) * 4 * 100
    except Exception:
        irr = None

    detail_df = pd.DataFrame({
        "Quarter": quarters,
        "Subscribers": subs_pattern,
        "Quarterly Revenue": quarterly_revenue,
        "Quarterly Costs": quarterly_costs,
        "Cash Flow": cash_flow,
        "Revenue (Cumulative)": total_revenue,
        "Costs (Cumulative)": total_costs,
        "ROI": roi
    })

    return {
        "quarters": quarters,
        "roi": roi,
        "cash_flow": cash_flow,
        "payback": payback_text,
        "net_profit": net_profit,
        "roi_pct": roi_pct,
        "npv": npv,
        "irr": irr,
        "detail": detail_df
    }

def export_scenarios(kpi_df, base, opt, pes):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        kpi_df.to_excel(writer, index=False, sheet_name="KPI Summary")
        base["detail"].to_excel(writer, index=False, sheet_name="Base Scenario")
        opt["detail"].to_excel(writer, index=False, sheet_name="Optimistic Scenario")
        pes["detail"].to_excel(writer, index=False, sheet_name="Pessimistic Scenario")
    return output.getvalue()

# ---------------------------
# Sidebar Inputs
# ---------------------------
st.sidebar.header("Base Inputs")
subscribers = st.sidebar.number_input("Total Subscribers", 1, 5000, 188)
max_customers = st.sidebar.number_input("Max Customers", 1, 5000, 200)
install_cost = st.sidebar.number_input("Install Cost per Customer", 0.0, 1000.0, 99.95, step=1.0)
years = st.sidebar.slider("Projection Years", 1, 10, 5)
project_cost = st.sidebar.number_input("Project Cost (from BOM)", 0.0, 1e7, 40000.0, step=1000.0)
discount_rate = st.sidebar.number_input("Discount Rate (%)", 0.0, 20.0, 5.0, step=0.5) / 100

# Scenario definitions
st.sidebar.header("Scenario Settings")

def scenario_inputs(label, default_take, default_rev, default_cost):
    st.sidebar.subheader(label)
    take_rate = st.sidebar.slider(f"{label} - Take Rate", 0.1, 1.0, default_take, 0.05)
    monthly_rev = st.sidebar.number_input(f"{label} - Monthly Revenue", 0.0, 500.0, default_rev, step=5.0)
    cost_per_cust = st.sidebar.number_input(f"{label} - Cost per Customer", 0.0, 500.0, default_cost, step=5.0)
    return take_rate, monthly_rev, cost_per_cust

base_take, base_rev, base_cost = scenario_inputs("Base", 0.5, 70.0, 50.0)
opt_take, opt_rev, opt_cost = scenario_inputs("Optimistic", 0.7, 80.0, 45.0)
pes_take, pes_rev, pes_cost = scenario_inputs("Pessimistic", 0.3, 60.0, 55.0)

# Run scenarios
base = calculate_roi(subscribers, base_take, max_customers, install_cost,
                     base_cost, base_rev, years, project_cost, discount_rate)
opt = calculate_roi(subscribers, opt_take, max_customers, install_cost,
                    opt_cost, opt_rev, years, project_cost, discount_rate)
pes = calculate_roi(subscribers, pes_take, max_customers, install_cost,
                    pes_cost, pes_rev, years, project_cost, discount_rate)

# ---------------------------
# Display KPI Comparison
# ---------------------------
st.title("📊 ROI Scenario Comparison Dashboard")

st.subheader("KPI Comparison")
kpi_df = pd.DataFrame([
    ["Base", base["payback"], f"${base['net_profit']:,.0f}", f"{base['roi_pct']:.1f}%", f"${base['npv']:,.0f}", f"{base['irr']:.1f}%" if base["irr"] else "n/a"],
    ["Optimistic", opt["payback"], f"${opt['net_profit']:,.0f}", f"{opt['roi_pct']:.1f}%", f"${opt['npv']:,.0f}", f"{opt['irr']:.1f}%" if opt["irr"] else "n/a"],
    ["Pessimistic", pes["payback"], f"${pes['net_profit']:,.0f}", f"{pes['roi_pct']:.1f}%", f"${pes['npv']:,.0f}", f"{pes['irr']:.1f}%" if pes["irr"] else "n/a"],
], columns=["Scenario", "Payback", "Net Profit", "ROI %", "NPV", "IRR"])
st.dataframe(kpi_df)

# ---------------------------
# Plot ROI Comparison
# ---------------------------
st.subheader("ROI Over Time (Scenarios)")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=base["quarters"], y=base["roi"], name="Base", line=dict(color="blue")))
fig1.add_trace(go.Scatter(x=opt["quarters"], y=opt["roi"], name="Optimistic", line=dict(color="green")))
fig1.add_trace(go.Scatter(x=pes["quarters"], y=pes["roi"], name="Pessimistic", line=dict(color="red")))
fig1.update_layout(title="Cumulative ROI by Scenario", xaxis_title="Quarter", yaxis_title="USD ($)", hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

# ---------------------------
# Plot Cash Flow Comparison
# ---------------------------
st.subheader("Cash Flow Over Time (Scenarios)")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=base["quarters"], y=base["cash_flow"], name="Base", line=dict(color="blue")))
fig2.add_trace(go.Scatter(x=opt["quarters"], y=opt["cash_flow"], name="Optimistic", line=dict(color="green")))
fig2.add_trace(go.Scatter(x=pes["quarters"], y=pes["cash_flow"], name="Pessimistic", line=dict(color="red")))
fig2.update_layout(title="Quarterly Cash Flow by Scenario", xaxis_title="Quarter", yaxis_title="USD ($)", hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# Download
# ---------------------------
st.subheader("Download Scenario Results")
excel_data = export_scenarios(kpi_df, base, opt, pes)
st.download_button(
    label="📥 Download All Scenarios (Excel)",
    data=excel_data,
    file_name="ROI_Scenarios.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)