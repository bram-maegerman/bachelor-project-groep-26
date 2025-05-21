import pytesseract, re
from PIL import ImageEnhance
from termcolor import colored
from typing import Literal

log_messages = []

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
    
    return log_messages