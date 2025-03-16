import streamlit as st
import pandas as pd
import io
import numpy as np
from scipy.optimize import linprog
import altair as alt
import datetime

# Helper function for formatting numbers with Indonesian style (comma for decimal separator, dot for thousands)
def format_id(value, precision=2):
    """
    Format number with Indonesian number convention:
    - Comma (,) as decimal separator
    - Dot (.) as thousand separator
    
    Args:
        value: The number to format
        precision: Number of decimal places
        
    Returns:
        String with formatted number
    """
    if not isinstance(value, (int, float)):
        return value
    
    # Format to specified precision and get parts
    formatted = f"{value:.{precision}f}"
    parts = formatted.split('.')
    
    # Handle the integer part with thousand separators
    integer_part = parts[0]
    formatted_integer = ""
    
    # Add thousand separators
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            formatted_integer = '.' + formatted_integer
        formatted_integer = digit + formatted_integer
    
    # Add decimal part with comma as separator
    if len(parts) > 1 and precision > 0:
        return formatted_integer + ',' + parts[1]
    else:
        return formatted_integer

# App configuration
st.set_page_config(
    page_title="Aplikasi Perhitungan Ransum Ruminansia",
    page_icon="🐄",
    layout="wide"
)

# Hide default Streamlit elements
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Title and header with emojis for better visual appeal
st.title("🐄 Aplikasi Perhitungan Ransum Ruminansia 🐐")
st.subheader("✨ Solusi Nutrisi untuk Sapi, Kambing, dan Domba 🐑")
st.markdown("""
<div style="text-align: center; font-size: 16px; color: #555;">
    🌾 **Optimalkan pakan ternak Anda dengan mudah dan efisien!** 🌟
</div>
""", unsafe_allow_html=True)

# Function to load feed data from CSV
@st.cache_data(ttl=3600)
def load_feed_data(animal_type):
    """Load feed data from CSV based on animal type"""
    try:
        df = pd.read_csv("tabeldatapakan.csv")
        return df[df['Jenis Hewan'] == animal_type].reset_index(drop=True)
    except Exception as e:
        st.error(f"Error loading feed data: {e}")
        # Return default feed data if CSV file is missing
        default_data = {
            "Nama Pakan": ["Rumput Gajah", "Jerami Padi", "Bungkil Kedelai", "Dedak Padi", "Jagung Giling"],
            "Jenis Hewan": [animal_type] * 5,
            "Kategori": ["Hijauan", "Hijauan", "Konsentrat", "Konsentrat", "Konsentrat"],
            "Protein (%)": [10.2, 4.5, 42.0, 12.5, 9.0], 
            "TDN (%)": [55.0, 43.0, 75.0, 65.0, 78.0],
            "Ca (%)": [0.5, 0.4, 0.3, 0.1, 0.1],
            "P (%)": [0.3, 0.2, 0.6, 0.5, 0.3],
            "Mg (%)": [0.2, 0.1, 0.3, 0.4, 0.2],
            "Fe (ppm)": [250, 200, 120, 300, 50],
            "Cu (ppm)": [10, 5, 15, 20, 8],
            "Zn (ppm)": [40, 30, 50, 70, 25],
            "Harga (Rp/kg)": [1000, 800, 8000, 3500, 5000]
        }
        return pd.DataFrame(default_data)

# Function to load mineral data from CSV
@st.cache_data(ttl=3600)
def load_mineral_data():
    """Load mineral supplement data from CSV"""
    try:
        return pd.read_csv("tabeldatamineral.csv")
    except Exception as e:
        st.error(f"Error loading mineral data: {e}")
        # Return default mineral data if CSV file is missing
        default_data = {
            "Nama Pakan": ["Kapur (CaCO3)", "Tepung Tulang", "Mineral Mix", "Garam Dapur", "Premix"],
            "Protein (%)": [0, 0, 0, 0, 0],
            "TDN (%)": [0, 0, 0, 0, 0],
            "Ca (%)": [38.0, 24.0, 16.0, 0.1, 5.0],
            "P (%)": [0.1, 12.0, 8.0, 0, 2.0],
            "Mg (%)": [0.5, 0.7, 2.5, 0.1, 1.0],
            "Fe (ppm)": [100, 500, 2000, 50, 4000],
            "Cu (ppm)": [0, 20, 1500, 5, 2000],
            "Zn (ppm)": [0, 50, 1800, 10, 5000],
            "Harga (Rp/kg)": [2500, 5000, 15000, 8000, 25000]
        }
        return pd.DataFrame(default_data)

# Calculate nutrition content from feed mix
def calculate_nutrition_content(feed_data, feed_amounts, jumlah_ternak=1):
    """Calculate nutritional content of combined feed for all animals"""
    total_amount = sum(feed_amounts.values())
    
    if total_amount <= 0:
        return None, None, None, None, None, None, None, None, None
        
    total_protein = sum(feed_amounts[feed] * feed_data[feed]['protein'] for feed in feed_amounts)
    total_tdn = sum(feed_amounts[feed] * feed_data[feed]['tdn'] for feed in feed_amounts)
    total_cost = sum(feed_amounts[feed] * feed_data[feed]['harga'] for feed in feed_amounts)
    
    # Add mineral calculations
    total_ca = sum(feed_amounts[feed] * feed_data[feed].get('ca', 0) for feed in feed_amounts)
    total_p = sum(feed_amounts[feed] * feed_data[feed].get('p', 0) for feed in feed_amounts)
    total_mg = sum(feed_amounts[feed] * feed_data[feed].get('mg', 0) for feed in feed_amounts)
    
    # Calculate percentages in the mix
    avg_protein = total_protein / total_amount if total_amount > 0 else 0
    avg_tdn = total_tdn / total_amount if total_amount > 0 else 0
    avg_ca = total_ca / total_amount if total_amount > 0 else 0
    avg_p = total_p / total_amount if total_amount > 0 else 0
    avg_mg = total_mg / total_amount if total_amount > 0 else 0
    
    # Total costs and amount for all animals
    total_cost_all = total_cost * jumlah_ternak
    total_amount_all = total_amount * jumlah_ternak
    
    return avg_protein, avg_tdn, avg_ca, avg_p, avg_mg, total_cost, total_amount, total_cost_all, total_amount_all

# Save formula function
def save_formula(name, selected_feeds, feed_amounts, animal_type, age_category):
    """Save feed formula"""
    if 'saved_formulas' not in st.session_state:
        st.session_state.saved_formulas = {}
    
    st.session_state.saved_formulas[name] = {
        'feeds': selected_feeds,
        'amounts': feed_amounts,
        'animal_type': animal_type,
        'age_category': age_category,
        'timestamp': pd.Timestamp.now()
    }
    return True

# Load nutrition requirements
@st.cache_data(ttl=3600)
def load_nutrition_requirements():
    """Load nutrition requirements for different animal types and life stages"""
    try:
        return pd.read_csv("kebutuhannutrisi.csv")
    except Exception as e:
        # If CSV doesn't exist, return the hardcoded requirements
        return default_nutrition_requirements()

