# Spirit of America - Global Contract Opportunities Dashboard

Interactive dashboard tracking U.S. Government contract opportunities worldwide.

## Features

- **5 Continent Tabs**: Africa, Asia, Europe, Americas, Oceania
- **Searchable/Filterable Tables**: Filter by country, agency, NAICS code, etc.
- **Weekly Auto-Updates**: Data refreshed every Monday via GitHub Actions
- **Manual Upload Fallback**: Upload CSV manually if automation fails
- **2023-2025 Data**: Contract opportunities from the past 2 years

## Data Source

[SAM.gov Contract Opportunities](https://sam.gov/data-services/Contract%20Opportunities/datagov?privacy=Public)

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `streamlit run app.py`

## Deployment

Deployed on Streamlit Cloud. Updates automatically every Monday.

---
*Built for Spirit of America*
