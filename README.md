# ROI Calculator from BOM 📊

This Streamlit app calculates the number of customers needed to achieve ROI based on a BOM Excel file.

## Features
- Upload an Excel file containing a BOM sheet
- Automatically extracts **section subtotals** and **Grand Total**
- Displays a **pie chart** showing section cost breakdown
- Adjustable **monthly revenue per customer**
- Adjustable **ROI timeframe (years)**
- Includes a **one-time install fee per customer**
- Shows **required customers for break-even**
- Includes **multi-year comparison table**

## How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.
