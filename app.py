import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(
    page_title="SAM.gov Global Contract Opportunities",
    page_icon="🌍",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/processed_contracts.csv')
        df['DatePosted'] = pd.to_datetime(df['Date Posted'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load continent mapping
@st.cache_data
def load_continent_mapping():
    try:
        continent_df = pd.read_csv('reference_data/PopCountry_by_Continent.csv')
        mapping = {}
        
        for continent in continent_df.columns:
            for cell in continent_df[continent].dropna():
                matches = re.findall(r'"([^"]+)"', str(cell))
                for match in matches:
                    mapping[match.strip()] = continent
                    mapping[match.strip().upper()] = continent
                    mapping[match.strip().lower()] = continent
        
        return mapping
    except Exception as e:
        st.error(f"Error loading continent mapping: {e}")
        return {}

def get_continent(country, mapping):
    if pd.isna(country):
        return "Unknown"
    country = str(country).strip()
    
    if country in mapping:
        return mapping[country]
    if country.upper() in mapping:
        return mapping[country.upper()]
    if country.lower() in mapping:
        return mapping[country.lower()]
    
    return "Unknown"

def display_overview_section(df, section_title, continent_filter=None):
    """Display a section of the overview with 4 tables"""
    
    if continent_filter:
        section_df = df[df['Continent'] == continent_filter].copy()
    else:
        section_df = df.copy()
    
    st.markdown(f"### {section_title}")
    st.markdown("---")
    
    if section_df.empty:
        st.info(f"No data available for {section_title}")
        return
    
    # Row 1: Two tables side by side
    col1, col2 = st.columns(2)
    
    with col1:
        # Table 1: By Countries or Continents
        if continent_filter:
            country_counts = section_df.groupby('Country').size().reset_index(name='Count')
            country_counts = country_counts.sort_values('Count', ascending=False)
            country_counts.columns = ['Country', 'Opportunities']
            st.markdown(f"**By Country ({len(section_df)} Total)**")
        else:
            country_counts = section_df[section_df['Continent'] != 'Unknown'].groupby('Continent').size().reset_index(name='Count')
            country_counts = country_counts.sort_values('Count', ascending=False)
            country_counts.columns = ['Continent', 'Opportunities']
            st.markdown(f"**By Continent ({len(section_df)} Total)**")
        
        st.dataframe(country_counts, use_container_width=True, hide_index=True, height=300)
    
    with col2:
        # Table 2: By Federal Agency/Department
        agency_counts = section_df.groupby('Federal Agency/Department').size().reset_index(name='Count')
        agency_counts = agency_counts.sort_values('Count', ascending=False)
        agency_counts.columns = ['Federal Agency/Department', 'Opportunities']
        st.markdown("**By Federal Agency/Department**")
        st.dataframe(agency_counts, use_container_width=True, hide_index=True, height=300)
    
    # Row 2: Two tables side by side
    col3, col4 = st.columns(2)
    
    with col3:
        # Table 3: By Industry Classification
        industry_counts = section_df.groupby('Industry Classification').size().reset_index(name='Count')
        industry_counts = industry_counts.sort_values('Count', ascending=False)
        industry_counts.columns = ['Industry Classification', 'Opportunities']
        st.markdown("**By Industry Classification**")
        st.dataframe(industry_counts, use_container_width=True, hide_index=True, height=300)
    
    with col4:
        # Table 4: By Product/Service Classification
        product_counts = section_df.groupby('Product/Service Classification').size().reset_index(name='Count')
        product_counts = product_counts.sort_values('Count', ascending=False)
        product_counts.columns = ['Product/Service Classification', 'Opportunities']
        st.markdown("**By Product/Service Classification**")
        st.dataframe(product_counts, use_container_width=True, hide_index=True, height=300)
    
    st.markdown("<br>", unsafe_allow_html=True)

def display_continent_data(df, continent_name, container):
    """Display data table for a continent tab"""
    with container:
        continent_df = df[df['Continent'] == continent_name].copy()
        
        if continent_df.empty:
            st.info(f"No opportunities found for {continent_name}")
            return
        
        st.markdown(f"**{len(continent_df)} opportunities in {continent_name}**")
        
        # Filter row 1: Country and Type of Opportunity
        col1, col2 = st.columns(2)
        with col1:
            countries = sorted(continent_df['Country'].dropna().unique())
            selected_countries = st.multiselect(
                "Filter by Country",
                options=countries,
                default=[],
                key=f"country_{continent_name}"
            )
        with col2:
            opp_types = sorted(continent_df['Type of Opportunity'].dropna().unique())
            selected_types = st.multiselect(
                "Filter by Type of Opportunity",
                options=opp_types,
                default=[],
                key=f"type_{continent_name}"
            )
        
        # Filter row 2: Federal Agency and Industry Classification
        col3, col4 = st.columns(2)
        with col3:
            agencies = sorted(continent_df['Federal Agency/Department'].dropna().unique())
            selected_agencies = st.multiselect(
                "Filter by Federal Agency/Department",
                options=agencies,
                default=[],
                key=f"agency_{continent_name}"
            )
        with col4:
            industries = sorted(continent_df['Industry Classification'].dropna().unique())
            selected_industries = st.multiselect(
                "Filter by Industry Classification",
                options=industries,
                default=[],
                key=f"industry_{continent_name}"
            )
        
        # Filter row 3: Product/Service Classification
        col5, col6 = st.columns(2)
        with col5:
            products = sorted(continent_df['Product/Service Classification'].dropna().unique())
            selected_products = st.multiselect(
                "Filter by Product/Service Classification",
                options=products,
                default=[],
                key=f"product_{continent_name}"
            )
        
        # Apply all filters
        filtered_df = continent_df.copy()
        
        if selected_countries:
            filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]
        if selected_types:
            filtered_df = filtered_df[filtered_df['Type of Opportunity'].isin(selected_types)]
        if selected_agencies:
            filtered_df = filtered_df[filtered_df['Federal Agency/Department'].isin(selected_agencies)]
        if selected_industries:
            filtered_df = filtered_df[filtered_df['Industry Classification'].isin(selected_industries)]
        if selected_products:
            filtered_df = filtered_df[filtered_df['Product/Service Classification'].isin(selected_products)]
        
        # Sort by DatePosted
        sorted_df = filtered_df.sort_values('DatePosted', ascending=False).copy()
        
        # Create display dataframe
        display_df = sorted_df[[
            'SAM.gov Link',
            'Date Posted',
            'Country',
            'Industry Classification',
            'Product/Service Classification',
            'Federal Agency/Department',
            'Type of Opportunity',
            'Notice ID'
        ]].copy()
        
        # Rename Link column for display
        display_df = display_df.rename(columns={'SAM.gov Link': 'Link'})
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link",
                    display_text="View"
                )
            }
        )
        
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label=f"Download {continent_name} Data (CSV)",
            data=csv,
            file_name=f"sam_gov_{continent_name.lower()}_contracts.csv",
            mime="text/csv",
            key=f"download_{continent_name}"
        )

