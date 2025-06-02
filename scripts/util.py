import re, fitz, io
from typing import Literal
import pytesseract
from PIL import ImageEnhance, Image, ImageFilter
from roman_numeral import RomanNumeral

log_messages = []

def extract_header_footer(full_image, doc_len=None):
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

    return to_string(combined_image, doc_len=doc_len)

def to_string(image, psm=None, whitelist=None, doc_len=1000):
    custom_psm = psm or 6
    if custom_psm < 0 or custom_psm > 13:
        raise "psm must be between 0 and 13"
    custom_whitelist = whitelist or "0123456789ivx"
    custom_config = f"--oem 2 --psm {custom_psm} -c tessedit_char_whitelist={custom_whitelist}"
    # OCR with contrast already handled by binarization
    content = pytesseract.image_to_string(image, config=custom_config)

    if not content: 
        if custom_psm == 13:
            return set()
        else:
            return to_string(image, psm=custom_psm + 1, whitelist=whitelist)
        
    else:
        # Extract numbers and Roman numerals
        found_numbers = set(int(x) for x in re.findall(r'[-+]?\d+', content) if int(x) < doc_len)

        found_romans = set()
        for x in re.findall(r'[ivx]+', content, re.IGNORECASE):
            try:
                roman = RomanNumeral(str(x).lower())
                if roman.decimal_value < doc_len:
                    found_romans.add(roman)
            except ValueError:
                pass

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

def find_sequence(all_found_numbers, current_key):
    for actual_page_num in all_found_numbers[current_key]:

        # Skips sequence check for this number if it is 0
        if actual_page_num == 0:
            continue

        estimated_next_1 = actual_page_num + 1
        estimated_next_2 = actual_page_num + 2

        if not (1 <= estimated_next_1 <= 3999 and 1 <= estimated_next_2 <= 3999):
            continue

        next_page_1 = all_found_numbers.get(current_key + 1, set())
        next_page_2 = all_found_numbers.get(current_key + 2, set())

        found_next_1 = (
            estimated_next_1 in next_page_1
            or str(estimated_next_1) in next_page_1
            or RomanNumeral(estimated_next_1).roman_representation.lower() in next_page_1
        )

        found_next_2 = (
            estimated_next_2 in next_page_2
            or str(estimated_next_2) in next_page_2
            or RomanNumeral(estimated_next_2).roman_representation.lower() in next_page_2
        )

        # Convert to roman if initial value of sequence is roman
        if type(actual_page_num) == RomanNumeral:
            estimated_next_1 = RomanNumeral(estimated_next_1)
            estimated_next_2 = RomanNumeral(estimated_next_2)

        if found_next_1 and found_next_2:
            custom_print(pdf_page=current_key, statement_type="INFO", statement=f"Found sequence on page {current_key} : {actual_page_num}, {estimated_next_1}, {estimated_next_2}")
            return actual_page_num

    return None

def custom_print(*, pdf_page=0, statement_type: Literal["INFO", "WARNING", "SUCCESS"], statement=None):
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
        log_messages.append(f"({pdf_page})[INFO]:    {statement}\n")
        pass

    elif statement_type == "WARNING":
        # print(f"{colored('WARNING', 'red')}: {statement}")
        log_messages.append(f"({pdf_page})[WARNING]: {statement}\n")

    elif statement_type == "SUCCESS":
        # print(f"{colored('SUCCESS', 'green')}: {statement}")
        log_messages.append(f"({pdf_page})[SUCCESS]: {statement}\n")
        pass

    return log_messages

def double_scan(image: Image):
    # From our analysis we concluded that:
    # Average height of pdf page = 3520
    # Average width of pdf page = 2375
    #
    # We allow a margin of 20%. Multiplying these values by 1.2 we get:
    # 4224 and 2850 for height and width respectively

    width, height = image.size

    return height > 4224 or width > 2850

def process_page(args):
    try:
        base_image, page_index, doc_len, progress_queue, process_messages = args
        # print(f"Start processing page {page_index} - PID: {os.getpid()}")  

        #   Reads out the bytes of the image
        image_bytes = base_image["image"]

        #   Creates an image from those bytes
        image = Image.open(io.BytesIO(image_bytes))

        if double_scan(image):
            custom_print(pdf_page=page_index + 1, statement_type="WARNING", statement=f"Found a probable double print on pdf page {page_index + 1}")
        #   Extract the numbers from the header and footer (defined by upper and lower)
        parsed_numbers = extract_header_footer(image, int(doc_len))

        progress_queue.put(1)

        # All log messages during processing get added to the shared memory list, so they don't get lost in seperate mutliprocessing memory
        if len(log_messages) > 0:
            process_messages.extend(log_messages)

        return parsed_numbers

    except Exception as e:
        print(f"Error processing page {args[1]}: {e}")
        progress_queue.put(1)
        return []
    

def compress_pdf(input_pdf_path: str, output_pdf_path: str, image_quality: int = 50, dpi: int = 100):
    """
    Compress a PDF images by reducing DPI and JPEG quality.

    :param input_pdf_path: Path to the input PDF
    :param output_pdf_path: Path to save the compressed PDF

    :param image_quality: JPEG quality (1-100), lower means more compression
    :param dpi: Dots per inch to render each page (lower = more compression)
    """
    doc = fitz.open(input_pdf_path)
    new_doc = fitz.open()

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))

        img_bytes = pix.tobytes("jpeg")
        img = Image.open(io.BytesIO(img_bytes))

        output_io = io.BytesIO()
        img.save(output_io, format="JPEG", quality=image_quality)
        output_io.seek(0)

        img_rect = fitz.Rect(0, 0, pix.width, pix.height)
        new_page = new_doc.new_page(width=img_rect.width, height=img_rect.height)
        new_page.insert_image(img_rect, stream=output_io.read())

    new_doc.save(output_pdf_path)
    doc.close()
    new_doc.close()

    return output_pdf_path
