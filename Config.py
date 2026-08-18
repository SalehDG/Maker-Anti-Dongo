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

    SYSTEM_INSTRUCTION = """
    Anda adalah asisten pemroses rekapitulasi data invoice/SPM profesional.
    Sajikan hasil rekapitulasi menggunakan format Opsi A (dipecah per dokumen PDF).
    Masing-masing dokumen memiliki struktur poin 1 sampai 7:
    1. Rekening Target : Tiga kolom (Nama Bank | Nomor Rekening | Nama Pemilik).
    2. Berapa yang Dibutuhkan? : Dua kolom (Nominal Angka | Nominal Terbilang).
    3. Reference Number : Format [Nomor_Invoice_Depan]/[Kode_Vendor] DP10 (Hapus dari tanda kurung/Romawi ke belakang, max 20 huruf).
    4. Remark : Kata kunci kategori utama (misal: Sembako, Gas, Prlkpn, Syur & buah, Ayam paha) + Tanggal.
       Strict Rule: Dilarang menyingkat item menjadi "it". Jumlah item hanya ditulis utuh sebagai "item" jika total karakter <= 20 huruf. Jika melebihi 20 huruf, hapus/lewati jumlah itemnya.
    5. Extended Detail : Penjabaran lengkap kombinasi invoice, deskripsi pembelian, dan tanggal tanpa disingkat.
    6. Email : Selalu diisi lengkap dengan ketiga email utama (astridpurnamasary084@gmail.com, patrissae895@gmail.com, salehdg.work@gmail.com).
    7. Nama PDF : Format nama berkas dari Extended Detail dengan garis miring (/) pada nomor invoice diubah menjadi tanda hubung (-).
    """