import fitz, io
from pathlib import Path
from PIL import Image
from termcolor import colored
from multiprocessing import Pool, Manager, Lock, current_process

# own python scripts
from util import find_sequence, custom_print, extract_header_footer, log_messages

curr_dir = Path(__file__).parent
files = curr_dir / "files"
filename = files / "DIGI_2007_000118_01.pdf"

avg_height = 3520
avg_width = 2375

# Global Lock for synchronized prints/logs
print_lock = Lock()

def process_page(args):
    index, total_pages, shared_found_numbers = args
    local_log = []
    
    try:
        doc = fitz.open(filename)
        page = doc[index]
        xref = page.get_images()[0][0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size

        if width > avg_width*1.2 or height > avg_height*1.2:
            with print_lock:
                custom_print(statement_type="WARNING", statement=f"Found a probable double print on page {index + 1}")
        
        parsed_numbers = extract_header_footer(image)

        shared_found_numbers[index] = parsed_numbers
        return index, parsed_numbers, None  # `None` for missing page
    except Exception as e:
        with print_lock:
            custom_print(statement_type="WARNING", statement=f"Error on page {index + 1}: {str(e)}")
        return index, [], f"Error on page {index + 1}"

def sequential_analysis(found_numbers):
    previous = None
    missing_numbers = set()
    first_index = -1

    for page_index, parsed_numbers in sorted(found_numbers.items()):
        pdf_page_number = page_index + 1

        if len(parsed_numbers) == 0:
            if previous is not None:
                previous += 1
                missing_numbers.add(previous)
                custom_print(statement_type="WARNING", statement=f"Expected to find {previous} but found nothing")
            else:
                custom_print(statement_type="WARNING", statement=f"No page number found on PDF page {pdf_page_number}")
        else:
            if page_index >= 2:
                if previous is not None:
                    if previous+1 in parsed_numbers:
                        previous += 1
                        custom_print(statement_type="SUCCESS", statement=f"Found expected page number {previous}")
                    else:
                        expected_num = previous + 1
                        custom_print(statement_type="WARNING", statement=f"Expected to find {expected_num} but found {parsed_numbers} instead.")
                        missing_numbers.add(expected_num)

                        if all(x > len(found_numbers) or x < previous for x in parsed_numbers):
                            custom_print(statement_type="INFO", statement=f"Found numbers are outside of range: {parsed_numbers}.")
                            previous = find_sequence(list(found_numbers.values()), page_index, previous)
                            if previous is not None:
                                missing_numbers.remove(expected_num)
                        else:
                            cap_range = set(previous + i for i in range(2, 12))
                            common = cap_range & parsed_numbers
                            if len(common) > 0:
                                first_found = min(common)
                                missing_numbers.update(x for x in range(previous + 1, first_found))
                                previous = first_found
                                custom_print(statement_type="SUCCESS", statement=f"Found expected page number on page {previous}.")
                            else:
                                custom_print(statement_type="WARNING", statement=f"Too many pages are missing. Last found page number was {previous}.")
                                break
                else:
                    previous = find_sequence(list(found_numbers.values()), page_index, previous)
            else:
                custom_print(statement_type="WARNING", statement="No page number found on PDF page 1.")

    return missing_numbers

if __name__ == "__main__":
    doc = fitz.open(filename)
    num_pages = len(doc)

    with Manager() as manager:
        shared_found_numbers = manager.dict()

        with Pool() as pool:
            results = pool.map(process_page, [(i, num_pages, shared_found_numbers) for i in range(num_pages)])

        # Filter valid results
        found_numbers_dict = {i: set(parsed) for i, parsed, err in results if err is None}

        missing_numbers = sequential_analysis(found_numbers_dict)

        if len(missing_numbers) > 0:
            print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored(', '.join(str(x) for x in sorted(missing_numbers)), 'red', attrs=['bold'])}")
        else:
            print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored('None', 'green', attrs=['bold'])}")

        print(f"\n{colored('Total pages in document','blue', attrs=['bold'])}: {num_pages}")
        print(f"{colored('Total pages with numbers','blue', attrs=['bold'])}: {len(found_numbers_dict) - len(missing_numbers)}")
        print(f"{colored('Total pages with missing numbers','blue', attrs=['bold'])}: {len(missing_numbers)}\n")

        with open(f"{filename}_LOG.txt", "w") as file:
            file.writelines(log_messages)
