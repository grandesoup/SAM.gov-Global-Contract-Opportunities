import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="Spirit of America - Global Contract Opportunities",
    page_icon="🌍",
    layout="wide"
)

DATA_FILE = "data/processed_contracts.csv"
COUNTRIES_FILE = "reference_data/PopCountry_by_Continent.csv"


@st.cache_data
def load_continent_countries():
    continents = {"AFRICA": [], "ASIA": [], "EUROPE": [], "AMERICAS": [], "OCEANIA": []}
    try:
        df = pd.read_csv(COUNTRIES_FILE, encoding='utf-8-sig')
        for continent in continents.keys():
            if continent in df.columns:
                for cell in df[continent].dropna():
                    parts = cell.replace('"', '').split(',')
                    for part in parts:
                        clean = part.strip()
                        if clean and len(clean) >= 2:
                            continents[continent].append(clean.upper())
    except Exception as e:
        st.error(f"Error loading country mappings: {e}")
    return continents


@st.cache_data
def load_contract_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig', dtype=str)
            date_cols = ['Date Posted', 'Response Deadline', 'Date Awarded', 'Date Archived']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            return df
        except Exception as e:
            st.error(f"Error loading contract data: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def filter_by_continent(df, continent, continent_countries):
    if df.empty or 'Country' not in df.columns:
        return df
    countries = continent_countries.get(continent, [])
    if not countries:
        return pd.DataFrame()
    mask = df['Country'].astype(str).str.upper().str.strip().isin(countries)
    return df[mask].copy()


def display_data_table(df, key_prefix):
    if df.empty:
        st.info("No contract opportunities found for this continent.")
        return
    
    countries = sorted(df['Country'].dropna().unique().tolist())
    selected_countries = st.multiselect(
        "Filter by Country",
        options=countries,
        default=[],
        key=f"{key_prefix}_country_filter"
    )
    
    if selected_countries:
        df = df[df['Country'].isin(selected_countries)]
    
    col1, col2 = st.columns(2)
    with col1:
        show_active = st.checkbox("Show Active", value=True, key=f"{key_prefix}_active")
    with col2:
        show_archived = st.checkbox("Show Archived", value=True, key=f"{key_prefix}_archived")
    
    if 'Active?' in df.columns:
        if show_active and not show_archived:
            df = df[df['Active?'] == 'Yes']
        elif show_archived and not show_active:
            df = df[df['Active?'] == 'No']
    
    st.markdown(f"**Showing {len(df)} opportunities**")
    
    st.dataframe(
        df,
        use_container_width=True,
        height=600,
        column_config={
            "SAM.gov Link": st.column_config.LinkColumn("SAM.gov Link"),
            "Award Amount $": st.column_config.NumberColumn("Award Amount $", format="$%d"),
            "Date Posted": st.column_config.DateColumn("Date Posted"),
            "Response Deadline": st.column_config.DateColumn("Response Deadline"),
            "Date Awarded": st.column_config.DateColumn("Date Awarded"),
            "Date Archived": st.column_config.DateColumn("Date Archived"),
        }
    )
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"{key_prefix}_contracts.csv",
        mime="text/csv",
        key=f"{key_prefix}_download"
    )


def main():
    st.title("Spirit of America - Global Contract Opportunities")
    st.markdown("**U.S. Government Contract Opportunities by Place of Performance**")
    
    continent_countries = load_continent_countries()
    df = load_contract_data()
    
    with st.sidebar:
        st.header("Data Management")
        
        if os.path.exists(DATA_FILE):
            mod_time = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
            st.info(f"Last updated: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        
        st.markdown("---")
        st.subheader("Manual Data Upload")
        st.markdown("If automatic updates fail, upload the SAM.gov CSV manually:")
        
        uploaded_file = st.file_uploader(
            "Upload ContractOpportunitiesFullCSV.csv",
            type=['csv'],
            help="Download from sam.gov/data-services"
        )
        
        if uploaded_file is not None:
            st.warning("Manual upload processing not yet implemented.")
        
        st.markdown("---")
        st.subheader("Date Filter")
        
        min_date = datetime(2023, 1, 1)
        max_date = datetime(2025, 12, 31)
        
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
    if not df.empty and len(date_range) == 2:
        start_date, end_date = date_range
        if 'Date Posted' in df.columns:
            mask = (df['Date Posted'] >= pd.Timestamp(start_date)) & (df['Date Posted'] <= pd.Timestamp(end_date))
            df = df[mask]
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Opportunities", len(df))
        with col2:
            active_count = len(df[df['Active?'] == 'Yes']) if 'Active?' in df.columns else 0
            st.metric("Active", active_count)
        with col3:
            countries = df['Country'].nunique() if 'Country' in df.columns else 0
            st.metric("Countries", countries)
        with col4:
            agencies = df['Federal Agency/Department'].nunique() if 'Federal Agency/Department' in df.columns else 0
            st.metric("Agencies", agencies)
    else:
        st.warning("No data loaded. Run the data processor or upload data manually.")
    
    st.markdown("---")
    
    tab_africa, tab_asia, tab_europe, tab_americas, tab_oceania = st.tabs([
        "AFRICA", "ASIA", "EUROPE", "AMERICAS", "OCEANIA"
    ])
    
    with tab_africa:
        st.header("Africa Contract Opportunities")
        africa_df = filter_by_continent(df, "AFRICA", continent_countries)
        display_data_table(africa_df, "africa")
    
    with tab_asia:
        st.header("Asia Contract Opportunities")
        asia_df = filter_by_continent(df, "ASIA", continent_countries)
        display_data_table(asia_df, "asia")
    
    with tab_europe:
        st.header("Europe Contract Opportunities")
        europe_df = filter_by_continent(df, "EUROPE", continent_countries)
        display_data_table(europe_df, "europe")
    
    with tab_americas:
        st.header("Americas Contract Opportunities")
        americas_df = filter_by_continent(df, "AMERICAS", continent_countries)
        display_data_table(americas_df, "americas")
    
    with tab_oceania:
        st.header("Oceania Contract Opportunities")
        oceania_df = filter_by_continent(df, "OCEANIA", continent_countries)
        display_data_table(oceania_df, "oceania")
    
    st.markdown("---")
    st.markdown("*Data sourced from SAM.gov. Updated weekly on Mondays.*")


if __name__ == "__main__":
    main()