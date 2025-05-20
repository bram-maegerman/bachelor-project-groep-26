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


import sys, ast

for index, line in enumerate(sys.stdin):
    line = line.strip()
    sets_list = ast.literal_eval(line)  # now a list of sets

    for page_index, page_numbers in enumerate(sets_list):
        # If no numbers found on page
        if not page_numbers:
            if previous is not None:
                previous += 1
                missing_numbers.add(previous)
                custom_print(statement_type="WARNING", statement=f"Expected to find {previous} but found nothing")
            else:
                custom_print(statement_type="WARNING", statement=f"No page number found on PDF page {page_index + 1}")

        else:
            found_numbers.append(page_numbers)  # Don't forget to track these!

            if page_index >= 2:
                if previous is not None:
                    if previous + 1 in page_numbers:
                        previous += 1
                        custom_print(statement_type="SUCCESS", statement=f"Found expected page number {previous}")
                    else:
                        expected_num = previous + 1
                        custom_print(statement_type="WARNING", statement=f"Expected to find {expected_num} but found {page_numbers} instead.")
                        missing_numbers.add(expected_num)

                        if all(x > len(doc) - first_index or x < previous for x in page_numbers):
                            custom_print(statement_type="INFO", statement=f"Found numbers are outside of range: {page_numbers}.")
                            previous = expected_num
                        else:
                            cap_range = set(previous + i for i in range(2, 12))
                            common = cap_range & page_numbers

                            if len(common) > 0:
                                first_found = min(common)
                                missing_numbers.update(x for x in range(previous + 1, first_found))
                                previous = first_found
                                custom_print(statement_type="SUCCESS", statement=f"Found expected page number on page {previous}.")
                            else:
                                custom_print(statement_type="WARNING", statement=f"Too many pages are missing. Last found page number was {previous}.")
                                quit()
                else:
                    first_index, actual_page_number = find_first_index(found_numbers, page_index)
                    if first_index != -1:
                        next_index = first_index + 1
                        custom_print(statement_type="INFO", statement=f"The first page with a page number is {next_index}.")
                        custom_print(statement_type="SUCCESS", statement=f"Found first three pages in order ({actual_page_number - 2}, {actual_page_number - 1}, {actual_page_number}).")
                        previous = actual_page_number
                    else:
                        custom_print(statement_type="WARNING", statement=f"No page number found on PDF page {page_index + 1}")

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