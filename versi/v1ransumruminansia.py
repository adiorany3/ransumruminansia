import streamlit as st

# Add favicon to the app
st.set_page_config(
    page_title="Aplikasi Perhitungan Ransum Ruminansia",
    page_icon="🐄",
    layout="wide"
)

# Hide default Streamlit elements
hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Rest of your imports
import pandas as pd
import io
import numpy as np
from scipy.optimize import linprog  # Untuk optimalisasi ransum
import altair as alt
import matplotlib.pyplot as plt
import datetime  # Add this import for the footer

# Define utility functions before they're used
def calculate_nutrition_content(feed_data, feed_amounts):
    """Menghitung kandungan nutrisi dari kombinasi pakan"""
    total_amount = sum(feed_amounts.values())
    
    if total_amount <= 0:
        return None, None, None, None, None, None, None
        
    total_protein = sum(feed_amounts[feed] * feed_data[feed]['protein'] for feed in feed_amounts)
    total_tdn = sum(feed_amounts[feed] * feed_data[feed]['tdn'] for feed in feed_amounts)
    total_cost = sum(feed_amounts[feed] * feed_data[feed]['harga'] for feed in feed_amounts)
    
    # Add mineral calculations with defaults if keys don't exist
    total_ca = sum(feed_amounts[feed] * feed_data[feed].get('ca', 0) for feed in feed_amounts)
    total_p = sum(feed_amounts[feed] * feed_data[feed].get('p', 0) for feed in feed_amounts)
    total_mg = sum(feed_amounts[feed] * feed_data[feed].get('mg', 0) for feed in feed_amounts)
    
    # Hitung persentase dalam campuran
    avg_protein = total_protein / total_amount
    avg_tdn = total_tdn / total_amount
    avg_ca = total_ca / total_amount
    avg_p = total_p / total_amount
    avg_mg = total_mg / total_amount
    
    return avg_protein, avg_tdn, avg_ca, avg_p, avg_mg, total_cost, total_amount

# Remove duplicate definitions of save_formula to avoid ambiguity.

# Judul aplikasi
st.title("Aplikasi Perhitungan Ransum Ruminansia")
st.subheader("Sapi, Kambing, Domba")

