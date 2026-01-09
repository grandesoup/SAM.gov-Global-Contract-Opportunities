"""
SAM.gov Contract Opportunities Data Processor
Downloads and processes the SAM.gov CSV file for Spirit of America dashboard.
"""

import pandas as pd
import requests
import os
from datetime import datetime
import sys

# Configuration
SAM_GOV_URL = "https://sam.gov/api/prod/fileextractservices/v2/download/Contract%20Opportunities/datagov/Contract%20Opportunities%20Full%20CSV?random={}"
OUTPUT_FILE = "data/processed_contracts.csv"
NAICS_FILE = "reference_data/NaicsCode_Descriptions.csv"
CLASSIFICATION_FILE = "reference_data/ClassificationCode_Descriptions.csv"
COUNTRIES_FILE = "reference_data/PopCountry_by_Continent.csv"

# Columns to keep from SAM.gov CSV (original names)
COLUMNS_TO_KEEP = [
    'PostedDate',
    'ResponseDeadLine',
    'PopCountry',
    'NaicsCode',
    'ClassificationCode',
    'Type',
    'Department/Ind.Agency',
    'Sub-Tier',
    'Description',
    'Award$',
    'Active',
    'AwardDate',
    'Awardee',
    'ArchiveDate',
    'Link',
    'NoticeId',
    'Sol#',
    'AwardNumber'
]

# Column renaming map
COLUMN_RENAME = {
    'PostedDate': 'Date Posted',
    'ResponseDeadLine': 'Response Deadline',
    'PopCountry': 'Country',
    'NaicsCode': 'Industry Classification',
    'ClassificationCode': 'Product/Service Classification',
    'Type': 'Type of Opportunity',
    'Department/Ind.Agency': 'Federal Agency/Department',
    'Sub-Tier': 'Sub-Agency/Department',
    'Description': 'Opportunity Description',
    'Award$': 'Award Amount $',
    'Active': 'Active?',
    'AwardDate': 'Date Awarded',
    'Awardee': 'Awardee',
    'ArchiveDate': 'Date Archived',
    'Link': 'SAM.gov Link',
    'NoticeId': 'Notice ID',
    'Sol#': 'Solicitation #',
    'AwardNumber': 'Award Number'
}

