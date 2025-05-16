import fitz, io, pytesseract, re
from pathlib import Path
from PIL import Image, ImageEnhance
from multiprocessing import Pool, Manager, cpu_count
from termcolor import colored
from typing import Literal

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000118_01_DELETED_PAGE.pdf"
log_messages = []
missing_numbers = set()

def extract_numbers(full_image, *, upper, lower):
    
    """
    Given an image, we crop only part of it, \n
    we then perform OCR on this part, \n
    we then use regex to extract all numbers
    """

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

def find_first_index(found_numbers, current_index):
    """
        Given a list of found numbers for each page, \n
        if there are three consecutive numbers in three consecutive lists \n
        then we have found the starting page.
    """

    #   Loop over the found numbers on current index
    for num in found_numbers[current_index]:

        #   Check if the current number-1 appears in the found numbers on previous index (index-1)
        #   and if the current number-2 appears in the found numbers on the one before the previous index (index-2)
        if num - 1 in found_numbers[current_index - 1] and num - 2 in found_numbers[current_index - 2]:
            
            #   Returns the index of the first numbered page, along with the page number of the third page
            return (current_index - 2, num)

    #   Returns -1 if the index of the first numbered page is not found
    return (-1, None)

def custom_print(*, statement_type: Literal["INFO", "WARNING", "SUCCESS"], statement=None):
    """
    Given a statement and a statement_type, apply a custom style to it.
    Allowed types: INFO, WARNING, SUCCESS
    """
    #  Safety checks
    if statement_type not in {"INFO", "WARNING", "SUCCESS"}:
        raise TypeError(f'Expected statement_type to be one of ["INFO", "WARNING", "SUCCESS"], got {statement_type}')

    if not statement:
        raise ValueError("statement cannot be empty")

    if statement_type == "INFO":
        print(f"{colored('INFO', 'yellow')}:    {statement}")
        log_messages.append(f"[INFO]:    {statement}\n")

    elif statement_type == "WARNING":
        print(f"{colored('WARNING', 'red')}: {statement}")
        log_messages.append(f"[WARNING]: {statement}\n")

    elif statement_type == "SUCCESS":
        print(f"{colored('SUCCESS', 'green')}: {statement}")
        log_messages.append(f"[SUCCESS]: {statement}\n")

def process_page(args):
    page_index, pdf_path, progress_queue = args
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    xref = page.get_images(full=True)[0][0]
    base_image = doc.extract_image(xref)

    #   Reads bytes out of image
    image_bytes = base_image["image"]
    image = Image.open(io.BytesIO(image_bytes))

    header = extract_numbers(image, upper=0, lower=0.12)
    footer = extract_numbers(image, upper=0.87, lower=1)

    parsed_numbers = set()
    parsed_numbers.update(int(num) for num in header)
    parsed_numbers.update(int(num) for num in footer)
    progress_queue.put(1)
    return parsed_numbers


# Goes over all pages of the scanned pdf document
# Converts each page to an image
# Extract the header and footer from this image
# Scan these sections for numbers
# Adds those numbers to the found_numbers list
def main():
    doc = fitz.open(filename)
    page_count = len(doc)

    with Manager() as manager:
        progress_queue = manager.Queue()
        args = [(i, str(filename), progress_queue) for i in range(page_count)]
        print("Processing...")
        with Pool(processes=cpu_count()) as pool:
            found_numbers_result = pool.map_async(process_page, args)

            completed = 0
            while completed < page_count:
                progress_queue.get()
                completed += 1
                print(f"\rProgress: {completed}/{page_count} ({(completed/page_count)*100:.1f}%)", end='')
            found_numbers = found_numbers_result.get()
        previous = None
        first_index = -1

        for page_index, parsed_numbers in enumerate(found_numbers):
            pdf_page_number = page_index + 1
            print(f"\nProcessing PDF page: {pdf_page_number}")
            print(f"Found numbers: {parsed_numbers}")

            if not parsed_numbers:
    
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

                            # Check if numbers could be possible page numbers
                            if all(x > len(doc) - first_index or x < previous for x in parsed_numbers):
                                custom_print(statement_type="INFO", statement=f"Found numbers are outside of range: {parsed_numbers}.")
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
        print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored(', '.join(str(x) for x in missing_numbers), 'red', attrs=['bold'])}")
    else:
        print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored('None', 'green', attrs=['bold'])}")

    # Show some stats
    print(f"\n{colored('Total pages in document','blue', attrs=['bold'])}: {len(doc)}")
    print(f"{colored('Total pages with numbers','blue', attrs=['bold'])}: {len(found_numbers) - len(missing_numbers)}")
    print(f"{colored('Total pages with missing numbers','blue', attrs=['bold'])}: {len(missing_numbers)}\n")

    with open(f"{filename}_LOG.txt", "w") as file:
        file.writelines(log_messages)

if __name__ == "__main__":
    main()