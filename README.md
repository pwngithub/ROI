# ROI Scenario Dashboard (with File Upload)

This Streamlit app calculates ROI, NPV, and IRR for broadband projects using inputs from the ROI and BOM sheets of an uploaded Excel workbook.

## Features
- Upload your ROI workbook (.xlsx)
- Input adjustable parameters (subscribers, take rate, fees, onboarding)
- Scenarios (Base, Optimistic, Pessimistic)
- ROI, NPV, IRR calculations
- Interactive charts with Plotly
- Excel export

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
