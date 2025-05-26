import fitz, sys, os
from pathlib import Path
from multiprocessing import Pool, Manager, cpu_count
# Extracted python logic
from util import find_sequence, custom_print, process_page, log_messages

# Creates a directory in /files if one doesn't exist already.
from datetime import date
today = "-".join(date.today().isoformat().split("-")[::-1])
# log_directory = f"../files/{today}"
log_directory = Path(__file__).parent.parent/"files"/today

os.makedirs(log_directory, exist_ok=True)


if len(sys.argv) < 2:
    print("Usage: python multi_main.py <path_to_pdf>")
    sys.exit(1)

filename = Path(sys.argv[1])
if not filename.exists():
    print(f"File not found: {filename}")
    sys.exit(1)

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

def main():
    previous = None
    first_index = -1
    missing_numbers = set()
    page_num_break = set()

    # Variable to check for swapped pages
    skipped_page = False

    with Manager() as manager:
        page_count = len(doc)

        progress_queue = manager.Queue()
        args = [(i, str(filename), progress_queue, previous) for i in range(page_count)]
        # print("Processing...")
        with Pool(processes=cpu_count()) as pool:
            found_numbers_result = pool.map_async(process_page, args)

            completed = 0
            while completed < page_count:
                progress_queue.get()
                completed += 1
                # print(f"\rProgress: {completed}/{page_count} ({(completed/page_count)*100:.1f}%)", end='')
            found_numbers_result = found_numbers_result.get()

        for page_index, parsed_numbers in enumerate(found_numbers_result):
            pdf_page_number = page_index
            found_numbers.append(parsed_numbers)

            #   If no numbers found on page
            if len(parsed_numbers) == 0:

                #   If pagination has started
                if previous is not None:
                    previous += 1
                    missing_numbers.add(previous)

                    page_num_break.add(previous)

                    # custom_print(statement_type="WARNING", statement=f"Expected to find {previous} but found nothing")

            #   If numbers have been found on current page
            else:
                if page_index >= 2:
                    if previous is not None:

                        #   If an increment of previous is on current page
                        #   i.e expected page number is previous page number+1
                        if previous+1 in parsed_numbers:
                            previous += 1

                            #   TODO Check 
                            if len(page_num_break) > 0:
                                if len(page_num_break) > 1:
                                    custom_print(statement_type="WARNING", statement=f"No page number found between pages {min(page_num_break)} - {max(page_num_break)}.")
                                else:
                                    custom_print(statement_type="WARNING", statement=f"No page number found one page {page_num_break[0]}.")
                                page_num_break = set()


                            custom_print(statement_type="SUCCESS", statement=f"Found expected page number {previous}")

                        #   Expected page number is not found on current page
                        else:
                            expected_num = previous + 1
                            missing_numbers.add(expected_num)

                            #   Check if numbers could be possible page numbers
                            if all(x > len(doc) - first_index or x < previous for x in parsed_numbers):
                                # When all numbers are out of range and the previous page was skipped,
                                # check if the previous found number - 1 is in found numbers on current page.
                                # When this is true, the pages are swapped.
                                if skipped_page: 
                                    custom_print(statement_type="WARNING", statement=f"SKIPPED PAGE SET {skipped_page}.") 
                                    skipped_page = False
                                    if previous - 1 in parsed_numbers:
                                        custom_print(statement_type="WARNING", statement=f"Page {previous - 1} and {previous} have swapped.")
                                        missing_numbers.remove(expected_num)

                                else: 

                                    custom_print(statement_type="INFO", statement=f"Found numbers are outside of range: {parsed_numbers}.")
                                    previous = find_sequence(found_numbers, page_index, previous)
                                    if previous is not None:
                                        missing_numbers.remove(expected_num)

                            else:
                                custom_print(statement_type="WARNING", statement=f"SKIPPED PAGE SET {skipped_page}. IS GOING TO BE SET FALSE") 
                                skipped_page = False
                                custom_print(statement_type="WARNING", statement=f"Expected to find {expected_num} but found {parsed_numbers} instead.")

                                #   Check if found page numbers are between previous and previous+10
                                cap_range = set(previous + i for i in range(2,12))
                                common = cap_range & parsed_numbers

                                #   If the intersection of both sets of numbers contains at least one number
                                if len(common) > 0:

                                    #   Lowest found number in intersection is **most likely** the next page number
                                    first_found = min(common)

                                    #   Add all numbers between previous+1 and the smallest found number to missing_numbers
                                    if type(previous) == type(first_found):
                                        missing_numbers.update(x for x in range(int(previous) + 1, int(first_found)))
                                        previous = first_found

                                    custom_print(statement_type="SUCCESS", statement=f"Found expected page number on page {previous}.")
                                    skipped_page = True
                                    custom_print(statement_type="WARNING", statement=f"SKIPPED PAGE SET {skipped_page}") 

                                #   If there is no intersection between the sets of numbers, then too many pages are missing
                                #   and we believe there is no use in continuing
                                else:
                                    custom_print(statement_type="WARNING", statement=f"Too many pages are missing. Last found page number was {previous}.")
                                    quit()

                    #   If starting index (for page numbers) hasn't been found
                    else:

                    #   Detection of three consecutive page numbers
                        previous = find_sequence(found_numbers, page_index, previous)

        log_messages.append(f"\nMissing pages: {', '.join(str(x) for x in sorted(missing_numbers)) if len(missing_numbers) > 0 else 'None'}")

        # Show some stats
        log_messages.append(f"\nTotal pages in document {len(doc)}")
        log_messages.append(f"\nTotal pages with numbers {len(found_numbers) - len(missing_numbers)}")
        log_messages.append(f"\nTotal pages with missing numbers {len(missing_numbers)}")

        log_file_location = f"{log_directory}/{filename.name}_LOG.txt"

        with open(log_file_location, "w") as file:
            file.writelines(log_messages)

        print(log_file_location)

if __name__ == "__main__":
    main()