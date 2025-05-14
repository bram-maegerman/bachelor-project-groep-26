import fitz, io, pytesseract, re
from pathlib import Path
from PIL import Image, ImageEnhance
import numpy as np

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000118_01.pdf"

doc = fitz.open(filename)

# All found numbers from header and footer scan
found_numbers = []

#uncomment to test with previously extracted values
# doc = fitz.open(None)
# found_numbers = [[1, 9000, 8794914, -10, 12, 1], [3, 8], [], [], [], [], [5], [], [], [1], [1, 2], [1, 3], [4], [2, 5], [2, 6], [2, 7, 8], [2, 8], [2, 9], [2, 10], [2, 11], [2, 12], [2, 13, 8], [2, 14], [2, 15, 8], [2, 16], [17], [3, 18], [3, 19], [3, 20], [21], [4, 22], [4, 23], [4, 24], [4, 25], [4, 26], [4, 27], [4, 28], [4, 29], [4, 30], [4, 31], [4, 32], [33], [5, 34], [5, 35], [5, 36], [5, 37], [5, 38, 0], [5, 39], [5, 40], [5, 41], [5, 42], [5, 43], [5, 44], [5, 45], [5, 46], [5, 47], [5, 48], [5, 49], [5, 50], [5, 51], [52], [53], [54], [55], [56], [57], [58, 8, 2, 8], [59], [60], [61], [62], [63], [64], [65], [66], [67, 2, 4], [68], [69, 25], [70], [71], [72], [73], [74], [75], [], [], [], [1], [], [], [82], [2, 5, 2, 6, 6, 6, 1, 2, 4, 4, 4, 8, 5, 2]]

# Goes over all pages of the scanned pdf document
# Converts each page to an image
# Extract the header and footer from this image
# Scan these sections for numbers
# Adds those numbers to the found_numbers list
for page_number in range(len(doc)):
    page = doc[page_number]
    xref = page.get_images(full=True)[0][0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]
    image = Image.open(io.BytesIO(image_bytes))

    width, height = image.size
    bottom = image.crop((
            int(width*0.05),
            int(height*0.87),
            int(width*0.95),
            int(height*1)
        )).convert("L")
    
    top = image.crop((
            int(width*0.05),
            int(height*0),
            int(width*0.95),
            int(height*0.12)
        )).convert("L")
    
    bottom = ImageEnhance.Contrast(bottom).enhance(2)
    top = ImageEnhance.Contrast(top).enhance(2)

    bottom_text = pytesseract.image_to_string(bottom, lang='eng', config=r'--psm 6')
    top_text = pytesseract.image_to_string(top, lang='eng', config=r'--psm 6')   

    top_numbers = re.findall(r'[-+]?\d+(?:\.\d+)?', top_text)         
    bottom_numbers = re.findall(r'[-+]?\d+(?:\.\d+)?', bottom_text)

    parsed_numbers = set()
    parsed_numbers.update(int(x) for x in top_numbers)
    parsed_numbers.update(int(x) for x in bottom_numbers)
    found_numbers.append(parsed_numbers)
    print(parsed_numbers)

# Return True or False if a specific number is inside a given list or set
def checkForNumber(array, num):
    return num in array

def recursive_check(page_numbers, wanted_number=1, missingNumbers:set=set()):
    if len(page_numbers) == 0:
        return missingNumbers
    if wanted_number not in page_numbers[0]:
        if wanted_number in missingNumbers:
            missingNumbers.remove(wanted_number)
        else:
            missingNumbers.add(wanted_number)

        return recursive_check(page_numbers[1:], wanted_number + 1, missingNumbers)
    return recursive_check(page_numbers[1:], wanted_number + 1, missingNumbers)

# Finding the first page with page numbers
firstPageWithPageNumber = -1
def find_first_page_with_page_number():
    for index in range(0, len(found_numbers) - 2):
        for num in found_numbers[index]:
            if checkForNumber(found_numbers[index + 1], num + 1) and checkForNumber(found_numbers[index + 2], num + 2):
                firstPageWithPageNumber = index
                break     
        if firstPageWithPageNumber != -1:
            break

def find_first_page_with_page_number_version_two():
    for index in range(0, len(found_numbers) - 2):
        # All numbers found on page with current index
        current_page_numbers = np.array(found_numbers[index])
        # Expected numbers on next page
        next_numbers = current_page_numbers + 1
        # Actual number of next page
        next_page_numbers = np.array(found_numbers[index + 1])
        # Intersection of expected and actual numbers
        common_numbers = np.intersect1d(next_page_numbers, next_numbers)

        if len(common_numbers) > 0:
            # Expected numbers on 2 pages ahead
            next_page = next_page_numbers + 1
            # Actual numbers on 2 pages ahead
            two_pages_ahead_numbers = np.array(found_numbers[index + 2])
            # Intersection of expected and actual numbers
            common_two_pages_ahead_numbers = np.intersect1d(two_pages_ahead_numbers, next_page)

            if len(common_two_pages_ahead_numbers) > 0:
                firstPageWithPageNumber = index
                break


if firstPageWithPageNumber == -1:
    print("Could not find a first page. " \
        "This could mean that the there is something wrong with the first 3 numerated pages")
else:
    print("The first page with a page number is " + str(firstPageWithPageNumber + 1))
    print(recursive_check(found_numbers[firstPageWithPageNumber:]))
    


    



