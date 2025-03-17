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
    
    # Replace the existing feed selection multiselect with separate ones for roughage and concentrates

    # Filter the feed dataframe by category
    if 'Kategori' in df_pakan.columns:
        hijauan_feeds = df_pakan[df_pakan['Kategori'] == 'Hijauan']['Nama Pakan'].tolist()
        konsentrat_feeds = df_pakan[df_pakan['Kategori'] == 'Konsentrat']['Nama Pakan'].tolist()
    else:
        # If no category column exists, provide empty lists
        hijauan_feeds = []
        konsentrat_feeds = []
        st.warning("Kolom 'Kategori' tidak ditemukan dalam data pakan. Silakan tambahkan kategori untuk setiap pakan.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Pilih Hijauan")
        selected_hijauan = st.multiselect(
            "Pilih bahan hijauan yang tersedia:", 
            hijauan_feeds,
            default=hijauan_feeds[:min(2, len(hijauan_feeds))]
        )

    with col2:
        st.subheader("Pilih Konsentrat")
        selected_konsentrat = st.multiselect(
            "Pilih bahan konsentrat yang tersedia:", 
            konsentrat_feeds,
            default=konsentrat_feeds[:min(2, len(konsentrat_feeds))]
        )

    # Combine the selected feeds for the optimization function
    selected_feeds = selected_hijauan + selected_konsentrat
    
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
                # Initialize avg_protein and avg_tdn to avoid undefined variable errors
                avg_protein = 0
                avg_tdn = 0
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

    # Create tabs for different optimization options
    opt_tabs = st.tabs(["Optimasi Standar", "Optimasi dengan Mineral"])
    
    with opt_tabs[0]:
        st.subheader("Optimasi Standar (Protein dan TDN)")
        st.write("Optimasi ransum untuk memenuhi kebutuhan protein dan TDN dengan biaya minimal")
        
        col1, col2 = st.columns(2)
        with col1:
            # Pilih bahan pakan yang tersedia untuk optimasi
            available_feeds = st.multiselect(
                "Pilih bahan pakan yang tersedia:", 
                df_pakan['Nama Pakan'].tolist(), 
                default=df_pakan['Nama Pakan'].tolist()[:3],
                key="standard_feed_selection"
            )
        
        with col2:
            # Batasan jumlah pakan
            min_amount = st.number_input("Jumlah pakan minimal (kg)", min_value=1.0, value=5.0, key="std_min_amount")
            max_amount = st.number_input("Jumlah pakan maksimal (kg)", min_value=1.0, value=10.0, key="std_max_amount", help="Batas maksimum jumlah total pakan")
        
        # Batasan tambahan untuk proporsi hijauan-konsentrat
        with st.expander("Batasan proporsi hijauan-konsentrat"):
            use_ratio_constraint = st.checkbox("Aktifkan batasan proporsi", value=False)
            
            if use_ratio_constraint and 'Kategori' in df_pakan.columns:
                col1, col2 = st.columns(2)
                with col1:
                    min_hijauan = st.slider("Minimum proporsi hijauan (%)", 0, 100, 40)
                with col2:
                    min_konsentrat = st.slider("Minimum proporsi konsentrat (%)", 0, 100, 20)
                
                if min_hijauan + min_konsentrat > 100:
                    st.error("Total minimum proporsi melebihi 100%. Harap kurangi salah satu nilai.")
        
        # Fungsi optimasi
        if st.button("Optimasi Ransum", key="optimize_standard_button") and available_feeds:
            with st.spinner("Menghitung optimasi ransum..."):
                # Persiapkan data untuk optimasi
                c = []  # Biaya per kg
                A_ub = []  # Matriks ketidaksetaraan
                b_ub = []  # Batas kanan ketidaksetaraan
                
                # Biaya tiap pakan (fungsi objektif)
                for feed in available_feeds:
                    feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                    c.append(feed_data['Harga (Rp/kg)'])
                
                # Protein minimum constraint
                protein_constraint = []
                for feed in available_feeds:
                    feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                    protein_constraint.append(-feed_data['Protein (%)'])
                A_ub.append(protein_constraint)
                required_protein = nutrient_req.get('Protein (%)', 0)
                b_ub.append(-required_protein * min_amount)
                
                # TDN minimum constraint
                tdn_constraint = []
                for feed in available_feeds:
                    feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                    tdn_constraint.append(-feed_data['TDN (%)'])
                A_ub.append(tdn_constraint)
                required_tdn = nutrient_req.get('TDN (%)', 0)
                b_ub.append(-required_tdn * min_amount)
                
                # Tambahkan constraint untuk proporsi hijauan-konsentrat jika diaktifkan
                if use_ratio_constraint and 'Kategori' in df_pakan.columns:
                    # Hijauan constraint (minimal min_hijauan%)
                    if min_hijauan > 0:
                        hijauan_constraint = []
                        for feed in available_feeds:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                            if feed_data['Kategori'] == 'Hijauan':
                                hijauan_constraint.append(-1 + min_hijauan/100)
                            else:
                                hijauan_constraint.append(min_hijauan/100)
                        A_ub.append(hijauan_constraint)
                        b_ub.append(0)
                    
                    # Konsentrat constraint (minimal min_konsentrat%)
                    if min_konsentrat > 0:
                        konsentrat_constraint = []
                        for feed in available_feeds:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                            if feed_data['Kategori'] == 'Konsentrat':
                                konsentrat_constraint.append(-1 + min_konsentrat/100)
                            else:
                                konsentrat_constraint.append(min_konsentrat/100)
                        A_ub.append(konsentrat_constraint)
                        b_ub.append(0)
                
                # Total amount constraint
                total_min_constraint = [-1] * len(available_feeds)
                A_ub.append(total_min_constraint)
                b_ub.append(-min_amount)
                
                total_max_constraint = [1] * len(available_feeds)
                A_ub.append(total_max_constraint)
                b_ub.append(max_amount)
                
                # Solve the linear programming problem
                # Validate inputs for linprog
                if len(c) == 0 or len(A_ub) != len(b_ub):
                    st.error("Invalid input for optimization: Ensure cost vector and constraints are properly defined.")
                else:
                    # Ensure bounds are correctly defined
                    bounds = [(0, None) for _ in range(len(c))]
                    
                    # Solve the linear programming problem
                    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
                    
                    # Check for success and handle errors
                    if not result.success:
                        st.error(f"Optimization failed: {result.message}")
                
                # Process optimization results
                if result.success:
                    st.success("✅ Optimasi ransum berhasil!")
                    
                    # Create dictionary of feed amounts
                    optimized_amounts = {}
                    for i, feed in enumerate(available_feeds):
                        if result.x[i] > 0.001:  # Only show feeds with non-zero amounts
                            optimized_amounts[feed] = result.x[i]
                    
                    # Display results
                    st.subheader("Hasil Optimasi Ransum")
                    
                    # Prepare data for display
                    feeds_used = []
                    amounts_used = []
                    feed_type_list = []
                    nutrition_data = {}
                    
                    # Initialize nutrition columns
                    nutrition_columns = ['Protein (%)', 'TDN (%)']
                    for column in nutrition_columns:
                        nutrition_data[column] = []
                    
                    nutrition_data['Harga (Rp/kg)'] = []
                    total_cost = 0
                    total_amount = 0
                    
                    # Collect data for each feed in the optimal solution
                    for feed, amount in optimized_amounts.items():
                        feeds_used.append(feed)
                        amounts_used.append(amount)
                        total_amount += amount
                        
                        # Get feed data
                        feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                        
                        # Get feed type if available
                        if 'Kategori' in feed_data:
                            feed_type_list.append(feed_data['Kategori'])
                        else:
                            feed_type_list.append("Tidak diketahui")
                        
                        # Collect nutrition data
                        for column in nutrition_columns:
                            nutrition_data[column].append(feed_data[column])
                        
                        # Calculate cost
                        feed_cost = feed_data['Harga (Rp/kg)']
                        nutrition_data['Harga (Rp/kg)'].append(feed_cost)
                        total_cost += amount * feed_cost
                    
                    # Create dataframe for display
                    result_data = {
                        'Bahan': feeds_used,
                        'Kategori': feed_type_list,
                        'Jumlah (kg)': amounts_used,
                        'Persentase (%)': [amount/total_amount*100 for amount in amounts_used]
                    }
                    
                    # Add nutrition columns
                    for column in nutrition_columns:
                        result_data[column] = nutrition_data[column]
                    
                    # Add cost column
                    result_data['Harga (Rp/kg)'] = nutrition_data['Harga (Rp/kg)']
                    result_data['Biaya (Rp)'] = [amounts_used[i] * nutrition_data['Harga (Rp/kg)'][i] for i in range(len(feeds_used))]
                    
                    df_result = pd.DataFrame(result_data)
                    st.dataframe(df_result)
                    
                    # Calculate and display total nutrition content
                    st.subheader("Kandungan Nutrisi Ransum")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Calculate protein percentage
                        protein_amount = sum(df_result['Jumlah (kg)'] * df_result['Protein (%)']) / total_amount
                        st.metric(
                            label="Protein Ransum", 
                            value=f"{protein_amount:.2f}%",
                            delta=f"{protein_amount - required_protein:.2f}%" 
                        )
                        
                    with col2:
                        # Calculate TDN percentage
                        tdn_amount = sum(df_result['Jumlah (kg)'] * df_result['TDN (%)']) / total_amount
                        st.metric(
                            label="TDN Ransum", 
                            value=f"{tdn_amount:.2f}%",
                            delta=f"{tdn_amount - required_tdn:.2f}%" 
                        )
                    
                    # Show proporsi hijauan-konsentrat if available
                    if 'Kategori' in df_pakan.columns:
                        hijauan_amount = sum(amount for i, amount in enumerate(amounts_used) if feed_type_list[i] == 'Hijauan')
                        konsentrat_amount = sum(amount for i, amount in enumerate(amounts_used) if feed_type_list[i] == 'Konsentrat')
                        
                        hijauan_percent = hijauan_amount / total_amount * 100 if total_amount > 0 else 0
                        konsentrat_percent = konsentrat_amount / total_amount * 100 if total_amount > 0 else 0
                        
                        st.subheader("Proporsi Hijauan dan Konsentrat")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Hijauan", f"{hijauan_percent:.1f}%")
                        with col2:
                            st.metric("Konsentrat", f"{konsentrat_percent:.1f}%")
                        
                        # Chart for visualizing proportions
                        chart_data = pd.DataFrame({
                            'Kategori': ['Hijauan', 'Konsentrat'],
                            'Persentase': [hijauan_percent, konsentrat_percent]
                        })
                        
                        chart = alt.Chart(chart_data).mark_bar().encode(
                            x='Kategori',
                            y='Persentase',
                            color=alt.Color('Kategori', scale=alt.Scale(domain=['Hijauan', 'Konsentrat'], 
                                                                    range=['#4CAF50', '#FFC107']))
                        ).properties(
                            width=400,
                            height=300,
                            title='Proporsi Hijauan vs Konsentrat'
                        )
                        
                        st.altair_chart(chart)
                    
                    # Cost summary
                    st.subheader("Biaya Ransum")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Biaya per kg", f"Rp {total_cost/total_amount:,.2f}")
                    with col2:
                        st.metric("Total Biaya", f"Rp {total_cost:,.2f}")
                    
                    # Total for all animals
                    if jumlah_ternak > 1:
                        st.metric("Total Biaya untuk Semua Ternak", f"Rp {total_cost * jumlah_ternak:,.2f}")
                    
                    # Charts for visualization
                    st.subheader("Visualisasi Komposisi Ransum")
                    
                    # Pie chart for feed composition
                    composition_pie_data = pd.DataFrame({
                        'Bahan': feeds_used,
                        'Persentase': [amount/total_amount*100 for amount in amounts_used]
                    })
                    
                    composition_pie = alt.Chart(composition_pie_data).mark_arc().encode(
                        theta=alt.Theta(field="Persentase", type="quantitative"),
                        color=alt.Color(field="Bahan", type="nominal"),
                        tooltip=['Bahan', 'Persentase']
                    ).properties(
                        width=350,
                        height=350,
                        title='Komposisi Ransum (%)'
                    )
                    
                    # Bar chart for cost breakdown
                    cost_bar_data = pd.DataFrame({
                        'Bahan': feeds_used,
                        'Biaya (Rp)': [amounts_used[i] * nutrition_data['Harga (Rp/kg)'][i] for i in range(len(feeds_used))]
                    })
                    
                    cost_bar = alt.Chart(cost_bar_data).mark_bar().encode(
                        x=alt.X('Bahan', sort='-y'),
                        y=alt.Y('Biaya (Rp)'),
                        color='Bahan',
                        tooltip=['Bahan', 'Biaya (Rp)']
                    ).properties(
                        width=350,
                        height=350,
                        title='Biaya per Bahan Pakan'
                    )
                    
                    # Display charts side by side
                    charts = alt.hconcat(composition_pie, cost_bar)
                    st.altair_chart(charts, use_container_width=True)
                    
                    # Save formula option
                    #st.subheader("Simpan Formula")
                    #formula_name = st.text_input("Nama formula:", value=f"Formula {jenis_hewan} {kategori_umur}")
                    
                    #if st.button("Simpan Formula Ini"):
                    #    if formula_name:
                    #        success = save_formula(formula_name, feeds_used, optimized_amounts, jenis_hewan, kategori_umur)
                    #        if success:
                    #            st.success(f"Formula '{formula_name}' berhasil disimpan!")
                    #        else:
                    #           st.error("Gagal menyimpan formula.")
                    #    else:
                    #        st.warning("Harap masukkan nama untuk formula ini.")
                    
                else:
                    st.error(f"❌ Optimasi ransum gagal: {result.message}")
                    st.warning("""
                    Beberapa kemungkinan penyebab kegagalan:
                    1. Batasan yang ditentukan terlalu ketat
                    2. Bahan pakan yang dipilih tidak dapat memenuhi kebutuhan nutrisi minimal
                    3. Batasan jumlah pakan tidak realistis
                    
                    Coba ubah batasan atau tambahkan lebih banyak pilihan pakan.
                    """)

    with opt_tabs[1]:
        st.subheader("Optimasi dengan Mineral")
        st.write("Optimasi ransum dengan mempertimbangkan kebutuhan mineral makro dan mikro")
        
        col1, col2 = st.columns(2)
        with col1:
            # Pilih bahan pakan yang tersedia untuk optimasi
            available_feeds = st.multiselect(
                "Pilih bahan pakan yang tersedia:", 
                df_pakan['Nama Pakan'].tolist(), 
                default=df_pakan['Nama Pakan'].tolist()[:3],
                key="mineral_feed_selection"
            )
        
        with col2:
            # Pilih mineral supplement yang tersedia
            available_minerals = st.multiselect(
                "Pilih mineral supplement yang tersedia:", 
                mineral_df['Nama Pakan'].tolist(), 
                default=mineral_df['Nama Pakan'].tolist()[:2],
                key="mineral_supplement_selection"
            )
        
        # Gabungkan bahan pakan dan mineral supplement
        all_available_feeds = available_feeds + available_minerals
        
        # Batasan jumlah pakan
        col1, col2 = st.columns(2)
        with col1:
            min_amount = st.number_input("Jumlah pakan minimal (kg)", min_value=1.0, value=5.0, key="mineral_min_amount")
        with col2:
            max_amount = st.number_input("Jumlah pakan maksimal (kg)", min_value=1.0, value=10.0, key="mineral_max_amount")
        
        # Pilih mineral yang akan dioptimalkan
        st.write("Pilih mineral yang akan dimasukkan dalam optimasi:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_ca = st.checkbox("Kalsium (Ca)", value=True)
            include_p = st.checkbox("Fosfor (P)", value=True)
        
        with col2:
            include_mg = st.checkbox("Magnesium (Mg)", value=True)
            include_fe = st.checkbox("Zat Besi (Fe)", value=False)
        
        with col3:
            include_cu = st.checkbox("Tembaga (Cu)", value=False)
            include_zn = st.checkbox("Zinc (Zn)", value=False)
        
        # Fungsi optimasi dengan mineral
        if st.button("Optimasi Ransum dengan Mineral", key="optimize_mineral_button") and all_available_feeds:
            with st.spinner("Menghitung optimasi ransum dengan mineral..."):
                # Persiapkan data untuk optimasi
                c = []  # Biaya per kg
                A_ub = []  # Matriks ketidaksetaraan
                b_ub = []  # Batas kanan ketidaksetaraan
                
                # Biaya tiap pakan (fungsi objektif)
                for feed in all_available_feeds:
                    if feed in df_pakan['Nama Pakan'].values:
                        feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                    else:
                        feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
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
                
                # Add mineral constraints based on user selection
                if include_ca:
                    ca_constraint = []
                    for feed in all_available_feeds:
                        if feed in df_pakan['Nama Pakan'].values:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                        else:
                            feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                        ca_constraint.append(-feed_data['Ca (%)'])
                    A_ub.append(ca_constraint)
                    required_ca = nutrient_req.get('Ca (%)', 0)
                    b_ub.append(-required_ca * min_amount)
                
                if include_p:
                    p_constraint = []
                    for feed in all_available_feeds:
                        if feed in df_pakan['Nama Pakan'].values:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                        else:
                            feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                        p_constraint.append(-feed_data['P (%)'])
                    A_ub.append(p_constraint)
                    required_p = nutrient_req.get('P (%)', 0)
                    b_ub.append(-required_p * min_amount)
                
                if include_mg:
                    mg_constraint = []
                    for feed in all_available_feeds:
                        if feed in df_pakan['Nama Pakan'].values:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                        else:
                            feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                        mg_constraint.append(-feed_data['Mg (%)'])
                    A_ub.append(mg_constraint)
                    required_mg = nutrient_req.get('Mg (%)', 0)
                    b_ub.append(-required_mg * min_amount)
                
                if include_fe:
                    fe_constraint = []
                    for feed in all_available_feeds:
                        if feed in df_pakan['Nama Pakan'].values:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                        else:
                            feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                        fe_value = feed_data['Fe (ppm)'] / 10000 if 'Fe (ppm)' in feed_data else 0
                        fe_constraint.append(-fe_value)
                    A_ub.append(fe_constraint)
                    required_fe = nutrient_req.get('Fe (ppm)', 0)
                    b_ub.append(-(required_fe / 10000) * min_amount)
                
                if include_cu:
                    cu_constraint = []
                    for feed in all_available_feeds:
                        if feed in df_pakan['Nama Pakan'].values:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                        else:
                            feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                        cu_value = feed_data['Cu (ppm)'] / 10000 if 'Cu (ppm)' in feed_data else 0
                        cu_constraint.append(-cu_value)
                    A_ub.append(cu_constraint)
                    required_cu = nutrient_req.get('Cu (ppm)', 0)
                    b_ub.append(-(required_cu / 10000) * min_amount)
                
                if include_zn:
                    zn_constraint = []
                    for feed in all_available_feeds:
                        if feed in df_pakan['Nama Pakan'].values:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                        else:
                            feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                        zn_value = feed_data['Zn (ppm)'] / 10000 if 'Zn (ppm)' in feed_data else 0
                        zn_constraint.append(-zn_value)
                    A_ub.append(zn_constraint)
                    required_zn = nutrient_req.get('Zn (ppm)', 0)
                    b_ub.append(-(required_zn / 10000) * min_amount)
                
                # Total amount constraint
                total_min_constraint = [-1] * len(all_available_feeds)
                A_ub.append(total_min_constraint)
                b_ub.append(-min_amount)
                
                total_max_constraint = [1] * len(all_available_feeds)
                A_ub.append(total_max_constraint)
                b_ub.append(max_amount)
                
                # Minimum proportion for feed types (optional)
                if len(available_feeds) > 0 and len(all_available_feeds) > len(available_feeds):
                    # Ensure at least 70% comes from regular feeds, not mineral supplements
                    feed_proportion_constraint = []
                    for feed in all_available_feeds:
                        if feed in available_feeds:
                            feed_proportion_constraint.append(-0.7)
                        else:
                            feed_proportion_constraint.append(0.3)
                    A_ub.append(feed_proportion_constraint)
                    b_ub.append(0)
                
                # Validate dimensions of c, A_ub, and b_ub
                if len(A_ub) != len(b_ub):
                    st.error("The number of rows in A_ub must match the length of b_ub.")
                elif len(A_ub[0]) != len(c):
                    st.error("The number of columns in A_ub must match the length of c.")
                else:
                    try:
                        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None) for _ in c], method='highs')
                        if result.success:
                            st.success("Optimization successful!")
                        else:
                            st.error(f"Optimization failed: {result.message}")
                    except Exception as e:
                        st.error(f"An error occurred during optimization: {e}")
                
                # Process optimization results
                if result.success:
                    st.success("✅ Optimasi ransum berhasil!")
                    
                    # Create dictionary of feed amounts
                    optimized_amounts = {}
                    for i, feed in enumerate(all_available_feeds):
                        if result.x[i] > 0.001:  # Only show feeds with non-zero amounts
                            optimized_amounts[feed] = result.x[i]
                    
                    # Display results
                    st.subheader("Hasil Optimasi Ransum")
                    
                    # Prepare data for display
                    feeds_used = []
                    amounts_used = []
                    feed_type_list = []
                    nutrition_data = {}
                    
                    # Initialize nutrition columns
                    nutrition_columns = ['Protein (%)', 'TDN (%)']
                    if include_ca:
                        nutrition_columns.append('Ca (%)')
                    if include_p:
                        nutrition_columns.append('P (%)')
                    if include_mg:
                        nutrition_columns.append('Mg (%)')
                    if include_fe:
                        nutrition_columns.append('Fe (ppm)')
                    if include_cu:
                        nutrition_columns.append('Cu (ppm)')
                    if include_zn:
                        nutrition_columns.append('Zn (ppm)')
                    
                    for column in nutrition_columns:
                        nutrition_data[column] = []
                    
                    nutrition_data['Harga (Rp/kg)'] = []
                    total_cost = 0
                    total_amount = 0
                    
                    # Collect data for each feed in the optimal solution
                    for feed, amount in optimized_amounts.items():
                        feeds_used.append(feed)
                        amounts_used.append(amount)
                        total_amount += amount
                        
                        # Get feed data and type
                        if feed in df_pakan['Nama Pakan'].values:
                            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                            feed_type_list.append("Pakan")
                        else:
                            feed_data = mineral_df[mineral_df['Nama Pakan'] == feed].iloc[0]
                            feed_type_list.append("Mineral")
                        
                        # Collect nutrition data
                        for column in nutrition_columns:
                            if column in feed_data:
                                nutrition_data[column].append(feed_data[column])
                            else:
                                nutrition_data[column].append(0)
                        
                        # Calculate cost
                        feed_cost = feed_data['Harga (Rp/kg)']
                        nutrition_data['Harga (Rp/kg)'].append(feed_cost)
                        total_cost += amount * feed_cost
                    
                    # Create dataframe for display
                    result_data = {
                        'Bahan': feeds_used,
                        'Jenis': feed_type_list,
                        'Jumlah (kg)': amounts_used,
                        'Persentase (%)': [amount/total_amount*100 for amount in amounts_used]
                    }
                    
                    # Add nutrition columns
                    for column in nutrition_columns:
                        result_data[column] = nutrition_data[column]
                    
                    # Add cost column
                    result_data['Harga (Rp/kg)'] = nutrition_data['Harga (Rp/kg)']
                    result_data['Biaya (Rp)'] = [amounts_used[i] * nutrition_data['Harga (Rp/kg)'][i] for i in range(len(feeds_used))]
                    
                    df_result = pd.DataFrame(result_data)
                    st.dataframe(df_result)
                    
                    # Calculate and display total nutrition content
                    st.subheader("Kandungan Nutrisi Ransum")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Calculate protein percentage
                        protein_amount = sum(df_result['Jumlah (kg)'] * df_result['Protein (%)']) / total_amount
                        st.metric(
                            label="Protein Ransum", 
                            value=f"{protein_amount:.2f}%",
                            delta=f"{protein_amount - required_protein:.2f}%" 
                        )
                        
                    with col2:
                        # Calculate TDN percentage
                        tdn_amount = sum(df_result['Jumlah (kg)'] * df_result['TDN (%)']) / total_amount
                        st.metric(
                            label="TDN Ransum", 
                            value=f"{tdn_amount:.2f}%",
                            delta=f"{tdn_amount - required_tdn:.2f}%" 
                        )
                    
                    # Display mineral content if included
                    if include_ca or include_p or include_mg:
                        st.subheader("Kandungan Mineral Makro")
                        cols = st.columns(3)
                        col_idx = 0
                        
                        if include_ca:
                            with cols[col_idx]:
                                ca_amount = sum(df_result['Jumlah (kg)'] * df_result['Ca (%)']) / total_amount
                                st.metric(
                                    label="Kalsium (Ca)", 
                                    value=f"{ca_amount:.2f}%",
                                    delta=f"{ca_amount - required_ca:.2f}%" 
                                )
                            col_idx += 1
                            
                        if include_p:
                            with cols[col_idx]:
                                p_amount = sum(df_result['Jumlah (kg)'] * df_result['P (%)']) / total_amount
                                st.metric(
                                    label="Fosfor (P)", 
                                    value=f"{p_amount:.2f}%",
                                    delta=f"{p_amount - required_p:.2f}%" 
                                )
                            col_idx += 1
                            
                        if include_mg:
                            with cols[col_idx]:
                                mg_amount = sum(df_result['Jumlah (kg)'] * df_result['Mg (%)']) / total_amount
                                st.metric(
                                    label="Magnesium (Mg)", 
                                    value=f"{mg_amount:.2f}%",
                                    delta=f"{mg_amount - required_mg:.2f}%" 
                                )
                    
                    # Display mineral micro content if included
                    if include_fe or include_cu or include_zn:
                        st.subheader("Kandungan Mineral Mikro")
                        cols = st.columns(3)
                        col_idx = 0
                        
                        if include_fe:
                            with cols[col_idx]:
                                fe_amount = sum(df_result['Jumlah (kg)'] * df_result['Fe (ppm)']) / total_amount
                                st.metric(
                                    label="Besi (Fe)", 
                                    value=f"{fe_amount:.2f} ppm",
                                    delta=f"{fe_amount - required_fe:.2f} ppm" 
                                )
                            col_idx += 1
                            
                        if include_cu:
                            with cols[col_idx]:
                                cu_amount = sum(df_result['Jumlah (kg)'] * df_result['Cu (ppm)']) / total_amount
                                st.metric(
                                    label="Tembaga (Cu)", 
                                    value=f"{cu_amount:.2f} ppm",
                                    delta=f"{cu_amount - required_cu:.2f} ppm" 
                                )
                            col_idx += 1
                            
                        if include_zn:
                            with cols[col_idx]:
                                zn_amount = sum(df_result['Jumlah (kg)'] * df_result['Zn (ppm)']) / total_amount
                                st.metric(
                                    label="Zinc (Zn)", 
                                    value=f"{zn_amount:.2f} ppm",
                                    delta=f"{zn_amount - required_zn:.2f} ppm" 
                                )
                    
                    # Cost summary
                    st.subheader("Biaya Ransum")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Biaya per kg", f"Rp {total_cost/total_amount:,.2f}")
                    with col2:
                        st.metric("Total Biaya", f"Rp {total_cost:,.2f}")
                    
                    # Total for all animals
                    if jumlah_ternak > 1:
                        st.metric("Total Biaya untuk Semua Ternak", f"Rp {total_cost * jumlah_ternak:,.2f}")
                    
                else:
                    st.error(f"❌ Optimasi ransum gagal: {result.message}")
                    st.warning("Coba ubah batasan atau tambahkan lebih banyak pilihan pakan")

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
                        
                        # Check if protein and TDN are deficient as well
                        protein_deficient = False
                        tdn_deficient = False
                        
                        # Calculate protein and TDN in base ration
                        if total_amount > 0:
                            base_protein = sum(base_feed_amounts[feed] * base_feed_data[feed]['protein'] for feed in base_feed_amounts) / total_amount
                            base_tdn = sum(base_feed_amounts[feed] * base_feed_data[feed]['tdn'] for feed in base_feed_amounts) / total_amount
                            
                            required_protein_pct = nutrient_req.get('Protein (%)', 0)
                            required_tdn_pct = nutrient_req.get('TDN (%)', 0)
                            
                            protein_deficient = base_protein < required_protein_pct
                            tdn_deficient = base_tdn < required_tdn_pct
                            
                            if protein_deficient or tdn_deficient:
                                st.warning("### Perhatian: Defisiensi Nutrisi Utama")
                                
                                if protein_deficient:
                                    protein_deficit = required_protein_pct - base_protein
                                    st.write(f"⚠️ **Defisiensi Protein**: {protein_deficit:.2f}% (Aktual: {base_protein:.2f}%, Dibutuhkan: {required_protein_pct:.2f}%)")
                                
                                if tdn_deficient:
                                    tdn_deficit = required_tdn_pct - base_tdn
                                    st.write(f"⚠️ **Defisiensi TDN**: {tdn_deficit:.2f}% (Aktual: {base_tdn:.2f}%, Dibutuhkan: {required_tdn_pct:.2f}%)")
                                
                                st.write("#### Saran untuk Mengatasi Defisiensi Nutrisi Utama:")
                                
                                with st.expander("Lihat Saran untuk Meningkatkan Protein dan TDN"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write("**Untuk meningkatkan protein:**")
                                        protein_feeds = df_pakan.sort_values(by='Protein (%)', ascending=False).head(5)
                                        st.write("Bahan pakan kaya protein:")
                                        for i, row in protein_feeds.iterrows():
                                            st.write(f"- {row['Nama Pakan']}: {row['Protein (%)']}% protein, Rp{row['Harga (Rp/kg)']:,.0f}/kg")
                                        
                                        st.write("""
                                        **Tips:**
                                        - Tambahkan bungkil kedelai, bungkil kacang tanah, atau bungkil kelapa
                                        - Pertimbangkan penggunaan urea pada ternak dewasa (maksimal 1% dari ransum)
                                        - Legume hay (seperti alfalfa, kaliandra, lamtoro) dapat menambah protein
                                        """)
                                    
                                    with col2:
                                        st.write("**Untuk meningkatkan TDN:**")
                                        energy_feeds = df_pakan.sort_values(by='TDN (%)', ascending=False).head(5)
                                        st.write("Bahan pakan kaya energi:")
                                        for i, row in energy_feeds.iterrows():
                                            st.write(f"- {row['Nama Pakan']}: {row['TDN (%)']}% TDN, Rp{row['Harga (Rp/kg)']:,.0f}/kg")
                                        
                                        st.write("""
                                        **Tips:**
                                        - Tambahkan biji-bijian (jagung, gandum, barley)
                                        - Tambahkan minyak nabati (1-3% dari ransum)
                                        - Molases dapat meningkatkan energi (maksimal 5% dari ransum)
                                        """)
                                
                                st.write("""
                                > **Penting:** Mineral supplement dapat memperbaiki defisiensi mineral, 
                                > tetapi untuk protein dan TDN diperlukan penyesuaian pakan utama.
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
                                
                                # Add analysis of protein and TDN contribution
                                if provides_needed and required_amount > 0:
                                    # Calculate protein and TDN contribution from supplement
                                    protein_contribution = mineral_data['Protein (%)'] * required_amount / total_amount
                                    tdn_contribution = mineral_data['TDN (%)'] * required_amount / total_amount
                                    
                                    if protein_deficient and protein_contribution > 0.1:
                                        rationale.append(f"- Berkontribusi protein: +{protein_contribution:.2f}% pada ransum")
                                    
                                    if tdn_deficient and tdn_contribution > 0.1:
                                        rationale.append(f"- Berkontribusi TDN: +{tdn_contribution:.2f}% pada ransum")
                                    
                                    # Calculate cost
                                    cost = required_amount * mineral_data['Harga (Rp/kg)']
                                    recommendations.append({
                                        'mineral': mineral,
                                        'amount': required_amount,
                                        'cost': cost,
                                        'rationale': rationale,
                                        'efficiency': 1/cost if cost > 0 else 0  # Efficiency measure (inverse of cost)
                                    })
                            
                            # Sort recommendations by cost
                            recommendations.sort(key=lambda x: x['cost'])
                            
                            # Display recommendations
                            if recommendations:
                                # Create tabs for different recommendation views
                                rec_tabs = st.tabs(["Rekomendasi Biaya Terendah", "Semua Opsi", "Analisis Detail"])
                                
                                # Tab 1: Best option
                                with rec_tabs[0]:
                                    best_rec = recommendations[0]
                                    st.write(f"### Rekomendasi Optimal: {best_rec['mineral']}")
                                    
                                    # Create recommendation box with colored border
                                    st.markdown(f"""
                                    <div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 15px; margin: 10px 0;">
                                        <h4 style="color: #4CAF50; margin-top: 0;">Detail Rekomendasi</h4>
                                        <p><b>Mineral Supplement:</b> {best_rec['mineral']}</p>
                                        <p><b>Jumlah:</b> {best_rec['amount']:.2f} kg</p>
                                        <p><b>Biaya:</b> Rp {best_rec['cost']:,.0f}</p>
                                        <p><b>Rasional:</b></p>
                                        <ul>
                                        {"".join(f"<li>{reason[2:]}</li>" for reason in best_rec['rationale'])}
                                        </ul>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Calculate what happens if we add the recommended supplement
                                    mineral_data = mineral_df[mineral_df['Nama Pakan'] == best_rec['mineral']].iloc[0]
                                    
                                    # Calculate new mineral levels
                                    new_ca = base_ca + best_rec['amount'] * mineral_data['Ca (%)'] / 100
                                    new_p = base_p + best_rec['amount'] * mineral_data['P (%)'] / 100
                                    new_mg = base_mg + best_rec['amount'] * mineral_data['Mg (%)'] / 100
                                    new_fe = base_fe + best_rec['amount'] * mineral_data['Fe (ppm)'] * (best_rec['amount']/1000)
                                    new_cu = base_cu + best_rec['amount'] * mineral_data['Cu (ppm)'] * (best_rec['amount']/1000)
                                    new_zn = base_zn + best_rec['amount'] * mineral_data['Zn (ppm)'] * (best_rec['amount']/1000)
                                    
                                    st.subheader("Kandungan Mineral Setelah Suplementasi")
                                    
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
                                    
                                    # Cara pemberian
                                    st.subheader("Cara Pemberian")
                                    st.markdown(f"""
                                    1. Campurkan {best_rec['mineral']} sebanyak {format_id(best_rec['amount'], 2)} kg ke dalam ransum total ({format_id(total_amount, 1)} kg)
                                    2. Aduk secara merata untuk memastikan distribusi yang baik
                                    3. Untuk pemberian harian, bagi jumlah total dengan jumlah hari pemberian
                                    
                                    **Dosis per ekor per hari:** {format_id(best_rec['amount']/jumlah_ternak, 3)} kg
                                    """)
                                    
                                # Tab 2: All options
                                with rec_tabs[1]:
                                    st.write("### Semua Opsi Mineral Supplement")
                                    
                                    for i, rec in enumerate(recommendations):
                                        with st.expander(f"Opsi {i+1}: {rec['mineral']} - {rec['amount']:.2f} kg (Rp{rec['cost']:,.0f})"):
                                            st.write(f"**Jumlah yang dibutuhkan:** {rec['amount']:.2f} kg")
                                            st.write(f"**Biaya:** Rp {rec['cost']:,.0f}")
                                            st.write("**Alasan:**")
                                            for reason in rec['rationale']:
                                                st.write(reason)
                                
                                # Tab 3: Detailed analysis
                                with rec_tabs[2]:
                                    st.write("### Analisis Detail Mineral Supplement")
                                    
                                    # Calculate cost effectiveness and create table
                                    analysis_data = []
                                    for rec in recommendations:
                                        mineral_data = mineral_df[mineral_df['Nama Pakan'] == rec['mineral']].iloc[0]
                                        
                                        # Calculate how much each supplement contributes to each mineral
                                        ca_contribution = mineral_data['Ca (%)'] * rec['amount'] / 100
                                        p_contribution = mineral_data['P (%)'] * rec['amount'] / 100
                                        mg_contribution = mineral_data['Mg (%)'] * rec['amount'] / 100
                                        fe_contribution = mineral_data['Fe (ppm)'] * rec['amount'] / 1000000
                                        cu_contribution = mineral_data['Cu (ppm)'] * rec['amount'] / 1000000
                                        zn_contribution = mineral_data['Zn (ppm)'] * rec['amount'] / 1000000
                                        
                                        # Calculate cost per unit mineral
                                        ca_cost = rec['cost'] / ca_contribution if ca_contribution > 0 else float('inf')
                                        p_cost = rec['cost'] / p_contribution if p_contribution > 0 else float('inf')
                                        mg_cost = rec['cost'] / mg_contribution if mg_contribution > 0 else float('inf')
                                        
                                        analysis_data.append({
                                            'Mineral': rec['mineral'],
                                            'Jumlah (kg)': rec['amount'],
                                            'Biaya (Rp)': rec['cost'],
                                            'Ca (kg)': ca_contribution,
                                            'P (kg)': p_contribution,
                                            'Mg (kg)': mg_contribution,
                                            'Fe (g)': fe_contribution * 1000, # Convert to g
                                            'Cu (g)': cu_contribution * 1000, # Convert to g
                                            'Zn (g)': zn_contribution * 1000, # Convert to g
                                            'Efisiensi Biaya': rec['efficiency']
                                        })
                                    
                                    analysis_df = pd.DataFrame(analysis_data)
                                    st.dataframe(analysis_df)
                                    
                                    # Create visualization
                                    if len(analysis_data) > 1:
                                        st.subheader("Perbandingan Kontribusi Mineral")
                                        
                                        # Prepare data for visualization
                                        chart_data = pd.melt(
                                            analysis_df, 
                                            id_vars=['Mineral'], 
                                            value_vars=['Ca (kg)', 'P (kg)', 'Mg (kg)'],
                                            var_name='Jenis Mineral', 
                                            value_name='Kontribusi (kg)'
                                        )
                                        
                                        chart = alt.Chart(chart_data).mark_bar().encode(
                                            x=alt.X('Mineral:N', title='Mineral Supplement'),
                                            y=alt.Y('Kontribusi (kg):Q'),
                                            color='Jenis Mineral:N',
                                            tooltip=['Mineral', 'Jenis Mineral', 'Kontribusi (kg)']
                                        ).properties(
                                            title='Kontribusi Mineral Makro dari Supplement',
                                            width=600,
                                            height=400
                                        )
                                        
                                        st.altair_chart(chart)
                                        
                                        # Cost comparison
                                        st.subheader("Perbandingan Biaya Mineral Supplement")
                                        
                                        cost_chart = alt.Chart(analysis_df).mark_bar().encode(
                                            x=alt.X('Mineral:N', title='Mineral Supplement'),
                                            y=alt.Y('Biaya (Rp):Q'),
                                            color=alt.Color('Mineral:N', legend=None),
                                            tooltip=['Mineral', 'Biaya (Rp)', 'Jumlah (kg)']
                                        ).properties(
                                            title='Biaya Mineral Supplement',
                                            width=600,
                                            height=300
                                        )
                                        
                                        st.altair_chart(cost_chart)
                                
                                # Show cost analysis
                                st.subheader("Analisis Biaya Suplementasi")
                                best_rec = recommendations[0]
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Biaya Suplemen", f"Rp{format_id(best_rec['cost'], 0)}")
                                with col2:
                                    st.metric("Biaya per kg total ransum", f"Rp{format_id(best_rec['cost']/(total_amount + best_rec['amount']), 1)}")
                                with col3:
                                    st.metric("Peningkatan biaya ransum", f"{format_id(best_rec['cost']/(total_amount + best_rec['amount'])*100, 1)}%")
                                
                                # Add suggestion about protein and TDN if they're deficient
                                if protein_deficient or tdn_deficient:
                                    st.info("""
                                    ⚠️ **Penting:** Mineral supplement hanya mengatasi defisiensi mineral, bukan protein atau TDN.
                                    Lihat rekomendasi di atas untuk mengatasi defisiensi protein dan TDN.
                                    """)
                            else:
                                st.warning("Tidak ada mineral supplement yang diperlukan untuk memenuhi kebutuhan.")
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