def main():
    # Title and subtitle only
    st.markdown("<h1 style='margin-bottom: 0;'>SAM.gov Global Contract Opportunities</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: gray; margin-top: 0;'>Project by Jack Kozmetsky</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Load data
    df = load_data()
    continent_mapping = load_continent_mapping()
    
    if df.empty:
        st.warning("No data available. Please run data_processor.py first.")
        return
    
    # Add continent column
    df['Continent'] = df['Country'].apply(lambda x: get_continent(x, continent_mapping))
    
    # Create tabs - Overview first, then continents
    tab_overview, tab_africa, tab_asia, tab_europe, tab_americas, tab_oceania = st.tabs([
        "📊 Overview", "🌍 Africa", "🌏 Asia", "🌍 Europe", "🌎 Americas", "🌏 Oceania"
    ])
    
    # Overview Tab
    with tab_overview:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Global Section
        display_overview_section(df, "🌐 Global Contract Opportunities by the Numbers", continent_filter=None)
        
        # Africa Section
        display_overview_section(df, "🌍 AFRICA by the Numbers", continent_filter='AFRICA')
        
        # Asia Section
        display_overview_section(df, "🌏 ASIA by the Numbers", continent_filter='ASIA')
        
        # Europe Section
        display_overview_section(df, "🌍 EUROPE by the Numbers", continent_filter='EUROPE')
        
        # Americas Section
        display_overview_section(df, "🌎 AMERICAS by the Numbers", continent_filter='AMERICAS')
        
        # Oceania Section
        display_overview_section(df, "🌏 OCEANIA by the Numbers", continent_filter='OCEANIA')
    
    # Continent data tabs
    display_continent_data(df, "AFRICA", tab_africa)
    display_continent_data(df, "ASIA", tab_asia)
    display_continent_data(df, "EUROPE", tab_europe)
    display_continent_data(df, "AMERICAS", tab_americas)
    display_continent_data(df, "OCEANIA", tab_oceania)
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center; color: gray;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
