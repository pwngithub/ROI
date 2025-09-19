import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="ROI Calculator", page_icon="📊", layout="wide")
st.title("📊 ROI Calculator from BOM")

uploaded_file = st.file_uploader("Upload BOM Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Load BOM sheet (clean version with headers at row 6)
        bom_clean = pd.read_excel(uploaded_file, sheet_name="BOM", skiprows=6)
        bom_clean = bom_clean.dropna(axis=1, how="all")

        if "Total price" not in bom_clean.columns:
            st.error("❌ 'Total price' column not found in BOM sheet.")
            st.stop()

        bom_clean["Total price"] = pd.to_numeric(bom_clean["Total price"], errors="coerce")

        # Reload raw sheet to find section headers
        raw_bom = pd.read_excel(uploaded_file, sheet_name="BOM", header=None)

        sections = []
        for i, row in raw_bom.iterrows():
            row_str = [str(v).strip() if pd.notna(v) else "" for v in row]
            for cell in row_str:
                if "entire project" in cell.lower():
                    sections.append((i, cell.strip()))

        section_totals = {}
        for idx, (row_index, section_name) in enumerate(sections):
            start = row_index + 2
            end = sections[idx + 1][0] if idx + 1 < len(sections) else len(bom_clean) + start
            section_data = bom_clean.iloc[(start-6):(end-6), :]
            subtotal = section_data["Total price"].sum(skipna=True)
            section_totals[section_name] = subtotal

        # Display section overview
        st.subheader("📋 Project Overview by Section")
        section_df = pd.DataFrame(
            {"Section": list(section_totals.keys()), "Subtotal": list(section_totals.values())}
        )
        section_df.loc[len(section_df.index)] = ["Grand Total", section_df["Subtotal"].sum()]
        st.dataframe(section_df.style.format({"Subtotal": "${:,.2f}"}), use_container_width=True)

        # 🔥 Bar chart instead of matplotlib pie
        st.markdown("### 📊 Cost Breakdown by Section")
        section_chart = alt.Chart(section_df[section_df["Section"] != "Grand Total"]).mark_bar().encode(
            x=alt.X("Section", sort="-y"),
            y="Subtotal",
            tooltip=["Section", "Subtotal"]
        ).properties(width=700, height=400)
        st.altair_chart(section_chart, use_container_width=True)

        # Use grand total for ROI calculator
        total_project_cost = section_df.loc[section_df["Section"] == "Grand Total", "Subtotal"].values[0]
        st.success(f"💰 Grand Total Project Cost: **${total_project_cost:,.2f}**")

        # ROI calculator inputs
        monthly_price = st.number_input("Monthly revenue per customer ($)", value=67.95, step=0.50, format="%.2f")
        install_fee = st.number_input("One-time install fee per customer ($)", value=99.95, step=1.00, format="%.2f")
        years = st.slider("ROI timeframe (years)", min_value=1, max_value=10, value=3)

        # ROI calculation with install fee
        months = years * 12
        revenue_per_customer = (monthly_price * months) + install_fee
        customers_needed = total_project_cost / revenue_per_customer

        st.subheader("📈 ROI Analysis")
        st.write(f"Over **{years} years ({months} months)** at **${monthly_price:.2f}/month + ${install_fee:.2f} install fee per customer**:")
        st.metric("Customers Needed", f"{customers_needed:,.0f}")

        # Scenario table
        st.markdown("### 🔍 Multi-Year Scenario Comparison")
        scenario_years = list(range(1, 11))
        roi_df = pd.DataFrame({
            "Years": scenario_years,
            "Months": [y * 12 for y in scenario_years],
        })
        roi_df["Revenue per Customer"] = (roi_df["Months"] * monthly_price) + install_fee
        roi_df["Customers Needed"] = total_project_cost / roi_df["Revenue per Customer"]

        st.dataframe(roi_df.style.format({
            "Revenue per Customer": "${:,.2f}",
            "Customers Needed": "{:,.0f}"
        }), use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error processing BOM: {e}")
