import fitz
import io
import pytesseract
import re
from pathlib import Path
from PIL import Image, ImageEnhance
from multiprocessing import Pool, Manager, cpu_count

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000118_01_DELETED_PAGE.pdf"

def extract_numbers(full_image, upper, lower):
    width, height = full_image.size
    cropped = full_image.crop((
        int(width * 0.05),
        int(height * upper),
        int(width * 0.95),
        int(height * lower)
    ))

    cropped = ImageEnhance.Contrast(cropped).enhance(2)

    content = pytesseract.image_to_string(cropped, lang='eng', config=r'--psm 6')
    return re.findall(r'[-+]?\d+(?:\.\d+)?', content)

def process_page(args):
    page_index, pdf_path, progress_queue = args
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    xref = page.get_images(full=True)[0][0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]
    image = Image.open(io.BytesIO(image_bytes))

    header = extract_numbers(image, 0, 0.12)
    footer = extract_numbers(image, 0.87, 1)

    parsed_numbers = set()
    parsed_numbers.update(int(num) for num in header)
    parsed_numbers.update(int(num) for num in footer)
    progress_queue.put(1)
    return parsed_numbers

def find_first_page_with_page_number_previous(found_numbers, current_index):
    for num in found_numbers[current_index]:
        if num - 1 in found_numbers[current_index - 1] and num - 2 in found_numbers[current_index - 2]:
            return (current_index - 2, num)
    return (-1, None)

def main():
    doc = fitz.open(filename)
    page_count = len(doc)

    with Manager() as manager:
        progress_queue = manager.Queue()
        args = [(i, str(filename), progress_queue) for i in range(page_count)]
        print("Multiprocessing")
        with Pool(processes=cpu_count()) as pool:
            found_numbers_result = pool.map_async(process_page, args)

            completed = 0
            while completed < page_count:
                progress_queue.get()
                completed += 1
                print(f"\rProgress: {completed}/{page_count} ({(completed/page_count)*100:.1f}%)", end='')
            found_numbers = found_numbers_result.get()
        previous = None
        first_index_with_page_number = -1
        missing_numbers = set()

        for page_index, parsed_numbers in enumerate(found_numbers):
            pdf_page_number = page_index + 1
            print(f"\nProcessing PDF page: {pdf_page_number}")
            print(f"Found numbers: {parsed_numbers}")

            if not parsed_numbers:
                if previous is not None:
                    print(f"WARNING: Expected to find {previous + 1}")
                    previous += 1
                    missing_numbers.add(previous)
                else:
                    print(f"WARNING: No page number found on PDF page {pdf_page_number}.")
            else:
                if page_index >= 2:
                    if previous is not None:
                        if previous+1 in parsed_numbers:
                            print(f"SUCCESS: Found expected page number {previous+1}")
                            previous += 1
                        else:
                            print(f"WARNING: Expected to find {previous+1} but found {parsed_numbers} instead")
                            missing_numbers.add(previous+1)

                            if all(x > len(doc) - first_index_with_page_number or x < previous for x in parsed_numbers):
                                print(f"INFO: Found numbers outside of range: {parsed_numbers}")
                            else:
                                for i in range(2, 12):
                                    print(f'Checking if {previous+i} in {parsed_numbers}')
                                    if previous + i in parsed_numbers:
                                        previous += i
                                        print(f"SUCCESS: Found expected page number on page {previous}")
                                        break
                                    else:
                                        missing_numbers.add(previous+i)
                                else:
                                    print(f"WARNING: Too many missing pages. Last found page number was {previous}")
                                    quit()
                    else:
                        first_index_with_page_number, actual_page_number = find_first_page_with_page_number_previous(found_numbers, page_index)
                        if first_index_with_page_number != -1:
                            print(f"INFO: The first page with a page number is {first_index_with_page_number + 1}")
                            previous = actual_page_number
                        else:
                            print(f"WARNING: No page number sequence found yet.")

    print(f"\nMissing page numbers: {sorted(missing_numbers)}")

if __name__ == "__main__":
    main()