def default_nutrition_requirements():
    """Return default nutrition requirements if CSV doesn't exist"""
    return {
        "Sapi Potong": {
            "Pedet (<6 bulan)": {
                "Protein (%)": 18.0, "TDN (%)": 70.0,
                "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Muda (6-12 bulan)": {
                "Protein (%)": 12.5, "TDN (%)": 65.0,
                "Ca (%)": 0.55, "P (%)": 0.35, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dewasa (>12 bulan)": {
                "Protein (%)": 10.5, "TDN (%)": 60.0,
                "Ca (%)": 0.35, "P (%)": 0.25, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Bunting": {
                "Protein (%)": 11.0, "TDN (%)": 65.0,
                "Ca (%)": 0.45, "P (%)": 0.30, "Mg (%)": 0.12,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Penggemukan": {
                "Protein (%)": 14.0, "TDN (%)": 70.0,
                "Ca (%)": 0.50, "P (%)": 0.30, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            }
        },
        "Sapi Perah": {
            "Pedet (<6 bulan)": {
                "Protein (%)": 18.0, "TDN (%)": 72.0,
                "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dara (6-12 bulan)": {
                "Protein (%)": 15.0, "TDN (%)": 65.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dara Bunting": {
                "Protein (%)": 12.0, "TDN (%)": 65.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.16,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Laktasi (Produksi Rendah)": {
                "Protein (%)": 14.0, "TDN (%)": 65.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.20,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Laktasi (Produksi Tinggi)": {
                "Protein (%)": 16.0, "TDN (%)": 75.0,
                "Ca (%)": 0.80, "P (%)": 0.50, "Mg (%)": 0.25,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Kering": {
                "Protein (%)": 12.0, "TDN (%)": 60.0,
                "Ca (%)": 0.45, "P (%)": 0.35, "Mg (%)": 0.16,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            }
        },
        "Kambing Potong": {
            "Anak (<6 bulan)": {
                "Protein (%)": 16.0, "TDN (%)": 68.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Muda (6-12 bulan)": {
                "Protein (%)": 14.0, "TDN (%)": 65.0,
                "Ca (%)": 0.45, "P (%)": 0.35, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dewasa (>12 bulan)": {
                "Protein (%)": 12.0, "TDN (%)": 60.0,
                "Ca (%)": 0.35, "P (%)": 0.25, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 40
            },
            "Bunting": {
                "Protein (%)": 14.0, "TDN (%)": 65.0,
                "Ca (%)": 0.50, "P (%)": 0.35, "Mg (%)": 0.12,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Penggemukan": {
                "Protein (%)": 16.0, "TDN (%)": 70.0,
                "Ca (%)": 0.50, "P (%)": 0.30, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 10, "Zn (ppm)": 40
            }
        },
        "Kambing Perah": {
            "Anak (<6 bulan)": {
                "Protein (%)": 18.0, "TDN (%)": 70.0,
                "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.10,
                "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dara (6-12 bulan)": {
                "Protein (%)": 14.0, "TDN (%)": 65.0,
                "Ca (%)": 0.55, "P (%)": 0.40, "Mg (%)": 0.10,
                "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dara Bunting": {
                "Protein (%)": 12.0, "TDN (%)": 65.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.16,
                "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Laktasi (Produksi Rendah)": {
                "Protein (%)": 16.0, "TDN (%)": 65.0,
                "Ca (%)": 0.75, "P (%)": 0.45, "Mg (%)": 0.20,
                "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Laktasi (Produksi Tinggi)": {
                "Protein (%)": 18.0, "TDN (%)": 75.0,
                "Ca (%)": 0.90, "P (%)": 0.55, "Mg (%)": 0.25,
                "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Kering": {
                "Protein (%)": 12.0, "TDN (%)": 60.0,
                "Ca (%)": 0.45, "P (%)": 0.35, "Mg (%)": 0.16,
                "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
            }
        },
        "Domba Potong": {
            "Anak (<6 bulan)": {
                "Protein (%)": 16.0, "TDN (%)": 68.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Muda (6-12 bulan)": {
                "Protein (%)": 14.0, "TDN (%)": 65.0,
                "Ca (%)": 0.45, "P (%)": 0.35, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Dewasa (>12 bulan)": {
                "Protein (%)": 12.0, "TDN (%)": 60.0,
                "Ca (%)": 0.35, "P (%)": 0.25, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Bunting": {
                "Protein (%)": 14.0, "TDN (%)": 65.0,
                "Ca (%)": 0.50, "P (%)": 0.35, "Mg (%)": 0.12,
                "Fe (ppm)": 50, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Penggemukan": {
                "Protein (%)": 16.0, "TDN (%)": 70.0,
                "Ca (%)": 0.50, "P (%)": 0.30, "Mg (%)": 0.10,
                "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 35
            }
        },
        "Domba Perah": {
            "Anak (<6 bulan)": {
                "Protein (%)": 18.0, "TDN (%)": 70.0,
                "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.10,
                "Fe (ppm)": 45, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Dara (6-12 bulan)": {
                "Protein (%)": 14.0, "TDN (%)": 65.0,
                "Ca (%)": 0.55, "P (%)": 0.40, "Mg (%)": 0.10,
                "Fe (ppm)": 45, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Dara Bunting": {
                "Protein (%)": 12.0, "TDN (%)": 65.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.16,
                "Fe (ppm)": 45, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Laktasi (Produksi Rendah)": {
                "Protein (%)": 16.0, "TDN (%)": 65.0,
                "Ca (%)": 0.75, "P (%)": 0.45, "Mg (%)": 0.20,
                "Fe (ppm)": 45, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Laktasi (Produksi Tinggi)": {
                "Protein (%)": 18.0, "TDN (%)": 75.0,
                "Ca (%)": 0.90, "P (%)": 0.55, "Mg (%)": 0.25,
                "Fe (ppm)": 45, "Cu (ppm)": 7, "Zn (ppm)": 35
            },
            "Kering": {
                "Protein (%)": 12.0, "TDN (%)": 60.0,
                "Ca (%)": 0.45, "P (%)": 0.35, "Mg (%)": 0.16,
                "Fe (ppm)": 45, "Cu (ppm)": 7, "Zn (ppm)": 35
            }
        }
    }
# Function to get nutrition requirement for specific animal and category
def get_nutrition_requirement(jenis_hewan, kategori_umur, nutrition_data):
    """Get nutrition requirements for specific animal type and age category"""
    if isinstance(nutrition_data, pd.DataFrame):
        filtered = nutrition_data[(nutrition_data['Jenis Hewan'] == jenis_hewan) & 
                                 (nutrition_data['Kategori Umur'] == kategori_umur)]
        if not filtered.empty:
            return filtered.iloc[0].to_dict()
    else:  # Dictionary format
        return nutrition_data.get(jenis_hewan, {}).get(kategori_umur, {})
    
    # Return default values if nothing found
    return {
        "Protein (%)": 12.0, "TDN (%)": 60.0,
        "Ca (%)": 0.40, "P (%)": 0.25, "Mg (%)": 0.10,
        "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 35
    }

# Load anti-nutrient data
@st.cache_data(ttl=3600)
def load_antinutrient_data():
    """Load anti-nutrient data from CSV"""
    try:
        return pd.read_csv("antinutrisi.csv")
    except Exception as e:
        # Default anti-nutrient data
        return {
            "Daun Kaliandra": {"Tanin": 2.8, "Saponin": 0.9},
            "Daun Lamtoro": {"Mimosin": 1.2, "Tanin": 0.6},
            "Bungkil Biji Kapok": {"Gosipol": 150, "Tanin": 0.8},
            "Daun Singkong": {"HCN": 30, "Tanin": 0.5},
            "Kulit Singkong": {"HCN": 45},
            "Ampas Tahu": {"Aflatoksin": 5},
            "Dedak Padi": {"Aflatoksin": 10, "Oksalat": 0.8},
            "Kulit Kakao": {"Tanin": 3.2, "Saponin": 1.2}
        }

# Function to validate uploaded data
def validasi_data_pakan_extended(df):
    """Validate feed data with comprehensive checks"""
    # Check required columns
    required_cols = ['Nama Pakan', 'Protein (%)', 'TDN (%)', 'Harga (Rp/kg)']
    
    # Add missing columns with default values if needed
    for col in required_cols:
        if col not in df.columns:
            if col == 'Nama Pakan':
                df[col] = [f"Pakan {i+1}" for i in range(len(df))]
            else:
                df[col] = 0.0
    
    # Check data types
    try:
        df['Protein (%)'] = df['Protein (%)'].astype(float)
        df['TDN (%)'] = df['TDN (%)'].astype(float)
        df['Harga (Rp/kg)'] = df['Harga (Rp/kg)'].astype(float)
        
        # Check mineral columns if present
        mineral_cols = ['Ca (%)', 'P (%)', 'Mg (%)', 'Fe (ppm)', 'Cu (ppm)', 'Zn (ppm)']
        for col in mineral_cols:
            if col in df.columns:
                df[col] = df[col].astype(float)
            else:
                df[col] = 0.0  # Add missing columns with default values
    except ValueError:
        return False, "Nilai numerik tidak valid"
    
    # Check value ranges
    if (df['Protein (%)'] > 100).any():
        return False, "Protein tidak boleh > 100%"
    if (df['TDN (%)'] > 100).any():
        return False, "TDN tidak boleh > 100%"
    if (df['Harga (Rp/kg)'] < 0).any():
        return False, "Harga tidak boleh negatif"
    if df['Nama Pakan'].duplicated().any():
        return False, "Terdapat duplikasi nama pakan"
    
    return True, df

# Main interface

# Animal type selection
jenis_hewan = st.selectbox(
    "Pilih jenis hewan:", 
    ["Sapi Potong", "Sapi Perah", "Kambing Potong", "Kambing Perah", "Domba Potong", "Domba Perah"]
)

# Add number of animals input
col1, col2 = st.columns(2)
with col1:
    jumlah_ternak = st.number_input("Jumlah Ternak", min_value=1, value=1)

with col2:
    jenis_kelamin = st.selectbox(
        "Pilih jenis kelamin:",
        ["Jantan", "Betina"]
    )

# Bobot badan dan pertambahan bobot badan
col1, col2 = st.columns(2)
with col1:
    bobot_badan = st.number_input("Bobot Badan (kg)", min_value=0.0, value=250.0, step=10.0)

with col2:
    if "Potong" in jenis_hewan:
        pertambahan_bobot = st.number_input("Target Pertambahan Bobot Badan (kg/hari)", 
                                          min_value=0.0, value=0.5, step=0.1)
    elif "Perah" in jenis_hewan and jenis_kelamin == "Betina":
        produksi_susu = st.number_input("Produksi Susu (liter/hari)", min_value=0.0, value=0.0, step=0.5)

# Load nutrition requirements
nutrition_requirements = load_nutrition_requirements()

# Load anti-nutrient data
antinutrient_data = load_antinutrient_data()

# Get animal categories based on selected animal type
if isinstance(nutrition_requirements, pd.DataFrame):
    kategori_list = nutrition_requirements[nutrition_requirements['Jenis Hewan'] == jenis_hewan]['Kategori Umur'].unique()
else:
    kategori_list = list(nutrition_requirements.get(jenis_hewan, {}).keys())

# Age/production phase selection
kategori_umur = st.selectbox(
    "Pilih kategori umur/fase produksi:",
    kategori_list
)

# Get nutrition requirement for the selected animal type and age category
nutrient_req = get_nutrition_requirement(jenis_hewan, kategori_umur, nutrition_requirements)

# Define anti-nutrient information dictionary for reference
antinutrient_info = {
    "Tanin": {
        "Deskripsi": "Senyawa yang mengikat protein dan mengurangi kecernaan",
        "Batas Aman": "< 2% dari total bahan kering"
    },
    "Saponin": {
        "Deskripsi": "Dapat menyebabkan bloat (kembung) pada ruminansia",
        "Batas Aman": "< 1% dari total bahan kering"
    },
    "Mimosin": {
        "Deskripsi": "Menghambat sintesis protein dan dapat menyebabkan kerontokan rambut",
        "Batas Aman": "< 0.5% dari total bahan kering"
    },
    "Gosipol": {
        "Deskripsi": "Dapat mengganggu reproduksi terutama pada jantan",
        "Batas Aman": "< 100 ppm dari total bahan kering"
    },
    "HCN": {
        "Deskripsi": "Senyawa beracun yang dapat menyebabkan gagal napas",
        "Batas Aman": "< 20 ppm dari total bahan kering"
    },
    "Aflatoksin": {
        "Deskripsi": "Toksin jamur yang dapat merusak hati",
        "Batas Aman": "< 5 ppb dari total bahan kering"
    },
    "Oksalat": {
        "Deskripsi": "Mengikat kalsium dan dapat menyebabkan batu ginjal",
        "Batas Aman": "< 0.5% dari total bahan kering"
    }
}

# Get animal type base (Sapi, Kambing, Domba) for data loading
def get_base_animal_type(jenis_hewan):
    if "Sapi" in jenis_hewan:
        return "Sapi"
    elif "Kambing" in jenis_hewan:
        return "Kambing"
    elif "Domba" in jenis_hewan:
        return "Domba"
    return "Sapi"  # Default

# Load feed data based on animal type
animal_base_type = get_base_animal_type(jenis_hewan)
df_pakan = load_feed_data(animal_base_type)

# Upload custom feed data (optional)
st.subheader("Upload Data Pakan (Opsional)")

with st.expander("Lihat format data yang diharapkan"):
    st.write("""
    ## Format Data yang Diharapkan
    
    File CSV atau Excel harus memiliki kolom-kolom berikut:
    - `Nama Pakan` (teks): Nama bahan pakan
    - `Protein (%)` (numerik): Kandungan protein
    - `TDN (%)` (numerik): Kandungan TDN (Total Digestible Nutrient)
    - `Harga (Rp/kg)` (numerik): Harga per kilogram
    
    Kolom tambahan yang direkomendasikan:
    - `Ca (%)`: Kandungan kalsium
    - `P (%)`: Kandungan fosfor
    - `Mg (%)`: Kandungan magnesium
    - `Fe (ppm)`: Kandungan zat besi
    - `Cu (ppm)`: Kandungan tembaga
    - `Zn (ppm)`: Kandungan seng
    """)

uploaded_file = st.file_uploader("Upload file CSV atau Excel (XLS/XLSX) untuk data pakan Anda (perhatikan format file)", 
                               type=["csv", "xls", "xlsx"])

# Process uploaded file if provided
use_default_data = True
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            uploaded_df = pd.read_csv(uploaded_file)
        else:
            uploaded_df = pd.read_excel(uploaded_file)
        
        valid, result = validasi_data_pakan_extended(uploaded_df)
        
        if valid:
            df_pakan = result
            use_default_data = False
            st.success("File berhasil diupload dan divalidasi!")
        else:
            st.error(f"Data tidak valid: {result}")
            st.warning("Menggunakan data default sebagai pengganti.")
    except Exception as e:
        st.error(f"Error saat membaca file: {e}")
        st.warning("Menggunakan data default sebagai pengganti.")

# Show data source information
if use_default_data:
    st.info(f"📋 Menggunakan data default untuk pakan **{animal_base_type}**")
else:
    st.info("📤 Menggunakan data pakan dari file yang diupload")

# Display feed data table
st.subheader("Tabel Data Pakan")

# Check if table exists and has data
if df_pakan is None or df_pakan.empty:
    st.warning("⚠️ Tabel Data Pakan tidak tersedia atau kosong.")
    
    st.info("Anda dapat membuat tabel data pakan baru di bawah ini.")
    
    # Create a form to add new feed data
    with st.form("create_feed_data"):
        st.subheader("Buat Tabel Data Pakan Baru")
        
        col1, col2 = st.columns(2)
        with col1:
            use_default_example = st.checkbox("Gunakan contoh data default", value=True)
        with col2:
            num_feeds = st.number_input("Jumlah bahan pakan yang akan ditambahkan:", 
                                      min_value=1, max_value=50, value=10, disabled=use_default_example)
        
        submitted = st.form_submit_button("Buat Tabel")
        
        if submitted:
            if use_default_example:
                # Create sample data
                sample_data = {
                    "Nama Pakan": ["Rumput Gajah", "Jerami Padi", "Bungkil Kedelai", "Dedak Padi", "Jagung Giling",
                                  "Lamtoro", "Gamal", "Ampas Tahu", "Onggok", "Molases"],
                    "Jenis Hewan": [animal_base_type] * 10,
                    "Kategori": ["Hijauan", "Hijauan", "Konsentrat", "Konsentrat", "Konsentrat", 
                                "Hijauan", "Hijauan", "Konsentrat", "Konsentrat", "Konsentrat"],
                    "Protein (%)": [10.2, 4.5, 42.0, 12.5, 9.0, 22.0, 20.0, 20.0, 2.5, 4.0], 
                    "TDN (%)": [55.0, 43.0, 75.0, 65.0, 78.0, 65.0, 62.0, 70.0, 76.0, 80.0],
                    "Ca (%)": [0.5, 0.4, 0.3, 0.1, 0.1, 1.2, 1.0, 0.3, 0.2, 0.8],
                    "P (%)": [0.3, 0.2, 0.6, 0.5, 0.3, 0.3, 0.2, 0.2, 0.1, 0.1],
                    "Mg (%)": [0.2, 0.1, 0.3, 0.4, 0.2, 0.4, 0.3, 0.1, 0.1, 0.3],
                    "Fe (ppm)": [250, 200, 120, 300, 50, 320, 290, 150, 120, 100],
                    "Cu (ppm)": [10, 5, 15, 20, 8, 15, 12, 10, 5, 15],
                    "Zn (ppm)": [40, 30, 50, 70, 25, 42, 40, 40, 15, 20],
                    "Harga (Rp/kg)": [1000, 800, 8000, 3500, 5000, 1500, 1400, 2500, 2000, 3000]
                }
                df_pakan = pd.DataFrame(sample_data)
                st.success("✅ Tabel data pakan contoh berhasil dibuat!")
            else:
                # Create empty dataframe with specified rows
                empty_data = {
                    "Nama Pakan": [f"Pakan {i+1}" for i in range(num_feeds)],
                    "Jenis Hewan": [animal_base_type] * num_feeds,
                    "Kategori": [""] * num_feeds,
                    "Protein (%)": [0.0] * num_feeds,
                    "TDN (%)": [0.0] * num_feeds,
                    "Ca (%)": [0.0] * num_feeds,
                    "P (%)": [0.0] * num_feeds,
                    "Mg (%)": [0.0] * num_feeds,
                    "Fe (ppm)": [0] * num_feeds,
                    "Cu (ppm)": [0] * num_feeds,
                    "Zn (ppm)": [0] * num_feeds,
                    "Harga (Rp/kg)": [0] * num_feeds
                }
                df_pakan = pd.DataFrame(empty_data)
                st.success("✅ Tabel data pakan kosong berhasil dibuat! Silakan isi data di bawah.")
            
            # Make this dataframe available for the rest of the app
            st.session_state.df_pakan = df_pakan
    
    # If the dataframe was created in this session, use it
    if 'df_pakan' in st.session_state:
        df_pakan = st.session_state.df_pakan
        
        # Display editable feed data
        edited_df = st.data_editor(
            df_pakan,
            column_config={
                "Kategori": st.column_config.SelectboxColumn(
                    "Kategori",
                    help="Kategori pakan",
                    options=["Hijauan", "Konsentrat"]
                ),
                "Protein (%)": st.column_config.NumberColumn(
                    "Protein (%)",
                    help="Kandungan protein pakan",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    format="%.1f"
                ),
                "TDN (%)": st.column_config.NumberColumn(
                    "TDN (%)",
                    help="Total Digestible Nutrient",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    format="%.1f"
                ),
                "Harga (Rp/kg)": st.column_config.NumberColumn(
                    "Harga (Rp/kg)",
                    help="Harga per kilogram",
                    min_value=0,
                    step=100,
                    format="%d"
                )
            },
            hide_index=True,
            num_rows="dynamic"
        )
        
        # Update the dataframe with edited values
        if edited_df is not None:
            st.session_state.df_pakan = edited_df
            df_pakan = edited_df
        
        # Option to save the dataframe to CSV
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Simpan Tabel Data ke CSV"):
                try:
                    df_pakan.to_csv("tabeldatapakan.csv", index=False)
                    st.success("✅ Data berhasil disimpan ke tabeldatapakan.csv!")
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan data: {e}")
        
        with col2:
            if st.button("Simpan Tabel Data ke Excel"):
                try:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_pakan.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="Download Excel File",
                        data=output.getvalue(),
                        file_name="tabeldatapakan.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan data: {e}")
        
        st.info("💡 Klik pada sel untuk mengedit nilai. Jangan lupa menyimpan tabel setelah selesai mengedit.")
                
else:
    # Filter by category if using default data
    if use_default_data and 'Kategori' in df_pakan.columns:
        kategori_pakan = ["Semua"] + list(df_pakan['Kategori'].unique())
        selected_kategori = st.selectbox("Filter berdasarkan kategori:", kategori_pakan)
        
        if selected_kategori != "Semua":
            filtered_df = df_pakan[df_pakan['Kategori'] == selected_kategori]
        else:
            filtered_df = df_pakan
    else:
        filtered_df = df_pakan

    # Display editable feed data
    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "Harga (Rp/kg)": st.column_config.NumberColumn(
                "Harga (Rp/kg)",
                help="Anda dapat mengedit harga pakan",
                min_value=0,
                step=100,
                format="%d"
            )
        },
        hide_index=True,
        num_rows="fixed"
    )

    # Update prices in the main dataframe
    if edited_df is not None and not edited_df.empty:
        for i, row in edited_df.iterrows():
            if 'Nama Pakan' in row and row['Nama Pakan'] in df_pakan['Nama Pakan'].values:
                df_pakan.loc[df_pakan['Nama Pakan'] == row['Nama Pakan'], 'Harga (Rp/kg)'] = row['Harga (Rp/kg)']

    st.info("💡 Klik pada nilai harga untuk mengedit secara langsung. Perubahan akan otomatis tersimpan.")

    # Add button to save changes
    if st.button("Simpan Perubahan ke File"):
        try:
            df_pakan.to_csv("tabeldatapakan.csv", index=False)
            st.success("✅ Perubahan berhasil disimpan ke tabeldatapakan.csv!")
        except Exception as e:
            st.error(f"❌ Gagal menyimpan perubahan: {e}")

# Feed search functionality
st.subheader("Cari Bahan Pakan")
search_term = st.text_input("Masukkan kata kunci:")

if search_term:
    search_results = df_pakan[df_pakan['Nama Pakan'].str.lower().str.contains(search_term.lower())]
    
    if not search_results.empty:
        st.success(f"Ditemukan {len(search_results)} hasil pencarian")
        st.dataframe(search_results)
        
        # Show nutrition comparison visualization for search results
        if len(search_results) > 1 and len(search_results) <= 10:
            st.subheader("Perbandingan Nutrisi")
            
            chart_data = pd.melt(
                search_results[['Nama Pakan', 'Protein (%)', 'TDN (%)', 'Ca (%)', 'P (%)']],
                id_vars=['Nama Pakan'],
                var_name='Nutrisi',
                value_name='Nilai'
            )
            
            chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('Nama Pakan:N', sort='-y'),
                y=alt.Y('Nilai:Q'),
                color='Nutrisi:N',
                tooltip=['Nama Pakan', 'Nutrisi', 'Nilai']
            ).properties(
                title='Perbandingan Kandungan Nutrisi',
                width=600,
                height=400
            ).facet(
                column='Nutrisi:N'
            )
            
            st.altair_chart(chart)
    else:
        st.warning(f"Tidak ditemukan bahan pakan dengan kata kunci '{search_term}'")

# Template download options
if use_default_data:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template CSV"):
            csv = df_pakan.to_csv(index=False)
            st.download_button(
                label="Download CSV Template",
                data=csv,
                file_name=f"template_pakan_{jenis_hewan}.csv",
                mime="text/csv"
            )
    with col2:
        if st.button("Download Template Excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_pakan.to_excel(writer, index=False)
            st.download_button(
                label="Download Excel Template",
                data=output.getvalue(),
                file_name=f"template_pakan_{jenis_hewan}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Application modes
mode = st.sidebar.radio("Mode Aplikasi", ["Formulasi Manual", "Optimalisasi Otomatis", "Mineral Supplement"])

if mode == "Formulasi Manual":
    # Feed selection
    st.subheader("Pilih Kombinasi Bahan Pakan")
    selected_feeds = st.multiselect("Pilih bahan pakan:", df_pakan['Nama Pakan'].tolist())
    
    # Store feed data and amounts
    feed_amounts = {}
    feed_data = {}
    
    if selected_feeds:
        st.subheader("Input Jumlah Pakan (kg)")
        cols = st.columns(min(3, len(selected_feeds)))
        
        for i, feed_name in enumerate(selected_feeds):
            col_idx = i % 3
            with cols[col_idx]:
                feed_row = df_pakan[df_pakan['Nama Pakan'] == feed_name].iloc[0]
                feed_data[feed_name] = {
                    'protein': feed_row['Protein (%)'],
                    'tdn': feed_row['TDN (%)'],
                    'ca': feed_row['Ca (%)'] if 'Ca (%)' in feed_row else 0,
                    'p': feed_row['P (%)'] if 'P (%)' in feed_row else 0,
                    'mg': feed_row['Mg (%)'] if 'Mg (%)' in feed_row else 0,
                    'harga': feed_row['Harga (Rp/kg)']
                }
                st.write(f"**{feed_name}**")
                st.write(f"Protein: {feed_data[feed_name]['protein']}%")
                st.write(f"TDN: {feed_data[feed_name]['tdn']}%")
                st.write(f"Harga: Rp {feed_data[feed_name]['harga']}/kg")
                feed_amounts[feed_name] = st.number_input(
                    f"Jumlah {feed_name} (kg)",
                    min_value=0.0,
                    step=0.1,
                    key=f"amount_{feed_name}"
                )
    else:
        st.warning("Silakan pilih minimal satu bahan pakan.")
    
    # Show nutrient requirements
    nutrient_req = get_nutrition_requirement(jenis_hewan, kategori_umur, nutrition_requirements)
    
    st.subheader("Kebutuhan Nutrisi Berdasarkan Umur")
    st.info(f"""
    **{jenis_hewan} - {kategori_umur}**
    - Protein: {nutrient_req.get('Protein (%)', 0)}%
    - TDN: {nutrient_req.get('TDN (%)', 0)}%
    - Ca: {nutrient_req.get('Ca (%)', 0)}%
    - P: {nutrient_req.get('P (%)', 0)}%
    """)
    
    # Calculate ration
    if st.button("Hitung Ransum"):
        if not selected_feeds:
            st.error("Silakan pilih minimal satu bahan pakan.")
        else:
            total_amount = sum(feed_amounts.values())
            
            if total_amount <= 0:
                st.error("Total jumlah pakan harus lebih dari 0 kg.")
            else:
                avg_protein, avg_tdn, avg_ca, avg_p, avg_mg, total_cost, total_amount, total_cost_all, total_amount_all = calculate_nutrition_content(feed_data, feed_amounts, jumlah_ternak)
                
                required_protein = nutrient_req.get('Protein (%)', 0)
                required_tdn = nutrient_req.get('TDN (%)', 0)
                
                # Show results
                st.subheader("Hasil Perhitungan")
                
                # Feed composition table for single animal
                composition_data = {
                    'Bahan Pakan': list(feed_amounts.keys()),
                    'Jumlah (kg/ekor)': [feed_amounts[feed] for feed in feed_amounts],
                    'Protein (kg)': [feed_amounts[feed] * feed_data[feed]['protein'] / 100 for feed in feed_amounts],
                    'TDN (kg)': [feed_amounts[feed] * feed_data[feed]['tdn'] / 100 for feed in feed_amounts],
                    'Biaya (Rp/ekor)': [feed_amounts[feed] * feed_data[feed]['harga'] for feed in feed_amounts]
                }
                
                df_composition = pd.DataFrame(composition_data)
                df_composition.loc['Total per ekor'] = [
                    'Total per ekor',
                    total_amount,
                    sum(composition_data['Protein (kg)']),
                    sum(composition_data['TDN (kg)']),
                    total_cost
                ]
                
                st.dataframe(df_composition)
                
                # Show total for all animals
                if jumlah_ternak > 1:
                    st.subheader(f"Total Kebutuhan untuk {jumlah_ternak} Ekor")
                    
                    total_composition_data = {
                        'Bahan Pakan': list(feed_amounts.keys()),
                        'Jumlah Total (kg)': [feed_amounts[feed] * jumlah_ternak for feed in feed_amounts],
                        'Biaya Total (Rp)': [feed_amounts[feed] * feed_data[feed]['harga'] * jumlah_ternak for feed in feed_amounts]
                    }
                    
                    df_total_composition = pd.DataFrame(total_composition_data)
                    df_total_composition.loc['Total'] = [
                        'Total',
                        total_amount_all,
                        total_cost_all
                    ]
                    
                    st.dataframe(df_total_composition)
                    
                    # Cost analysis section
                    st.subheader("Analisis Biaya")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Biaya Pakan per Ekor/Hari", f"Rp {total_cost:,.0f}")
                    with col2:
                        st.metric("Biaya Pakan per Bulan/Ekor", f"Rp {total_cost * 30:,.0f}")
                    with col3:
                        st.metric("Biaya Pakan Total per Bulan", f"Rp {total_cost_all * 30:,.0f}")
                
                # Nutrition summary
                st.subheader("Kandungan Nutrisi Ransum")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        label="Protein Ransum", 
                        value=f"{avg_protein:.2f}%",
                        delta=f"{avg_protein - required_protein:.2f}%" 
                    )
                    
                    if avg_protein < required_protein:
                        st.warning(f"⚠️ Protein ransum kurang dari kebutuhan ({required_protein}%)")
                    else:
                        st.success(f"✅ Protein ransum memenuhi kebutuhan ({required_protein}%)")
                
                with col2:
                    st.metric(
                        label="TDN Ransum", 
                        value=f"{avg_tdn:.2f}%",
                        delta=f"{avg_tdn - required_tdn:.2f}%" 
                    )
                    
                    if avg_tdn < required_tdn:
                        st.warning(f"⚠️ TDN ransum kurang dari kebutuhan ({required_tdn}%)")
                    else:
                        st.success(f"✅ TDN ransum memenuhi kebutuhan ({required_tdn}%)")
                
                # Additional recommendations based on gender and livestock type
                st.subheader("Rekomendasi Khusus")
                
                # Gender-specific recommendations
                if jenis_kelamin == "Jantan":
                    st.write("### Rekomendasi untuk Ternak Jantan")
                    st.write("- Pastikan tingkat energi cukup untuk pertumbuhan dan aktivitas fisik")
                    
                    if "Potong" in jenis_hewan:
                        st.write("- Fokus pada ransum dengan protein yang cukup untuk pembentukan massa otot")
                        st.write("- Pertimbangkan penambahan suplemen untuk meningkatkan kecepatan pertumbuhan")
                        
                        if pertambahan_bobot > 0.8 and "Sapi" in jenis_hewan:
                            st.info("ℹ️ Untuk mencapai target pertambahan bobot >0.8 kg/hari, pastikan ransum mengandung minimal 12-14% protein dan 65-70% TDN")
                        elif pertambahan_bobot > 0.1 and ("Kambing" in jenis_hewan or "Domba" in jenis_hewan):
                            st.info("ℹ️ Untuk mencapai target pertambahan bobot >0.1 kg/hari pada kambing/domba, pastikan ransum mengandung minimal 14-16% protein dan 65-70% TDN") 
                    
                    # Check for potential gosipol issues
                    gosipol_feeds = ["Bungkil Biji Kapas", "Biji Kapuk"]
                    has_gosipol = any(feed in gosipol_feeds for feed in selected_feeds)
                    
                    if has_gosipol:
                        st.error("⚠️ Terdeteksi bahan pakan yang mengandung gosipol. Pada jantan, gosipol dapat menyebabkan gangguan reproduksi. Pertimbangkan untuk mengurangi atau mengganti dengan bahan lain.")
                
                elif jenis_kelamin == "Betina":
                    st.write("### Rekomendasi untuk Ternak Betina")
                    
                    if "Perah" in jenis_hewan:
                        st.write("- Pastikan tingkat kalsium dan fosfor cukup untuk produksi susu")
                        st.write("- Perhatikan rasio Ca:P idealnya 1,5:1 hingga 2:1")
                        
                        if 'produksi_susu' in locals() and produksi_susu > 0:
                            if "Sapi" in jenis_hewan:
                                extra_protein = produksi_susu * 90  # g protein per liter
                                extra_energy = produksi_susu * 5.5   # MJ NEL per liter
                                
                                st.info(f"ℹ️ Untuk produksi susu {produksi_susu} liter/hari, Anda perlu menambah sekitar {extra_protein:.0f}g protein kasar dan {extra_energy:.1f} MJ NEL per hari")
                            elif "Kambing" in jenis_hewan or "Domba" in jenis_hewan:
                                extra_protein = produksi_susu * 60  # g protein per liter
                                extra_energy = produksi_susu * 4.5   # MJ NEL per liter
                                
                                st.info(f"ℹ️ Untuk produksi susu {produksi_susu} liter/hari, Anda perlu menambah sekitar {extra_protein:.0f}g protein kasar dan {extra_energy:.1f} MJ NEL per hari")
                    
                    # Recommendations for gestating females
                    with st.expander("Untuk Betina Bunting"):
                        st.write("**Kebutuhan khusus untuk betina bunting:**")
                        st.write("- Trimester pertama: kebutuhan nutrisi relatif sama dengan pemeliharaan")
                        st.write("- Trimester kedua: tambahkan 10-15% protein dan 10% energi dari kebutuhan normal")
                        st.write("- Trimester ketiga: tambahkan 20-25% protein dan 15-20% energi dari kebutuhan normal")
                        st.write("- Pastikan kecukupan vitamin A, D, E dan mineral Ca, P, I, dan Se untuk perkembangan fetus")
                
                # Recommendations based on number of animals
                if jumlah_ternak > 10:
                    st.write("### Rekomendasi untuk Ternak dalam Jumlah Besar")
                    st.write("- Pertimbangkan pembelian bahan pakan dalam jumlah besar untuk efisiensi biaya")
                    st.write("- Pastikan memiliki tempat penyimpanan pakan yang memadai untuk mencegah kerusakan")
                    st.write("- Pertimbangkan penggunaan complete feed atau TMR (Total Mixed Ration) untuk konsistensi nutrisi")
                    st.write("- Lakukan kontrol kualitas pakan secara berkala")
                
                # Recommendations based on animal type and weight
                if "Sapi" in jenis_hewan:
                    konsumsi_bk = bobot_badan * (2.5 if "Perah" in jenis_hewan else 2.2) / 100  # 2.2-2.5% BB konsumsi BK
                    
                    st.write(f"### Rekomendasi untuk {jenis_hewan}")
                    st.write(f"- Estimasi konsumsi bahan kering per ekor: **{format_id(konsumsi_bk, 1)} kg BK/hari**")
                    st.write(f"- Total kebutuhan bahan kering untuk {jumlah_ternak} ekor: **{format_id(konsumsi_bk * jumlah_ternak, 1)} kg BK/hari**")
                    
                    # Periksa apakah jumlah pakan sudah cukup
                    if total_amount < konsumsi_bk * 0.9:
                        st.warning(f"⚠️ Jumlah pakan ({format_id(total_amount, 1)} kg) kurang dari estimasi kebutuhan bahan kering ({format_id(konsumsi_bk, 1)} kg). Pertimbangkan untuk menambah jumlah pakan.")
                    
                    # Hitung kebutuhan hijauan dan konsentrat ideal
                    hijauan_ideal = konsumsi_bk * (0.6 if "Potong" in jenis_hewan else 0.4)
                    konsentrat_ideal = konsumsi_bk - hijauan_ideal
                    
                    st.write(f"- Proporsi ideal hijauan:konsentrat = {int(hijauan_ideal/konsumsi_bk*100)}:{int(konsentrat_ideal/konsumsi_bk*100)}")
                    
                    # Hitung aktual proporsi hijauan vs konsentrat
                    if 'Kategori' in df_pakan.columns:
                        hijauan_aktual = sum(feed_amounts[feed] for feed in feed_amounts if 
                                         feed in df_pakan[df_pakan['Kategori'] == 'Hijauan']['Nama Pakan'].tolist())
                        konsentrat_aktual = sum(feed_amounts[feed] for feed in feed_amounts if 
                                            feed in df_pakan[df_pakan['Kategori'] == 'Konsentrat']['Nama Pakan'].tolist())
                        
                        st.write(f"- Proporsi aktual hijauan:konsentrat = {int(hijauan_aktual/total_amount*100 if total_amount > 0 else 0)}:{int(konsentrat_aktual/total_amount*100 if total_amount > 0 else 0)}")
                        
                        if hijauan_aktual < hijauan_ideal * 0.8:
                            st.warning("⚠️ Proporsi hijauan terlalu rendah. Untuk kesehatan rumen, tambahkan lebih banyak hijauan.")
                        elif konsentrat_aktual < konsentrat_ideal * 0.8:
                            st.warning("⚠️ Proporsi konsentrat terlalu rendah. Untuk mencapai target produksi, tambahkan lebih banyak konsentrat.")
                
                elif "Kambing" in jenis_hewan or "Domba" in jenis_hewan:
                    konsumsi_bk = bobot_badan * (3.0 if "Perah" in jenis_hewan else 2.5) / 100  # 2.5-3.0% BB konsumsi BK
                    
                    st.write(f"### Rekomendasi untuk {jenis_hewan}")
                    st.write(f"- Estimasi konsumsi bahan kering per ekor: **{konsumsi_bk:.1f} kg BK/hari**")
                    st.write(f"- Total kebutuhan bahan kering untuk {jumlah_ternak} ekor: **{konsumsi_bk * jumlah_ternak:.1f} kg BK/hari**")
                    
                    # Periksa apakah jumlah pakan sudah cukup
                    if total_amount < konsumsi_bk * 0.9:
                        st.warning(f"⚠️ Jumlah pakan ({total_amount:.1f} kg) kurang dari estimasi kebutuhan bahan kering ({konsumsi_bk:.1f} kg). Pertimbangkan untuk menambah jumlah pakan.")
                    
                    # Hitung kebutuhan hijauan dan konsentrat ideal
                    hijauan_ideal = konsumsi_bk * (0.65 if "Potong" in jenis_hewan else 0.5)
                    konsentrat_ideal = konsumsi_bk - hijauan_ideal
                    
                    st.write(f"- Proporsi ideal hijauan:konsentrat = {int(hijauan_ideal/konsumsi_bk*100)}:{int(konsentrat_ideal/konsumsi_bk*100)}")
                    
                    # Hitung aktual proporsi hijauan vs konsentrat
                    if 'Kategori' in df_pakan.columns:
                        hijauan_aktual = sum(feed_amounts[feed] for feed in feed_amounts if 
                                         feed in df_pakan[df_pakan['Kategori'] == 'Hijauan']['Nama Pakan'].tolist())
                        konsentrat_aktual = sum(feed_amounts[feed] for feed in feed_amounts if 
                                            feed in df_pakan[df_pakan['Kategori'] == 'Konsentrat']['Nama Pakan'].tolist())
                        
                        st.write(f"- Proporsi aktual hijauan:konsentrat = {int(hijauan_aktual/total_amount*100 if total_amount > 0 else 0)}:{int(konsentrat_aktual/total_amount*100 if total_amount > 0 else 0)}")
                        
                        if hijauan_aktual < hijauan_ideal * 0.8:
                            st.warning("⚠️ Proporsi hijauan terlalu rendah. Untuk kesehatan rumen, tambahkan lebih banyak hijauan.")
                        elif konsentrat_aktual < konsentrat_ideal * 0.8:
                            st.warning("⚠️ Proporsi konsentrat terlalu rendah. Untuk mencapai target produksi, tambahkan lebih banyak konsentrat.")
                
                # Seasonal recommendations
                current_month = datetime.datetime.now().month
                if 11 <= current_month <= 12 or 1 <= current_month <= 4:  # Musim hujan di Indonesia
                    st.write("### Rekomendasi Musiman (Musim Hujan)")
                    st.write("- Pastikan pakan disimpan dengan baik untuk mencegah kerusakan akibat kelembaban tinggi")
                    st.write("- Perhatikan risiko kontaminasi aflatoksin pada bahan pakan yang disimpan dalam kondisi lembab")
                    st.write("- Manfaatkan ketersediaan hijauan segar yang melimpah")
                    st.write("- Kurangi penggunaan hay dan silase")
                else:  # Musim kemarau
                    st.write("### Rekomendasi Musiman (Musim Kemarau)")
                    st.write("- Buat stok pakan hijauan (hay/silase) untuk mengantisipasi kelangkaan hijauan")
                    st.write("- Manfaatkan produk samping pertanian yang tersedia musiman")
                    st.write("- Tingkatkan proporsi konsentrat jika hijauan berkualitas sulit diperoleh")
                    st.write("- Pastikan tersedia air minum yang cukup untuk ternak")

elif mode == "Optimalisasi Otomatis":
    st.header("Optimalisasi Ransum")
    st.write("Mengoptimalkan komposisi pakan untuk memenuhi kebutuhan nutrisi dengan biaya minimal, termasuk mineral")
    
    # Load mineral data before using it
    mineral_df = load_mineral_data()

    # Pilih bahan pakan yang tersedia untuk optimasi
    available_feeds = st.multiselect(
        "Pilih bahan pakan yang tersedia:", 
        df_pakan['Nama Pakan'].tolist(), 
        default=df_pakan['Nama Pakan'].tolist()[:3],
        key="feed_selection"  # Add unique key
    )

    # Pilih mineral supplement yang tersedia
    available_minerals = st.multiselect(
        "Pilih mineral supplement yang tersedia:", 
        mineral_df['Nama Pakan'].tolist(), 
        default=mineral_df['Nama Pakan'].tolist()[:2],
        key="mineral_selection"  # Add unique key
    )

    # Gabungkan bahan pakan dan mineral supplement
    all_available_feeds = available_feeds + available_minerals

    # Batasan jumlah pakan
    min_amount = st.number_input("Jumlah pakan minimal (kg)", min_value=1.0, value=5.0, key="min_amount")
    max_amount = st.number_input("Jumlah pakan maksimal (kg)", min_value=1.0, value=10.0, key="max_amount")

    # Fungsi optimasi
    if st.button("Optimasi Ransum", key="optimize_button") and all_available_feeds:
        # Persiapkan data untuk optimasi
        c = []  # Biaya per kg
        A_ub = []  # Matriks ketidaksetaraan
        b_ub = []  # Batas kanan ketidaksetaraan
        A_eq = []  # Matriks kesetaraan
        b_eq = []  # Batas kanan kesetaraan

        # Biaya tiap pakan (fungsi objektif)
        for feed in all_available_feeds:
            if feed in df_pakan['Nama Pakan'].values:
                feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
            elif feed in mineral_df['Nama Pakan'].values:
                feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
            else:
                st.error(f"Feed '{feed}' not found in either df_pakan or mineral_df. Please check your input.")
                continue
            c.append(feed_data['Harga (Rp/kg)'])

        # Protein minimum constraint
        protein_constraint = []
        for feed in all_available_feeds:
            if feed in df_pakan['Nama Pakan'].values:
                feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
            else:
                feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
            protein_constraint.append(-feed_data['Protein (%)'])
        A_ub.append(protein_constraint)
        required_protein = nutrient_req.get('Protein (%)', 0)
        b_ub.append(-required_protein * min_amount)

        # TDN minimum constraint
        tdn_constraint = []
        for feed in all_available_feeds:
            if feed in df_pakan['Nama Pakan'].values:
                feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
            else:
                feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
            tdn_constraint.append(-feed_data['TDN (%)'])
        A_ub.append(tdn_constraint)
        required_tdn = nutrient_req.get('TDN (%)', 0)
        b_ub.append(-required_tdn * min_amount)

        # Mineral constraints
        for mineral, key in zip(['Ca (%)', 'P (%)', 'Mg (%)', 'Fe (ppm)', 'Cu (ppm)', 'Zn (ppm)'], 
                                ['Ca (%)', 'P (%)', 'Mg (%)', 'Fe (ppm)', 'Cu (ppm)', 'Zn (ppm)']):
            mineral_constraint = []
            for feed in all_available_feeds:
                if feed in df_pakan['Nama Pakan'].values:
                    feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                else:
                    feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                mineral_constraint.append(-feed_data.get(mineral, 0))
            A_ub.append(mineral_constraint)
            required_mineral = nutrient_req.get(key, 0)
            b_ub.append(-required_mineral * min_amount if 'ppm' not in key else -required_mineral * min_amount / 1000)

        # Total amount constraint
        total_min_constraint = [-1] * len(all_available_feeds)
        A_ub.append(total_min_constraint)
        b_ub.append(-min_amount)

        total_max_constraint = [1] * len(all_available_feeds)
        A_ub.append(total_max_constraint)
        b_ub.append(max_amount)

        # Solve the linear programming problem
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method='highs')

        if result.success:
        else:
            st.error("Optimasi gagal. Silakan periksa kembali input dan batasan.")
            st.success("Optimasi berhasil!")
            if result.success and result.x is not None:
                optimized_amounts = result.x
            else:
                st.error("Optimasi gagal atau menghasilkan data yang tidak valid. Silakan periksa kembali input dan batasan.")
                return
            def calculate_opt_data(all_available_feeds, optimized_amounts, df_pakan, mineral_df):
                """Helper function to calculate optimized data."""
                opt_data = {
                    'Bahan Pakan': all_available_feeds,
                    'Jumlah (kg)': optimized_amounts,
                    'Protein (kg)': [],
                    'TDN (kg)': [],
                    'Ca (kg)': [],
                    'P (kg)': [],
                    'Mg (kg)': [],
                    'Fe (g)': [],
                    'Cu (g)': [],
                    'Zn (g)': [],
                    'Biaya (Rp)': []
                }

                for i, feed in enumerate(all_available_feeds):
                    if feed in df_pakan['Nama Pakan'].values:
                        feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                    else:
                        feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                    opt_data['Protein (kg)'].append(optimized_amounts[i] * feed_data['Protein (%)'] / 100)
                    opt_data['TDN (kg)'].append(optimized_amounts[i] * feed_data['TDN (%)'] / 100)
                    opt_data['Fe (g)'].append(optimized_amounts[i] * feed_data.get('Fe (ppm)', 0) / 1000)
                    opt_data['Cu (g)'].append(optimized_amounts[i] * feed_data.get('Cu (ppm)', 0) / 1000)
                    opt_data['Zn (g)'].append(optimized_amounts[i] * feed_data.get('Zn (ppm)', 0) / 1000)
                    opt_data['Fe (g)'].append(optimized_amounts[i] * feed_data['Fe (ppm)'] / 1000)
                    opt_data['Cu (g)'].append(optimized_amounts[i] * feed_data['Cu (ppm)'] / 1000)
                    opt_data['Zn (g)'].append(optimized_amounts[i] * feed_data['Zn (ppm)'] / 1000)
                    opt_data['Biaya (Rp)'].append(optimized_amounts[i] * feed_data['Harga (Rp/kg)'])

                return opt_data

            opt_data = calculate_opt_data(all_available_feeds, optimized_amounts, df_pakan, mineral_df)
                opt_data['Fe (g)'].append(optimized_amounts[i] * feed_data['Fe (ppm)'] / 1000)
                opt_data['Cu (g)'].append(optimized_amounts[i] * feed_data['Cu (ppm)'] / 1000)
                opt_data['Zn (g)'].append(optimized_amounts[i] * feed_data['Zn (ppm)'] / 1000)
                opt_data['Biaya (Rp)'].append(optimized_amounts[i] * feed_data['Harga (Rp/kg)'])

            df_opt = pd.DataFrame(opt_data)
            df_opt.loc['Total'] = [
                'Total',
                sum(opt_data['Jumlah (kg)']),
                sum(opt_data['Protein (kg)']),
                sum(opt_data['TDN (kg)']),
                sum(opt_data['Ca (kg)']),
                sum(opt_data['P (kg)']),
                sum(opt_data['Mg (kg)']),
                sum(opt_data['Fe (g)']),
                sum(opt_data['Cu (g)']),
                sum(opt_data['Zn (g)']),
                sum(opt_data['Biaya (Rp)'])
            ]

            # Tampilkan hasil
            st.dataframe(df_opt)

            # Tampilkan ringkasan nutrisi
            total_amt = sum(opt_data['Jumlah (kg)'])
            avg_protein = sum(opt_data['Protein (kg)']) * 100 / total_amt
            avg_tdn = sum(opt_data['TDN (kg)']) * 100 / total_amt
            avg_ca = sum(opt_data['Ca (kg)']) * 100 / total_amt
            avg_p = sum(opt_data['P (kg)']) * 100 / total_amt
            avg_mg = sum(opt_data['Mg (kg)']) * 100 / total_amt

            st.subheader("Kandungan Nutrisi Ransum Optimal")
            st.write("Berikut adalah kandungan nutrisi ransum yang telah dihitung berdasarkan bahan pakan yang dipilih. "
                     "Nilai-nilai ini mencerminkan rata-rata kandungan nutrisi seperti protein, TDN, dan mineral dalam ransum.")
            cols = st.columns(5)
            with cols[0]:
                st.metric("Protein (%)", f"{avg_protein:.2f}%", f"{avg_protein - required_protein:.2f}%")

            with cols[1]:
                st.metric("TDN", f"{avg_tdn:.2f}%", f"{avg_tdn - required_tdn:.2f}%")

            with cols[2]:
                st.metric("Kalsium (Ca)", f"{avg_ca:.2f}%", f"{avg_ca - nutrient_req.get('Ca (%)', 0):.2f}%")
                if avg_ca < nutrient_req.get('Ca (%)', 0):
                    st.warning("⚠️ Kandungan Kalsium (Ca) kurang dari kebutuhan. Pertimbangkan untuk menambahkan bahan pakan yang kaya Kalsium, seperti kapur (CaCO3) atau tepung tulang.")

            with cols[3]:
                st.metric("Fosfor (P)", f"{avg_p:.2f}%", f"{avg_p - nutrient_req.get('P (%)', 0):.2f}%")
                if avg_p < nutrient_req.get('P (%)', 0):
                    st.warning("⚠️ Kandungan Fosfor (P) kurang dari kebutuhan. Pertimbangkan untuk menambahkan bahan pakan seperti tepung tulang atau mineral mix yang mengandung Fosfor.")

            with cols[4]:
                st.metric("Magnesium (Mg)", f"{avg_mg:.2f}%", f"{avg_mg - nutrient_req.get('Mg (%)', 0):.2f}%")
                if avg_mg < nutrient_req.get('Mg (%)', 0):
                    st.warning("⚠️ Kandungan Magnesium (Mg) kurang dari kebutuhan. Pertimbangkan untuk menambahkan bahan pakan seperti dolomit atau mineral mix yang mengandung Magnesium.")

            # Total biaya
            st.metric("Total Biaya", f"Rp {sum(opt_data['Biaya (Rp)']):,.0f}")
            st.metric("Biaya per kg", f"Rp {sum(opt_data['Biaya (Rp)']) / total_amt:,.0f}")
            
            # Add explanation for optimal nutrient content and cost
            st.subheader("Keterangan Hasil Kandungan Nutrisi Optimal dan Harganya")
            st.write("""
            **Penjelasan Kandungan Nutrisi Optimal:**
            - Kandungan nutrisi optimal dihitung berdasarkan kebutuhan minimum nutrisi ternak yang dipilih.
            - Hasil menunjukkan bahwa ransum yang dioptimalkan memenuhi kebutuhan protein, TDN, dan mineral dengan biaya terendah.
            - Kandungan nutrisi seperti protein, TDN, dan mineral lainnya dihitung sebagai rata-rata dari semua bahan pakan yang digunakan.

            **Penjelasan Biaya:**
            - Total biaya dihitung berdasarkan jumlah bahan pakan yang digunakan dikalikan dengan harga per kilogram masing-masing bahan.
            - Biaya per kilogram ransum menunjukkan efisiensi biaya untuk setiap kilogram pakan yang dihasilkan.
            - Dengan menggunakan hasil optimasi, Anda dapat mengurangi biaya pakan tanpa mengorbankan kualitas nutrisi yang dibutuhkan ternak.
            """)

        else:
            st.error("Optimasi gagal. Silakan periksa kembali input dan batasan.")
            
            # Helper function for formatting numbers with comma as decimal separator (Indonesian style)
            def format_id(value, precision=2):
                """Format number with comma as decimal separator (Indonesian style)"""
                formatted = f"{value:.{precision}f}".replace(".", ",")
                return formatted
            
            st.subheader("Kandungan Nutrisi Ransum Optimal")
            cols = st.columns(4)
            
            with cols[0]:
                st.metric("Protein", f"{format_id(avg_protein)}%", 
                         f"{format_id(avg_protein - required_protein)}%")
            
            with cols[1]:
                st.metric("TDN", f"{format_id(avg_tdn)}%", 
                         f"{format_id(avg_tdn - required_tdn)}%")
            
            with cols[2]:
                st.metric("Kalsium (Ca)", f"{format_id(avg_ca)}%", 
                         f"{format_id(avg_ca - nutrient_req.get('Ca (%)', 0))}%")
            
            with cols[3]:
                st.metric("Fosfor (P)", f"{format_id(avg_p)}%", 
                         f"{format_id(avg_p - nutrient_req.get('P (%)', 0))}%")
            
            # Total biaya with Indonesian formatting
            st.metric("Total Biaya", f"Rp {format_id(sum(opt_data['Biaya (Rp)']), 0)}")
            st.metric("Biaya per kg", f"Rp {format_id(sum(opt_data['Biaya (Rp)']) / total_amt)}")

            # Implement the format_id function for all other number displays
            # Replace the dataframe formatting with Indonesian style
            # Format numbers in the DataFrame for display
            df_display = df_opt.copy()
            for col in ['Jumlah (kg)', 'Protein (kg)', 'TDN (kg)', 'Ca (kg)', 'P (kg)', 'Biaya (Rp)']:
                if col in df_display.columns:
                    # Skip formatting for the 'Total' row
                    for idx in df_display.index:
                        if idx != 'Total' and isinstance(df_display.loc[idx, col], (int, float)):
                            precision = 0 if col == 'Biaya (Rp)' else 2
                            df_display.loc[idx, col] = format_id(df_display.loc[idx, col], precision)
            
            # Display the formatted dataframe
            st.dataframe(df_display)
            
            # Tampilkan ringkasan nutrisi
            total_amt = sum(opt_data['Jumlah (kg)'])
            avg_protein = sum(opt_data['Protein (kg)']) * 100 / total_amt
            avg_tdn = sum(opt_data['TDN (kg)']) * 100 / total_amt
            avg_ca = sum(opt_data['Ca (kg)']) * 100 / total_amt
            avg_p = sum(opt_data['P (kg)']) * 100 / total_amt
            
            st.subheader("Kandungan Nutrisi Ransum Optimal")
            cols = st.columns(4)
            
            with cols[0]:
                st.metric("Protein", f"{format_id(avg_protein)}%", 
                         f"{format_id(avg_protein - required_protein)}%")
            
            with cols[1]:
                st.metric("TDN", f"{format_id(avg_tdn)}%", 
                         f"{format_id(avg_tdn - required_tdn)}%")
            
            with cols[2]:
                st.metric("Kalsium (Ca)", f"{format_id(avg_ca)}%", 
                         f"{format_id(avg_ca - nutrient_req.get('Ca (%)', 0))}%")
            
            with cols[3]:
                st.metric("Fosfor (P)", f"{format_id(avg_p)}%", 
                         f"{format_id(avg_p - nutrient_req.get('P (%)', 0))}%")
            
            # Total biaya with Indonesian formatting (dot for thousands, no decimal places)
            st.metric("Total Biaya", f"Rp {format_id(sum(opt_data['Biaya (Rp)']), 0)}")
            st.metric("Biaya per kg", f"Rp {format_id(sum(opt_data['Biaya (Rp)']) / total_amt)}")
            
            # Tambahkan saran dan keterangan
            st.subheader("Analisis dan Saran")

            # Analisis hasil optimasi
            st.write("""
            **Hasil Analisis:**
            - Ransum yang dihasilkan telah dioptimalkan untuk memenuhi kebutuhan nutrisi dengan biaya minimal.
            - Kandungan nutrisi seperti protein, TDN, dan mineral telah disesuaikan dengan kebutuhan ternak berdasarkan jenis, umur, dan fase produksi.
            - Biaya per kilogram ransum menunjukkan efisiensi yang tinggi, sehingga dapat membantu mengurangi pengeluaran pakan.

            **Saran Perbaikan:**
            - Jika hasil optimasi belum memuaskan, pertimbangkan langkah berikut:
                1. Tambahkan lebih banyak jenis bahan pakan untuk memberikan fleksibilitas dalam optimasi.
                2. Gunakan bahan pakan dengan kandungan protein atau TDN yang lebih tinggi jika kebutuhan nutrisi belum terpenuhi.
                3. Perhatikan rasio hijauan dan konsentrat sesuai dengan fase produksi ternak.
                4. Pastikan bahan pakan yang digunakan memiliki palatabilitas yang baik agar ternak mau mengonsumsinya.
            - Jika terdapat kekurangan mineral, tambahkan mineral supplement yang sesuai untuk memenuhi kebutuhan mikro dan makro mineral.
            """)

            # Rekomendasi tambahan
            st.write("""
            **Rekomendasi Tambahan:**
            - Lakukan evaluasi berkala terhadap performa ternak untuk memastikan ransum yang diberikan memberikan hasil yang optimal.
            - Simpan bahan pakan di tempat yang kering dan terlindung dari kelembaban untuk mencegah kerusakan atau kontaminasi.
            - Jika memungkinkan, gunakan analisis laboratorium untuk memastikan kandungan nutrisi bahan pakan yang digunakan.
            - Pertimbangkan penggunaan premix atau mineral mix untuk memastikan kebutuhan mikro mineral terpenuhi, terutama pada ternak laktasi atau penggemukan.
            """)
            
            
            # Saran perbaikan atau alternatif
            st.subheader("Saran Penyesuaian")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Jika hasil tidak memuaskan, coba:**")
                st.write("✅ Menambahkan lebih banyak jenis pakan")
                st.write("✅ Menyesuaikan batasan jumlah minimum/maksimum")
                st.write("✅ Menambahkan pakan sumber protein tinggi jika protein di bawah ekspektasi")
            
            with col2:
                st.write("**Alternatif pakan yang bisa dipertimbangkan:**")
                # Berikan saran alternatif pakan berdasarkan ketersediaan nutrisi
                if avg_protein < required_protein * 1.1:  # Jika protein hanya sedikit di atas minimum
                    high_protein = df_pakan[~df_pakan['Nama Pakan'].isin(available_feeds)].sort_values('Protein (%)', ascending=False).head(2)
                    if not high_protein.empty:
                        for _, feed in high_protein.iterrows():
                            st.write(f"🔹 {feed['Nama Pakan']} - Protein: {feed['Protein (%)']}%, Harga: Rp{feed['Harga (Rp/kg)']}/kg")
                
                if avg_tdn < required_tdn * 1.1:  # Jika TDN hanya sedikit di atas minimum
                    high_tdn = df_pakan[~df_pakan['Nama Pakan'].isin(available_feeds)].sort_values('TDN (%)', ascending=False).head(2)
                    if not high_tdn.empty:
                        for _, feed in high_tdn.iterrows():
                            st.write(f"🔹 {feed['Nama Pakan']} - TDN: {feed['TDN (%)']}%, Harga: Rp{feed['Harga (Rp/kg)']}/kg")
            
            # Tampilkan analisis efektivitas biaya
            st.subheader("Analisis Efektivitas Biaya")
            
            # Hitung biaya per protein dan TDN
            total_protein_kg = sum(opt_data['Protein (kg)'])
            total_tdn_kg = sum(opt_data['TDN (kg)'])
            total_cost = sum(opt_data['Biaya (Rp)'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Biaya per kg Protein", f"Rp {total_cost/total_protein_kg:,.2f}")
            with col2:
                st.metric("Biaya per kg TDN", f"Rp {total_cost/total_tdn_kg:,.2f}")
            
            # Saran terkait komposisi nutrien
            st.write("""
            **Catatan Penting:**
            
            1. Ransum optimal ini **meminimalkan biaya** tetapi tetap memenuhi kebutuhan nutrisi dasar.
            
            2. Perhatikan **rasio hijauan dan konsentrat** sesuai fase produksi ternak.
               - Sapi/kambing/domba muda: Hindari terlalu banyak konsentrat (maksimal 40-50%)
               - Ternak penggemukan: Konsentrat bisa lebih tinggi (60-70%)
               - Ternak laktasi: Seimbangkan hijauan berkualitas dan konsentrat
            
            3. **Palatabilitas** juga penting - ransum paling murah belum tentu yang paling baik jika ternak tidak mau memakannya.
            """)

elif mode == "Mineral Supplement":
    st.header("Perhitungan Mineral Supplement")
    
    # Create tabs for different mineral supplement sections - removed Mineral Makro tab
    mineral_tabs = st.tabs(["Data Mineral", "Analisis Kebutuhan", "Mineral Mikro"])
    
    # Tab 1: Data Mineral
    with mineral_tabs[0]:
        # Tambahkan data mineral ke tabel pakan
        mineral_df = load_mineral_data()
        
        # Tampilkan mineral supplements tersedia
        st.subheader("Mineral Supplements Tersedia")
        
        # Add filters for mineral type
        mineral_type = st.radio("Jenis Mineral:", ["Semua", "Makro", "Mikro", "Premix"], horizontal=True)

        try:
            # Make sure mineral_df is available
            if mineral_df is None or mineral_df.empty:
                st.error("Data mineral tidak tersedia. Pastikan file tabeldatamineral.csv ada dalam direktori yang sama.")
                filtered_minerals = pd.DataFrame(columns=["Nama Pakan", "Protein (%)", "TDN (%)", "Ca (%)", "P (%)", 
                                                         "Mg (%)", "Fe (ppm)", "Cu (ppm)", "Zn (ppm)", "Harga (Rp/kg)"])
            else:
                # Check if necessary columns exist
                required_cols = ["Ca (%)", "P (%)", "Mg (%)", "Fe (ppm)", "Cu (ppm)", "Zn (ppm)"]
                missing_cols = [col for col in required_cols if col not in mineral_df.columns]
                
                if missing_cols:
                    st.warning(f"Kolom yang dibutuhkan tidak ada dalam data: {', '.join(missing_cols)}")
                    # Add missing columns with zeros
                    for col in missing_cols:
                        mineral_df[col] = 0
                
                # Filter based on mineral type
                if mineral_type != "Semua":
                    if mineral_type == "Makro":
                        filtered_minerals = mineral_df[
                            (mineral_df['Ca (%)'] > 5) | 
                            (mineral_df['P (%)'] > 5) | 
                            (mineral_df['Mg (%)'] > 2)
                        ]
                    elif mineral_type == "Mikro":
                        filtered_minerals = mineral_df[
                            (mineral_df['Fe (ppm)'] > 1000) | 
                            (mineral_df['Cu (ppm)'] > 500) | 
                            (mineral_df['Zn (ppm)'] > 500)
                        ]
                    elif mineral_type == "Premix":
                        filtered_minerals = mineral_df[
                            (mineral_df['Fe (ppm)'] > 1000) & 
                            (mineral_df['Cu (ppm)'] > 1000) & 
                            (mineral_df['Zn (ppm)'] > 1000)
                        ]
                    else:
                        filtered_minerals = pd.DataFrame()  # Fallback to an empty DataFrame if type is invalid
                else:
                    filtered_minerals = mineral_df

                # Ensure filtered_minerals is not None or empty
                if filtered_minerals is None or filtered_minerals.empty:
                    st.warning(f"Tidak ada mineral yang termasuk kategori {mineral_type}.")
                
                # If filtering resulted in empty DataFrame, show a message
                if filtered_minerals.empty:
                    st.warning(f"Tidak ada mineral yang termasuk kategori {mineral_type}.")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
            filtered_minerals = pd.DataFrame(columns=["Nama Pakan", "Protein (%)", "TDN (%)", "Ca (%)", "P (%)", 
                                                     "Mg (%)", "Fe (ppm)", "Cu (ppm)", "Zn (ppm)", "Harga (Rp/kg)"])

        # Display the data editor regardless of errors
        edited_mineral_df = st.data_editor(
            filtered_minerals,
            column_config={
                "Ca (%)": st.column_config.NumberColumn(
                    "Ca (%)",
                    help="Persentase kandungan kalsium",
                    min_value=0.0,
                    step=0.1,
                    format="%.1f"
                ),
                "P (%)": st.column_config.NumberColumn(
                    "P (%)",
                    help="Persentase kandungan fosfor",
                    min_value=0.0,
                    step=0.1,
                    format="%.1f"
                ),
                "Mg (%)": st.column_config.NumberColumn(
                    "Mg (%)",
                    help="Persentase kandungan magnesium",
                    min_value=0.0,
                    step=0.1,
                    format="%.1f"
                ),
                "Fe (ppm)": st.column_config.NumberColumn(
                    "Fe (ppm)",
                    help="Kandungan zat besi dalam ppm",
                    min_value=0,
                    step=100,
                    format="%d"
                ),
                "Cu (ppm)": st.column_config.NumberColumn(
                    "Cu (ppm)",
                    help="Kandungan tembaga dalam ppm",
                    min_value=0,
                    step=100,
                    format="%d"
                ),
                "Zn (ppm)": st.column_config.NumberColumn(
                    "Zn (ppm)",
                    help="Kandungan seng dalam ppm",
                    min_value=0,
                    step=100,
                    format="%d"
                ),
                "Harga (Rp/kg)": st.column_config.NumberColumn(
                    "Harga (Rp/kg)",
                    help="Harga per kilogram",
                    min_value=0,
                    step=100,
                    format="%d"
                )
            },
            hide_index=True,
            num_rows="fixed"
        )
        
        # Tambahkan deskripsi mineral supplement
        with st.expander("Deskripsi Jenis Mineral Supplement"):
            st.markdown("""
            ### Jenis Mineral Supplement
            
            #### 1. Mineral Makro
            Mineral yang dibutuhkan dalam jumlah relatif besar (g/kg pakan):
            - **Kalsium (Ca)**: Pembentukan tulang, kontraksi otot, pembekuan darah
            - **Fosfor (P)**: Pembentukan tulang, metabolisme energi (ATP), asam nukleat
            - **Magnesium (Mg)**: Aktivator enzim, metabolisme karbohidrat dan lipid
            - **Natrium (Na)**: Keseimbangan cairan, transmisi impuls saraf
            - **Kalium (K)**: Keseimbangan elektrolit, kontraksi otot
            - **Klorida (Cl)**: Keseimbangan asam-basa, pembentukan HCl lambung
            - **Sulfur (S)**: Komponen asam amino (metionin, sistein)

            #### 2. Mineral Mikro
            Mineral yang dibutuhkan dalam jumlah kecil (mg/kg atau ppm):
            - **Zat Besi (Fe)**: Komponen hemoglobin, transport oksigen
            - **Tembaga (Cu)**: Pembentukan hemoglobin, metabolisme besi
            - **Seng (Zn)**: Komponen lebih dari 300 enzim, fungsi kekebalan
            - **Mangan (Mn)**: Pembentukan tulang, reproduksi
            - **Iodium (I)**: Komponen hormon tiroid
            - **Kobalt (Co)**: Komponen vitamin B12
            - **Selenium (Se)**: Antioksidan, metabolisme hormon tiroid

            #### 3. Premix
            Campuran berbagai mineral mikro dan vitamin dalam konsentrasi tinggi:
            - **Mineral Mix**: Kombinasi mineral makro dan mikro
            - **Trace Mineral Mix**: Fokus pada mineral mikro
            - **Complete Premix**: Kombinasi mineral dan vitamin
            """)
        
        # Update mineral dataframe dengan nilai yang diedit
        if edited_mineral_df is not None:
            mineral_df = edited_mineral_df.copy()
            st.success("✅ Nilai mineral supplement berhasil diperbarui!")
        
        # Tambahkan informasi cara penggunaan
        st.info("💡 Klik pada nilai untuk mengedit langsung. Perubahan akan digunakan untuk perhitungan.")
        
        # Tambahkan opsi untuk menambah mineral baru
        with st.expander("Tambah Mineral Supplement Baru"):
            new_mineral_name = st.text_input("Nama Mineral:")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_ca = st.number_input("Ca (%)", min_value=0.0, step=0.1, format="%.1f")
                new_p = st.number_input("P (%)", min_value=0.0, step=0.1, format="%.1f")
                new_mg = st.number_input("Mg (%)", min_value=0.0, step=0.1, format="%.1f")
            
            with col2:
                new_fe = st.number_input("Fe (ppm)", min_value=0, step=100)
                new_cu = st.number_input("Cu (ppm)", min_value=0, step=100)
                new_zn = st.number_input("Zn (ppm)", min_value=0, step=100)
            
            with col3:
                new_price = st.number_input("Harga (Rp/kg)", min_value=0, step=100)
                
            if st.button("Tambahkan Mineral") and new_mineral_name:
                # Buat baris baru
                new_row = pd.DataFrame({
                    "Nama Pakan": [new_mineral_name],
                    "Protein (%)": [0.0],
                    "TDN (%)": [0.0],
                    "Ca (%)": [new_ca],
                    "P (%)": [new_p],
                    "Mg (%)": [new_mg],
                    "Fe (ppm)": [new_fe],
                    "Cu (ppm)": [new_cu],
                    "Zn (ppm)": [new_zn],
                    "Harga (Rp/kg)": [new_price]
                })
                
                # Tambahkan ke dataframe
                mineral_df = pd.concat([mineral_df, new_row], ignore_index=True)
                st.success(f"Mineral {new_mineral_name} berhasil ditambahkan!")
                st.experimental_rerun()
    
    # Tab 2: Analisis Kebutuhan
    with mineral_tabs[1]:
        # TAMBAHKAN: Analisis Kebutuhan Mineral pada Ransum Dasar
        st.subheader("Analisis Kebutuhan Mineral")
        
        # Pilih ransum dasar untuk dianalisis
        st.write("Pilih bahan pakan ransum dasar untuk dianalisis kebutuhan mineralnya:")
        base_feeds = st.multiselect(
            "Pilih bahan pakan ransum dasar:", 
            df_pakan['Nama Pakan'].tolist()
        )
        
        base_feed_amounts = {}
        base_feed_data = {}
        
        if base_feeds:
            st.subheader("Input Jumlah Pakan (kg)")
            cols = st.columns(min(3, len(base_feeds)))
            
            for i, feed_name in enumerate(base_feeds):
                col_idx = i % 3
                with cols[col_idx]:
                    feed_row = df_pakan[df_pakan['Nama Pakan'] == feed_name].iloc[0]
                    base_feed_data[feed_name] = {
                        'protein': feed_row['Protein (%)'],
                        'tdn': feed_row['TDN (%)'],
                        'ca': feed_row['Ca (%)'],
                        'p': feed_row['P (%)'],
                        'mg': feed_row['Mg (%)'],
                        'fe': feed_row['Fe (ppm)'],
                        'cu': feed_row['Cu (ppm)'],
                        'zn': feed_row['Zn (ppm)'],
                        'harga': feed_row['Harga (Rp/kg)']
                    }
                    st.write(f"**{feed_name}**")
                    st.write(f"Ca: {feed_row['Ca (%)']}%, P: {feed_row['P (%)']}%, Mg: {feed_row['Mg (%)']}%")
                    st.write(f"Fe: {feed_row['Fe (ppm)']} ppm, Cu: {feed_row['Cu (ppm)']} ppm, Zn: {feed_row['Zn (ppm)']} ppm")
                    base_feed_amounts[feed_name] = st.number_input(
                        f"Jumlah {feed_name} (kg)",
                        min_value=0.0,
                        step=0.1,
                        key=f"base_amount_{feed_name}"
                    )
        
        # Pilih mineral supplement yang akan digunakan
        st.subheader("Pilih Mineral Supplement")
        selected_minerals = st.multiselect(
            "Pilih mineral supplement yang tersedia:", 
            mineral_df['Nama Pakan'].tolist(),
            default=mineral_df['Nama Pakan'].tolist()  # Preselect all available minerals
        )
        
        # Analisis kebutuhan mineral
        if st.button("Analisis Mineral"):
            if not base_feeds:
                st.error("Silakan pilih minimal satu bahan pakan untuk ransum dasar.")
            else:
                # Hitung total mineral dalam ransum dasar
                total_amount = sum(base_feed_amounts.values())
                
                if total_amount <= 0:
                    st.error("Total jumlah pakan harus lebih dari 0 kg.")
                else:
                    # Kalkulas mineral dalam ransum dasar
                    base_ca = sum(base_feed_amounts[feed] * base_feed_data[feed]['ca'] / 100 for feed in base_feed_amounts)
                    base_p = sum(base_feed_amounts[feed] * base_feed_data[feed]['p'] / 100 for feed in base_feed_amounts)
                    base_mg = sum(base_feed_amounts[feed] * base_feed_data[feed]['mg'] / 100 for feed in base_feed_amounts)
                    base_fe = sum(base_feed_amounts[feed] * base_feed_data[feed]['fe'] * (base_feed_amounts[feed]/1000) for feed in base_feed_amounts)
                    base_cu = sum(base_feed_amounts[feed] * base_feed_data[feed]['cu'] * (base_feed_amounts[feed]/1000) for feed in base_feed_amounts)
                    base_zn = sum(base_feed_amounts[feed] * base_feed_data[feed]['zn'] * (base_feed_amounts[feed]/1000) for feed in base_feed_amounts)
                    
                    # Kebutuhan nutrisi berdasarkan umur dan jenis hewan
                    req_ca = nutrient_req.get('Ca (%)', 0) * total_amount / 100
                    req_p = nutrient_req.get('P (%)', 0) * total_amount / 100
                    req_mg = nutrient_req.get('Mg (%)', 0) * total_amount / 100
                    req_fe = nutrient_req.get('Fe (ppm)', 0) * total_amount / 1000
                    req_cu = nutrient_req.get('Cu (ppm)', 0) * total_amount / 1000
                    req_zn = nutrient_req.get('Zn (ppm)', 0) * total_amount / 1000
                    
                    # Tampilkan hasil analisis mineral
                    st.subheader("Analisis Mineral Ransum Dasar")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Kalsium (Ca)", f"{format_id(base_ca, 3)} kg", 
                                 f"{format_id(base_ca - req_ca, 3)} kg" + " %")
                        if base_ca < req_ca:
                            st.warning(f"Kekurangan Ca: {format_id(req_ca - base_ca, 3)} kg")
                        else:
                            st.success(f"Ca mencukupi kebutuhan")
                    
                    with col2:
                        st.metric("Fosfor (P)", f"{format_id(base_p, 3)} kg",
                                 f"{format_id(base_p - req_p, 3)} kg")
                        if base_p < req_p:
                            st.warning(f"Kekurangan P: {format_id(req_p - base_p, 3)} kg")
                        else:
                            st.success(f"P mencukupi kebutuhan")
                    
                    with col3:
                        st.metric("Magnesium (Mg)", f"{format_id(base_mg, 3)} kg",
                                 f"{format_id(base_mg - req_mg, 3)} kg")
                        if base_mg < req_mg:
                            st.warning(f"Kekurangan Mg: {format_id(req_mg - base_mg, 3)} kg")
                        else:
                            st.success(f"Mg mencukupi kebutuhan")
                    
                    # Mikro mineral
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Zat Besi (Fe)", f"{format_id(base_fe, 3)} g",
                                 f"{format_id(base_fe - req_fe, 3)} g")
                        if base_fe < req_fe:
                            st.warning(f"Kekurangan Fe: {format_id(req_fe - base_fe, 3)} g")
                        else:
                            st.success(f"Fe mencukupi kebutuhan")
                        
                    with col2:
                        st.metric("Tembaga (Cu)", f"{format_id(base_cu, 3)} g",
                                 f"{format_id(base_cu - req_cu, 3)} g")
                        if base_cu < req_cu:
                            st.warning(f"Kekurangan Cu: {format_id(req_cu - base_cu, 3)} g")
                        else:
                            st.success(f"Cu mencukupi kebutuhan")
                        
                    with col3:
                        st.metric("Zinc (Zn)", f"{format_id(base_zn, 3)} g",
                                 f"{format_id(base_zn - req_zn, 3)} g")
                        if base_zn < req_zn:
                            st.warning(f"Kekurangan Zn: {format_id(req_zn - base_zn, 3)} g")
                        else:
                            st.success(f"Zn mencukupi kebutuhan")
                    
                    # Rekomendasi premix jika ada kekurangan mikro mineral
                    if base_ca < req_ca or base_p < req_p or base_mg < req_mg or base_fe < req_fe or base_cu < req_cu or base_zn < req_zn:
                        st.subheader("Rekomendasi Mineral Supplement")
                        
                        # Tambahkan penjelasan mengenai pentingnya mineral
                        st.info("""
                        ### Pentingnya Mineral dalam Pakan Ruminansia
                        
                        Defisiensi mineral dapat menyebabkan:
                        - Penurunan pertumbuhan dan produksi
                        - Gangguan reproduksi
                        - Penurunan fungsi kekebalan tubuh
                        - Berbagai gangguan metabolisme
                        
                        Penambahan mineral supplement sebaiknya dilakukan secara bertahap dan dalam jumlah yang tepat.
                        """)
                        
                        # Tambahkan tips dan saran
                        st.write("### Saran Pemberian Mineral")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Tips Umum:**")
                            st.write("✅ Berikan mineral secara teratur")
                            st.write("✅ Sesuaikan dengan kebutuhan fase produksi")
                            st.write("✅ Perhatikan rasio Ca:P idealnya 1.5:1 - 2:1")
                            st.write("✅ Mineral mikro penting walau jumlahnya sedikit")
                        
                        with col2:
                            st.write("**Perhatian Khusus:**")
                            
                            if base_ca < req_ca:
                                st.write("🔶 Kekurangan Ca dapat menyebabkan osteomalasia dan gangguan pertumbuhan")
                            
                            if base_p < req_p:
                                st.write("🔶 Kekurangan P dapat menyebabkan pica (makan benda asing) dan penurunan nafsu makan")
                            
                            if base_mg < req_mg:
                                st.write("🔶 Kekurangan Mg dapat menyebabkan grass tetany terutama pada ternak yang merumput")
                            
                            if base_cu < req_cu:
                                st.write("🔶 Kekurangan Cu dapat menyebabkan anemia dan gangguan pertumbuhan")
                            
                            if base_zn < req_zn:
                                st.write("🔶 Kekurangan Zn dapat mengganggu sistem kekebalan dan kesehatan kulit")
                        
                        if selected_minerals:
                            # Kalkulasi jumlah mineral supplement
                            st.write("### Jumlah Mineral Supplement yang Direkomendasikan:")
                            
                            recommendations = []
                            
                            for mineral in selected_minerals:
                                mineral_data = mineral_df[mineral_df['Nama Pakan'] == mineral].iloc[0]
                                
                                # Hitung kebutuhan untuk masing-masing mineral
                                required_amount = 0
                                rationale = []
                                
                                # Check if this supplement contributes to needed minerals
                                provides_needed = False
                                
                                if base_ca < req_ca and mineral_data['Ca (%)'] > 0:
                                    ca_needed = max(0, (req_ca - base_ca) / (mineral_data['Ca (%)'] / 100))
                                    required_amount = max(required_amount, ca_needed)
                                    rationale.append(f"- Untuk memenuhi Ca: {ca_needed:.2f} kg")
                                    provides_needed = True
                                    
                                if base_p < req_p and mineral_data['P (%)'] > 0:
                                    p_needed = max(0, (req_p - base_p) / (mineral_data['P (%)'] / 100))
                                    required_amount = max(required_amount, p_needed)
                                    rationale.append(f"- Untuk memenuhi P: {p_needed:.2f} kg")
                                    provides_needed = True
                                    
                                if base_mg < req_mg and mineral_data['Mg (%)'] > 0:
                                    mg_needed = max(0, (req_mg - base_mg) / (mineral_data['Mg (%)'] / 100))
                                    required_amount = max(required_amount, mg_needed)
                                    rationale.append(f"- Untuk memenuhi Mg: {mg_needed:.2f} kg")
                                    provides_needed = True
                                
                                if base_fe < req_fe and mineral_data['Fe (ppm)'] > 0:
                                    # Convert ppm to absolute amounts
                                    fe_needed = max(0, (req_fe - base_fe) * 1000000 / mineral_data['Fe (ppm)'])
                                    fe_needed = fe_needed / 1000  # Convert to kg
                                    required_amount = max(required_amount, fe_needed)
                                    rationale.append(f"- Untuk memenuhi Fe: {fe_needed:.2f} kg")
                                    provides_needed = True
                                    
                                if base_cu < req_cu and mineral_data['Cu (ppm)'] > 0:
                                    cu_needed = max(0, (req_cu - base_cu) * 1000000 / mineral_data['Cu (ppm)'])
                                    cu_needed = cu_needed / 1000  # Convert to kg
                                    required_amount = max(required_amount, cu_needed)
                                    rationale.append(f"- Untuk memenuhi Cu: {cu_needed:.2f} kg")
                                    provides_needed = True
                                    
                                if base_zn < req_zn and mineral_data['Zn (ppm)'] > 0:
                                    zn_needed = max(0, (req_zn - base_zn) * 1000000 / mineral_data['Zn (ppm)'])
                                    zn_needed = zn_needed / 1000  # Convert to kg
                                    required_amount = max(required_amount, zn_needed)
                                    rationale.append(f"- Untuk memenuhi Zn: {zn_needed:.2f} kg")
                                    provides_needed = True
                                
                                if provides_needed and required_amount > 0:
                                    # Calculate cost
                                    cost = required_amount * mineral_data['Harga (Rp/kg)']
                                    recommendations.append({
                                        'mineral': mineral,
                                        'amount': required_amount,
                                        'cost': cost,
                                        'rationale': rationale
                                    })
                            
                            # Sort recommendations by cost
                            recommendations.sort(key=lambda x: x['cost'])
                            
                            # Display recommendations
                            if recommendations:
                                for i, rec in enumerate(recommendations):
                                    st.write(f"**Opsi {i+1}: {rec['mineral']}**")
                                    st.write(f"- Jumlah: {rec['amount']:.2f} kg")
                                    st.write(f"- Biaya: Rp {rec['cost']:,.0f}")
                                    for reason in rec['rationale']:
                                        st.write(reason)
                                    st.write("---")
                            else:
                                st.info("Tidak ada mineral supplement yang diperlukan untuk memenuhi kebutuhan.")
                            
                            # Sort by cost effectiveness
                            if recommendations:
                                recommendations.sort(key=lambda x: x['cost'])
                                
                                for i, rec in enumerate(recommendations):
                                    st.write(f"**Opsi {i+1}: {rec['mineral']}** - {rec['amount']:.2f} kg (Rp{rec['cost']:,.0f})")
                                    for reason in rec['rationale']:
                                        st.write(reason)
                                    st.write("---")
                                
                                # Calculate what happens if we add the top recommendation
                                best_rec = recommendations[0]
                                mineral_data = mineral_df[mineral_df['Nama Pakan'] == best_rec['mineral']].iloc[0]
                                
                                st.subheader("Setelah Penambahan Mineral Supplement")
                                
                                # Calculate new mineral levels
                                new_ca = base_ca + best_rec['amount'] * mineral_data['Ca (%)'] / 100
                                new_p = base_p + best_rec['amount'] * mineral_data['P (%)'] / 100
                                new_mg = base_mg + best_rec['amount'] * mineral_data['Mg (%)'] / 100
                                new_fe = base_fe + best_rec['amount'] * mineral_data['Fe (ppm)'] * (best_rec['amount']/1000)
                                new_cu = base_cu + best_rec['amount'] * mineral_data['Cu (ppm)'] * (best_rec['amount']/1000)
                                new_zn = base_zn + best_rec['amount'] * mineral_data['Zn (ppm)'] * (best_rec['amount']/1000)
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Kalsium (Ca)", f"{format_id(new_ca, 3)} kg", f"{format_id(new_ca - req_ca, 3)} kg")
                                    
                                with col2:
                                    st.metric("Fosfor (P)", f"{format_id(new_p, 3)} kg", f"{format_id(new_p - req_p, 3)} kg")
                                    
                                with col3:
                                    st.metric("Magnesium (Mg)", f"{format_id(new_mg, 3)} kg", f"{format_id(new_mg - req_mg, 3)} kg")
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("Zat Besi (Fe)", f"{format_id(new_fe, 3)} g", f"{format_id(new_fe - req_fe, 3)} g")
                                    
                                with col2:
                                    st.metric("Tembaga (Cu)", f"{format_id(new_cu, 3)} g", f"{format_id(new_cu - req_cu, 3)} g")
                                    
                                with col3:
                                    st.metric("Zinc (Zn)", f"{format_id(new_zn, 3)} g", f"{format_id(new_zn - req_zn, 3)} g")
                                
                                # Show cost analysis
                                st.subheader("Analisis Biaya Suplemen")
                                st.write(f"**Biaya Suplemen**: Rp{format_id(best_rec['cost'], 0)}")
                                st.write(f"**Biaya per kg total ransum**: Rp{format_id(best_rec['cost']/(total_amount + best_rec['amount']), 1)}")
                                
                        else:
                            st.warning("Pilih mineral supplement untuk melihat rekomendasi jumlah yang dibutuhkan")
                    else:
                        st.success("Kandungan mineral dalam ransum dasar sudah memenuhi kebutuhan!")

    # Tab 3: Mineral Mikro (previously Tab 4)
    with mineral_tabs[2]:
        st.subheader("Mineral Mikro pada Ruminansia")
        st.write("""
        Mineral mikro (trace minerals) dibutuhkan dalam jumlah sangat kecil (mg/kg atau ppm), 
        namun memiliki peran penting dalam berbagai fungsi metabolisme.
        """)
        
        # Create expandable sections for each micro mineral
        with st.expander("Zat Besi (Fe)"):
            st.markdown("""
            ### Zat Besi (Fe)
            
            **Fungsi:**
            - Komponen hemoglobin dan mioglobin
            - Transport oksigen dalam darah
            - Komponen enzim (cytochrome, catalase)
            - Proses respirasi sel
            
            **Gejala Defisiensi:**
            - Anemia
            - Kelemahan
            - Penurunan pertumbuhan
            - Peningkatan kerentanan terhadap infeksi
            
            **Tingkat Optimal:**
            - 50-100 ppm BK
            
            **Toksisitas:**
            - >1000 ppm: gangguan pencernaan, penurunan pertumbuhan
            
            **Sumber:**
            - Ferrous sulfate
            - Ferrous carbonate
            - Iron oxide
            """)
            
        with st.expander("Tembaga (Cu)"):
            st.markdown("""
            ### Tembaga (Cu)
            
            **Fungsi:**
            - Pembentukan hemoglobin
            - Pigmentasi rambut dan wol
            - Fungsi enzim antioksidan
            - Metabolisme besi
            - Perkembangan tulang
            
            **Gejala Defisiensi:**
            - Anemia
            - Pertumbuhan lambat
            - Depigmentasi rambut/wol
            - Gangguan tulang
            - Diare kronis (ternak muda)
            
            **Tingkat Optimal:**
            - Sapi: 10-15 ppm BK
            - Domba: 7-11 ppm BK (lebih sensitif terhadap toksisitas Cu)
            
            **Toksisitas:**
            - Domba: >25 ppm dapat menyebabkan toksisitas
            - Sapi: >100 ppm dapat menyebabkan toksisitas
            
            **Sumber:**
            - Copper sulfate
            - Copper oxide
            - Copper chloride
            
            **Catatan:** Interaksi antagonis dengan Mo, S, dan Zn perlu diperhatikan
            """)
            
        with st.expander("Seng (Zn)"):
            st.markdown("""
            ### Seng (Zn)
            
            **Fungsi:**
            - Komponen >300 enzim
            - Sintesis protein
            - Metabolisme karbohidrat
            - Fungsi sistem kekebalan tubuh
            - Kesehatan kulit dan kuku
            - Fungsi reproduksi
            
            **Gejala Defisiensi:**
            - Parakeratosis (kulit bersisik)
            - Pertumbuhan lambat
            - Penurunan nafsu makan
            - Gangguan reproduksi
            - Kaki bengkak dan kuku abnormal
            
            **Tingkat Optimal:**
            - 30-50 ppm BK
            
            **Toksisitas:**
            - >500 ppm: gangguan penyerapan Cu
            
            **Sumber:**
            - Zinc oxide
            - Zinc sulfate
            - Zinc proteinate (organik, bioavailabilitas lebih tinggi)
            """)
            
        with st.expander("Mangan (Mn)"):
            st.markdown("""
            ### Mangan (Mn)
            
            **Fungsi:**
            - Pembentukan tulang
            - Reproduksi
            - Metabolisme lemak dan karbohidrat
            - Aktivasi berbagai enzim
            
            **Gejala Defisiensi:**
            - Pertumbuhan lambat
            - Kelainan bentuk tulang
            - Gangguan reproduksi
            - Ataxia pada anak yang baru lahir
            
            **Tingkat Optimal:**
            - 40-70 ppm BK
            
            **Toksisitas:**
            - >1000 ppm: penurunan pertumbuhan dan nafsu makan
            
            **Sumber:**
            - Manganese oxide
            - Manganese sulfate
            - Manganese chloride
            """)
            
        with st.expander("Iodium (I)"):
            st.markdown("""
            ### Iodium (I)
            
            **Fungsi:**
            - Komponen hormon tiroid
            - Metabolisme energi
            - Termoregulasi
            - Pertumbuhan dan perkembangan
            
            **Gejala Defisiensi:**
            - Gondok
            - Kelahiran anak yang lemah atau mati
            - Rambut kasar
            - Penurunan produksi susu
            
            **Tingkat Optimal:**
            - 0.5-2.0 ppm BK
            
            **Toksisitas:**
            - >50 ppm: lakrimasi berlebihan, batuk, gangguan pernapasan
            
            **Sumber:**
            - Kalium iodat
            - Kalium iodida
            - EDDI (ethylenediamine dihydroiodide)
            """)
            
        with st.expander("Kobalt (Co)"):
            st.markdown("""
            ### Kobalt (Co)
            
            **Fungsi:**
            - Komponen vitamin B12 (diproduksi mikroba rumen)
            - Produksi sel darah merah
            - Metabolisme propionat
            
            **Gejala Defisiensi:**
            - Penurunan nafsu makan
            - Anemia
            - Pertumbuhan lambat
            - Kelelahan
            
            **Tingkat Optimal:**
            - 0.1-0.2 ppm BK
            
            **Toksisitas:**
            - >10 ppm: penurunan nafsu makan
            
            **Sumber:**
            - Cobalt sulfate
            - Cobalt carbonate
            - Cobalt chloride
            """)
            
        with st.expander("Selenium (Se)"):
            st.markdown("""
            ### Selenium (Se)
            
            **Fungsi:**
            - Antioksidan (komponen glutathione peroxidase)
            - Metabolisme hormon tiroid
            - Fungsi sistem kekebalan tubuh
            - Reproduksi
            
            **Gejala Defisiensi:**
            - White muscle disease (myopati nutrisional)
            - Retensi plasenta
            - Infertilitas
            - Penurunan sistem kekebalan
            
            **Tingkat Optimal:**
            - 0.1-0.3 ppm BK
            
            **Toksisitas:**
            - >5 ppm: kerontokan rambut, kuku abnormal, kelumpuhan
            
            **Sumber:**
            - Sodium selenite
            - Sodium selenate
            - Selenium yeast (organik, bioavailabilitas lebih tinggi)
            
            **Catatan:** Batas antara kebutuhan dan toksisitas sangat sempit
            """)
            
        with st.expander("Molibdenum (Mo)"):
            st.markdown("""
            ### Molibdenum (Mo)
            
            **Fungsi:**
            - Komponen enzim xanthine oxidase
            - Metabolisme nitrogen
            - Metabolisme purin
            
            **Gejala Defisiensi:**
            - Jarang terjadi dalam kondisi praktis
            
            **Tingkat Optimal:**
            - 0.1-0.5 ppm BK
            
            **Toksisitas:**
            - >5 ppm: defisiensi Cu sekunder, diare, penurunan pertumbuhan
            
            **Sumber:**
            - Sodium molybdate
            - Ammonium molybdate
            
            **Catatan:** Berinteraksi dengan Cu dan S, kelebihan Mo menurunkan penyerapan Cu
            """)
            
        st.info("💡 Interaksi antar mineral mikro sangat kompleks. Kelebihan satu mineral dapat menyebabkan defisiensi mineral lainnya. Perhatikan rasio Cu:Mo:S yang ideal untuk mencegah gangguan metabolisme.")
        
        # Chart showing mineral relationships
        st.subheader("Interaksi Antar Mineral Mikro")
        st.write("""
        Diagram berikut menunjukkan interaksi antagonis utama antar mineral yang perlu diperhatikan:
        
        - (+) menunjukkan efek menguntungkan
        - (-) menunjukkan efek antagonis
        """)
        
        interactions_data = """
        ```
        Cu ──(-)─── Mo
         │         │
         │         │
        (-)       (-)
         │         │
         ▼         ▼
         Zn ───(-)─── Fe
         │         │
         │         │
        (-)       (-)
         │         │
         ▼         ▼
         Ca ───(-)─── P
        ```
        """
        st.text(interactions_data)
        
        st.write("""
        **Interaksi penting:**
        - Cu-Mo-S: Kelebihan Mo dan S menurunkan ketersediaan Cu
        - Fe-Zn: Kelebihan Fe menurunkan penyerapan Zn
        - Ca-P: Rasio Ca:P mempengaruhi penyerapan keduanya
        - Ca-Zn: Kelebihan Ca dapat menurunkan penyerapan Zn
        """)

# Footer with LinkedIn profile link and improved styling
st.markdown("""
<hr style="height:1px;border:none;color:#333;background-color:#333;margin-top:30px;margin-bottom:20px">
""", unsafe_allow_html=True)

# Get current year for footer
current_year = datetime.datetime.now().year

st.markdown(f"""
<div style="text-align:center; padding:15px; margin-top:10px; margin-bottom:20px">
    <p style="font-size:16px; color:#555">
        © {current_year} Developed by: 
        <a href="https://www.linkedin.com/in/galuh-adi-insani-1aa0a5105/" target="_blank" 
           style="text-decoration:none; color:#0077B5; font-weight:bold">
            <img src="https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Bug.svg.original.svg" 
                 width="16" height="16" style="vertical-align:middle; margin-right:5px">
            Galuh Adi Insani
        </a> 
        with <span style="color:#e25555">❤️</span>
    </p>
    <p style="font-size:12px; color:#777">All rights reserved.</p>
</div>
""", unsafe_allow_html=True)