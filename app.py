import time
from datetime import date

import streamlit as st
from config import config
from Services.bukti_maker_service import (
    format_uploaded_files_message,
    generate_lampiran_pdf,
    render_pdf_to_images,
)
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
    fase1_tab, fase2_tab = st.tabs(["📋 Fase 1: Rekap Data Maker", "📑 Fase 2: Bukti Lengkap Maker"])

    with fase1_tab:
        render_fase1()
    with fase2_tab:
        render_fase2()


def render_fase1():
    # 1. Penanganan API Key dari config / Sidebar Override
    env_api_key = config.get_api_key()

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

    if "fase1_results" not in st.session_state:
        st.session_state.fase1_results = {}

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
                model_name=config.MODEL_NAME,
                system_instruction=config.SYSTEM_INSTRUCTION,
                fallback_models=config.ALTERNATIVE_MODELS,
                max_retries=3,
                retry_delay=2.0,
            )
        except Exception as e:
            st.error(f"Inisialisasi Service Gagal: {e}")
            return

        st.session_state.fase1_results = {}

        # Indikator Progress
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
                file_key = f"{uploaded_file.name}:{uploaded_file.size}"
                st.session_state.fase1_results[file_key] = {
                    "name": uploaded_file.name,
                    "result": result_text,
                    "error": None,
                }

                update_progress(85, "Gemini sedang mengekstrak data...", "info")
                time.sleep(0.3)

                update_progress(100, "Selesai", "success")

                status_text.success(f"Selesai: {uploaded_file.name} | Menyelesaikan proses PDF")

            except Exception as err:
                update_progress(100, str(err), "error")
                file_key = f"{uploaded_file.name}:{uploaded_file.size}"
                st.session_state.fase1_results[file_key] = {
                    "name": uploaded_file.name,
                    "result": None,
                    "error": str(err),
                }

            st.markdown("---")

    if uploaded_files and st.session_state.fase1_results:
        st.divider()
        st.subheader("📋 Hasil Rekapitulasi Data")

        for idx, uploaded_file in enumerate(uploaded_files, start=1):
            file_key = f"{uploaded_file.name}:{uploaded_file.size}"
            result = st.session_state.fase1_results.get(file_key)
            if not result:
                continue

            with st.expander(f"📌 Rekap Data PDF {idx}: {uploaded_file.name}", expanded=True):
                if result["error"]:
                    st.error(f"Gagal memproses file {uploaded_file.name}: {result['error']}")
                else:
                    st.markdown(result["result"])
                    st.markdown(f"**Nama file:** {uploaded_file.name}")

                st.checkbox(
                    "✅ Mark as done",
                    key=f"fase1_done_{file_key}",
                )


def render_fase2():
    tanggal_maker = st.text_input("Tanggal Pembuatan Maker", value=date.today().strftime("%d-%m-%Y"), key="maker_date")
    evidence_files = st.file_uploader(
        "Unggah PDF Bukti TF / E-Advice Mandiri:", type=["pdf"], accept_multiple_files=True, key="fase2_upload"
    )
    titles: list[str] = []
    if evidence_files:
        st.subheader("Judul SPM")
        for index, evidence_file in enumerate(evidence_files):
            default_title = evidence_file.name.rsplit(".", 1)[0]
            titles.append(st.text_input(f"Nama Judul SPM - {evidence_file.name}", value=default_title, key=f"spm_title_{index}"))

    if st.button("🚀 Generate Bukti Lengkap Maker", type="primary", key="fase2_generate"):
        if not tanggal_maker.strip():
            st.error("Tanggal pembuatan maker wajib diisi.")
            return
        if not evidence_files:
            st.warning("Silakan unggah minimal satu PDF bukti transfer terlebih dahulu.")
            return

        items = []
        with st.spinner("Merender dan menggabungkan bukti PDF..."):
            try:
                for evidence_file, title in zip(evidence_files, titles):
                    items.append({"title": title, "images": render_pdf_to_images(evidence_file.read())})
                output_pdf = generate_lampiran_pdf(tanggal_maker, items)
            except Exception as error:
                st.error(f"Gagal membuat PDF bukti lengkap: {error}")
                return

        filename = f"LAMPIRAN DOKUMEN PENDUKUNG, Maker {tanggal_maker.strip()}.pdf"
        st.success("PDF Bukti Lengkap Maker berhasil dibuat.")

        uploaded_names = [evidence_file.name for evidence_file in evidence_files]
        st.markdown("### Pesan Follow Up")
        st.code(format_uploaded_files_message(uploaded_names), language="text")

        st.download_button("⬇️ Download Bukti Lengkap Maker", output_pdf.getvalue(), filename, "application/pdf", key="fase2_download")

if __name__ == "__main__":
    main()