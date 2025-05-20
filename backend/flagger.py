import sys, ast
from termcolor import colored

# Self written exported functions and variables
from util import find_first_index, custom_print, log_messages

# Average height and width of a pdf page
avg_height = 3520
avg_width = 2375




# TODO: still needed for this to function the same way: 
filename = "NEEDS_TO_BE_REPLACED"

for index, line in enumerate(sys.stdin):

    # Variables used in the flagging algorithm
    previous = None
    first_index = -1
    missing_numbers = set()

    # Convert input line to list of sets
    found_numbers_per_page = ast.literal_eval(line.strip())

    for page_index, page in enumerate(found_numbers_per_page):
        # If no numbers found on page
        if not page:
            if previous is not None:
                previous += 1
                missing_numbers.add(previous)
                custom_print(statement_type="WARNING", statement=f"Expected to find {previous} but found nothing")
            else:
                custom_print(statement_type="WARNING", statement=f"No page number found on PDF page {page_index + 1}")

        else:
            if page_index >= 2:
                if previous is not None:
                    if previous + 1 in page:
                        previous += 1
                        custom_print(statement_type="SUCCESS", statement=f"Found expected page number {previous}")
                    else:
                        expected_num = previous + 1
                        custom_print(statement_type="WARNING", statement=f"Expected to find {expected_num} but found {page} instead.")
                        missing_numbers.add(expected_num)

                        if all(x > len(found_numbers_per_page) - first_index or x < previous for x in page):
                            custom_print(statement_type="INFO", statement=f"Found numbers are outside of range: {page}.")
                            previous = expected_num
                        else:
                            cap_range = set(previous + i for i in range(2, 12))
                            common = cap_range & page

                            if len(common) > 0:
                                first_found = min(common)
                                missing_numbers.update(x for x in range(previous + 1, first_found))
                                previous = first_found
                                custom_print(statement_type="SUCCESS", statement=f"Found expected page number on page {previous}.")
                            else:
                                custom_print(statement_type="WARNING", statement=f"Too many pages are missing. Last found page number was {previous}.")
                                quit()
                else:
                    first_index, actual_page_number = find_first_index(found_numbers_per_page, page_index)
                    if first_index != -1:
                        next_index = first_index + 1
                        custom_print(statement_type="INFO", statement=f"The first page with a page number is {next_index}.")
                        custom_print(statement_type="SUCCESS", statement=f"Found first three pages in order ({actual_page_number - 2}, {actual_page_number - 1}, {actual_page_number}).")
                        previous = actual_page_number
                    else:
                        custom_print(statement_type="WARNING", statement=f"No page number found on PDF page {page_index + 1}")

    if len(missing_numbers) > 0:
        print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored(', '.join(str(x) for x in sorted(missing_numbers)), 'red', attrs=['bold'])}")
    else:
        print(f"\n{colored('Missing pages','red', attrs=['bold','underline'])}: {colored('None', 'green', attrs=['bold'])}")

    # Show some stats
    print(f"\n{colored('Total pages in document','blue', attrs=['bold'])}: {len(found_numbers_per_page)}")
    print(f"{colored('Total pages with numbers','blue', attrs=['bold'])}: {len(found_numbers_per_page) - len(missing_numbers)}")
    print(f"{colored('Total pages with missing numbers','blue', attrs=['bold'])}: {len(missing_numbers)}\n")

    with open(f"{filename}_LOG.txt", "w") as file:
        file.writelines(log_messages)