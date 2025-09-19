# Extra inputs for max customers and take rate
st.subheader("📌 Market Assumptions")

max_customers = st.number_input("Maximum serviceable customers", value=1000, step=50)
take_rate = st.slider("Expected take rate (%)", min_value=1, max_value=100, value=40)

# Effective customers
effective_customers = int(max_customers * (take_rate / 100.0))

# Cost per customer
if effective_customers > 0:
    cost_per_customer = total_project_cost / effective_customers
else:
    cost_per_customer = 0

st.write(f"**Effective Customers (based on {take_rate}% take rate):** {effective_customers:,}")
st.write(f"**Cost per Customer:** ${cost_per_customer:,.2f}")

# Compare with customers needed for ROI
if effective_customers >= customers_needed:
    st.success(f"✅ With {effective_customers:,} effective customers, the project covers costs (needs {customers_needed:,.0f}).")
else:
    st.error(f"❌ With {effective_customers:,} effective customers, the project falls short (needs {customers_needed:,.0f}).")
