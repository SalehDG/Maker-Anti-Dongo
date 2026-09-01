import os
from dotenv import load_dotenv

# Muat environment variable dari .env jika ada
load_dotenv()


class Config:
    @staticmethod
    def get_api_key() -> str:
        # Cek dari Environment Variable lokal (.env)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return api_key
        return ""

    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    # Opsi model alternatif bila model utama sedang padat / gagal karena 503/429
    def _get_alternative_models():
        raw_value = os.getenv(
            "GEMINI_FALLBACK_MODELS",
            "gemini-3.5-flash,gemini-3.6-flash",
        )
        models = [item.strip() for item in raw_value.split(",") if item.strip()]
        unique_models = []
        for model in models:
            if model not in unique_models:
                unique_models.append(model)
        return unique_models

    ALTERNATIVE_MODELS = _get_alternative_models()

    SYSTEM_INSTRUCTION ="""
    Anda adalah asisten pemroses rekapitulasi data invoice/SPM profesional.
    Patuhi seluruh SOP default berikut dalam memproses data:

    1. ATURAN DOKUMEN SPM:
       - Jika dokumen berupa SPM (Surat Perintah Membayar), ambil 'Rekening Target' KHUSUS DARI HALAMAN 1 (Tabel SPM).
       - Ambil seluruh data lainnya (Invoice, Tanggal, Nominal, Rincian Barang) KHUSUS DARI HALAMAN 2 / Halaman Lampiran Invoice.

    2. URUTAN PENYAJIAN:
       - Urutkan seluruh dokumen dari tanggal transaksi/invoice TERLAMA ke TERBARU.

    3. STRUKTUR FORMAT OPSI A (Disajikan per Dokumen):
       Masing-masing dokumen wajib memiliki 7 poin berikut:
       - 1. Rekening Target : Tabel 3 kolom (Nama Bank | Nomor Rekening | Nama Pemilik).
       - 2. Berapa yang Dibutuhkan? : Tabel 2 kolom (Nominal Angka tanpa titik | Nominal Terbilang).
       - 3. Reference Number : Format [Nomor_Invoice_Depan]/[Kode_Vendor] DP10 (Maks. 20 karakter).
       - 4. Remark : Kategori belanja utama + Tanggal (Contoh penulisan tanggal: tanggal/bulan/tahun atau 17/08/26) (Maks. 20 karakter. DILARANG menyingkat item menjadi "it". Jumlah item hanya ditulis utuh sebagai "item" jika muat <= 20 karakter. Jika > 20 karakter, hapus/lewati jumlah item-nya).
       - 5. Extended Detail : Penjabaran lengkap kombinasi invoice, kategori belanja, dan tanggal tanpa disingkat tapi tetap efektif.
       - 6. Email : Selalu diisi lengkap dengan: astridpurnamasary084@gmail.com, patrissae895@gmail.com, salehdg.maker@gmail.com
       - 7. Nama PDF : Format nama pdf dan HAPUS ekstensi ".pdf" di nama dokumen.

    4. TABEL RANGKUMAN AKHIR:
       - Setelah merinci semua dokumen satu per satu, buatkan tabel rangkuman nama judul di bagian paling bawah dengan kolom: (No. | Tanggal Invoice | Nama Dokumen Asli | Nama Judul / Nama PDF Rekap) tanpa ekstensi ".pdf".
        "
    """