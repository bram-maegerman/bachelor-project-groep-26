import fitz, io, pytesseract, re
from pathlib import Path
from PIL import Image, ImageEnhance
from termcolor import colored
from typing import Literal

# own python scripts
from util import extract_numbers, find_first_index, custom_print, log_messages

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000121_01.pdf"

doc = fitz.open(filename)

#   All found numbers from header and footer scan
found_numbers = []
avg_height = 3520
avg_width = 2375

#   Goes over all pages of the scanned pdf document
#   Converts each page to an image
#   Extract the header and footer from this image
#   Scan these sections for numbers
#   Adds those numbers to the found_numbers list
previous = None
first_index = -1
missing_numbers = set()

for page_index in range(len(doc)):
   
    pdf_page_number = page_index + 1
    print(f"\nProcessing PDF page: {pdf_page_number}")
    page = doc[page_index]
    xref = page.get_images()[0][0]
    base_image = doc.extract_image(xref)

    #   Reads out the bytes of the image
    image_bytes = base_image["image"]

    #   Creates an image from those bytes
    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size

    if width > avg_width*1.2 or height > avg_height*1.2:
        custom_print(statement_type="WARNING", statement=f"Found a probable double print on page {previous + 1}")

    #   Extract the numbers from the header and footer (defined by upper and lower)
    header = extract_numbers(image, upper=0, lower=0.12)
    footer = extract_numbers(image, upper=0.87, lower=1)


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
            custom_print(statement_type="WARNING", statement=f"Expected to find {previous} but found nothing")

        #   If pagination hasn't started
        else:
            custom_print(statement_type="WARNING", statement=f"No page number found on PDF page {pdf_page_number}")

    #   If numbers have been found on current page
    else:
        if page_index >= 2:
            if previous is not None:

                #   If an increment of previous is on current page
                #   i.e expected page number is previous page number+1
                if previous+1 in parsed_numbers:
                    previous += 1
                    custom_print(statement_type="SUCCESS", statement=f"Found expected page number {previous}")


                #   Expected page number is not found on current page
                else:
                    expected_num = previous + 1

                    custom_print(statement_type="WARNING", statement=f"Expected to find {expected_num} but found {parsed_numbers} instead.")
                    missing_numbers.add(expected_num)

                    #   Check if numbers could be possible page numbers
                    if all(x > len(doc) - first_index or x < previous for x in parsed_numbers):
                        custom_print(statement_type="INFO", statement=f"Found numbers are outside of range: {parsed_numbers}.")
                        previous = expected_num
                    else:

                        #   Check if found page numbers are between previous and previous+10
                        cap_range = set(previous + i for i in range(2,12))
                        common = cap_range & parsed_numbers

                        #   If the intersection of both sets of numbers contains at least one number
                        if len(common) > 0:

                            #   Lowest found number in intersection is **most likely** the next page number
                            first_found = min(common)

                            #   Add all numbers between previous+1 and the smallest found number to missing_numbers
                            missing_numbers.update(x for x in range(previous + 1, first_found))
                            previous = first_found

                            custom_print(statement_type="SUCCESS", statement=f"Found expected page number on page {previous}.")

                        #   If there is no intersection between the sets of numbers, then too many pages are missing
                        #   and we believe there is no use in continuing
                        else:
                            custom_print(statement_type="WARNING", statement=f"Too many pages are missing. Last found page number was {previous}.")
                            quit()

            #   If starting index (for page numbers) hasn't been found
            else:

            #   Detection of three consecutive page numbers
                first_index, actual_page_number = find_first_index(found_numbers, page_index)

                #   If three consecutive page numbers are found, that means pagination has started
                if first_index != -1:
                    next_index = first_index + 1

                    custom_print(statement_type="INFO", statement=f"The first page with a page number is {next_index}.")
                    custom_print(statement_type="SUCCESS", statement=f"Found first three pages in order ({actual_page_number-2}, {actual_page_number-1}, {actual_page_number}).")
                    previous = actual_page_number
                else:
                    custom_print(statement_type="WARNING", statement=f"No page number found on PDF page {pdf_page_number}.")
        else:
            custom_print(statement_type="WARNING", statement="No page number found on PDF page 1.")

if len(missing_numbers) > 0:
    print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored(', '.join(str(x) for x in sorted(missing_numbers)), 'red', attrs=['bold'])}")
else:
    print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored('None', 'green', attrs=['bold'])}")

# Show some stats
print(f"\n{colored('Total pages in document','blue', attrs=['bold'])}: {len(doc)}")
print(f"{colored('Total pages with numbers','blue', attrs=['bold'])}: {len(found_numbers) - len(missing_numbers)}")
print(f"{colored('Total pages with missing numbers','blue', attrs=['bold'])}: {len(missing_numbers)}\n")

with open(f"{filename}_LOG.txt", "w") as file:
    file.writelines(log_messages)