# Data contoh untuk berbagai jenis pakan (tambahkan kandungan mineral)
data_pakan_default = {
    "Sapi": {
        "Nama Pakan": [
            # Hijauan
            "Rumput Gajah", "Rumput Raja", "Rumput Benggala", "Rumput Setaria", "Rumput Odot", 
            "Alang-alang", "Rumput Lapangan",
            # Limbah Pertanian
            "Jerami Padi", "Jerami Jagung", "Jerami Kedelai", "Pucuk Tebu", "Kulit Singkong",
            "Daun Singkong", "Daun Ubi Jalar", "Klobot Jagung",
            # Sumber Protein
            "Bungkil Kedelai", "Bungkil Kelapa", "Bungkil Inti Sawit", "Ampas Tahu", "Tepung Ikan",
            "Daun Gamal", "Daun Lamtoro", "Daun Kaliandra", "Daun Indigofera",
            # Konsentrat & By-product
            "Dedak Padi", "Dedak Jagung", "Onggok", "Molases", "Pollard", "Ampas Bir", 
            "Kulit Kopi", "Kulit Kakao", "Bungkil Biji Kapok"
        ],
        "Protein (%)": [
            # Hijauan
            10.2, 9.1, 8.7, 8.2, 11.5, 6.5, 7.5,
            # Limbah Pertanian
            4.3, 5.8, 6.2, 5.5, 4.8, 16.7, 12.0, 3.8,
            # Sumber Protein
            44.0, 21.0, 16.5, 23.5, 55.0, 25.2, 23.7, 24.0, 27.9,
            # Konsentrat & By-product
            12.9, 9.0, 2.5, 4.0, 17.0, 27.0, 10.0, 15.0, 31.0
        ],
        "TDN (%)": [
            # Hijauan
            51.0, 52.0, 50.0, 48.0, 54.0, 42.0, 45.0,
            # Limbah Pertanian
            39.0, 54.0, 45.0, 43.0, 68.0, 65.0, 60.0, 48.0,
            # Sumber Protein
            75.0, 78.0, 73.0, 79.0, 72.0, 65.0, 68.0, 60.0, 72.0,
            # Konsentrat & By-product
            65.0, 73.0, 83.0, 76.0, 70.0, 65.0, 58.0, 62.0, 70.0
        ],
        "Ca (%)": [
            # Hijauan
            0.48, 0.50, 0.46, 0.45, 0.52, 0.30, 0.42,
            # Limbah Pertanian
            0.18, 0.28, 0.25, 0.22, 0.30, 1.20, 0.85, 0.20,
            # Sumber Protein
            0.27, 0.20, 0.25, 0.25, 5.50, 1.20, 1.35, 1.05, 1.45,
            # Konsentrat & By-product
            0.10, 0.05, 0.18, 0.12, 0.14, 0.30, 0.55, 0.48, 0.30
        ],
        "P (%)": [
            # Hijauan
            0.23, 0.25, 0.22, 0.20, 0.26, 0.15, 0.17,
            # Limbah Pertanian
            0.08, 0.12, 0.16, 0.10, 0.12, 0.28, 0.18, 0.10,
            # Sumber Protein
            0.62, 0.65, 0.54, 0.29, 2.80, 0.27, 0.22, 0.28, 0.33,
            # Konsentrat & By-product
            1.27, 0.90, 0.10, 0.10, 0.95, 0.55, 0.20, 0.23, 0.45
        ],
        "Mg (%)": [
            # Hijauan
            0.26, 0.25, 0.22, 0.20, 0.24, 0.18, 0.18,
            # Limbah Pertanian
            0.10, 0.15, 0.18, 0.12, 0.14, 0.32, 0.26, 0.10,
            # Sumber Protein
            0.27, 0.32, 0.28, 0.22, 0.15, 0.34, 0.38, 0.33, 0.42,
            # Konsentrat & By-product
            0.95, 0.45, 0.08, 0.05, 0.65, 0.16, 0.22, 0.28, 0.38
        ],
        "Fe (ppm)": [
            # Hijauan
            120, 115, 105, 100, 125, 95, 140,
            # Limbah Pertanian
            185, 160, 175, 150, 165, 220, 180, 110,
            # Sumber Protein
            150, 155, 145, 110, 320, 210, 180, 195, 195,
            # Konsentrat & By-product
            310, 240, 120, 85, 290, 180, 160, 175, 220
        ],
        "Cu (ppm)": [
            # Hijauan
            11, 10, 9, 8, 12, 7, 8,
            # Limbah Pertanian
            5, 7, 8, 6, 7, 15, 12, 5,
            # Sumber Protein
            15, 17, 14, 8, 25, 15, 12, 14, 14,
            # Konsentrat & By-product
            12, 11, 5, 9, 14, 15, 10, 11, 18
        ],
        "Zn (ppm)": [
            # Hijauan
            27, 25, 23, 22, 30, 18, 22,
            # Limbah Pertanian
            18, 22, 25, 20, 23, 32, 28, 16,
            # Sumber Protein
            55, 50, 45, 40, 85, 35, 42, 38, 45,
            # Konsentrat & By-product
            70, 58, 20, 15, 65, 45, 32, 38, 52
        ],
        "Harga (Rp/kg)": [
            # Hijauan
            1500, 1400, 1200, 1100, 1600, 800, 800,
            # Limbah Pertanian
            1000, 1200, 1500, 900, 1800, 2000, 1800, 800,
            # Sumber Protein
            7500, 5000, 4500, 1800, 12000, 2000, 1500, 1800, 2500,
            # Konsentrat & By-product
            2500, 2200, 1500, 3000, 4500, 3500, 2000, 2200, 4000
        ]
    },
    
    "Kambing": {
        "Nama Pakan": [
            # Hijauan
            "Daun Gamal", "Daun Lamtoro", "Daun Kaliandra", "Daun Kelor", "Daun Turi", 
            "Daun Singkong", "Rumput Lapangan", "Rumput Odot", "Rumput Gajah Mini",
            # Limbah Pertanian
            "Kulit Pisang", "Kulit Singkong", "Daun Pepaya", "Daun Nanas", "Jerami Kacang Tanah",
            # Sumber Protein
            "Konsentrat", "Ampas Kecap", "Bungkil Kelapa", "Ampas Tahu", "Daun Indigofera",
            # By-products
            "Daun Nangka", "Dedak Padi", "Onggok", "Kulit Kopi", "Ampas Nanas", "Ampas Kelapa"
        ],
        "Protein (%)": [
            # Hijauan
            25.2, 23.7, 24.0, 27.0, 25.5, 16.7, 7.5, 11.5, 12.0,
            # Limbah Pertanian
            3.8, 4.8, 20.5, 9.8, 14.0,
            # Sumber Protein
            16.0, 21.0, 21.0, 23.5, 27.9,
            # By-products
            14.5, 12.9, 2.5, 10.0, 4.5, 5.0
        ],
        "TDN (%)": [
            # Hijauan
            65.0, 68.0, 60.0, 65.0, 62.0, 65.0, 45.0, 54.0, 56.0,
            # Limbah Pertanian
            58.0, 68.0, 60.0, 55.0, 60.0,
            # Sumber Protein
            70.0, 75.0, 78.0, 79.0, 72.0,
            # By-products
            57.0, 65.0, 83.0, 58.0, 70.0, 75.0
        ],
        "Ca (%)": [
            # Hijauan
            1.2, 1.35, 1.05, 2.0, 1.3, 1.2, 0.42, 0.52, 0.50,
            # Limbah Pertanian
            0.32, 0.30, 0.95, 0.40, 0.52,
            # Sumber Protein
            0.8, 0.72, 0.20, 0.25, 1.45,
            # By-products
            0.95, 0.10, 0.18, 0.55, 0.25, 0.35
        ],
        "P (%)": [
            # Hijauan
            0.27, 0.22, 0.28, 0.32, 0.25, 0.28, 0.17, 0.26, 0.25,
            # Limbah Pertanian
            0.16, 0.12, 0.24, 0.15, 0.22,
            # Sumber Protein
            0.45, 0.48, 0.65, 0.29, 0.33,
            # By-products
            0.18, 1.27, 0.10, 0.20, 0.18, 0.22
        ],
        "Mg (%)": [
            # Hijauan
            0.34, 0.38, 0.33, 0.45, 0.35, 0.32, 0.18, 0.24, 0.23,
            # Limbah Pertanian
            0.20, 0.14, 0.30, 0.22, 0.28,
            # Sumber Protein
            0.32, 0.35, 0.32, 0.22, 0.42,
            # By-products
            0.25, 0.95, 0.08, 0.22, 0.18, 0.20
        ],
        "Fe (ppm)": [
            # Hijauan
            210, 180, 195, 250, 185, 220, 140, 125, 130,
            # Limbah Pertanian
            115, 165, 180, 120, 165,
            # Sumber Protein
            250, 280, 155, 110, 195,
            # By-products
            165, 310, 120, 160, 130, 150
        ],
        "Cu (ppm)": [
            # Hijauan
            15, 12, 14, 18, 13, 15, 8, 12, 12,
            # Limbah Pertanian
            6, 7, 12, 8, 10,
            # Sumber Protein
            18, 20, 17, 8, 14,
            # By-products
            10, 12, 5, 10, 7, 9
        ],
        "Zn (ppm)": [
            # Hijauan
            35, 42, 38, 48, 36, 32, 22, 30, 32,
            # Limbah Pertanian
            18, 23, 38, 25, 30,
            # Sumber Protein
            65, 70, 50, 40, 45,
            # By-products
            38, 70, 20, 32, 28, 25
        ],
        "Harga (Rp/kg)": [
            # Hijauan
            2000, 1500, 1800, 2500, 1700, 2000, 800, 1600, 1700,
            # Limbah Pertanian
            500, 1800, 1500, 700, 1200,
            # Sumber Protein
            5000, 4500, 5000, 1800, 2500,
            # By-products
            1000, 2500, 1500, 2000, 1000, 1200
        ]
    },
    
    "Domba": {
        "Nama Pakan": [
            # Hijauan
            "Rumput Gajah", "Rumput Benggala", "Rumput Lapangan", "Rumput Odot", "Daun Turi",
            "Rumput Setaria", "Alang-alang", "Rumput Raja",
            # Limbah Pertanian
            "Jerami Padi", "Jerami Kedelai", "Jerami Jagung", "Daun Singkong", "Kulit Singkong",
            # Sumber Protein
            "Daun Gamal", "Konsentrat", "Daun Indigofera", "Ampas Tahu", "Bungkil Kelapa",
            "Bungkil Inti Sawit", "Tepung Ikan", 
            # By-products
            "Dedak Padi", "Onggok", "Kulit Kopi", "Ampas Nanas", "Ampas Kelapa"
        ],
        "Protein (%)": [
            # Hijauan
            10.2, 8.7, 7.5, 11.5, 25.5, 8.2, 6.5, 9.1,
            # Limbah Pertanian
            4.3, 6.2, 5.8, 16.7, 4.8,
            # Sumber Protein
            25.2, 16.0, 27.9, 23.5, 21.0, 16.5, 55.0,
            # By-products
            12.9, 2.5, 10.0, 4.5, 5.0
        ],
        "TDN (%)": [
            # Hijauan
            51.0, 50.0, 45.0, 54.0, 62.0, 48.0, 42.0, 52.0,
            # Limbah Pertanian
            39.0, 45.0, 54.0, 65.0, 68.0,
            # Sumber Protein
            65.0, 70.0, 72.0, 79.0, 78.0, 73.0, 72.0,
            # By-products
            65.0, 83.0, 58.0, 70.0, 75.0
        ],
        "Ca (%)": [
            # Hijauan
            0.48, 0.46, 0.42, 0.52, 1.3, 0.45, 0.30, 0.50,
            # Limbah Pertanian
            0.18, 0.25, 0.28, 1.2, 0.30,
            # Sumber Protein
            1.2, 0.8, 1.45, 0.25, 0.20, 0.25, 5.50,
            # By-products
            0.10, 0.18, 0.55, 0.25, 0.35
        ],
        "P (%)": [
            # Hijauan
            0.23, 0.22, 0.17, 0.26, 0.25, 0.20, 0.15, 0.25,
            # Limbah Pertanian
            0.08, 0.16, 0.12, 0.28, 0.12,
            # Sumber Protein
            0.27, 0.45, 0.33, 0.29, 0.65, 0.54, 2.80,
            # By-products
            1.27, 0.10, 0.20, 0.18, 0.22
        ],
        "Mg (%)": [
            # Hijauan
            0.26, 0.22, 0.18, 0.24, 0.35, 0.20, 0.18, 0.25,
            # Limbah Pertanian
            0.10, 0.18, 0.15, 0.32, 0.14,
            # Sumber Protein
            0.34, 0.32, 0.42, 0.22, 0.32, 0.28, 0.15,
            # By-products
            0.95, 0.08, 0.22, 0.18, 0.20
        ],
        "Fe (ppm)": [
            # Hijauan
            120, 105, 140, 125, 185, 100, 95, 115,
            # Limbah Pertanian
            185, 175, 160, 220, 165,
            # Sumber Protein
            210, 250, 195, 110, 155, 145, 320,
            # By-products
            310, 120, 160, 130, 150
        ],
        "Cu (ppm)": [
            # Hijauan
            11, 9, 8, 12, 13, 8, 7, 10,
            # Limbah Pertanian
            5, 8, 7, 15, 7,
            # Sumber Protein
            15, 18, 14, 8, 17, 14, 25,
            # By-products
            12, 5, 10, 7, 9
        ],
        "Zn (ppm)": [
            # Hijauan
            27, 23, 22, 30, 36, 22, 18, 25,
            # Limbah Pertanian
            18, 25, 22, 32, 23,
            # Sumber Protein
            35, 65, 45, 40, 50, 45, 85,
            # By-products
            70, 20, 32, 28, 25
        ],
        "Harga (Rp/kg)": [
            # Hijauan
            1500, 1200, 800, 1600, 1700, 1100, 800, 1400,
            # Limbah Pertanian
            1000, 1500, 1200, 2000, 1800,
            # Sumber Protein
            2000, 5000, 2500, 1800, 5000, 4500, 12000,
            # By-products
            2500, 1500, 2000, 1000, 1200
        ]
    }
}

