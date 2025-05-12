import fitz
from pathlib import Path
import os
import shutil
from PIL import Image
import io
import pytesseract

curr_dir = Path(__file__).parent
files = curr_dir / "files"
# filename = files / "seminarie.pdf"
filename = files / "DIGI_2007_000118_01.pdf"
temp_dir = curr_dir/'temp'

if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.mkdir(temp_dir)

doc = fitz.open("backend/files/DIGI_2007_000118_01.pdf")

for page_number in range(len(doc)):
    if page_number == 9:
        page = doc[page_number]
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image = Image.open(io.BytesIO(image_bytes))
                # with open(f"{temp_dir}/image_page{page_number+1}_{img_index}.{image_ext}", "wb") as f:
                text = pytesseract.image_to_string(image, lang='nld')
                print(text)
                    # f.write(image_bytes)