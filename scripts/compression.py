import fitz, io, sys
from PIL import Image
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: python compression.py <path_to_pdf> <path_to_log_file>")
    sys.exit(1)

original_pdf_path = Path(sys.argv[1])
if not original_pdf_path.exists():
    print(f"File not found: {original_pdf_path}")
    sys.exit(1)

log_file_path = Path(sys.argv[2])
if not log_file_path.exists():
    print(f"File not found: {log_file_path}")
    sys.exit(1)

export_dir = log_file_path.parent


def compress_pdf(input_pdf_path: str, output_pdf_path: str, image_quality: int = 50, dpi: int = 90):
    """
    Compress a PDF images by reducing DPI and JPEG quality.

    :param input_pdf_path: Path to the input PDF
    :param output_pdf_path: Path to save the compressed PDF

    :param image_quality: JPEG quality (1-100), lower means more compression
    :param dpi: Dots per inch to render each page (lower = more compression)
    """
    doc = fitz.open(input_pdf_path)
    new_doc = fitz.open()

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))

        img_bytes = pix.tobytes("jpeg")
        img = Image.open(io.BytesIO(img_bytes))

        output_io = io.BytesIO()
        img.save(output_io, format="JPEG", quality=image_quality)
        output_io.seek(0)

        img_rect = fitz.Rect(0, 0, pix.width, pix.height)
        new_page = new_doc.new_page(width=img_rect.width, height=img_rect.height)
        new_page.insert_image(img_rect, stream=output_io.read())

    new_doc.save(output_pdf_path)
    doc.close()
    new_doc.close()

    return output_pdf_path

compressed_output_path = compress_pdf(original_pdf_path, f"{export_dir}/compressed_{original_pdf_path.name}")

with open(log_file_path, "a") as file:
    file.write(f"\n\nPath to original pdf: \n{compressed_output_path}")

print("done!")