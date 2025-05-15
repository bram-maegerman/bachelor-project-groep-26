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

    """
    Given an image, we crop only part of it, \n
    we then perform OCR on this part, \n
    we then use regex to extract all numbers
    """

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
    """
        Given a list of found numbers for each page, \n
        if there are three consecutive numbers in three consecutive lists \n
        then we have found the starting page.
    """

    #   Loop over the found numbers on current index
    for num in found_numbers[current_index]:

        #   Check if the current number-1 appears in the found numbers on previous index (index-1)
        #   and if the current number-2 appears in the found numbers on the one before the previous index (index-2)
        if num - 1 in found_numbers[current_index - 1] and num-2 in found_numbers[current_index - 2]:

            #   Returns the index of the first numbered page, along with the page number of the third page
            return (current_index - 2, num)
    
    #   Returns -1 if the index of the first numbered page is not found
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

    #   If numbers have been found on current page
    else:
        if page_index >= 2:
            if previous is not None:

                #   If an increment of previous is on current page
                #   i.e expected page number is previous page number+1
                if previous+1 in parsed_numbers:
                    previous += 1
                    print(f"{colored('SUCCESS', 'green')}: Found expected page number {previous}")

                #   Expected page number is not found on current page
                else:
                    expected_num = previous + 1
                    print(f"{colored('WARNING', 'red')}: Expected to find {expected_num} but found {parsed_numbers} instead.")
                    missing_numbers.add(expected_num)

                    # Check if numbers could be possible page numbers
                    if all(x > len(doc) - first_index or x < previous for x in parsed_numbers):
                        print(f"{colored('INFO', 'yellow')}: Found numbers are outside of range: {parsed_numbers}.")
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
                            print(f"{colored('SUCCESS', 'green')}: Found expected page number on page {previous}")

                        #   If there is no intersection between the sets of numbers, then too many pages are missing
                        #   and we believe there is no use in continuing
                        else:
                            print(f"{colored('WARNING', 'red')}: Too many missing pages. Last found page number was {previous}")
                            quit()

            #   If starting index (for page numbers) hasn't been found 
            else:

            #   Detection of three consecutive page numbers  
                first_index, actual_page_number = find_first_index(found_numbers, page_index)

                #   If three consecutive page numbers are found, that means pagination has started
                if first_index != -1:
                    print(f"{colored('INFO', 'yellow')}: The first page with a page number is {first_index + 1}")
                    previous = actual_page_number
                else:
                    print(f"{colored('WARNING', 'red')}: No page number found on PDF page {pdf_page_number}.")

print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {missing_numbers}")