import re, fitz, io
from typing import Literal
import pytesseract
from PIL import ImageEnhance, Image, ImageFilter
from roman_numeral import RomanNumeral

log_messages = []
avg_height = 3520
avg_width = 2375

def extract_header_footer(full_image):
    # Crop header and footer
    header = full_image.crop((120, 20, 2250, 420))
    footer = full_image.crop((120, 3085, 2250, 3500))

    # Convert to grayscale
    header_gray = header.convert("L")
    footer_gray = footer.convert("L")

    # Apply binary threshold (turns into black & white only)
    threshold = 160  # Adjust as needed
    header_bw = header_gray.point(lambda x: 255 if x > threshold else 0, mode='1')
    footer_bw = footer_gray.point(lambda x: 255 if x > threshold else 0, mode='1')

    # Get dimensions
    width = header_bw.width
    header_height = header_bw.height
    footer_height = footer_bw.height
    gap = 0 # gap = 3085 - 420
    
    # Create a new black background image
    total_height = header_height + gap + footer_height
    combined_image = Image.new("L", (width, total_height), color=0)  # 'L' mode, black background

    # Paste header and footer
    combined_image.paste(header_bw, (0, 0))
    combined_image.paste(footer_bw, (0, header_height + gap))
    combined_image = combined_image.filter(ImageFilter.EDGE_ENHANCE_MORE)

    # OCR with contrast already handled by binarization
    content = pytesseract.image_to_string(
        combined_image,
        config=r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ivx'# -c tessedit_char_whitelist=0123456789ivxlcdIVXLCDM'
    )
        
    # Extract numbers and Roman numerals
    found_numbers = set(int(x) for x in re.findall(r'[-+]?\d+', content))
    found_romans = set(RomanNumeral(str(x).lower()) for x in re.findall(r'[ivx]+', content, re.IGNORECASE))

    return found_numbers.union(found_romans)


def extract_numbers(full_image, *, width, height, upper, lower):
    """
    Given an image, we crop only part of it, \n
    we then perform OCR on this part, \n
    we then use regex to extract all numbers
    """

    cropped = full_image.crop((
            int(width*0.05),
            int(height*upper),
            int(width*0.95),
            int(height*lower)
        ))


    cropped = ImageEnhance.Contrast(cropped).enhance(2)

    content = pytesseract.image_to_string(cropped, lang='eng', config=r'--psm 6')
    return re.findall(r'[-+]?\d+', content)

def find_sequence(found_numbers, current_index, previous=None):
    """
        Given a list of found numbers for each page, \n
        if there are three consecutive numbers in three consecutive lists \n
        then we have found the starting page.
    """

    #   Loop over the found numbers on current index
    for actual_page_number in found_numbers[current_index]:

        #   Check if the current number-1 appears in the found numbers on previous index (index-1)
        #   and if the current number-2 appears in the found numbers on the one before the previous index (index-2)
        estimated_previous_1 = actual_page_number - 1
        estimated_previous_2 = actual_page_number - 2

        if estimated_previous_1 in found_numbers[current_index - 1] and estimated_previous_2 in found_numbers[current_index - 2]:

            #   Returns the index of the first numbered page, along with the page number of the third page
            next_index = current_index - 1

            previous_1 = RomanNumeral(estimated_previous_1) if type(actual_page_number) == RomanNumeral else estimated_previous_1
            previous_2 = RomanNumeral(estimated_previous_2) if type(actual_page_number) == RomanNumeral else estimated_previous_2

            custom_print(statement_type="INFO", statement=f"The first page with a page number is {next_index}.")
            custom_print(statement_type="SUCCESS", statement=f"Found first three pages in order ({previous_2}, {previous_1}, {actual_page_number}).")
            return actual_page_number

    #   Returns -1 if the index of the first numbered page is not found
    #   If three consecutive page numbers are found, that means pagination has started
    return previous if previous else None

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
        # print(f"{colored('INFO', 'yellow')}:    {statement}")
        # log_messages.append(f"[INFO]:    {statement}\n")
        pass

    elif statement_type == "WARNING":
        # print(f"{colored('WARNING', 'red')}: {statement}")
        log_messages.append(f"[WARNING]: {statement}\n")

    elif statement_type == "SUCCESS":
        # print(f"{colored('SUCCESS', 'green')}: {statement}")
        # log_messages.append(f"[SUCCESS]: {statement}\n")
        pass

    return log_messages

def process_page(args):
    try:
        page_index, pdf_path, progress_queue, previous = args
        # print(f"Start processing page {page_index} - PID: {os.getpid()}")  

        doc = fitz.open(pdf_path)
        
            
        pdf_page_number = page_index + 1
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
        parsed_numbers = extract_header_footer(image)

        progress_queue.put(1)

        return parsed_numbers
    except Exception as e:
        print(f"Error processing page {args[0]}: {e}")
        progress_queue.put(1)
        return []
