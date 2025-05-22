import fitz, io
from pathlib import Path
from PIL import Image
from termcolor import colored
from concurrent.futures import ProcessPoolExecutor
from util import find_sequence, custom_print, extract_header_footer, log_messages

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000118_01.pdf"

doc = fitz.open(filename)
avg_height = 3520
avg_width = 2375

# Needed to be serializable (avoid shared state)
def process_page(index):
    page = doc[index]
    xref = page.get_images()[0][0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]
    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size

    is_double = width > avg_width * 1.2 or height > avg_height * 1.2
    parsed_numbers = extract_header_footer(image)

    return index, parsed_numbers, is_double

found_numbers = []
missing_numbers = set()
previous = None
first_index = -1

# Process pages in parallel
with ProcessPoolExecutor(max_workers=12) as executor:
    futures = list(executor.map(process_page, range(len(doc))))

# Now handle the sequential logic
for index, parsed_numbers, is_double in sorted(futures):
    pdf_page_number = index + 1
    print(f"\nProcessing PDF page: {pdf_page_number}")
    found_numbers.append(parsed_numbers)

    if is_double:
        custom_print("WARNING", f"Found a probable double print on page {pdf_page_number}")

    if not parsed_numbers:
        if previous is not None:
            previous += 1
            missing_numbers.add(previous)
            custom_print("WARNING", f"Expected to find {previous} but found nothing")
        else:
            custom_print("WARNING", f"No page number found on PDF page {pdf_page_number}")
    else:
        if index >= 2:
            if previous is not None:
                if previous + 1 in parsed_numbers:
                    previous += 1
                    custom_print("SUCCESS", f"Found expected page number {previous}")
                else:
                    expected_num = previous + 1
                    custom_print("WARNING", f"Expected to find {expected_num} but found {parsed_numbers} instead.")
                    missing_numbers.add(expected_num)

                    if all(x > len(doc) - first_index or x < previous for x in parsed_numbers):
                        custom_print("INFO", f"Found numbers are outside of range: {parsed_numbers}.")
                        previous = find_sequence(found_numbers, index, previous)
                        if previous is not None:
                            missing_numbers.remove(expected_num)
                    else:
                        cap_range = set(previous + i for i in range(2, 12))
                        common = cap_range & parsed_numbers
                        if common:
                            first_found = min(common)
                            missing_numbers.update(range(int(previous) + 1, int(first_found)))
                            previous = first_found
                            custom_print("SUCCESS", f"Found expected page number on page {previous}.")
                        else:
                            custom_print("WARNING", f"Too many pages are missing. Last found page number was {previous}.")
                            quit()
            else:
                previous = find_sequence(found_numbers, index, previous)
        else:
            custom_print("WARNING", f"No page number found on PDF page {pdf_page_number}")

# Final report
if missing_numbers:
    print(f"\n{colored('Missing pages', 'red', attrs=['bold', 'underline'])}: {colored(', '.join(str(x) for x in sorted(missing_numbers)), 'red', attrs=['bold'])}")
else:
    print(f"\n{colored('Missing pages', 'red', attrs=['bold', 'underline'])}: {colored('None', 'green', attrs=['bold'])}")

print(f"\n{colored('Total pages in document', 'blue', attrs=['bold'])}: {len(doc)}")
print(f"{colored('Total pages with numbers', 'blue', attrs=['bold'])}: {len(found_numbers) - len(missing_numbers)}")
print(f"{colored('Total pages with missing numbers', 'blue', attrs=['bold'])}: {len(missing_numbers)}\n")

with open(f"{filename}_LOG.txt", "w") as file:
    file.writelines(log_messages)
