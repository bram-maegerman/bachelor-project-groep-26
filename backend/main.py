import fitz, io, pytesseract, re
from pathlib import Path
from PIL import Image, ImageEnhance
from termcolor import colored

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000118_01_DELETED_PAGE.pdf"

doc = fitz.open(filename)

# All found numbers from header and footer scan
found_numbers = []

def extract_numbers(full_image, upper, lower):
    width, height = full_image.size
    cropped = full_image.crop((
            int(width*0.05),
            int(height*upper),
            int(width*0.95),
            int(height*lower)
        ))

    cropped = ImageEnhance.Contrast(cropped).enhance(2)

    content = pytesseract.image_to_string(cropped, lang='eng', config=r'--psm 6')
    return re.findall(r'[-+]?\d+(?:\.\d+)?', content)

def find_first_index(found_numbers, current_index):
    for num in found_numbers[current_index]:
        if num - 1 in found_numbers[current_index - 1] and num-2 in found_numbers[current_index - 2]:
            return (current_index - 2, num)
    return (-1, None)
    

# Goes over all pages of the scanned pdf document
# Converts each page to an image
# Extract the header and footer from this image
# Scan these sections for numbers
# Adds those numbers to the found_numbers list
previous = None
first_index = -1
missing_numbers = set()
for page_index in range(len(doc)):
    pdf_page_number = page_index + 1
    print(f"\nProcessing PDF page: {pdf_page_number}")
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
    found_numbers.append(parsed_numbers)

    #   If no numbers found on page
    if len(parsed_numbers) == 0:

        #   If pagination has started
        if previous is not None:
            previous += 1
            missing_numbers.add(previous)
            print(f"{colored('WARNING', 'red')}: Expected to find {previous} but found nothing.")

        #   If pagination hasn't started
        else:
            print(f"{colored('WARNING', 'red')}: No page number found on PDF page {pdf_page_number}.")
    else:
        
        #
        if page_index >= 2:
            if previous is not None:
                if previous+1 in parsed_numbers:
                    print(f"{colored('SUCCESS', 'green')}: Found expected page number {previous+1}")
                    previous += 1
                else:
                    print(f"{colored('WARNING', 'red')}: Expected to find {previous+1} but found {parsed_numbers} instead")
                    missing_numbers.add(previous+1)

                    if all(x > len(doc) - first_index or x < previous for x in parsed_numbers):
                        print(f"{colored('INFO', 'yellow')}: Found numbers outside of range: {parsed_numbers}")
                    else:
                        cap_range = set(previous + i for i in range(2,12))
                        common = cap_range & parsed_numbers

                        if len(common) > 0:
                            first_found = min(common)
                            missing_numbers.update(x for x in range(previous + 1, first_found))
                            previous = first_found
                            print(f"{colored('SUCCESS', 'green')}: Found expected page number on page {previous}")
                        else:
                            print(f"{colored('WARNING', 'red')}: Too many missing pages. Last found page number was {previous}")
                            quit()
            else:
                first_index, actual_page_number = find_first_index(found_numbers, page_index)
                if first_index != -1:
                    print(f"{colored('INFO', 'yellow')}: The first page with a page number is {first_index + 1}")
                    previous = actual_page_number
                else:
                    print(f"{colored('WARNING', 'red')}: No page number found on PDF page {pdf_page_number}.")

print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {missing_numbers}")