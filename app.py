import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# ---------------------------
# Helper Functions
# ---------------------------
def calculate_roi(subscribers, take_rate, max_customers, install_cost,
                  monthly_revenue, years, project_cost, discount_rate):
    total_possible = min(int(subscribers * take_rate), max_customers)

    subs_pattern = [total_possible] * years
    years_list = list(range(1, years+1))

    annual_revenue = [subs * monthly_revenue * 12 for subs in subs_pattern]
    annual_costs = [0]*years
    annual_costs[0] = project_cost + install_cost

    cash_flow = [rev - cost for rev, cost in zip(annual_revenue, annual_costs)]
    cum_revenue = np.cumsum(annual_revenue).tolist()
    cum_costs = np.cumsum(annual_costs).tolist()
    roi = [r - c for r, c in zip(cum_revenue, cum_costs)]

    # KPIs
    payback_year = next((i+1 for i,v in enumerate(roi) if v >= 0), None)
    net_profit = roi[-1]
    roi_pct = (net_profit/cum_costs[-1])*100 if cum_costs[-1] > 0 else 0

    # NPV & IRR
    discount_factors = [(1+discount_rate)**y for y in years_list]
    npv = sum(cf/df for cf,df in zip(cash_flow,discount_factors))
    try:
        irr = np.irr([-annual_costs[0]] + annual_revenue[1:]) * 100
    except Exception:
        irr = None

    detail_df = pd.DataFrame({
        "Year": years_list,
        "Subscribers": subs_pattern,
        "Revenue": annual_revenue,
        "Costs": annual_costs,
        "Cash Flow": cash_flow,
        "Cumulative Revenue": cum_revenue,
        "Cumulative Costs": cum_costs,
        "ROI": roi
    })

    return {
        "years": years_list,
        "roi": roi,
        "cash_flow": cash_flow,
        "revenue": annual_revenue,
        "costs": annual_costs,
        "payback": payback_year,
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
# Upload File
# ---------------------------
st.title("📊 ROI Scenario Dashboard")

uploaded_file = st.file_uploader("Upload ROI Workbook", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        bom_df = pd.read_excel(xls, sheet_name="BOM")

        # Pull project cost (look for 'Grand Total')
        project_cost = None
        for i, row in bom_df.iterrows():
            if row.astype(str).str.contains("Grand Total", case=False, na=False).any():
                nums = [v for v in row if isinstance(v, (int, float))]
                if nums:
                    project_cost = nums[0]
                    break
        if project_cost is None:
            st.warning("⚠️ Could not find Grand Total in BOM sheet. Defaulting to 0.")
            project_cost = 0.0

        # ---------------------------
        # Sidebar Inputs
        # ---------------------------
        st.sidebar.header("Base Inputs")
        subscribers = st.sidebar.number_input("Total Subscribers (Households)", 1, 100000, 188)
        max_customers = st.sidebar.number_input("Max Customers", 1, 100000, 200)
        years = st.sidebar.slider("Projection Years", 1, 10, 5)
        discount_rate = st.sidebar.number_input("Discount Rate (%)", 0.0, 20.0, 5.0, step=0.5)/100

        # Scenario inputs
        def scenario_inputs(label, default_take, default_rev, default_cost):
            st.sidebar.subheader(label)
            take_rate = st.sidebar.slider(f"{label} - Take Rate", 0.1, 1.0, default_take, 0.05)
            monthly_rev = st.sidebar.number_input(f"{label} - Monthly Fee", 0.0, 500.0, default_rev, step=5.0)
            onboard_cost = st.sidebar.number_input(f"{label} - Onboarding Cost", 0.0, 1e6, default_cost, step=100.0)
            return take_rate, monthly_rev, onboard_cost

        base_take, base_rev, base_cost = scenario_inputs("Base", 0.5, 70.0, 50000.0)
        opt_take, opt_rev, opt_cost = scenario_inputs("Optimistic", 0.7, 80.0, 40000.0)
        pes_take, pes_rev, pes_cost = scenario_inputs("Pessimistic", 0.3, 60.0, 60000.0)

        # Run scenarios
        base = calculate_roi(subscribers, base_take, max_customers, base_cost, base_rev, years, project_cost, discount_rate)
        opt = calculate_roi(subscribers, opt_take, max_customers, opt_cost, opt_rev, years, project_cost, discount_rate)
        pes = calculate_roi(subscribers, pes_take, max_customers, pes_cost, pes_rev, years, project_cost, discount_rate)

        # KPI Table
        st.subheader("KPI Comparison")
        kpi_df = pd.DataFrame([
            ["Base", base["payback"], f"${base['net_profit']:,.0f}", f"{base['roi_pct']:.1f}%", f"${base['npv']:,.0f}", f"{base['irr']:.1f}%" if base["irr"] else "n/a"],
            ["Optimistic", opt["payback"], f"${opt['net_profit']:,.0f}", f"{opt['roi_pct']:.1f}%", f"${opt['npv']:,.0f}", f"{opt['irr']:.1f}%" if opt["irr"] else "n/a"],
            ["Pessimistic", pes["payback"], f"${pes['net_profit']:,.0f}", f"{pes['roi_pct']:.1f}%", f"${pes['npv']:,.0f}", f"{pes['irr']:.1f}%" if pes["irr"] else "n/a"],
        ], columns=["Scenario","Payback Year","Net Profit","ROI %","NPV","IRR"])
        st.dataframe(kpi_df)

        # ROI Chart
        st.subheader("ROI Over Time")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=base["years"], y=base["roi"], name="Base"))
        fig1.add_trace(go.Scatter(x=opt["years"], y=opt["roi"], name="Optimistic"))
        fig1.add_trace(go.Scatter(x=pes["years"], y=pes["roi"], name="Pessimistic"))
        fig1.update_layout(title="Cumulative ROI", xaxis_title="Year", yaxis_title="USD")
        st.plotly_chart(fig1, use_container_width=True)

        # Cash Flow Chart
        st.subheader("Cash Flow Over Time")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=base["years"], y=base["cash_flow"], name="Base"))
        fig2.add_trace(go.Scatter(x=opt["years"], y=opt["cash_flow"], name="Optimistic"))
        fig2.add_trace(go.Scatter(x=pes["years"], y=pes["cash_flow"], name="Pessimistic"))
        fig2.update_layout(title="Annual Cash Flow", xaxis_title="Year", yaxis_title="USD")
        st.plotly_chart(fig2, use_container_width=True)

        # Download
        st.subheader("Download Results")
        excel_data = export_scenarios(kpi_df, base, opt, pes)
        st.download_button(
            label="📥 Download All Scenarios (Excel)",
            data=excel_data,
            file_name="ROI_Scenarios.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("👆 Please upload your ROI workbook to begin.")
