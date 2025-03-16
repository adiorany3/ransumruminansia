# Aplikasi Perhitungan Ransum Ruminansia

![Logo](https://github.com/favicon.ico) 

Aplikasi berbasis web untuk menyusun ransum pakan ruminansia secara optimal berdasarkan kebutuhan nutrisi, biaya, dan ketersediaan bahan pakan.

## Fitur Utama

Aplikasi ini memiliki tiga mode utama:

### 1. Formulasi Manual
- Pilih bahan pakan dari database yang komprehensif
- Tentukan proporsi masing-masing bahan
- Analisis kandungan nutrisi secara real-time
- Bandingkan dengan kebutuhan nutrisi standar berdasarkan jenis ternak dan fase produksi
- Perhitungan biaya pakan secara otomatis
- Rekomendasi penyesuaian berdasarkan jenis kelamin, jumlah ternak, dan musim

### 2. Optimalisasi Otomatis
- Formulasi ransum dengan biaya paling ekonomis
- Menggunakan algoritma linear programming untuk optimasi
- Tetap memenuhi semua kebutuhan nutrisi minimum
- Penyajian hasil dalam bentuk tabel dan ringkasan
- Analisis efektivitas biaya (cost per unit nutrient)

### 3. Mineral Supplement
- Analisis kebutuhan mineral dalam ransum dasar
- Perhitungan defisiensi mineral makro dan mikro
- Rekomendasi suplemen mineral yang tepat dan ekonomis
- Penjelasan komprehensif mengenai fungsi, gejala defisiensi, dan toksisitas berbagai mineral

## Persyaratan Sistem

- Python 3.8+
- Streamlit 1.29.0+
- Pandas 2.1.0+
- NumPy 1.24.0+
- SciPy 1.11.0+
- Altair 5.1.0+
- Dan beberapa library pendukung lainnya

## Instalasi

1. Clone repositori ini:
```bash
git clone https://github.com/username/ransumruminansia.git
cd ransumruminansia
```

2. Instal dependensi yang diperlukan:
```bash
pip install -r requirements.txt
```

3. Jalankan aplikasi:
```bash
streamlit run ransumruminansia.py
```

## Penggunaan

### Persiapan Data

Aplikasi menyediakan database default bahan pakan untuk Sapi, Kambing, dan Domba. Anda juga dapat:
- Menggunakan data default yang tersedia dalam aplikasi
- Mengunggah file CSV/Excel berisi data pakan kustom
- Membuat dan mengedit data pakan langsung di dalam aplikasi

### Formulasi Manual

1. Pilih jenis hewan (Sapi/Kambing/Domba, Potong/Perah)
2. Masukkan bobot badan dan parameter produksi
3. Pilih bahan pakan yang tersedia
4. Tentukan jumlah masing-masing bahan pakan
5. Hitung ransum untuk melihat analisis nutrisi dan biaya
6. Sesuaikan komposisi berdasarkan rekomendasi yang diberikan

### Optimalisasi Otomatis

1. Pilih bahan pakan yang tersedia untuk dioptimasi
2. Tentukan batasan jumlah pakan minimal dan maksimal
3. Klik "Optimasi Ransum" untuk mendapatkan formula dengan biaya minimal
4. Tinjau hasil dan analisis nutrisi yang disajikan

### Mineral Supplement

1. Masukkan ransum dasar yang ingin dianalisis
2. Pilih mineral supplement yang tersedia
3. Analisis defisiensi mineral dalam ransum dasar
4. Tinjau rekomendasi jenis dan jumlah mineral supplement

## Format Data

### Data Pakan
File CSV/Excel dengan kolom minimum:
- `Nama Pakan`: Nama bahan pakan
- `Jenis Hewan`: Sapi/Kambing/Domba
- `Kategori`: Hijauan/Konsentrat
- `Protein (%)`: Kandungan protein kasar
- `TDN (%)`: Total Digestible Nutrients
- `Harga (Rp/kg)`: Harga per kilogram

Kolom tambahan yang direkomendasikan:
- `Ca (%)`: Kandungan kalsium
- `P (%)`: Kandungan fosfor
- `Mg (%)`: Kandungan magnesium
- `Fe (ppm)`, `Cu (ppm)`, `Zn (ppm)`: Kandungan mineral mikro

### Data Anti-nutrisi
File CSV dengan kolom:
- `Nama Pakan`: Nama bahan pakan
- Kolom anti-nutrisi: `Tanin (%)`, `Saponin (%)`, `Mimosin (%)`, `Gosipol (ppm)`, `HCN (ppm)`, `Aflatoksin (ppb)`, `Oksalat (%)`

## Kontribusi

Kontribusi untuk meningkatkan aplikasi ini sangat diapresiasi. Anda dapat:
1. Fork repositori
2. Buat branch fitur baru (`git checkout -b fitur-baru`)
3. Commit perubahan (`git commit -am 'Menambahkan fitur baru'`)
4. Push ke branch (`git push origin fitur-baru`)
5. Buat Pull Request

## Keterangan Mode Aplikasi

### Formulasi Manual

**Fungsi Utama:** Memungkinkan pengguna untuk menyusun ransum secara manual dengan memilih bahan pakan dan menentukan jumlahnya sendiri.

**Ideal untuk:** Peternak yang sudah memiliki pengalaman dalam penyusunan ransum atau yang ingin menyesuaikan formula berdasarkan ketersediaan bahan pakan lokal.

### Optimalisasi Otomatis

**Fungsi Utama:** Mencari komposisi ransum paling ekonomis yang memenuhi semua kebutuhan nutrisi minimum ternak.

**Ideal untuk:** Peternak yang menginginkan efisiensi biaya maksimal atau yang memiliki keterbatasan anggaran namun tetap ingin memenuhi kebutuhan nutrisi ternak.

### Mineral Supplement

**Fungsi Utama:** Menganalisis kebutuhan mineral dalam ransum dan memberikan rekomendasi suplemen mineral yang tepat.

**Ideal untuk:** Peternak yang ingin memastikan keseimbangan mineral dalam ransum atau yang menghadapi masalah defisiensi mineral pada ternaknya.

## Lisensi

Program ini dilisensikan di bawah MIT License.

## Kontak

Untuk pertanyaan atau saran, silakan hubungi:
- Email: adioranye@gmail.com
- LinkedIn: [Galuh Adi Insani](https://www.linkedin.com/in/galuh-adi-insani-1aa0a5105/)

---

© 2025 Developed by Galuh Adi Insani with ❤️