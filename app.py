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

        # Reload raw sheet to find section headers & official Grand Total
        raw_bom = pd.read_excel(uploaded_file, sheet_name="BOM", header=None)

        sections = []
        grand_total_value = None

        for i, row in raw_bom.iterrows():
            row_str = [str(v).strip().lower() if pd.notna(v) else "" for v in row]

            # Section headers
            for cell in row_str:
                if "entire project" in cell.lower():
                    sections.append((i, cell.strip()))

            # Grand Total detection
            for j, cell in enumerate(row_str):
                if "grand total" in cell:
                    try:
                        grand_total_value = float(row[j+1])
                    except:
                        continue

        # Compute section subtotals
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
        if grand_total_value is not None:
            section_df.loc[len(section_df.index)] = ["Grand Total", grand_total_value]
        else:
            section_df.loc[len(section_df.index)] = ["Grand Total", section_df["Subtotal"].sum()]

        st.dataframe(section_df.style.format({"Subtotal": "${:,.2f}"}), use_container_width=True)

        # Altair bar chart of section breakdown
        st.markdown("### 📊 Cost Breakdown by Section")
        section_chart = alt.Chart(section_df[section_df["Section"] != "Grand Total"]).mark_bar().encode(
            x=alt.X("Section", sort="-y"),
            y="Subtotal",
            tooltip=["Section", "Subtotal"]
        ).properties(width=700, height=400)
        st.altair_chart(section_chart, use_container_width=True)

        # Use official Grand Total for ROI calculator
        if grand_total_value is not None:
            total_project_cost = grand_total_value
        else:
            total_project_cost = section_df.loc[section_df["Section"] == "Grand Total", "Subtotal"].values[0]

        st.success(f"💰 Grand Total Project Cost: **${total_project_cost:,.2f}**")

        # ROI calculator inputs
        monthly_price = st.number_input("Monthly revenue per customer ($)", value=67.95, step=0.50, format="%.2f")
        install_fee = st.number_input("One-time install fee per customer ($)", value=99.95, step=1.00, format="%.2f")
        years = st.slider("ROI timeframe (years)", min_value=1, max_value=10, value=3)

        # Market assumptions
        st.subheader("📌 Market Assumptions")
        max_customers = st.number_input("Maximum serviceable customers", value=1000, step=50)
        take_rate = st.slider("Expected take rate (%)", min_value=1, max_value=100, value=40)

        effective_customers = int(max_customers * (take_rate / 100.0))

        if effective_customers > 0:
            cost_per_customer = total_project_cost / effective_customers
        else:
            cost_per_customer = 0

        st.write(f"**Effective Customers (based on {take_rate}% take rate):** {effective_customers:,}")
        st.write(f"**Cost per Customer:** ${cost_per_customer:,.2f}")

        # ROI calculation with install fee using effective customers
        months = years * 12
        revenue_per_customer = (monthly_price * months) + install_fee
        total_revenue = effective_customers * revenue_per_customer
        roi_coverage = total_revenue / total_project_cost

        st.subheader("📈 ROI Analysis (Based on Market Assumptions)")
        st.write(f"Over **{years} years ({months} months)** with {effective_customers:,} effective customers:")
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
        st.metric("Project Cost", f"${total_project_cost:,.2f}")
        st.metric("ROI Coverage", f"{roi_coverage:.2f}x")

        if roi_coverage >= 1:
            st.success("✅ The project covers its cost with the given customers and take rate.")
        else:
            st.error("❌ The project does not cover its cost with the given customers and take rate.")

        # Scenario table by years
        st.markdown("### 🔍 Multi-Year Scenario Comparison")
        scenario_years = list(range(1, 11))
        roi_df = pd.DataFrame({
            "Years": scenario_years,
            "Months": [y * 12 for y in scenario_years],
        })
        roi_df["Revenue per Customer"] = (roi_df["Months"] * monthly_price) + install_fee
        roi_df["Total Revenue"] = effective_customers * roi_df["Revenue per Customer"]
        roi_df["ROI Coverage (x)"] = roi_df["Total Revenue"] / total_project_cost

        st.dataframe(roi_df.style.format({
            "Revenue per Customer": "${:,.2f}",
            "Total Revenue": "${:,.2f}",
            "ROI Coverage (x)": "{:,.2f}"
        }), use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error processing BOM: {e}")
