import fitz, io, pytesseract, re
from pathlib import Path
from PIL import Image, ImageEnhance
import numpy as np

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

def find_first_page_with_page_number_previous(found_numbers, current_index):
    for num in found_numbers[current_index]:
        if num - 1 in found_numbers[current_index - 1] and num-2 in found_numbers[current_index - 2]:
            return (current_index - 2, num)
    return (-1, None)

#uncomment to test with previously extracted values
# doc = fitz.open(None)
# found_numbers = [[1, 9000, 8794914, -10, 12, 1], [3, 8], [], [], [], [], [5], [], [], [1], [1, 2], [1, 3], [4], [2, 5], [2, 6], [2, 7, 8], [2, 8], [2, 9], [2, 10], [2, 11], [2, 12], [2, 13, 8], [2, 14], [2, 15, 8], [2, 16], [17], [3, 18], [3, 19], [3, 20], [21], [4, 22], [4, 23], [4, 24], [4, 25], [4, 26], [4, 27], [4, 28], [4, 29], [4, 30], [4, 31], [4, 32], [33], [5, 34], [5, 35], [5, 36], [5, 37], [5, 38, 0], [5, 39], [5, 40], [5, 41], [5, 42], [5, 43], [5, 44], [5, 45], [5, 46], [5, 47], [5, 48], [5, 49], [5, 50], [5, 51], [52], [53], [54], [55], [56], [57], [58, 8, 2, 8], [59], [60], [61], [62], [63], [64], [65], [66], [67, 2, 4], [68], [69, 25], [70], [71], [72], [73], [74], [75], [], [], [], [1], [], [], [82], [2, 5, 2, 6, 6, 6, 1, 2, 4, 4, 4, 8, 5, 2]]
# found_numbers = [{1}, {2}, {3}, {5}, {6}]
# Goes over all pages of the scanned pdf document
# Converts each page to an image
# Extract the header and footer from this image
# Scan these sections for numbers
# Adds those numbers to the found_numbers list
previous = None
first_index_with_page_number = -1
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

    if len(parsed_numbers) == 0:
        if previous is not None:
            print(f"WARNING: Expected to find {previous+1}")
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
                    # previous+1 toevoegen aan missing numbers?

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
                    print(f"WARNING: No page number found on PDF page {pdf_page_number}.")

print(f"Missing pages: {missing_numbers}")



# # Return True or False if a specific number is inside a given list or set
# def check_for_number(array, num):
#     return num in array

# def recursive_check(page_numbers, wanted_number=1, missingNumbers:set=set()):
#     if len(page_numbers) == 0:
#         return missingNumbers
#     if wanted_number not in page_numbers[0]:
#         if wanted_number in missingNumbers:
#             missingNumbers.remove(wanted_number)
#         else:
#             missingNumbers.add(wanted_number)

#         return recursive_check(page_numbers[1:], wanted_number + 1, missingNumbers)
#     return recursive_check(page_numbers[1:], wanted_number + 1, missingNumbers)

# # Finding the first page with page numbers
# def find_first_page_with_page_number():
#     for index in range(0, len(found_numbers) - 2):
#         for num in found_numbers[index]:
#             if check_for_number(found_numbers[index + 1], num + 1) and check_for_number(found_numbers[index + 2], num + 2):
#                 return index

# def find_first_page_with_numpy():
#     for index in range(0, len(found_numbers) - 2):
#         # All numbers found on page with current index
#         current_page_numbers = np.array(found_numbers[index])
#         # Expected numbers on next page
#         next_numbers = current_page_numbers + 1
#         # Actual number of next page
#         next_page_numbers = np.array(found_numbers[index + 1])
#         # Intersection of expected and actual numbers
#         common_numbers = np.intersect1d(next_page_numbers, next_numbers)

#         if len(common_numbers) > 0:
#             # Expected numbers on 2 pages ahead
#             next_page = next_page_numbers + 1
#             # Actual numbers on 2 pages ahead
#             two_pages_ahead_numbers = np.array(found_numbers[index + 2])
#             # Intersection of expected and actual numbers
#             common_two_pages_ahead_numbers = np.intersect1d(two_pages_ahead_numbers, next_page)

#             if len(common_two_pages_ahead_numbers) > 0:
#                 return index

# first_page_with_page_number = find_first_page_with_page_number() or -1
# if first_page_with_page_number == -1:
#     print("Could not find a first page. " \
#         "This could mean that the there is something wrong with the first 3 numerated pages")
# else:
#     print("The first page with a page number is " + str(first_page_with_page_number + 1))
#     missing_numbers = recursive_check(found_numbers[first_page_with_page_number:])
#     for num in missing_numbers:
#         print(f"WARNING: No page number found on page {num}.")
# # gives warning for every missing number