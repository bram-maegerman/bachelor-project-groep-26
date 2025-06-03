import fitz, io, sys
from PIL import Image
from pathlib import Path
from multiprocessing import Pool, cpu_count


def compress_page(args):
    pdf_path, page_index, dpi, image_quality = args
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
    doc.close()

    img_bytes = pix.tobytes("jpeg")
    img = Image.open(io.BytesIO(img_bytes))

    output_io = io.BytesIO()
    img.save(output_io, format="JPEG", quality=image_quality)
    output_io.seek(0)

    return (pix.width, pix.height, output_io.read())


def compress_pdf(input_pdf_path: str, output_pdf_path: str, image_quality: int = 50, dpi: int = 90):
    doc = fitz.open(input_pdf_path)
    num_pages = len(doc)
    doc.close()

    args = [(str(input_pdf_path), i, dpi, image_quality) for i in range(num_pages)]

    with Pool(processes=min(cpu_count(), num_pages)) as pool:
        results = pool.map(compress_page, args)

    new_doc = fitz.open()
    for width, height, img_data in results:
        img_rect = fitz.Rect(0, 0, width, height)
        new_page = new_doc.new_page(width=width, height=height)
        new_page.insert_image(img_rect, stream=img_data)

    new_doc.save(output_pdf_path)
    new_doc.close()
    return output_pdf_path


if __name__ == '__main__':
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
    output_pdf = export_dir / f"compressed_{original_pdf_path.name}"

    compressed_output_path = compress_pdf(original_pdf_path, output_pdf)

    with open(log_file_path, "a") as file:
        file.write(f"\n\nPath to original pdf: \n{compressed_output_path}")
