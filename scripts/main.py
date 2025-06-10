import fitz, sys, os
from pathlib import Path
from multiprocessing import Pool, Manager, cpu_count
from datetime import date

# Extracted python logic
from util import find_sequence, custom_print, process_page, log_messages

if len(sys.argv) < 3:
    print("Usage: python multi_main.py <path_to_pdf> <log_files_export_path>")
    sys.exit(1)

filename = Path(sys.argv[1])
if not filename.exists():
    print(f"File not found: {filename}")
    sys.exit(1)

export_directory = Path(sys.argv[2])
if not export_directory.exists():
    print(f"Directory not found: {export_directory}")
    sys.exit(1)

# Creates a directory in /files if one doesn't exist already.
today = date.today().strftime("%d-%m-%Y")
log_directory = export_directory / today
os.makedirs(log_directory, exist_ok=True)

def main():
    #   last found page number
    last_found_number = None
    #   expected number to find on current page
    expected_number = None
    #   dict of missing numbers, containing pdf page as key & expected page number as value
    missing_numbers = dict()
    skip_next = False

    with Manager() as manager:
        # This list shared among processes and gets passed to the process_page method, so that process errors also get added to log_messages
        process_messages = manager.list()

        doc = fitz.open(filename)
        doc_len = len(doc)

        # Multiprocessing
        progress_queue = manager.Queue()
        args = [(doc.extract_image(doc[i].get_images()[0][0]), i, doc_len, progress_queue, process_messages) for i in range(doc_len)]
        with Pool(processes=cpu_count()) as pool:
            all_found_numbers_list = pool.map_async(process_page, args)

            completed = 0
            while completed < doc_len:
                progress_queue.get()
                completed += 1
                print(f"\r{completed/doc_len*100:.1f}%", end="", flush=True)
            all_found_numbers = {i + 1: val for i, val in enumerate(all_found_numbers_list.get())}


        # list(dict.fromkeys(process_messages)) removes duplicates from the list
        log_messages.extend(list(dict.fromkeys(process_messages)))

        #   Loop over all found numbers
        #   Every entry of all_found_numbers holds a set of numbers which are found a specific page
        #   This page is represented by the key in this loop
        for key, parsed_numbers in all_found_numbers.items():
            if skip_next:
                skip_next = False
                continue

            #   Increment expected number on each page if pagination has started
            if expected_number:
                expected_number += 1

            #   If no numbers are found on page
            if len(parsed_numbers) == 0:

                #   If pagination has started
                if last_found_number and expected_number:
                    missing_numbers[key] = expected_number
                    if key == max(all_found_numbers):
                        custom_print(pdf_page=key, statement_type="WARNING", statement=f"No page number found on last page {key}. Manual check!")

            #   If numbers are found on page
            else:
                if last_found_number:
                    if expected_number in parsed_numbers:
                        #   amount of consecutive missing numbers
                        amt_consec_missing_numbers = expected_number - 1 - int(last_found_number)

                        if amt_consec_missing_numbers > 0:
                            #   find the first & last missing number in amt_consec_missing_numbers
                            first_missing = expected_number - amt_consec_missing_numbers
                            last_missing = expected_number - 1

                            #   Difference between PDF page & page number
                            key_page_num_diff = key - expected_number

                            if amt_consec_missing_numbers > 1:
                                custom_print(pdf_page=key, statement_type="WARNING",
                                             statement=f"No page number found between pages {first_missing + key_page_num_diff} and {last_missing + key_page_num_diff}. Missing page numbers are {first_missing} - {last_missing}.")
                            else:
                                custom_print(pdf_page=key, statement_type="WARNING", statement=f"No page number found on page {key - 1}. Missing page number is {last_missing}.")

                        last_found_number = expected_number
                        custom_print(pdf_page=key, statement_type="SUCCESS", statement=f"Found expected page number {last_found_number} on page {key}.")

                    #   Expected number is not in parsed numbers
                    else:
                        missing_numbers[key] = expected_number
                        if key == max(all_found_numbers):
                            custom_print(pdf_page=key, statement_type="WARNING", statement=f"No page number found on last page {key}. Manual check!")
                        else:
                            #   Check if numbers could be possible page numbers
                            if all(x < last_found_number or x > len(all_found_numbers)
                                for x in parsed_numbers):
                                if expected_number + 1 in all_found_numbers[key + 1]:
                                    last_found_number = expected_number
                                    custom_print(pdf_page=key, statement_type="WARNING", statement=f"No page number found on page {key}. Missing page number is {expected_number}.")
                                else:
                                    sequence_start = find_sequence(all_found_numbers, key)
                                    if sequence_start:
                                        last_found_number = expected_number = sequence_start
                                        del missing_numbers[key]
                                    #  Print warning when all found numbers are out of range and no new sequence is found
                                    else:
                                        custom_print(pdf_page=key, statement_type="WARNING", statement=f"No page number found on page {key}. Missing page number is {expected_number}.")
                                        # Sets the last_found_number to the expected number so the print doesn't get shown in the next entry.
                                        last_found_number = expected_number
                            else:
                                #   Check if found page numbers are between previous and previous+10
                                cap_range = set(last_found_number + i for i in range(2, 12))
                                common = cap_range & parsed_numbers

                                if len(common) > 0:
                                    #   Lowest found number in intersection is **most likely** the next page number
                                    estimated_next_number = min(common)

                                    #   Add all numbers between previous+1 and the smallest found number to missing_numbers
                                    if type(last_found_number) == type(estimated_next_number):
                                        #   All page numbers that have been skipped
                                        skipped_page_numbers = [x for x in range(int(last_found_number) + 1, int(estimated_next_number))]

                                        #   Check if only one page has been skipped & the next page is the expected (pages have swapped)
                                        if len(skipped_page_numbers) == 1 and estimated_next_number - 1 in all_found_numbers[key + 1]:
                                            #   remove swapped page from missing numbers
                                            del missing_numbers[key]
                                            skip_next = True

                                            custom_print(pdf_page=key, statement_type="WARNING", statement=f"Page {key} and {key + 1} have swapped.")

                                        #   If pages aren't swapped, add all skipped pages to missing numbers
                                        else:
                                            missing_numbers[key] = skipped_page_numbers
                                            if len(skipped_page_numbers) == 1:
                                                custom_print(pdf_page=key, statement_type="WARNING", statement=f"Page number {skipped_page_numbers[0]} was skipped on page {key}.")
                                            else:
                                                custom_print(pdf_page=key, statement_type="WARNING", statement=f"Page numbers {', '.join(str(x) for x in skipped_page_numbers)} were skipped on page {key}.")


                                        last_found_number = expected_number = estimated_next_number

                                else:
                                    continue

                #   If pagination hasn't started, look for sequence
                else:
                    last_found_number = expected_number = find_sequence(all_found_numbers, key)

    if len(log_messages) == 0:
        custom_print(pdf_page=0, statement_type="WARNING", statement=f"No status messages are present in this log file, this could mean that something went wrong during the execution of the script.")

    log_messages.append(f"\nMissing pages: {', '.join(str(x) for x in sorted(missing_numbers)) if len(missing_numbers) > 0 else 'None'}")

    # Show some stats
    log_messages.append(f"\nTotal pages in document {len(doc)}")
    log_messages.append(f"\nTotal pages with numbers {len(all_found_numbers) - len(missing_numbers)}")
    log_messages.append(f"\nTotal pages with missing numbers {len(missing_numbers)}")

    log_messages.append(f"\n\nmanually_checked=false")

    log_file_location = f"{log_directory}/{filename.name}_LOG.txt"

    with open(log_file_location, "w") as file:
        file.writelines(log_messages)

    print(f"\n{log_file_location}")


if __name__ == "__main__":
    main()