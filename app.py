import streamlit as st
import pandas as pd

st.set_page_config(page_title="ROI Calculator", page_icon="📊", layout="wide")
st.title("📊 ROI Calculator from BOM")

uploaded_file = st.file_uploader("Upload BOM Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Read BOM sheet without headers to scan for total
        raw_bom = pd.read_excel(uploaded_file, sheet_name="BOM", header=None)

        total_project_cost = None

        # Search for "grand total" (case-insensitive, ignores punctuation like ':')
        for i, row in raw_bom.iterrows():
            row_str = [str(v).strip().lower() if pd.notna(v) else "" for v in row]
            for j, cell in enumerate(row_str):
                if "grand total" in cell:
                    try:
                        total_project_cost = float(row[j+1])
                        break
                    except:
                        continue
            if total_project_cost is not None:
                break

        if total_project_cost is None:
            st.error("❌ Could not find 'Grand Total' in BOM sheet. Please check formatting.")
            st.stop()

        st.success(f"💰 Total Project Cost: **${total_project_cost:,.2f}**")

        # User inputs
        monthly_price = st.number_input(
            "Monthly revenue per customer ($)",
            value=67.95, step=0.50, format="%.2f"
        )
        years = st.slider("ROI timeframe (years)", min_value=1, max_value=10, value=3)

        # ROI calculation
        months = years * 12
        revenue_per_customer = monthly_price * months
        customers_needed = total_project_cost / revenue_per_customer

        # Results
        st.subheader("📈 ROI Analysis")
        st.write(f"Over **{years} years ({months} months)** at **${monthly_price:.2f}/customer**:")
        st.metric("Customers Needed", f"{customers_needed:,.0f}")

        # Scenario table
        st.markdown("### 🔍 Multi-Year Scenario Comparison")
        scenario_years = list(range(1, 11))
        roi_df = pd.DataFrame({
            "Years": scenario_years,
            "Months": [y * 12 for y in scenario_years],
        })
        roi_df["Revenue per Customer"] = roi_df["Months"] * monthly_price
        roi_df["Customers Needed"] = total_project_cost / roi_df["Revenue per Customer"]

        st.dataframe(roi_df.style.format({
            "Revenue per Customer": "${:,.2f}",
            "Customers Needed": "{:,.0f}"
        }), use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