# Tambahkan data mineral supplement
mineral_supplements = {
    "Nama Pakan": ["Kapur (CaCO3)", "Dikalsium Fosfat", "Premix Mineral", "Garam (NaCl)", "MgO", 
                  "Mineral Blok", "Tepung Tulang", "ZnSO4", "CuSO4", "Fe2(SO4)3", "Belerang (S)"],
    "Protein (%)": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0],
    "TDN (%)": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Ca (%)": [38.0, 23.0, 15.0, 0.0, 0.0, 18.0, 30.0, 0.0, 0.0, 0.0, 0.0],
    "P (%)": [0.0, 18.0, 8.0, 0.0, 0.0, 9.0, 14.0, 0.0, 0.0, 0.0, 0.0],
    "Mg (%)": [0.0, 0.0, 5.0, 0.0, 54.0, 3.0, 0.5, 0.0, 0.0, 0.0, 0.0],
    "Fe (ppm)": [0, 0, 5000, 0, 0, 3500, 800, 0, 0, 200000, 0],
    "Cu (ppm)": [0, 0, 1500, 0, 0, 1200, 0, 0, 250000, 0, 0],
    "Zn (ppm)": [0, 0, 8000, 0, 0, 5000, 0, 350000, 0, 0, 0],
    "Harga (Rp/kg)": [3000, 8000, 15000, 2500, 9000, 12000, 10000, 25000, 30000, 18000, 7000]
}

