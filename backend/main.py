import fitz
from pathlib import Path
import os
import shutil
from PIL import Image, ImageEnhance
import io
import pytesseract

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000118_01.pdf"

doc = fitz.open(filename)

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

                # changes
                width, height = image.size
                image = image.crop((
                        int(width*0.05),
                        int(height*0.87),
                        int(width*0.95),
                        int(height*1)
                    ))
                
                image = image.convert("L")
                image = ImageEnhance.Contrast(image).enhance(2)

                text = pytesseract.image_to_string(image, lang='eng', config=r'--psm 6')
                print(text)

                image.save("cropped_image.png")