import fitz, sys, os
from pathlib import Path
from multiprocessing import Pool, Manager, cpu_count
# Extracted python logic
from util import find_sequence, custom_print, process_page, log_messages
from roman_numeral import RomanNumeral

# Creates a directory in /files if one doesn't exist already.
from datetime import date
today = "-".join(date.today().isoformat().split("-")[::-1])
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

def find_next_sequence(all_found_numbers, current_key):
    for actual_page_num in all_found_numbers[current_key]:
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
            custom_print(statement_type="INFO", statement=f"Found sequence on page {current_key} : {actual_page_num}, {estimated_next_1}, {estimated_next_2}")
            return actual_page_num

    return None

def main():
    #   last found page number
    last_found_number = None
    #   expected number to find on current page
    expected_number = None
    #   dict of missing numbers, containing pdf page as key & expected page number as value
    missing_numbers = dict()
    skip_next = False

    with Manager() as manager:
        page_count = len(doc)

        # Multiprocessing
        progress_queue = manager.Queue()
        args = [(i, str(filename), progress_queue, last_found_number) for i in range(page_count)]
        with Pool(processes=cpu_count()) as pool:
            all_found_numbers_list = pool.map_async(process_page, args).get()
            all_found_numbers = {i + 1: val for i, val in enumerate(all_found_numbers_list)}

        #   Loop over all found numbers
        #   Every entry of all_found_numbers holds a set of numbers which are found a specific page
        #   This page is represented by the key in this loop
        for key, parsed_numbers in all_found_numbers.items():
            if skip_next:
                skip_next = False
                continue

            #   Increment expected number on each page if pagination has started
            if expected_number: expected_number += 1
            
            #   If no numbers are found on page
            if len(parsed_numbers) == 0:
                
                #   If pagination has started
                if last_found_number and expected_number:
                    missing_numbers[key] = expected_number

                    #TODO   Check if this is neccesary
                    # # custom_print(statement_type="WARNING", statement=f"No page number has been found on page {key}.")

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
                                custom_print(statement_type="WARNING", 
                                             statement=f"No page number found between pages {first_missing + key_page_num_diff} and {last_missing + key_page_num_diff}. Missing page numbers are {first_missing} - {last_missing}.")
                            else:
                                custom_print(statement_type="WARNING", statement=f"No page number found on page {key}. Missing page number is {last_missing}.")
                    
                        last_found_number = expected_number
                        custom_print(statement_type="SUCCESS", statement=f"Found expected page number {last_found_number} on page {key}")

                    #   Expected number is not in parsed numbers
                    else:
                        missing_numbers[key] = expected_number
                        if key == max(all_found_numbers):
                            custom_print(statement_type="WARNING", statement=f"No page number found on last page {key}. Manual check!")


                        #   Check if numbers could be possible page numbers
                        if all(x < last_found_number or x > len(all_found_numbers) 
                               for x in parsed_numbers):
                            sequence_start = find_next_sequence(all_found_numbers, key)
                            if sequence_start:
                                last_found_number = expected_number = sequence_start
                                del missing_numbers[key]
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
                                    skipped_page_numbers = {x for x in range(int(last_found_number) + 1, int(estimated_next_number))}
                                    
                                    #   Check if only one page has been skipped & the next page is the expected (pages have swapped)
                                    if len(skipped_page_numbers) == 1 and estimated_next_number - 1 in all_found_numbers[key + 1]:
                                        #   remove swapped page from missing numbers
                                        del missing_numbers[key]
                                        skip_next = True

                                        custom_print(statement_type="WARNING", statement=f"Page {key} and {key + 1} have swapped.")

                                    #   If pages aren't swapped, add all skipped pages to missing numbers
                                    else:
                                        missing_numbers[key] = skipped_page_numbers

                                    last_found_number = expected_number = estimated_next_number

                            else:
                                custom_print(statement_type="WARNING", statement=f"Too many pages are missing. Last found page number was {last_found_number}.")
                                # quit()   

                #   If pagination hasn't started, look for sequence
                else:
                    last_found_number = expected_number = find_next_sequence(all_found_numbers, key)

    log_messages.append(f"\nMissing pages: {', '.join(str(x) for x in sorted(missing_numbers)) if len(missing_numbers) > 0 else 'None'}")

    # Show some stats
    log_messages.append(f"\nTotal pages in document {len(doc)}")
    log_messages.append(f"\nTotal pages with numbers {len(all_found_numbers) - len(missing_numbers)}")
    log_messages.append(f"\nTotal pages with missing numbers {len(missing_numbers)}")

    log_file_location = f"{log_directory}/{filename.name}_LOG.txt"

    with open(log_file_location, "w") as file:
        file.writelines(log_messages)

    print(log_file_location)
    # # print(log_messages)
            
            
if __name__ == "__main__":
    main()