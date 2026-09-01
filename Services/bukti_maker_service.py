import io
from collections.abc import Iterable, Mapping
from typing import Any

import fitz
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def format_uploaded_files_message(file_names: Iterable[str]) -> str:
    """Format daftar nama file yang diunggah menjadi pesan follow-up."""
    cleaned_names = [str(name).strip() for name in file_names if str(name).strip()]
    if not cleaned_names:
        return "Mohon untuk segera di follow up dan diproses lebih lanjut. Terima kasih."

    lines = [f"{index}. {name}" for index, name in enumerate(cleaned_names, start=1)]
    lines.append("")
    lines.append("Mohon untuk segera di follow up dan diproses lebih lanjut. Terima kasih.")
    return "\n".join(lines)


def render_pdf_to_images(pdf_bytes: bytes, dpi: int = 180) -> list[io.BytesIO]:
    """Render every PDF page to a PNG stream at a print-friendly resolution."""
    if not pdf_bytes:
        raise ValueError("Data PDF kosong.")
    if dpi <= 0:
        raise ValueError("DPI harus lebih besar dari nol.")

    images: list[io.BytesIO] = []
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            for page in document:
                image_stream = io.BytesIO(page.get_pixmap(matrix=matrix, alpha=False).tobytes("png"))
                image_stream.seek(0)
                images.append(image_stream)
    except Exception as error:
        raise ValueError(f"PDF bukti tidak dapat dirender: {error}") from error

    if not images:
        raise ValueError("PDF bukti tidak memiliki halaman.")
    return images


def generate_lampiran_pdf(
    tanggal_maker: str,
    items: Iterable[Mapping[str, Any]],
) -> io.BytesIO:
    """Create an A4 attachment PDF from rendered evidence images.

    Each item must contain ``title`` and an iterable of PNG streams under ``images``.
    One evidence page is placed on one A4 page to preserve readability.
    """
    tanggal_maker = tanggal_maker.strip()
    if not tanggal_maker:
        raise ValueError("Tanggal maker wajib diisi.")

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    page_width, page_height = A4
    margin = 36
    header_height = 78

    item_count = 0
    for item in items:
        title = str(item.get("title", "")).strip() or "Tanpa Judul SPM"
        images = item.get("images")
        if not images:
            raise ValueError(f"Tidak ada gambar bukti untuk SPM: {title}")

        for image_index, image_stream in enumerate(images):
            if image_index == 0:
                pdf.setFont("Helvetica-Bold", 14)
                pdf.drawString(margin, page_height - margin, f"LAMPIRAN DOKUMEN PENDUKUNG, Maker {tanggal_maker}")
                pdf.setFont("Helvetica-Bold", 11)
                pdf.drawString(margin, page_height - margin - 24, title)

            image_stream.seek(0)
            image = ImageReader(image_stream)
            image_width, image_height = image.getSize()
            available_width = page_width - (2 * margin)
            available_height = page_height - (2 * margin) - header_height
            scale = min(available_width / image_width, available_height / image_height)
            draw_width = image_width * scale
            draw_height = image_height * scale
            x = (page_width - draw_width) / 2
            y = margin + (available_height - draw_height) / 2
            pdf.drawImage(image, x, y, width=draw_width, height=draw_height, preserveAspectRatio=True, mask="auto")
            pdf.showPage()
            item_count += 1

    if item_count == 0:
        raise ValueError("Belum ada bukti yang dapat digabungkan.")
    pdf.save()
    output.seek(0)
    return output