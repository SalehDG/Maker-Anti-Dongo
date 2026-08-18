import time

import streamlit as st
from config import Config
from Services.gemini_services import GeminiService

# Setup Halaman
st.set_page_config(
    page_title="Sistem Rekapitulasi Invoice",
    page_icon="📄",
    layout="wide"
)
def main():
    st.title("📄 AI Invoice & SPM Data Extractor")
    st.caption("Aplikasi Rekapitulasi Dokumen Otomatis Berbasis Gemini AI")
    
    # 1. Penanganan API Key dari Config / Sidebar Override
    env_api_key = Config.get_api_key()
    
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        if env_api_key:
            st.success("API Key terdeteksi dari sistem (.env / Secrets)")
            user_api_key = env_api_key
        else:
            st.warning("API Key belum terkonfigurasi di env!")
            user_api_key = st.text_input("Masukkan Gemini API Key:", type="password")

    # 2. Area Unggah Berkas
    uploaded_files = st.file_uploader(
        "Unggah berkas PDF (Bisa lebih dari 1 file):", 
        type=["pdf"], 
        accept_multiple_files=True
    )

    # 3. Tombol Eksekusi & Pemrosesan
    if st.button("🚀 Proses Rekapitulasi", type="primary"):
        if not user_api_key:
            st.error("API Key belum dimasukkan. Silakan atur .env atau masukkan API Key di sidebar.")
            return

        if not uploaded_files:
            st.warning("Silakan unggah minimal satu berkas PDF terlebih dahulu.")
            return

        # Inisialisasi Service
        try:
            gemini_service = GeminiService(
                api_key=user_api_key,
                model_name=Config.MODEL_NAME,
                system_instruction=Config.SYSTEM_INSTRUCTION,
                fallback_models=Config.ALTERNATIVE_MODELS,
                max_retries=3,
                retry_delay=2.0,
            )
        except Exception as e:
            st.error(f"Inisialisasi Service Gagal: {e}")
            return

        # Indikator Progress
        st.divider()
        st.subheader("📋 Hasil Rekapitulasi Data")

        for idx, uploaded_file in enumerate(uploaded_files, start=1):
            progress_container = st.container()
            status_text = progress_container.empty()
            percent_text = progress_container.empty()
            progress_bar = progress_container.progress(0)

            def update_progress(value: int, message: str, type_text: str = "info"):
                progress_bar.progress(value)
                percent_text.markdown(f"<div style='text-align:right; font-weight:bold; color:#4f46e5;'> {value}% </div>", unsafe_allow_html=True)
                if type_text == "info":
                    status_text.info(f"Memproses PDF {idx}/{len(uploaded_files)}: {uploaded_file.name} | {message}")
                elif type_text == "success":
                    status_text.success(f"Selesai: {uploaded_file.name} | {message}")
                elif type_text == "error":
                    status_text.error(f"Gagal: {uploaded_file.name} | {message}")

            update_progress(10, "Membaca file PDF...", "info")
            time.sleep(0.2)

            update_progress(30, "Mengirim dokumen ke Gemini AI...", "info")
            time.sleep(0.2)

            update_progress(55, "Menunggu respons Gemini...", "info")

            try:
                file_bytes = uploaded_file.read()
                result_text = gemini_service.extract_invoice_data(file_bytes)

                update_progress(85, "Gemini sedang mengekstrak data...", "info")
                time.sleep(0.3)

                update_progress(100, "Selesai", "success")

                with st.expander(f"📌 Rekap Data PDF {idx}: {uploaded_file.name}", expanded=True):
                    st.markdown(result_text)

            except Exception as err:
                update_progress(100, str(err), "error")
                st.error(f"Gagal memproses file {uploaded_file.name}: {err}")

            st.markdown("---")

if __name__ == "__main__":
    main()