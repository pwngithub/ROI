# ROI Calculator from BOM 📊

This Streamlit app calculates ROI based on BOM costs and your market assumptions.

## Features
- Upload an Excel file containing a BOM sheet
- Automatically extracts **section subtotals** and the official **Grand Total**
- Displays a **bar chart** showing section cost breakdown
- Adjustable **monthly revenue per customer**
- Adjustable **ROI timeframe (years)**
- Includes a **one-time install fee per customer**
- Uses the **Grand Total from the BOM sheet**
- Shows ROI results only based on **your max customers and take rate**
- Calculates:
  - Effective customers
  - Cost per customer
  - Total revenue vs. project cost
  - ROI coverage (x multiple)
- Includes **multi-year scenario table**

## How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.