# Country code to name mapping
COUNTRY_NAMES = {
    "DZA": "Algeria", "AGO": "Angola", "BEN": "Benin", "BWA": "Botswana",
    "BFA": "Burkina Faso", "BDI": "Burundi", "CPV": "Cabo Verde", "CMR": "Cameroon",
    "CAF": "Central African Republic", "TCD": "Chad", "COM": "Comoros", "COG": "Congo",
    "COD": "Democratic Republic of the Congo", "DJI": "Djibouti", "EGY": "Egypt",
    "GNQ": "Equatorial Guinea", "ERI": "Eritrea", "SWZ": "Eswatini", "ETH": "Ethiopia",
    "GAB": "Gabon", "GMB": "Gambia", "GHA": "Ghana", "GIN": "Guinea", "GNB": "Guinea-Bissau",
    "CIV": "Côte d'Ivoire", "KEN": "Kenya", "LSO": "Lesotho", "LBR": "Liberia",
    "LBY": "Libya", "MDG": "Madagascar", "MWI": "Malawi", "MLI": "Mali", "MRT": "Mauritania",
    "MUS": "Mauritius", "MAR": "Morocco", "MOZ": "Mozambique", "NAM": "Namibia",
    "NER": "Niger", "NGA": "Nigeria", "RWA": "Rwanda", "STP": "Sao Tome and Principe",
    "SEN": "Senegal", "SYC": "Seychelles", "SLE": "Sierra Leone", "SOM": "Somalia",
    "ZAF": "South Africa", "SSD": "South Sudan", "SDN": "Sudan", "TZA": "Tanzania",
    "TGO": "Togo", "TUN": "Tunisia", "UGA": "Uganda", "ZMB": "Zambia", "ZWE": "Zimbabwe",
    "AFG": "Afghanistan", "ARM": "Armenia", "AZE": "Azerbaijan", "BHR": "Bahrain",
    "BGD": "Bangladesh", "BTN": "Bhutan", "BRN": "Brunei", "KHM": "Cambodia",
    "CHN": "China", "CYP": "Cyprus", "GEO": "Georgia", "IND": "India", "IDN": "Indonesia",
    "IRN": "Iran", "IRQ": "Iraq", "ISR": "Israel", "JPN": "Japan", "JOR": "Jordan",
    "KAZ": "Kazakhstan", "KWT": "Kuwait", "KGZ": "Kyrgyzstan", "LAO": "Laos",
    "LBN": "Lebanon", "MYS": "Malaysia", "MDV": "Maldives", "MNG": "Mongolia",
    "MMR": "Myanmar", "NPL": "Nepal", "PRK": "North Korea", "OMN": "Oman",
    "PAK": "Pakistan", "PHL": "Philippines", "QAT": "Qatar", "SAU": "Saudi Arabia",
    "SGP": "Singapore", "KOR": "South Korea", "LKA": "Sri Lanka", "SYR": "Syria",
    "TWN": "Taiwan", "TJK": "Tajikistan", "THA": "Thailand", "TLS": "Timor-Leste",
    "TUR": "Turkey", "TKM": "Turkmenistan", "ARE": "United Arab Emirates",
    "UZB": "Uzbekistan", "VNM": "Vietnam", "HKG": "Hong Kong", "MAC": "Macau",
    "ALB": "Albania", "AND": "Andorra", "AUT": "Austria", "BLR": "Belarus",
    "BEL": "Belgium", "BIH": "Bosnia and Herzegovina", "BGR": "Bulgaria",
    "HRV": "Croatia", "CZE": "Czech Republic", "DNK": "Denmark", "EST": "Estonia",
    "FIN": "Finland", "FRA": "France", "DEU": "Germany", "GRC": "Greece",
    "HUN": "Hungary", "ISL": "Iceland", "IRL": "Ireland", "ITA": "Italy",
    "XKX": "Kosovo", "LVA": "Latvia", "LIE": "Liechtenstein", "LTU": "Lithuania",
    "LUX": "Luxembourg", "MLT": "Malta", "MDA": "Moldova", "MCO": "Monaco",
    "MNE": "Montenegro", "NLD": "Netherlands", "MKD": "North Macedonia",
    "NOR": "Norway", "POL": "Poland", "PRT": "Portugal", "ROU": "Romania",
    "SMR": "San Marino", "SRB": "Serbia", "SVK": "Slovakia", "SVN": "Slovenia",
    "ESP": "Spain", "SWE": "Sweden", "CHE": "Switzerland", "UKR": "Ukraine",
    "GBR": "United Kingdom", "VAT": "Vatican City",
    "ATG": "Antigua and Barbuda", "BHS": "Bahamas", "BRB": "Barbados", "BLZ": "Belize",
    "CAN": "Canada", "CRI": "Costa Rica", "CUB": "Cuba", "DMA": "Dominica",
    "DOM": "Dominican Republic", "SLV": "El Salvador", "GRD": "Grenada",
    "GTM": "Guatemala", "HTI": "Haiti", "HND": "Honduras", "JAM": "Jamaica",
    "MEX": "Mexico", "NIC": "Nicaragua", "PAN": "Panama", "KNA": "Saint Kitts and Nevis",
    "LCA": "Saint Lucia", "VCT": "Saint Vincent and the Grenadines",
    "TTO": "Trinidad and Tobago", "ARG": "Argentina", "BOL": "Bolivia", "BRA": "Brazil",
    "CHL": "Chile", "COL": "Colombia", "ECU": "Ecuador", "GUY": "Guyana",
    "PRY": "Paraguay", "PER": "Peru", "SUR": "Suriname", "URY": "Uruguay", "VEN": "Venezuela",
    "AUS": "Australia", "FJI": "Fiji", "KIR": "Kiribati", "MHL": "Marshall Islands",
    "FSM": "Micronesia", "NRU": "Nauru", "NZL": "New Zealand", "PLW": "Palau",
    "PNG": "Papua New Guinea", "WSM": "Samoa", "SLB": "Solomon Islands",
    "TON": "Tonga", "TUV": "Tuvalu", "VUT": "Vanuatu",
    "GRL": "Greenland", "PRI": "Puerto Rico", "AIA": "Anguilla", "GUM": "Guam"
}


def load_all_valid_countries():
    """Load all valid country codes/names from the continent mapping file."""
    valid_countries = set()
    
    try:
        df = pd.read_csv(COUNTRIES_FILE, encoding='utf-8-sig')
        for continent in ['AFRICA', 'ASIA', 'EUROPE', 'AMERICAS', 'OCEANIA']:
            if continent in df.columns:
                for cell in df[continent].dropna():
                    parts = cell.replace('"', '').split(',')
                    for part in parts:
                        clean = part.strip().upper()
                        if clean and len(clean) >= 2:
                            valid_countries.add(clean)
    except Exception as e:
        print(f"Error loading countries file: {e}")
    
    return valid_countries


def load_naics_descriptions():
    """Load NAICS code descriptions."""
    try:
        df = pd.read_csv(NAICS_FILE, encoding='utf-8-sig', dtype=str)
        df.columns = ['NaicsCode', 'Description']
        return dict(zip(df['NaicsCode'].astype(str).str.strip(), df['Description']))
    except Exception as e:
        print(f"Error loading NAICS descriptions: {e}")
        return {}


def load_classification_descriptions():
    """Load Classification code descriptions."""
    try:
        df = pd.read_csv(CLASSIFICATION_FILE, encoding='utf-8-sig', dtype=str)
        df.columns = ['ClassificationCode', 'Description']
        return dict(zip(df['ClassificationCode'].astype(str).str.strip(), df['Description']))
    except Exception as e:
        print(f"Error loading Classification descriptions: {e}")
        return {}


