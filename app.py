import streamlit as st
import pandas as pd
import plotly.express as px
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
                # Extract all quoted values from the cell
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

def main():
    st.markdown("<h1 style='margin-bottom: 0;'>SAM.gov Global Contract Opportunities</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: gray; margin-top: 0;'>Project by Jack Kozmetsky</p>", unsafe_allow_html=True)
    
    df = load_data()
    continent_mapping = load_continent_mapping()
    
    if df.empty:
        st.warning("No data available. Please run data_processor.py first.")
        return
    
    df['Continent'] = df['Country'].apply(lambda x: get_continent(x, continent_mapping))
    
    continent_counts = df[df['Continent'] != 'Unknown'].groupby('Continent').size().reset_index(name='Count')
    total_opportunities = continent_counts['Count'].sum()
    
    if total_opportunities == 0:
        st.warning("No countries matched the continent mapping.")
        st.write("Sample countries in data:", df['Country'].dropna().unique()[:10].tolist())
        return
    
    fig = px.pie(
        continent_counts, 
        values='Count', 
        names='Continent',
        color='Continent',
        color_discrete_map={
            'AFRICA': '#FF6B6B',
            'ASIA': '#4ECDC4',
            'EUROPE': '#45B7D1',
            'AMERICAS': '#96CEB4',
            'OCEANIA': '#FFEAA7'
        }
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='label+value',
        hovertemplate='%{label}: %{value} opportunities<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=20, b=80, l=20, r=20),
        height=350,
        annotations=[
            dict(
                text=f"<b>{total_opportunities}</b><br>Total Opportunities",
                x=0.5, y=-0.15,
                font_size=14,
                showarrow=False,
                xanchor='center'
            )
        ]
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    tab_africa, tab_asia, tab_europe, tab_americas, tab_oceania = st.tabs([
        "🌍 Africa", "🌏 Asia", "🌍 Europe", "🌎 Americas", "🌏 Oceania"
    ])
    
    def display_continent_data(continent_name, container):
        with container:
            continent_df = df[df['Continent'] == continent_name].copy()
            
            if continent_df.empty:
                st.info(f"No opportunities found for {continent_name}")
                return
            
            st.markdown(f"**{len(continent_df)} opportunities in {continent_name}**")
            
            col1, col2 = st.columns(2)
            with col1:
                min_date = continent_df['DatePosted'].min()
                if pd.isna(min_date):
                    min_date = datetime(2023, 1, 1)
                start_date = st.date_input(
                    "Start Date", 
                    value=min_date,
                    key=f"start_{continent_name}"
                )
            with col2:
                max_date = continent_df['DatePosted'].max()
                if pd.isna(max_date):
                    max_date = datetime.now()
                end_date = st.date_input(
                    "End Date", 
                    value=max_date,
                    key=f"end_{continent_name}"
                )
            
            mask = (continent_df['DatePosted'].dt.date >= start_date) & (continent_df['DatePosted'].dt.date <= end_date)
            filtered_df = continent_df[mask]
            
            countries = sorted(filtered_df['Country'].dropna().unique())
            selected_countries = st.multiselect(
                "Filter by Country",
                options=countries,
                default=[],
                key=f"country_{continent_name}"
            )
            
            if selected_countries:
                filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]
            
            display_cols = [
                'Notice ID', 'Date Posted', 'Country', 'Federal Agency/Department',
                'Industry Classification', 'Product/Service Classification', 
                'Response Deadline', 'Type of Opportunity'
            ]
            available_cols = [c for c in display_cols if c in filtered_df.columns]
            
            # Sort by DatePosted then select only display columns
            sorted_df = filtered_df.sort_values('DatePosted', ascending=False)
            
            st.dataframe(
                sorted_df[available_cols],
                use_container_width=True,
                height=400
            )
            
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label=f"Download {continent_name} Data (CSV)",
                data=csv,
                file_name=f"sam_gov_{continent_name.lower()}_contracts.csv",
                mime="text/csv",
                key=f"download_{continent_name}"
            )
    
    display_continent_data("AFRICA", tab_africa)
    display_continent_data("ASIA", tab_asia)
    display_continent_data("EUROPE", tab_europe)
    display_continent_data("AMERICAS", tab_americas)
    display_continent_data("OCEANIA", tab_oceania)
    
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center; color: gray;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
