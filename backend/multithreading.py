import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
import pytesseract
import io
import re
from pathlib import Path

def process_page(page_bytes):
    page_number, image_bytes = page_bytes
    try:
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size

        # Crop top and bottom
        top = image.crop((
                int(width * 0.05), 
                int(height * 0.00), 
                int(width * 0.95), 
                int(height * 0.12)
            )).convert("L")
        bottom = image.crop((
                int(width * 0.05), 
                int(height * 0.87), 
                int(width * 0.95), 
                int(height * 1.00)
            )).convert("L")

        # Enhance contrast
        top = ImageEnhance.Contrast(top).enhance(2.0)
        bottom = ImageEnhance.Contrast(bottom).enhance(2.0)

        # OCR
        bottom_text = pytesseract.image_to_string(bottom, lang='eng', config=r'--psm 6')
        top_text = pytesseract.image_to_string(top, lang='eng', config=r'--psm 6')   

        # Extract numbers
        numbers = re.findall(r'\b\d{1,3}\b', top_text + ' ' + bottom_text)
        return (page_number, [int(n) for n in numbers if n.isdigit()])
    except Exception:
        return (page_number, [])

def checkForNumber(array, num):
    return num in array

def recursive_check(page_numbers, wanted_number=1, missingNumbers: set = set()):
    if len(page_numbers) == 0:
        return missingNumbers
    if wanted_number not in page_numbers[0]:
        if wanted_number in missingNumbers:
            missingNumbers.remove(wanted_number)
        else:
            missingNumbers.add(wanted_number)
    return recursive_check(page_numbers[1:], wanted_number + 1, missingNumbers)

if __name__ == "__main__":
    from multiprocessing import Pool, cpu_count

    curr_dir = Path(__file__).parent
    files = curr_dir / "files"
    filename = files / "DIGI_2007_000118_01.pdf"

    doc = fitz.open(filename)

    # Extract images from pages
    page_images = []
    for i in range(len(doc)):
        page = doc[i]
        images = page.get_images(full=True)
        if not images:
            continue

        # Pick largest image on the page
        largest = max(images, key=lambda im: im[2] * im[3])
        xref = largest[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        page_images.append((i, image_bytes))

    # Use multiprocessing for OCR
    with Pool(cpu_count()) as pool:
        results = pool.map(process_page, page_images)

    # Collect results
    found_page_numbers = [res[1] for res in sorted(results, key=lambda x: x[0])]
    print("Extracted page numbers per image:")
    print(found_page_numbers)

    # Find the first sequential page (1,2,3)
    firstPageWithPageNumber = -1
    for index, page in enumerate(found_page_numbers):
        if index + 2 >= len(found_page_numbers):
            break
        if checkForNumber(page, 1) and \
           checkForNumber(found_page_numbers[index + 1], 2) and \
           checkForNumber(found_page_numbers[index + 2], 3):
            firstPageWithPageNumber = index
            break

    if firstPageWithPageNumber == -1:
        print("Could not find a valid first page with sequential numbers 1, 2, 3.")
    else:
        print(f"The first page with a page number is page {firstPageWithPageNumber + 1}")

        # Detect missing page numbers
        missing = recursive_check(found_page_numbers[firstPageWithPageNumber:])
        print("Missing page numbers:", sorted(missing))