def download_sam_csv():
    """
    Attempt to download SAM.gov CSV.
    Returns DataFrame if successful, None if blocked/failed.
    """
    print("Attempting to download SAM.gov CSV...")
    
    # Add random parameter to avoid caching
    url = SAM_GOV_URL.format(int(datetime.now().timestamp()))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/csv,application/csv,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=300, stream=True)
        
        if response.status_code == 200:
            # Check if it's actually CSV content
            content_type = response.headers.get('content-type', '')
            if 'text' in content_type or 'csv' in content_type:
                print("Download successful!")
                # Save to temp file and read
                temp_file = "data/temp_download.csv"
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                df = pd.read_csv(temp_file, encoding='utf-8', dtype=str, low_memory=False)
                os.remove(temp_file)
                return df
            else:
                print(f"Unexpected content type: {content_type}")
                return None
        else:
            print(f"Download failed with status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Download error: {e}")
        return None


def process_csv_from_file(filepath):
    """Process a manually uploaded CSV file."""
    print(f"Processing file: {filepath}")
    return pd.read_csv(filepath, encoding='latin-1', dtype=str, low_memory=False)


def filter_and_process(df, valid_countries, naics_desc, classification_desc):
    """Filter to international countries and process data."""
    print(f"Starting with {len(df)} records")
    
    # Filter to only columns we need
    available_cols = [c for c in COLUMNS_TO_KEEP if c in df.columns]
    df = df[available_cols].copy()
    
    # Filter by PopCountry - only international (non-USA)
    if 'PopCountry' in df.columns:
        df['PopCountry'] = df['PopCountry'].astype(str).str.strip().str.upper()
        
        # Remove USA and empty
        df = df[~df['PopCountry'].isin(['USA', 'US', 'UNITED STATES', '', 'NAN'])]
        
        # Keep only countries in our valid list
        df = df[df['PopCountry'].isin(valid_countries)]
    
    print(f"After country filter: {len(df)} records")
    
    # Filter by date (2023-2025)
    if 'PostedDate' in df.columns:
        df['PostedDate'] = pd.to_datetime(df['PostedDate'], errors='coerce', utc=True)
        df = df[df['PostedDate'].notna()]
        df = df[(df['PostedDate'].dt.year >= 2023) & (df['PostedDate'].dt.year <= 2025)]
        df['PostedDate'] = df['PostedDate'].dt.tz_localize(None)
    
    print(f"After date filter: {len(df)} records")
    
    # Convert country codes to full names
    if 'PopCountry' in df.columns:
        df['PopCountry'] = df['PopCountry'].apply(
            lambda x: COUNTRY_NAMES.get(x, x)
        )
    
    # Convert NAICS codes to descriptions
    if 'NaicsCode' in df.columns:
        df['NaicsCode'] = df['NaicsCode'].astype(str).str.strip()
        df['NaicsCode'] = df['NaicsCode'].apply(
            lambda x: naics_desc.get(x, x) if pd.notna(x) and x != 'nan' else ''
        )
    
    # Convert Classification codes to descriptions
    if 'ClassificationCode' in df.columns:
        df['ClassificationCode'] = df['ClassificationCode'].astype(str).str.strip()
        df['ClassificationCode'] = df['ClassificationCode'].apply(
            lambda x: classification_desc.get(x, x) if pd.notna(x) and x != 'nan' else ''
        )
    
    # Rename columns
    df = df.rename(columns=COLUMN_RENAME)
    
    # Remove duplicates based on Notice ID
    if 'Notice ID' in df.columns:
        df = df.drop_duplicates(subset=['Notice ID'], keep='last')
    
    print(f"Final record count: {len(df)}")
    
    return df


def main():
    """Main processing function."""
    print(f"=== SAM.gov Data Processor ===")
    print(f"Run time: {datetime.now()}")
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Load reference data
    valid_countries = load_all_valid_countries()
    print(f"Loaded {len(valid_countries)} valid country codes")
    
    naics_desc = load_naics_descriptions()
    print(f"Loaded {len(naics_desc)} NAICS descriptions")
    
    classification_desc = load_classification_descriptions()
    print(f"Loaded {len(classification_desc)} Classification descriptions")
    
    # Try to download from SAM.gov
    df = download_sam_csv()
    
    # If download failed, check for manual upload
    if df is None:
        manual_file = "data/manual_upload.csv"
        if os.path.exists(manual_file):
            print("Using manually uploaded file...")
            df = process_csv_from_file(manual_file)
        else:
            print("ERROR: Could not download from SAM.gov and no manual file found.")
            print("Please download the CSV manually from:")
            print("https://sam.gov/data-services/Contract%20Opportunities/datagov?privacy=Public")
            print("Save it as: data/manual_upload.csv")
            sys.exit(1)
    
    # Process the data
    df = filter_and_process(df, valid_countries, naics_desc, classification_desc)
    
    # Save processed data
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} records to {OUTPUT_FILE}")
    
    print("=== Processing Complete ===")


if __name__ == "__main__":
    main()
