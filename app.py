import streamlit as st
import pandas as pd

st.set_page_config(page_title="ROI Calculator", page_icon="📊", layout="wide")
st.title("📊 ROI Calculator from BOM")

# Upload Excel file
uploaded_file = st.file_uploader("Upload BOM Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Load Excel and BOM sheet
        xls = pd.ExcelFile(uploaded_file)

        if "BOM" in xls.sheet_names:
            # Get project cost from BOM sheet header (Grand Total is in row 2, col 6)
            raw_bom = pd.read_excel(uploaded_file, sheet_name="BOM", header=None)
            
            try:
                total_project_cost = float(raw_bom.iloc[2, 6])  # Grand Total
            except Exception:
                st.error("❌ Could not find Grand Total in BOM sheet. Please check format.")
                st.stop()

            st.success(f"💰 Total Project Cost: **${total_project_cost:,.2f}**")

            # User inputs
            monthly_price = st.number_input(
                "Monthly revenue per customer ($)", 
                value=67.95, step=0.50, format="%.2f"
            )
            years = st.slider("ROI timeframe (years)", min_value=1, max_value=10, value=3)

            # Calculation
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

        else:
            st.error("❌ BOM sheet not found in uploaded Excel file.")

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