# Kebutuhan nutrisi berdasarkan umur dan tujuan produksi
kebutuhan_nutrisi_umur = {
    "Sapi Potong": {
        "Pedet (<6 bulan)": {
            "Protein (%)": 18.0, "TDN (%)": 70.0,
            "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.10,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Muda (6-12 bulan)": {
            "Protein (%)": 15.0, "TDN (%)": 68.0,
            "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.10,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Dewasa (>12 bulan)": {
            "Protein (%)": 12.0, "TDN (%)": 65.0,
            "Ca (%)": 0.40, "P (%)": 0.25, "Mg (%)": 0.10,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Bunting": {
            "Protein (%)": 14.0, "TDN (%)": 68.0,
            "Ca (%)": 0.50, "P (%)": 0.35, "Mg (%)": 0.15,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Penggemukan": {
            "Protein (%)": 14.0, "TDN (%)": 70.0,
            "Ca (%)": 0.50, "P (%)": 0.35, "Mg (%)": 0.10,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        }
    },
    
    "Sapi Perah": {
        "Pedet (<6 bulan)": {
            "Protein (%)": 20.0, "TDN (%)": 72.0,
            "Ca (%)": 0.80, "P (%)": 0.50, "Mg (%)": 0.15,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Dara (6-12 bulan)": {
            "Protein (%)": 16.0, "TDN (%)": 68.0,
            "Ca (%)": 0.65, "P (%)": 0.45, "Mg (%)": 0.15,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Dewasa Kering": {
            "Protein (%)": 12.0, "TDN (%)": 60.0,
            "Ca (%)": 0.45, "P (%)": 0.30, "Mg (%)": 0.20,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Laktasi Awal": {
            "Protein (%)": 18.0, "TDN (%)": 75.0,
            "Ca (%)": 0.80, "P (%)": 0.50, "Mg (%)": 0.25,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 60
        },
        "Laktasi Tengah": {
            "Protein (%)": 16.0, "TDN (%)": 70.0,
            "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.20,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 50
        },
        "Laktasi Akhir": {
            "Protein (%)": 14.0, "TDN (%)": 65.0,
            "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.20,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Bunting": {
            "Protein (%)": 15.0, "TDN (%)": 65.0,
            "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.20,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 50
        }
    },
    
    "Kambing Potong": {
        "Pedet (<3 bulan)": {
            "Protein (%)": 18.0, "TDN (%)": 70.0,
            "Ca (%)": 0.70, "P (%)": 0.40, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Muda (3-8 bulan)": {
            "Protein (%)": 16.0, "TDN (%)": 65.0,
            "Ca (%)": 0.60, "P (%)": 0.35, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Dewasa (>8 bulan)": {
            "Protein (%)": 14.0, "TDN (%)": 60.0,
            "Ca (%)": 0.35, "P (%)": 0.25, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Bunting": {
            "Protein (%)": 15.0, "TDN (%)": 65.0,
            "Ca (%)": 0.50, "P (%)": 0.35, "Mg (%)": 0.12,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Penggemukan": {
            "Protein (%)": 16.0, "TDN (%)": 68.0,
            "Ca (%)": 0.45, "P (%)": 0.30, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 35
        }
    },
    
    "Kambing Perah": {
        "Pedet (<3 bulan)": {
            "Protein (%)": 20.0, "TDN (%)": 72.0,
            "Ca (%)": 0.80, "P (%)": 0.45, "Mg (%)": 0.12,
            "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Dara (3-8 bulan)": {
            "Protein (%)": 17.0, "TDN (%)": 68.0,
            "Ca (%)": 0.65, "P (%)": 0.40, "Mg (%)": 0.12,
            "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Dewasa Kering": {
            "Protein (%)": 12.0, "TDN (%)": 60.0,
            "Ca (%)": 0.35, "P (%)": 0.25, "Mg (%)": 0.15,
            "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Laktasi Awal": {
            "Protein (%)": 18.0, "TDN (%)": 73.0,
            "Ca (%)": 0.80, "P (%)": 0.50, "Mg (%)": 0.25,
            "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 50
        },
        "Laktasi Tengah": {
            "Protein (%)": 16.0, "TDN (%)": 70.0,
            "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.20,
            "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 45
        },
        "Laktasi Akhir": {
            "Protein (%)": 14.0, "TDN (%)": 65.0,
            "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.15,
            "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 40
        },
        "Bunting": {
            "Protein (%)": 16.0, "TDN (%)": 67.0,
            "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.18,
            "Fe (ppm)": 45, "Cu (ppm)": 10, "Zn (ppm)": 45
        }
    },
    
    "Domba Potong": {
        "Pedet (<3 bulan)": {
            "Protein (%)": 18.0, "TDN (%)": 68.0,
            "Ca (%)": 0.65, "P (%)": 0.40, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 30
        },
        "Muda (3-8 bulan)": {
            "Protein (%)": 16.0, "TDN (%)": 65.0,
            "Ca (%)": 0.55, "P (%)": 0.35, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 30
        },
        "Dewasa (>8 bulan)": {
            "Protein (%)": 13.0, "TDN (%)": 60.0,
            "Ca (%)": 0.35, "P (%)": 0.25, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 30
        },
        "Bunting": {
            "Protein (%)": 14.0, "TDN (%)": 63.0,
            "Ca (%)": 0.45, "P (%)": 0.30, "Mg (%)": 0.12,
            "Fe (ppm)": 45, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Penggemukan": {
            "Protein (%)": 16.0, "TDN (%)": 67.0,
            "Ca (%)": 0.40, "P (%)": 0.30, "Mg (%)": 0.10,
            "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 30
        }
    },
    
    "Domba Perah": {
        "Pedet (<3 bulan)": {
            "Protein (%)": 19.0, "TDN (%)": 70.0,
            "Ca (%)": 0.75, "P (%)": 0.45, "Mg (%)": 0.12,
            "Fe (ppm)": 45, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Dara (3-8 bulan)": {
            "Protein (%)": 16.0, "TDN (%)": 67.0,
            "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.12,
            "Fe (ppm)": 45, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Dewasa Kering": {
            "Protein (%)": 12.0, "TDN (%)": 60.0,
            "Ca (%)": 0.35, "P (%)": 0.25, "Mg (%)": 0.15,
            "Fe (ppm)": 40, "Cu (ppm)": 7, "Zn (ppm)": 30
        },
        "Laktasi Awal": {
            "Protein (%)": 17.0, "TDN (%)": 72.0,
            "Ca (%)": 0.75, "P (%)": 0.48, "Mg (%)": 0.22,
            "Fe (ppm)": 45, "Cu (ppm)": 9, "Zn (ppm)": 45
        },
        "Laktasi Tengah": {
            "Protein (%)": 15.0, "TDN (%)": 68.0,
            "Ca (%)": 0.65, "P (%)": 0.40, "Mg (%)": 0.18,
            "Fe (ppm)": 45, "Cu (ppm)": 8, "Zn (ppm)": 40
        },
        "Laktasi Akhir": {
            "Protein (%)": 13.0, "TDN (%)": 62.0,
            "Ca (%)": 0.55, "P (%)": 0.35, "Mg (%)": 0.15,
            "Fe (ppm)": 40, "Cu (ppm)": 8, "Zn (ppm)": 35
        },
        "Bunting": {
            "Protein (%)": 15.0, "TDN (%)": 65.0,
            "Ca (%)": 0.65, "P (%)": 0.40, "Mg (%)": 0.18,
            "Fe (ppm)": 45, "Cu (ppm)": 8, "Zn (ppm)": 40
        }
    }
}

# Update kebutuhan nutrisi to include gender differences
kebutuhan_nutrisi_gender = {
    "Sapi Potong": {
        "Jantan": {
            "Pedet (<6 bulan)": {
                "Protein (%)": 18.0, "TDN (%)": 70.0,
                "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Muda (6-12 bulan)": {
                "Protein (%)": 15.5, "TDN (%)": 68.0,  # Higher protein for males
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dewasa (>12 bulan)": {
                "Protein (%)": 12.5, "TDN (%)": 65.0,  # Higher protein for males
                "Ca (%)": 0.40, "P (%)": 0.25, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Penggemukan": {
                "Protein (%)": 14.5, "TDN (%)": 72.0,  # Higher energy for males
                "Ca (%)": 0.50, "P (%)": 0.35, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            }
        },
        "Betina": {
            "Pedet (<6 bulan)": {
                "Protein (%)": 18.0, "TDN (%)": 70.0,
                "Ca (%)": 0.70, "P (%)": 0.45, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Muda (6-12 bulan)": {
                "Protein (%)": 14.5, "TDN (%)": 67.0,
                "Ca (%)": 0.60, "P (%)": 0.40, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Dewasa (>12 bulan)": {
                "Protein (%)": 11.5, "TDN (%)": 63.0,
                "Ca (%)": 0.40, "P (%)": 0.25, "Mg (%)": 0.10,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            },
            "Bunting": {
                "Protein (%)": 14.0, "TDN (%)": 68.0,
                "Ca (%)": 0.50, "P (%)": 0.35, "Mg (%)": 0.15,
                "Fe (ppm)": 50, "Cu (ppm)": 10, "Zn (ppm)": 40
            }
        }
    }
    # Similar structures for other animal types
}

# Add anti-nutrient data to feed database
antinutrisi_info = {
    "Gosipol": {
        "Deskripsi": "Terkandung dalam biji kapas, dapat mengganggu reproduksi pada jantan",
        "Batas Aman": "Sapi: <200 ppm, Domba: <100 ppm, Kambing: <100 ppm"
    },
    "Tanin": {
        "Deskripsi": "Ditemukan pada tanaman legum seperti kaliandra, dapat mengurangi kecernaan protein",
        "Batas Aman": "Sapi: <4%, Domba: <3%, Kambing: <5%"
    },
    "Mimosin": {
        "Deskripsi": "Terdapat pada lamtoro, dapat menyebabkan kerontokan rambut dan gangguan tiroid",
        "Batas Aman": "Sapi: <2%, Domba: <0.5%, Kambing: <1%"
    },
    "HCN": {
        "Deskripsi": "Ditemukan pada singkong, dapat menyebabkan keracunan sianida",
        "Batas Aman": "Semua ruminansia: <50 ppm"
    },
    "Aflatoksin": {
        "Deskripsi": "Kontaminasi jamur pada pakan lembab, beresiko kanker dan kerusakan hati",
        "Batas Aman": "Semua ruminansia: <20 ppb"
    },
    "Saponin": {
        "Deskripsi": "Terdapat pada berbagai legum, dapat menurunkan konsumsi pakan",
        "Batas Aman": "Sapi: <3%, Domba: <2%, Kambing: <3%"
    },
    "Oksalat": {
        "Deskripsi": "Terdapat pada rumput seperti sorgum, mengikat kalsium dan magnesium",
        "Batas Aman": "Semua ruminansia: <2%"
    }
}

# Add anti-nutrient content to selected feeds
antinutrisi_pakan = {
    "Daun Kaliandra": {"Tanin": 2.8, "Saponin": 0.9},
    "Daun Lamtoro": {"Mimosin": 1.2, "Tanin": 0.6},
    "Bungkil Biji Kapok": {"Gosipol": 150, "Tanin": 0.8},
    "Daun Singkong": {"HCN": 30, "Tanin": 0.5},
    "Kulit Singkong": {"HCN": 45},
    "Ampas Tahu": {"Aflatoksin": 5},
    "Dedak Padi": {"Aflatoksin": 10, "Oksalat": 0.8},
    "Kulit Kakao": {"Tanin": 3.2, "Saponin": 1.2}
}

# Add gender selection after jenis_hewan selection
jenis_hewan = st.selectbox(
    "Pilih jenis hewan:", 
    ["Sapi Potong", "Sapi Perah", "Kambing Potong", "Kambing Perah", "Domba Potong", "Domba Perah"]
)

# Add gender selection
jenis_kelamin = st.selectbox(
    "Pilih jenis kelamin:",
    ["Jantan", "Betina"]
)

# Pilih kategori umur hewan (sesuai dengan jenis hewan yang dipilih)
kategori_umur = st.selectbox(
    "Pilih kategori umur/fase produksi:",
    list(kebutuhan_nutrisi_umur[jenis_hewan].keys())
)

# Upload file pakan (opsional)
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
    
    Contoh format data (3 baris pertama):
    
    | Nama Pakan    | Protein (%) | TDN (%) | Ca (%) | P (%) | Fe (ppm) | Harga (Rp/kg) |
    |---------------|-------------|---------|--------|-------|----------|---------------|
    | Rumput Gajah  | 10.2        | 51.0    | 0.48   | 0.23  | 120      | 1500          |
    | Jerami Padi   | 4.3         | 39.0    | 0.18   | 0.08  | 185      | 1000          |
    """)

uploaded_file = st.file_uploader("Upload file CSV atau Excel (XLS/XLSX)", 
                               type=["csv", "xls", "xlsx"])

# Fungsi untuk validasi data pakan
def validasi_data_pakan(df):
    # Kolom minimal yang harus ada
    kolom_wajib = ['Nama Pakan', 'Protein (%)', 'TDN (%)', 'Harga (Rp/kg)']
    
    # Periksa apakah kolom wajib ada
    for kolom in df.columns:
        if kolom not in kolom_wajib:
            return False, f"Kolom '{kolom}' tidak ditemukan dalam data"
    
    # Periksa tipe data
    try:
        # Pastikan kolom numerik bisa dikonversi ke float
        df['Protein (%)'] = df['Protein (%)'].astype(float)
        df['TDN (%)'] = df['TDN (%)'].astype(float)
        df['Harga (Rp/kg)'] = df['Harga (Rp/kg)'].astype(float)
        
        # Periksa kolom mineral jika ada
        if 'Ca (%)' in df.columns: df['Ca (%)'] = df['Ca (%)'].astype(float)
        if 'P (%)' in df.columns: df['P (%)'] = df['P (%)'].astype(float)
        if 'Mg (%)' in df.columns: df['Mg (%)'] = df['Mg (%)'].astype(float)
        if 'Fe (ppm)' in df.columns: df['Fe (ppm)'] = df['Fe (ppm)'].astype(float)
        if 'Cu (ppm)' in df.columns: df['Cu (ppm)'] = df['Cu (ppm)'].astype(float)
        if 'Zn (ppm)' in df.columns: df['Zn (ppm)'] = df['Zn (ppm)'].astype(float)
    except ValueError:
        return False, "Nilai dalam kolom numerik tidak valid"
    
    # Periksa apakah ada data
    if len(df) == 0:
        return False, "File tidak berisi data"
    
    # Tambahkan kolom mineral yang tidak ada dengan nilai default
    kolom_mineral = ['Ca (%)', 'P (%)', 'Mg (%)', 'Fe (ppm)', 'Cu (ppm)', 'Zn (ppm)']
    for kolom in kolom_mineral:
        if kolom not in df.columns:
            df[kolom] = 0.0
    
    return True, df

# Perbaikan validasi data
def validasi_data_pakan_extended(df):
    """Validasi data dengan pengecekan lebih menyeluruh"""
    # Validasi dasar seperti sebelumnya
    valid, result = validasi_data_pakan(df)
    if not valid:
        return valid, result
    
    # Validasi lanjutan
    try:
        # Validasi rentang nilai yang masuk akal
        if (df['Protein (%)'] > 100).any():
            return False, "Protein tidak boleh > 100%"
            
        if (df['TDN (%)'] > 100).any():
            return False, "TDN tidak boleh > 100%"
            
        if (df['Ca (%)'] > 50).any():
            return False, "Kalsium tidak boleh > 50%"
            
        if (df['P (%)'] > 50).any():
            return False, "Fosfor tidak boleh > 50%"
            
        if (df['Harga (Rp/kg)'] < 0).any():
            return False, "Harga tidak boleh negatif"
        
        # Periksa duplikat nama pakan
        if df['Nama Pakan'].duplicated().any():
            return False, "Terdapat duplikat nama pakan"
            
    except Exception as e:
        return False, f"Error validasi: {str(e)}"
        
    return True, df

# Untuk data pakan default, kita perlu memetakan jenis hewan termodifikasi ke data pakan
def get_pakan_category(jenis_hewan):
    if "Sapi" in jenis_hewan:
        return "Sapi"
    elif "Kambing" in jenis_hewan:
        return "Kambing"
    elif "Domba" in jenis_hewan:
        return "Domba"
    return "Sapi"  # Default fallback

# Tambahkan caching untuk mempercepat loading data
@st.cache_data(ttl=3600)
def load_default_data(jenis_hewan_category):
    """Load data pakan default dengan caching untuk meningkatkan performa"""
    return pd.DataFrame(data_pakan_default[jenis_hewan_category])

# Pilih sumber data dan siapkan data pakan
use_default_data = True  # Default ke True
df_pakan = pd.DataFrame()  # Inisialisasi dataframe kosong

if uploaded_file is not None:
    try:
        # Tentukan format file dan baca
        if uploaded_file.name.endswith('.csv'):
            uploaded_df = pd.read_csv(uploaded_file)
        else:
            uploaded_df = pd.read_excel(uploaded_file)
        
        # Validasi data yang diupload
        valid, result = validasi_data_pakan_extended(uploaded_df)
        
        if valid:
            df_pakan = result
            use_default_data = False
            st.success("File berhasil diupload dan divalidasi!")
        else:
            st.error(f"Data tidak valid: {result}")
            st.warning("Menggunakan data default sistem sebagai pengganti.")
            pakan_category = get_pakan_category(jenis_hewan)
            df_pakan = load_default_data(pakan_category)
    except Exception as e:
        st.error(f"Error saat membaca file: {e}")
        st.warning("Menggunakan data default sistem sebagai pengganti.")
        pakan_category = get_pakan_category(jenis_hewan)
        df_pakan = load_default_data(pakan_category)
else:
    # Gunakan data default jika tidak ada file yang diupload
    pakan_category = get_pakan_category(jenis_hewan)
    df_pakan = load_default_data(pakan_category)

# Tampilkan sumber data yang digunakan
if use_default_data:
    st.info(f"📋 Menggunakan data default untuk pakan **{get_pakan_category(jenis_hewan)}**")
else:
    st.info("📤 Menggunakan data pakan dari file yang diupload")

# Tampilkan tabel data pakan dengan opsi filter
st.subheader("Tabel Data Pakan")

# Tambahkan filter kategori pakan
if use_default_data:
    # Filter berdasarkan kategori untuk data default
    kategori_pakan = ["Semua", "Hijauan", "Limbah Pertanian", "Sumber Protein", "Konsentrat & By-product"]
    selected_kategori = st.selectbox("Filter berdasarkan kategori:", kategori_pakan)
    
    if selected_kategori != "Semua":
        # Tentukan indeks untuk setiap kategori berdasarkan urutan data di data_pakan_default
        pakan_category = get_pakan_category(jenis_hewan)
        if pakan_category == "Sapi":
            kategori_indeks = {
                "Hijauan": range(0, 7),
                "Limbah Pertanian": range(7, 15),
                "Sumber Protein": range(15, 24),
                "Konsentrat & By-product": range(24, 33)
            }
        elif pakan_category == "Kambing":
            kategori_indeks = {
                "Hijauan": range(0, 9),
                "Limbah Pertanian": range(9, 14),
                "Sumber Protein": range(14, 19),
                "Konsentrat & By-product": range(19, 25)
            }
        elif pakan_category == "Domba":
            kategori_indeks = {
                "Hijauan": range(0, 8),
                "Limbah Pertanian": range(8, 13),
                "Sumber Protein": range(13, 20),
                "Konsentrat & By-product": range(20, 25)
            }
            
        # Filter dataframe berdasarkan indeks
        filtered_df = df_pakan.iloc[kategori_indeks[selected_kategori]]
        
        # Tampilkan dengan harga yang bisa diedit
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
        
        # Update dataframe dengan nilai yang diedit
        if edited_df is not None:
            for i, row in edited_df.iterrows():
                df_pakan.loc[df_pakan['Nama Pakan'] == row['Nama Pakan'], 'Harga (Rp/kg)'] = row['Harga (Rp/kg)']
    else:
        # Tampilkan semua data dengan harga yang bisa diedit
        edited_df = st.data_editor(
            df_pakan,
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
        
        # Update dataframe dengan nilai yang diedit
        if edited_df is not None:
            for i, row in edited_df.iterrows():
                df_pakan.loc[df_pakan['Nama Pakan'] == row['Nama Pakan'], 'Harga (Rp/kg)'] = row['Harga (Rp/kg)']
else:
    # Untuk data yang diupload, tampilkan semua dengan harga yang bisa diedit
    edited_df = st.data_editor(
        df_pakan,
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
    
    # Update dataframe dengan nilai yang diedit
    if edited_df is not None:
        for i, row in edited_df.iterrows():
            df_pakan.loc[df_pakan['Nama Pakan'] == row['Nama Pakan'], 'Harga (Rp/kg)'] = row['Harga (Rp/kg)']

# Tambahkan informasi cara penggunaan
st.info("💡 Klik pada nilai harga untuk mengedit secara langsung. Perubahan akan otomatis tersimpan untuk perhitungan.")

# Tambahkan di bagian setelah menampilkan dataframe pakan

# Tambahkan pencarian bahan pakan
st.subheader("Cari Bahan Pakan")
search_term = st.text_input("Masukkan kata kunci:")

if search_term:
    # Cari dalam nama pakan (case insensitive)
    search_results = df_pakan[df_pakan['Nama Pakan'].str.lower().str.contains(search_term.lower())]
    
    if not search_results.empty:
        st.success(f"Ditemukan {len(search_results)} hasil pencarian")
        st.dataframe(search_results)
        
        # Tampilkan visualisasi perbandingan nutrisi
        if len(search_results) > 1 and len(search_results) <= 10:  # Batasi untuk perbandingan yang masuk akal
            st.subheader("Perbandingan Nutrisi")
            
            # Persiapkan data untuk chart
            chart_data = pd.melt(
                search_results[['Nama Pakan', 'Protein (%)', 'TDN (%)', 'Ca (%)', 'P (%)']],
                id_vars=['Nama Pakan'],
                var_name='Nutrisi',
                value_name='Nilai'
            )
            
            # Buat chart perbandingan
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

# Tambahkan tombol untuk menyimpan data default ke file
if use_default_data:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template CSV"):
            pakan_category = get_pakan_category(jenis_hewan)
            csv = pd.DataFrame(data_pakan_default[pakan_category]).to_csv(index=False)
            st.download_button(
                label="Download CSV Template",
                data=csv,
                file_name=f"template_pakan_{jenis_hewan}.csv",
                mime="text/csv"
            )
    with col2:
        if st.button("Download Template Excel"):
            pakan_category = get_pakan_category(jenis_hewan)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.DataFrame(data_pakan_default[pakan_category]).to_excel(writer, index=False)
            st.download_button(
                label="Download Excel Template",
                data=output.getvalue(),
                file_name=f"template_pakan_{jenis_hewan}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Pisahkan fungsi untuk kalkulasi nutrisi
def calculate_nutrition_content(feed_data, feed_amounts):
    """Menghitung kandungan nutrisi dari kombinasi pakan"""
    total_amount = sum(feed_amounts.values())
    
    if total_amount <= 0:
        return None, None, None, None, None, None, None
        
    total_protein = sum(feed_amounts[feed] * feed_data[feed]['protein'] for feed in feed_amounts)
    total_tdn = sum(feed_amounts[feed] * feed_data[feed]['tdn'] for feed in feed_amounts)
    total_ca = sum(feed_amounts[feed] * feed_data[feed].get('ca', 0) for feed in feed_amounts)
    total_p = sum(feed_amounts[feed] * feed_data[feed].get('p', 0) for feed in feed_amounts)
    total_mg = sum(feed_amounts[feed] * feed_data[feed].get('mg', 0) for feed in feed_amounts)
    total_cost = sum(feed_amounts[feed] * feed_data[feed]['harga'] for feed in feed_amounts)
    
    # Hitung persentase dalam campuran
    avg_protein = total_protein / total_amount
    avg_tdn = total_tdn / total_amount
    avg_ca = total_ca / total_amount
    avg_p = total_p / total_amount
    avg_mg = total_mg / total_amount
    
    return avg_protein, avg_tdn, avg_ca, avg_p, avg_mg, total_cost, total_amount

# Tambahkan tab untuk memilih mode aplikasi
mode = st.sidebar.radio("Mode Aplikasi", ["Formulasi Manual", "Optimalisasi Otomatis", "Mineral Supplement"])

if mode == "Formulasi Manual":
    # Pilih bahan pakan dari tabel (multi-select)
    st.subheader("Pilih Kombinasi Bahan Pakan")
    if not df_pakan.empty and 'Nama Pakan' in df_pakan.columns:
        selected_feeds = st.multiselect("Pilih bahan pakan:", df_pakan['Nama Pakan'].tolist())
        
        # Container untuk input jumlah pakan
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
    else:
        st.error("Data pakan tidak tersedia. Harap upload file dengan format yang benar.")

    # Tampilkan kebutuhan nutrisi hewan berdasarkan umur
    st.subheader("Kebutuhan Nutrisi Berdasarkan Umur")
    st.info(f"""
    **{jenis_hewan} - {kategori_umur}**
    - Protein: {kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Protein (%)']}%
    - TDN: {kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['TDN (%)']}%
    """)

    # Perhitungan
    if st.button("Hitung Ransum"):
        if not selected_feeds:
            st.error("Silakan pilih minimal satu bahan pakan.")
        else:
            # Hitung total pakan, protein, TDN, dan harga
            total_amount = sum(feed_amounts.values())
            
            if total_amount <= 0:
                st.error("Total jumlah pakan harus lebih dari 0 kg.")
            else:
                avg_protein, avg_tdn, avg_ca, avg_p, avg_mg, total_cost, total_amount = calculate_nutrition_content(feed_data, feed_amounts)
                
                # Kebutuhan nutrisi berdasarkan umur
                required_protein = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Protein (%)']
                required_tdn = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['TDN (%)']
                
                # Tampilkan hasil
                st.subheader("Hasil Perhitungan")
                
                # Tampilkan tabel komposisi pakan
                composition_data = {
                    'Bahan Pakan': list(feed_amounts.keys()),
                    'Jumlah (kg)': [feed_amounts[feed] for feed in feed_amounts],
                    'Protein (kg)': [feed_amounts[feed] * feed_data[feed]['protein'] / 100 for feed in feed_amounts],
                    'TDN (kg)': [feed_amounts[feed] * feed_data[feed]['tdn'] / 100 for feed in feed_amounts],
                    'Biaya (Rp)': [feed_amounts[feed] * feed_data[feed]['harga'] for feed in feed_amounts]
                }
                
                df_composition = pd.DataFrame(composition_data)
                df_composition.loc['Total'] = [
                    'Total',
                    total_amount,
                    sum(composition_data['Protein (kg)']),
                    sum(composition_data['TDN (kg)']),
                    total_cost
                ]
                
                st.dataframe(df_composition)
                
                # Tampilkan ringkasan nutrisi
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
                
                st.subheader("Biaya Ransum")
                st.metric("Total Biaya", f"Rp {total_cost:,.2f}")
                st.metric("Biaya per kg", f"Rp {(total_cost / total_amount):,.2f}" if total_amount > 0 else "Rp 0")
                
                # Saran perbaikan jika tidak memenuhi kebutuhan
                if avg_protein < required_protein or avg_tdn < required_tdn:
                    st.subheader("Saran Perbaikan Ransum")
                    
                    if avg_protein < required_protein:
                        high_protein_feeds = df_pakan[df_pakan['Protein (%)'] > required_protein].sort_values('Protein (%)', ascending=False)
                        if not high_protein_feeds.empty:
                            st.write("Untuk meningkatkan protein, tambahkan:")
                            for _, feed in high_protein_feeds.head(3).iterrows():
                                st.write(f"- {feed['Nama Pakan']} (Protein: {feed['Protein (%)']}%, TDN: {feed['TDN (%)']}%)")

                # Set result_calculated flag
                result_calculated = True
                
                # Tambahkan opsi untuk menyimpan hasil formula
                if result_calculated:
                    st.subheader("Simpan Formula Ransum")
                    saved_name = st.text_input("Nama formula ransum:", 
                                              value=f"{jenis_hewan}_{kategori_umur}_Formula_{len(selected_feeds)}_bahan")
                    
                    if st.button("Simpan Formula"):
                        if saved_name:
                            save_formula(saved_name, selected_feeds, feed_amounts, jenis_hewan, kategori_umur)
                            st.success(f"Formula '{saved_name}' berhasil disimpan!")
                        else:
                            st.error("Masukkan nama untuk formula")
                    
                    # Opsi ekspor hasil perhitungan
                    st.subheader("Ekspor Hasil")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'df_composition' in locals():
                            csv_result = df_composition.to_csv(index=False)
                            st.download_button(
                                label="Download Hasil CSV",
                                data=csv_result,
                                file_name=f"ransum_{jenis_hewan}_{kategori_umur}.csv",
                                mime="text/csv"
                            )
                    
                    with col2:
                        if 'df_composition' in locals():
                            # Generate Excel dengan hasil lengkap
                            excel_buffer = io.BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                # Tab 1: Komposisi ransum
                                df_composition.to_excel(writer, sheet_name='Komposisi Ransum', index=False)
                                
                                # Tab 2: Info kebutuhan nutrisi
                                pd.DataFrame({
                                    'Nutrisi': ['Protein (%)', 'TDN (%)', 'Ca (%)', 'P (%)', 'Mg (%)', 
                                               'Fe (ppm)', 'Cu (ppm)', 'Zn (ppm)'],
                                    'Kebutuhan': [
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Protein (%)'],
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['TDN (%)'],
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Ca (%)'],
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['P (%)'],
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Mg (%)'],
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Fe (ppm)'],
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Cu (ppm)'],
                                        kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Zn (ppm)'],
                                    ],
                                    'Hasil Ransum': [
                                        avg_protein, avg_tdn, avg_ca, avg_p, avg_mg, 
                                        'Tidak dihitung', 'Tidak dihitung', 'Tidak dihitung'
                                    ],
                                    'Status': [
                                        'Memenuhi' if avg_protein >= required_protein else 'Kurang',
                                        'Memenuhi' if avg_tdn >= required_tdn else 'Kurang',
                                        'Memenuhi' if avg_ca >= kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Ca (%)'] else 'Kurang',
                                        'Memenuhi' if avg_p >= kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['P (%)'] else 'Kurang',
                                        'Memenuhi' if avg_mg >= kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Mg (%)'] else 'Kurang',
                                        'Tidak dievaluasi', 'Tidak dievaluasi', 'Tidak dievaluasi'
                                    ]
                                }).to_excel(writer, sheet_name='Kebutuhan Nutrisi', index=False)
                                
                                # Tab 3: Info hewan
                                pd.DataFrame({
                                    'Info': ['Jenis Hewan', 'Kategori Umur', 'Tanggal Perhitungan'],
                                    'Nilai': [jenis_hewan, kategori_umur, pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
                                }).to_excel(writer, sheet_name='Info Hewan', index=False)
                            
                            st.download_button(
                                label="Download Laporan Excel Lengkap",
                                data=excel_buffer.getvalue(),
                                file_name=f"laporan_ransum_{jenis_hewan}_{kategori_umur}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                # Add this to the result section after nutrient analysis is complete

                # Anti-nutrient analysis
                if 'df_composition' in locals():
                    st.subheader("Analisis Anti-Nutrisi")
                    
                    # Check for anti-nutrients in selected feeds
                    antinutrisi_terdeteksi = {}
                    
                    for feed in selected_feeds:
                        if feed in antinutrisi_pakan:
                            for nutrient, value in antinutrisi_pakan[feed].items():
                                if nutrient not in antinutrisi_terdeteksi:
                                    antinutrisi_terdeteksi[nutrient] = 0
                                
                                # Calculate weighted contribution based on feed amount
                                antinutrisi_terdeteksi[nutrient] += value * feed_amounts[feed] / total_amount
                    
                    if antinutrisi_terdeteksi:
                        st.warning("⚠️ Terdeteksi anti-nutrisi dalam ransum:")
                        
                        for nutrient, level in antinutrisi_terdeteksi.items():
                            st.write(f"**{nutrient}**: {level:.2f} unit")
                            st.write(f"*{antinutrisi_info[nutrient]['Deskripsi']}*")
                            st.write(f"Batas aman: {antinutrisi_info[nutrient]['Batas Aman']}")
                            
                            # Special warnings for gender-specific anti-nutrients
                            if nutrient == "Gosipol" and jenis_kelamin == "Jantan":
                                st.error("⚠️ PERHATIAN: Gosipol dapat menyebabkan gangguan reproduksi pada jantan!")
                            
                        # Add recommendations for mitigating anti-nutrient effects
                        st.subheader("Rekomendasi Mitigasi Anti-Nutrisi")
                        
                        if "Tanin" in antinutrisi_terdeteksi and antinutrisi_terdeteksi["Tanin"] > 2:
                            st.write("- Tambahkan binder/pengikat tanin seperti Polyethylene Glycol (PEG)")
                            st.write("- Lakukan perendaman atau penjemuran bahan pakan untuk menurunkan kadar tanin")
                        
                        if "HCN" in antinutrisi_terdeteksi:
                            st.write("- Pastikan singkong dikeringkan dengan baik sebelum diberikan")
                            st.write("- Proses pemanasan dapat mengurangi kadar HCN")
                        
                        if "Mimosin" in antinutrisi_terdeteksi:
                            st.write("- Campur lamtoro dengan pakan lain agar tidak melebihi 30% dari total ransum")
                            st.write("- Pilih varietas lamtoro rendah mimosin jika tersedia")
                        
                        if "Aflatoksin" in antinutrisi_terdeteksi:
                            st.write("- Tambahkan binder aflatoksin seperti clay mineral atau yeast cell wall")
                            st.write("- Pastikan penyimpanan pakan dalam kondisi kering dan tidak lembab")
                    else:
                        st.success("✓ Tidak terdeteksi anti-nutrisi dalam ransum yang dipilih")

elif mode == "Optimalisasi Otomatis":
    st.header("Optimalisasi Ransum")
    st.write("Mengoptimalkan komposisi pakan untuk memenuhi kebutuhan nutrisi dengan biaya minimal")
    
    # Pilih bahan pakan yang tersedia untuk optimasi
    available_feeds = st.multiselect(
        "Pilih bahan pakan yang tersedia:", 
        df_pakan['Nama Pakan'].tolist(), 
        default=df_pakan['Nama Pakan'].tolist()[:3]
    )
    
    # Batasan jumlah pakan
    min_amount = st.number_input("Jumlah pakan minimal (kg)", min_value=1.0, value=5.0)
    max_amount = st.number_input("Jumlah pakan maksimal (kg)", min_value=1.0, value=10.0)
    
    # Fungsi optimasi
    if st.button("Optimasi Ransum") and available_feeds:
        # Persiapkan data untuk optimasi
        c = []  # Biaya per kg
        A_ub = []  # Matriks ketidaksetaraan
        b_ub = []  # Batas kanan ketidaksetaraan
        A_eq = []  # Matriks kesetaraan
        b_eq = []  # Batas kanan kesetaraan
        
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
        required_protein = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Protein (%)']
        b_ub.append(-required_protein * min_amount)
        
        # TDN minimum constraint
        tdn_constraint = []
        for feed in available_feeds:
            feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
            tdn_constraint.append(-feed_data['TDN (%)'])
        A_ub.append(tdn_constraint)
        required_tdn = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['TDN (%)']
        b_ub.append(-required_tdn * min_amount)
        
        # Total amount constraint
        total_min_constraint = [-1] * len(available_feeds)
        A_ub.append(total_min_constraint)
        b_ub.append(-min_amount)
        
        total_max_constraint = [1] * len(available_feeds)
        A_ub.append(total_max_constraint)
        b_ub.append(max_amount)
        
        # Solve the linear programming problem
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method='highs')
        
        if result.success:
            st.success("Optimasi berhasil!")
            
            # Tampilkan hasil optimasi
            optimized_amounts = result.x
            
            # Buat dataframe untuk hasil optimasi
            opt_data = {
                'Bahan Pakan': available_feeds,
                'Jumlah (kg)': optimized_amounts,
                'Protein (kg)': [],
                'TDN (kg)': [],
                'Ca (kg)': [],
                'P (kg)': [],
                'Biaya (Rp)': []
            }
            
            for i, feed in enumerate(available_feeds):
                feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
                opt_data['Protein (kg)'].append(optimized_amounts[i] * feed_data['Protein (%)'] / 100)
                opt_data['TDN (kg)'].append(optimized_amounts[i] * feed_data['TDN (%)'] / 100)
                opt_data['Ca (kg)'].append(optimized_amounts[i] * feed_data['Ca (%)'] / 100)
                opt_data['P (kg)'].append(optimized_amounts[i] * feed_data['P (%)'] / 100)
                opt_data['Biaya (Rp)'].append(optimized_amounts[i] * feed_data['Harga (Rp/kg)'])
            
            df_opt = pd.DataFrame(opt_data)
            df_opt.loc['Total'] = [
                'Total',
                sum(opt_data['Jumlah (kg)']),
                sum(opt_data['Protein (kg)']),
                sum(opt_data['TDN (kg)']),
                sum(opt_data['Ca (kg)']),
                sum(opt_data['P (kg)']),
                sum(opt_data['Biaya (Rp)'])
            ]
            
            st.dataframe(df_opt)
            
            # Tampilkan ringkasan nutrisi
            total_amt = sum(opt_data['Jumlah (kg)'])
            avg_protein = sum(opt_data['Protein (kg)']) * 100 / total_amt
            avg_tdn = sum(opt_data['TDN (kg)']) * 100 / total_amt
            avg_ca = sum(opt_data['Ca (kg)']) * 100 / total_amt
            avg_p = sum(opt_data['P (kg)']) * 100 / total_amt
            
            st.subheader("Kandungan Nutrisi Ransum Optimal")
            cols = st.columns(4)
            
            with cols[0]:
                st.metric("Protein", f"{avg_protein:.2f}%", 
                         f"{avg_protein - required_protein:.2f}%")
            
            with cols[1]:
                st.metric("TDN", f"{avg_tdn:.2f}%", 
                         f"{avg_tdn - required_tdn:.2f}%")
            
            with cols[2]:
                st.metric("Kalsium (Ca)", f"{avg_ca:.2f}%", 
                         f"{avg_ca - kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Ca (%)']:.2f}%")
            
            with cols[3]:
                st.metric("Fosfor (P)", f"{avg_p:.2f}%", 
                         f"{avg_p - kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['P (%)']:.2f}%")
            
            # Total biaya
            st.metric("Total Biaya", f"Rp {sum(opt_data['Biaya (Rp)']):.2f}")
            st.metric("Biaya per kg", f"Rp {sum(opt_data['Biaya (Rp)']) / total_amt:.2f}")
            
            # Tambahkan saran dan keterangan
            st.subheader("Analisis dan Saran")
            
            # Penjelasan optimasi
            st.info("""
            ℹ️ **Tentang Hasil Optimasi**
            
            Formula di atas adalah hasil optimasi dengan biaya terendah yang memenuhi kebutuhan nutrisi minimal. 
            Optimasi dilakukan dengan memperhatikan batasan protein, TDN, dan jumlah total ransum.
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
            
            # Opsi untuk menyimpan formula optimasi
            st.subheader("Simpan Formula Optimal")
            opt_formula_name = st.text_input("Nama formula ransum optimal:", 
                                          value=f"Optimal_{jenis_hewan}_{kategori_umur}_{len(available_feeds)}_bahan")
            
            # Konversi hasil optimasi ke format yang dapat disimpan
            opt_feed_amounts = {}
            for i, feed in enumerate(available_feeds):
                if optimized_amounts[i] > 0.01:  # Hanya simpan jumlah yang signifikan
                    opt_feed_amounts[feed] = optimized_amounts[i]
            
            if st.button("Simpan Formula Optimal"):
                if opt_formula_name:
                    save_formula(opt_formula_name, list(opt_feed_amounts.keys()), 
                              opt_feed_amounts, jenis_hewan, kategori_umur)
                    st.success(f"Formula optimal '{opt_formula_name}' berhasil disimpan!")
                else:
                    st.error("Masukkan nama untuk formula")

elif mode == "Mineral Supplement":
    st.header("Perhitungan Mineral Supplement")
    
    # Tambahkan data mineral ke tabel pakan
    mineral_df = pd.DataFrame(mineral_supplements)
    
    # Tampilkan mineral supplements dengan semua nilai yang bisa diedit
    st.subheader("Mineral Supplements Tersedia")
    edited_mineral_df = st.data_editor(
        mineral_df,
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
        mineral_df['Nama Pakan'].tolist()
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
                req_ca = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Ca (%)'] * total_amount / 100
                req_p = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['P (%)'] * total_amount / 100
                req_mg = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Mg (%)'] * total_amount / 100
                req_fe = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Fe (ppm)'] * total_amount / 1000
                req_cu = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Cu (ppm)'] * total_amount / 1000
                req_zn = kebutuhan_nutrisi_umur[jenis_hewan][kategori_umur]['Zn (ppm)'] * total_amount / 1000
                
                # Tampilkan hasil analisis mineral
                st.subheader("Analisis Mineral Ransum Dasar")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Kalsium (Ca)", f"{base_ca:.3f} kg", 
                             f"{base_ca - req_ca:.3f} kg")
                    if base_ca < req_ca:
                        st.warning(f"Kekurangan Ca: {req_ca - base_ca:.3f} kg")
                    else:
                        st.success(f"Ca mencukupi kebutuhan")
                
                with col2:
                    st.metric("Fosfor (P)", f"{base_p:.3f} kg",
                             f"{base_p - req_p:.3f} kg")
                    if base_p < req_p:
                        st.warning(f"Kekurangan P: {req_p - base_p:.3f} kg")
                    else:
                        st.success(f"P mencukupi kebutuhan")
                
                with col3:
                    st.metric("Magnesium (Mg)", f"{base_mg:.3f} kg",
                             f"{base_mg - req_mg:.3f} kg")
                    if base_mg < req_mg:
                        st.warning(f"Kekurangan Mg: {req_mg - base_mg:.3f} kg")
                    else:
                        st.success(f"Mg mencukupi kebutuhan")
                
                # Mikro mineral
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Zat Besi (Fe)", f"{base_fe:.3f} g",
                             f"{base_fe - req_fe:.3f} g")
                    if base_fe < req_fe:
                        st.warning(f"Kekurangan Fe: {req_fe - base_fe:.3f} g")
                    else:
                        st.success(f"Fe mencukupi kebutuhan")
                    
                with col2:
                    st.metric("Tembaga (Cu)", f"{base_cu:.3f} g",
                             f"{base_cu - req_cu:.3f} g")
                    if base_cu < req_cu:
                        st.warning(f"Kekurangan Cu: {req_cu - base_cu:.3f} g")
                    else:
                        st.success(f"Cu mencukupi kebutuhan")
                    
                with col3:
                    st.metric("Zinc (Zn)", f"{base_zn:.3f} g",
                             f"{base_zn - req_zn:.3f} g")
                    if base_zn < req_zn:
                        st.warning(f"Kekurangan Zn: {req_zn - base_zn:.3f} g")
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
                                ca_needed = (req_ca - base_ca) / (mineral_data['Ca (%)'] / 100)
                                required_amount = max(required_amount, ca_needed)
                                rationale.append(f"- Untuk memenuhi Ca: {ca_needed:.2f} kg")
                                provides_needed = True
                                
                            if base_p < req_p and mineral_data['P (%)'] > 0:
                                p_needed = (req_p - base_p) / (mineral_data['P (%)'] / 100)
                                required_amount = max(required_amount, p_needed)
                                rationale.append(f"- Untuk memenuhi P: {p_needed:.2f} kg")
                                provides_needed = True
                                
                            if base_mg < req_mg and mineral_data['Mg (%)'] > 0:
                                mg_needed = (req_mg - base_mg) / (mineral_data['Mg (%)'] / 100)
                                required_amount = max(required_amount, mg_needed)
                                rationale.append(f"- Untuk memenuhi Mg: {mg_needed:.2f} kg")
                                provides_needed = True
                            
                            if base_fe < req_fe and mineral_data['Fe (ppm)'] > 0:
                                # Convert ppm to absolute amounts
                                fe_needed = (req_fe - base_fe) * 1000000 / mineral_data['Fe (ppm)']
                                fe_needed = fe_needed / 1000  # Convert to kg
                                required_amount = max(required_amount, fe_needed)
                                rationale.append(f"- Untuk memenuhi Fe: {fe_needed:.2f} kg")
                                provides_needed = True
                                
                            if base_cu < req_cu and mineral_data['Cu (ppm)'] > 0:
                                cu_needed = (req_cu - base_cu) * 1000000 / mineral_data['Cu (ppm)']
                                cu_needed = cu_needed / 1000  # Convert to kg
                                required_amount = max(required_amount, cu_needed)
                                rationale.append(f"- Untuk memenuhi Cu: {cu_needed:.2f} kg")
                                provides_needed = True
                                
                            if base_zn < req_zn and mineral_data['Zn (ppm)'] > 0:
                                zn_needed = (req_zn - base_zn) * 1000000 / mineral_data['Zn (ppm)']
                                zn_needed = zn_needed / 1000  # Convert to kg
                                required_amount = max(required_amount, zn_needed)
                                rationale.append(f"- Untuk memenuhi Zn: {zn_needed:.2f} kg")
                                provides_needed = True
                            
                            if provides_needed:
                                # Calculate cost
                                cost = required_amount * mineral_data['Harga (Rp/kg)']
                                recommendations.append({
                                    'mineral': mineral,
                                    'amount': required_amount,
                                    'cost': cost,
                                    'rationale': rationale
                                })
                        
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
                                st.metric("Kalsium (Ca)", f"{new_ca:.3f} kg", f"{new_ca - req_ca:.3f} kg")
                                
                            with col2:
                                st.metric("Fosfor (P)", f"{new_p:.3f} kg", f"{new_p - req_p:.3f} kg")
                                
                            with col3:
                                st.metric("Magnesium (Mg)", f"{new_mg:.3f} kg", f"{new_mg - req_mg:.3f} kg")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Zat Besi (Fe)", f"{new_fe:.3f} g", f"{new_fe - req_fe:.3f} g")
                                
                            with col2:
                                st.metric("Tembaga (Cu)", f"{new_cu:.3f} g", f"{new_cu - req_cu:.3f} g")
                                
                            with col3:
                                st.metric("Zinc (Zn)", f"{new_zn:.3f} g", f"{new_zn - req_zn:.3f} g")
                            
                            # Show cost analysis
                            st.subheader("Analisis Biaya Suplemen")
                            st.write(f"**Biaya Suplemen**: Rp{best_rec['cost']:,.0f}")
                            st.write(f"**Biaya per kg total ransum**: Rp{best_rec['cost']/(total_amount + best_rec['amount']):,.1f}")
                            
                    else:
                        st.warning("Pilih mineral supplement untuk melihat rekomendasi jumlah yang dibutuhkan")
                else:
                    st.success("Kandungan mineral dalam ransum dasar sudah memenuhi kebutuhan!")

# Pisahkan fungsi untuk kalkulasi nutrisi
def calculate_nutrition_content(feed_data, feed_amounts):
    """Menghitung kandungan nutrisi dari kombinasi pakan"""
    total_amount = sum(feed_amounts.values())
    
    if total_amount <= 0:
        return None, None, None, None, None, None, None
        
    total_protein = sum(feed_amounts[feed] * feed_data[feed]['protein'] for feed in feed_amounts)
    total_tdn = sum(feed_amounts[feed] * feed_data[feed]['tdn'] for feed in feed_amounts)
    total_cost = sum(feed_amounts[feed] * feed_data[feed]['harga'] for feed in feed_amounts)
    
# Ensure only one definition of save_formula exists in the codebase.
def save_formula(name, selected_feeds, feed_amounts, animal_type, age_category):
    """Simpan formula ransum"""
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

def load_formula(name):
    """Muat formula ransum yang tersimpan"""
    if 'saved_formulas' not in st.session_state or name not in st.session_state.saved_formulas:
        return None
    
    return st.session_state.saved_formulas[name]

import concurrent.futures

def optimize_with_constraints(constraints, available_feeds, df_pakan):
    """Jalankan optimasi dengan parameter tertentu"""
    min_amount, max_amount = constraints['min_amount'], constraints['max_amount']
    required_protein = constraints['required_protein'] 
    required_tdn = constraints['required_tdn']
    
    # Implementasi optimasi seperti sebelumnya
    # ...
    
    return result

# Jalankan beberapa optimasi dengan parameter berbeda secara paralel
def run_multi_optimization(param_sets, available_feeds, df_pakan):
    results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_params = {
            executor.submit(optimize_with_constraints, params, available_feeds, df_pakan): params 
            for params in param_sets
        }
        
        for future in concurrent.futures.as_completed(future_to_params):
            params = future_to_params[future]
            try:
                result = future.result()
                results.append((params, result))
            except Exception as exc:
                results.append((params, None))
    
    return results

def price_sensitivity_analysis(optimal_feeds, df_pakan, price_range=(-20, 20), steps=5):
    """Analisa sensitivitas harga terhadap komposisi optimal"""
    results = []
    price_changes = np.linspace(price_range[0], price_range[1], steps) / 100
    
    original_prices = {}
    for feed in optimal_feeds:
        feed_data = df_pakan[df_pakan['Nama Pakan'] == feed].iloc[0]
        original_prices[feed] = feed_data['Harga (Rp/kg)']
    
    # Simulasikan perubahan harga dan dampaknya
    for change in price_changes:
        # Update harga berdasarkan persentase perubahan
        for feed in optimal_feeds:
            df_pakan.loc[df_pakan['Nama Pakan'] == feed, 'Harga (Rp/kg)'] = \
                original_prices[feed] * (1 + change)
    
    return results

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