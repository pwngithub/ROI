import streamlit as st
import pandas as pd

st.set_page_config(page_title="ROI Calculator", page_icon="📊", layout="wide")
st.title("📊 ROI Calculator from BOM")

uploaded_file = st.file_uploader("Upload BOM Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Load BOM sheet (clean version with headers at row 6)
        bom_clean = pd.read_excel(uploaded_file, sheet_name="BOM", skiprows=6)

        # Drop empty columns
        bom_clean = bom_clean.dropna(axis=1, how="all")

        # Ensure numeric conversion for Total price
        if "Total price" in bom_clean.columns:
            bom_clean["Total price"] = pd.to_numeric(bom_clean["Total price"], errors="coerce")
        else:
            st.error("❌ 'Total price' column not found in BOM sheet.")
            st.stop()

        # Reload raw sheet to find section headers
        raw_bom = pd.read_excel(uploaded_file, sheet_name="BOM", header=None)

        # Find section headers
        sections = []
        for i, row in raw_bom.iterrows():
            row_str = [str(v).strip() if pd.notna(v) else "" for v in row]
            for cell in row_str:
                if "bill of materials" in cell.lower() and "entire project" in cell.lower():
                    sections.append((i, cell.strip()))

        # Compute subtotals by slicing BOM rows
        section_totals = {}
        for idx, (row_index, section_name) in enumerate(sections):
            # Start = next data row, End = next header or end of file
            start = row_index + 2
            end = sections[idx + 1][0] if idx + 1 < len(sections) else len(bom_clean) + start

            # Extract slice of BOM clean data (adjust for skiprows=6)
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

        # Use grand total for ROI calculator
        total_project_cost = section_df.loc[section_df["Section"] == "Grand Total", "Subtotal"].values[0]

        st.success(f"💰 Grand Total Project Cost: **${total_project_cost:,.2f}**")

        # ROI calculator inputs
        monthly_price = st.number_input(
            "Monthly revenue per customer ($)",
            value=67.95, step=0.50, format="%.2f"
        )
        years = st.slider("ROI timeframe (years)", min_value=1, max_value=10, value=3)

        # ROI calculation
        months = years * 12
        revenue_per_customer = monthly_price * months
        customers_needed = total_project_cost / revenue_per_customer

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
        st.error(f"⚠️ Error processing BOM: {e}")
