import webview, os, threading, json, base64, fitz, sys, io, re, io, pytesseract, zipfile
from pathlib import Path
from datetime import date
from PIL import Image
from multiprocessing import Pool, Manager, cpu_count, freeze_support
from typing import Literal
from PIL import ImageEnhance, Image, ImageFilter
from roman_numeral import RomanNumeral

internal_dir = Path(__file__).parent
cur_dir = internal_dir.parent

CONFIG_FILE = internal_dir / "config.json"

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

def find_file(filename, search_path):
    for root, _, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None


class GUI:
    def __init__(self):
        self._window_loaded = threading.Event()
        self._latest_run = set()
        self._init_config()  #  Ensure config file exists with defaults
        self.projects, self.log_level = self._load_config()
        self.next_run = []
        self.next_export_path = None

    def _init_config(self):
        if not CONFIG_FILE.exists():
            default_config = {
                "projects": {},
                "log_level": 1
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=2)

    def _load_config(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                try:
                    data = json.load(f)
                    return (data.get("projects", {}), data.get("log_level", 1))
                except json.JSONDecodeError:
                    # In case of corrupted JSON, reset to default
                    self._init_config()
                    return ({}, 1)
        else:
            self._init_config()
            return ({}, 1)

    def _save_config(self):
        data = {
            "projects": self.projects,
            "log_level": self.log_level
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _save_projects(self, paths: list):
        self.projects = paths
        self._save_config()

    def choose_folder(self):
        window = webview.windows[0]
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0]
        else:
            return ""

    def set_log_level(self, log_level: int):
        self.log_level = log_level
        self._save_config()

    def add_project(self, name: str, path: str):
        if not name or not path:
            print("Project name and path cannot be empty.")
            return
        if not os.path.exists(path):
            print(f"Path '{path}' does not exist.")
            return
        if name in self.projects:
            print(f"Project '{name}' already exists.")
            return
        if not os.path.isabs(path):
            print(f"Path '{path}' must be an absolute path.")
            return
        if not os.path.isdir(path):
            print(f"Path '{path}' is not a directory.")
            return
        paths = self.projects
        paths[name] = path
        self._save_projects(paths)

    def remove_project(self, name: str):
        paths = self.projects
        try:
            pathname = paths[name]
            projects = self.get_files_for_project(name)
            del paths[name]
            if os.path.exists(pathname):
                # empty the directory
                for file in projects:
                    try:
                        os.remove(file + '_LOG.txt')
                    except Exception as e:
                        print(f"Error removing file '{file}': {e}")
            else:
                print(f"Path '{pathname}' does not exist, cannot remove files.")
            self._save_projects(paths)
        except KeyError:
            print(f"Project '{name}' not found.")
            return

    def edit_project(self, name: str, new_name: str, new_path: str):
        if not name or not new_name or not new_path:
            print("Project name, new name, and new path cannot be empty.")
            return
        if not os.path.exists(new_path):
            print(f"Path '{new_path}' does not exist.")
            return
        if name not in self.projects:
            print(f"Project '{name}' does not exist.")
            return
        if not os.path.isabs(new_path):
            print(f"Path '{new_path}' must be an absolute path.")
            return
        if not os.path.isdir(new_path):
            print(f"Path '{new_path}' is not a directory.")
            return

        paths = self.projects
        del paths[name]
        paths[new_name] = new_path
        self._save_projects(paths)

    def get_export_path(self, project: str):
        if project not in self.projects:
            print(f"Project '{project}' not found.")
            return None
        return self.projects[project]

    def get_projects(self):
        return self.projects

    def get_log_level(self):
        return self.log_level

    def set_log_level(self, level: int):
        self.log_level = level
        self._save_config()

    def get_files_for_project(self, project: str):
        projects = self.projects
        if project not in projects:
            print(f"Project '{project}' not found.")
            return []

        project_path = projects[project]
        if not os.path.exists(project_path):
            print(f"Project path '{project_path}' does not exist.")
            return []

        files = []
        for root, _, filenames in os.walk(project_path):
            for filename in filenames:
                if filename.endswith("_LOG.txt"):
                    file_path_without_suffix = os.path.join(root, filename).removesuffix("_LOG.txt")
                    files.append(file_path_without_suffix)
        return files

    def get_all_files(self):
        result = dict()

        projects: dict = self.projects

        for project in projects.keys():
            base_path = Path(projects[project])

            if not base_path.exists():
                continue

            for sub_dir in base_path.iterdir():
                if sub_dir.is_dir():
                    sub_result = []
                    for file in sub_dir.iterdir():
                        if file.name.endswith("_LOG.txt"):
                            file_path_without_suffix = str(file).removesuffix("_LOG.txt")
                            sub_result.append(file_path_without_suffix)

                    if sub_result:
                        result[f"{project}_{sub_dir.name}"] = sub_result
        return result


    def open_file_dialog(self):
        window = webview.windows[0]
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        return result if result else []

    def run_overview(self):
        webview.windows[0].evaluate_js(f"renderOverview({json.dumps(self.get_all_files())})")

    def run_last(self):
        webview.windows[0].evaluate_js(f"loadLastRunFiles({list(self._latest_run)})")

    def project_overview(self, project: str):
        files = self.get_files_for_project(project)
        if not files:
            print(f"No files found for project '{project}'.")
            return
        # Convert file paths to a JSON-compatible format
        files = [str(Path(file).resolve()) for file in files]
        webview.windows[0].evaluate_js(f"renderProjectOverview({json.dumps(files)})")

    def set_next(self, files: list):
        self.next_run = files

    def set_export_path(self, path: str):
        if not path:
            print("Export path cannot be empty.")
            return
        if not os.path.exists(path):
            print(f"Export path '{path}' does not exist.")
            return
        if not os.path.isabs(path):
            print(f"Export path '{path}' must be an absolute path.")
            return
        self.next_export_path = path

    def open_file(self, file_path: str):
        file_path = Path(file_path.replace("/", os.sep)).resolve()
        if not file_path.exists():
            print(f"File '{file_path}' does not exist.")
            return
        if not file_path.is_file():
            print(f"Path '{file_path}' is not a file.")
            return

        # open the file with like the file explorer
        if os.name == 'nt':  # Windows
            os.startfile(file_path)

    def update_progress(self, percentage: float):
        # Cast to string with 2 decimal places
        if not (0 <= percentage <= 100):
            print("Percentage must be between 0 and 100.")
            return

        # Update the progress bar in the webview
        webview.windows[0].evaluate_js(f"updatePercentage('{percentage:.2f}%')")

    def run_script_on_files(self):
        file_paths = [Path(x) for x in self.next_run]
        formatted_files = ["/".join(p.parts[-4:]) for p in file_paths]

        if not formatted_files:
            print("No files to process.")
            return

        if not self.next_export_path:
            print("No export path set.")
            return

        # Ensure the export path exists
        export_path = Path(self.next_export_path)
        if not export_path.exists():
            print(f"Export path '{self.next_export_path}' does not exist.")
            return

        webview.windows[0].evaluate_js(f"loadFilesInTable({formatted_files})")

        self._latest_run = set()

        for index, file_path in enumerate(self.next_run):
            current_file = formatted_files[index]
            # Updates table of files to see which one is processing a.t.m.
            webview.windows[0].evaluate_js(f"setFileInProgress({json.dumps(current_file)})")

            log_file_location = self.main_script(str(file_path), str(export_path))

            webview.windows[0].evaluate_js(f"startCompressing({json.dumps(current_file)})")

            # Run compression.exe instead of compression.py

            compress_pdf(str(file_path), str(log_file_location))

            success = log_file_location and os.path.exists(log_file_location) and log_file_location.endswith("_LOG.txt")

            # Updates table with the result of the current file
            result_object = {
                "file": current_file,
                "success": success,
            }
            webview.windows[0].evaluate_js(f"updateResult({json.dumps(result_object)})")

            if success:
                if log_file_location.endswith("_LOG.txt"):
                    file_name = log_file_location.removesuffix("_LOG.txt")
                    self._latest_run.add(file_name)

        webview.windows[0].evaluate_js(f"finished()")
        return

    def get_log(self, key):
        file_path = key + "_LOG.txt" #TODO revisit this
        if not os.path.exists(file_path):
            return "Log file not found."

        with open(file_path, "r") as f:
            text = f.read()

        summary_index = text.find("\n\n")


        log_lines = text[:summary_index]
        summary_block = text[summary_index:].split("\n")

        # Filter log_lines based on log_level
        filtered_logs = []
        for line in log_lines.split("\n"):
            if ")[W" in line:
                filtered_logs.append(line)
            if self.log_level == 2:
                if ")[I" in line:
                    filtered_logs.append(line)
            if self.log_level == 3:
                if ")[I" in line or ")[S" in line:
                    filtered_logs.append(line)

        filtered_logs.extend(summary_block)
        return "\n".join(filtered_logs)



    def read_pdf_as_data_url(self, path):
        path = Path(path.replace("/", os.sep)).resolve()

        if not path.exists():
            return None

        with open(path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f'data:application/pdf;base64,{encoded}'

    def change_manual_check_status(self, path, checkedBool):
        with open(path, 'r') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if line.strip().startswith('manually_checked='):
                lines[i] = f'manually_checked={"true" if checkedBool else "false"}\n'
                break

        with open(path, 'w') as file:
            file.writelines(lines)

    def create(self):
        webview.create_window("Scan-Checker", homepage, js_api=self, width=800, height=600, resizable=True, maximized=True)


    def start(self):
        webview.start(print("Starting GUI..."))


    def main_script(self, path_to_pdf: str, log_files_export_path: str):
        filename = Path(path_to_pdf)
        if not filename.exists():
            print(f"File not found: {filename}")
            return

        export_directory = Path(log_files_export_path)
        if not export_directory.exists():
            print(f"Directory not found: {export_directory}")
            return

        # Creates a directory in /files if one doesn't exist already.
        today = date.today().strftime("%d-%m-%Y")
        log_directory = export_directory / today
        os.makedirs(log_directory, exist_ok=True)
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

                    self.update_progress(completed / doc_len * 100)
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

        return log_file_location

def compress_page(args):
    pdf_path, page_index, dpi, image_quality = args
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
    doc.close()

    img_bytes = pix.tobytes("jpeg")
    img = Image.open(io.BytesIO(img_bytes))

    output_io = io.BytesIO()
    img.save(output_io, format="JPEG", quality=image_quality)
    output_io.seek(0)

    return (pix.width, pix.height, output_io.read())

def compress_pdf(input_pdf_path: str, log_file_location: str, image_quality: int = 50, dpi: int = 90):
    original_pdf_path = Path(input_pdf_path)
    if not original_pdf_path.exists():
        print(f"File not found: {original_pdf_path}")
        sys.exit(1)

    log_file_path = Path(log_file_location)
    if not log_file_path.exists():
        print(f"File not found: {log_file_path}")
        sys.exit(1)

    export_dir = log_file_path.parent
    output_pdf_path = export_dir / f"compressed_{original_pdf_path.name}"
    doc = fitz.open(input_pdf_path)
    num_pages = len(doc)
    doc.close()

    args = [(str(input_pdf_path), i, dpi, image_quality) for i in range(num_pages)]

    with Pool(processes=min(cpu_count(), num_pages)) as pool:
        results = pool.map(compress_page, args)

    new_doc = fitz.open()
    for width, height, img_data in results:
        img_rect = fitz.Rect(0, 0, width, height)
        new_page = new_doc.new_page(width=width, height=height)
        new_page.insert_image(img_rect, stream=img_data)

    new_doc.save(output_pdf_path)
    new_doc.close()

    with open(log_file_path, "a") as file:
        file.write(f"\n\nPath to original pdf: \n{original_pdf_path}\n")
        file.write(f"Path to compressed pdf: \n{output_pdf_path}\n")

    return output_pdf_path

if __name__ == "__main__":
    freeze_support()
    print(r"""

     _______.  ______     ___      .__   __.            ______  __    __   _______   ______  __  ___  _______ .______
    /       | /      |   /   \     |  \ |  |           /      ||  |  |  | |   ____| /      ||  |/  / |   ____||   _  \
   |   (----`|  ,----'  /  ^  \    |   \|  |  ______  |  ,----'|  |__|  | |  |__   |  ,----'|  '  /  |  |__   |  |_)  |
    \   \    |  |      /  /_\  \   |  . `  | |______| |  |     |   __   | |   __|  |  |     |    <   |   __|  |      /
.----)   |   |  `----./  _____  \  |  |\   |          |  `----.|  |  |  | |  |____ |  `----.|  .  \  |  |____ |  |\  \----.
|_______/     \______/__/     \__\ |__| \__|           \______||__|  |__| |_______| \______||__|\__\ |_______|| _| `._____|


    Scan-Checker - A tool to verify page numbers in scanned documents.


    Created by:
        - Davy Bellens
        - Elliott Leigh
        - Bram Maegerman
        - Brecht Saelens

    """)

    print("-" * 50)

    print("Starting Scan-Checker...")

    # Determine path to tesseract.exe (for both development and PyInstaller environments)
    if getattr(sys, 'frozen', False):  # running as bundled exe
        # Unzip the tesseract.zip file to the bin/tesseract directory
        tesseract_zip_path = os.path.join(sys._MEIPASS, 'bin', 'tesseract', 'tesseract.zip')

        # Check if the tesseract.zip file exists in the bundled resources
        if os.path.exists(tesseract_zip_path):
            print("As this is the first run, we need to unzip tesseract. This may take a while...")

            with zipfile.ZipFile(tesseract_zip_path, 'r') as zip_ref:
                print("Unzipping tesseract...")
                zip_ref.extractall(os.path.join(sys._MEIPASS, 'bin', 'tesseract'))

            print("Tesseract unzipped successfully.")

            # Remove the zip file after extraction
            os.remove(tesseract_zip_path)

        tesseract_path = os.path.join(sys._MEIPASS, 'bin', 'tesseract', 'tesseract', 'tesseract.exe')
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")

    gui = GUI()
    homepage = find_file("homepage.html", cur_dir.parent)

    if homepage is not None:
        gui.create()
        gui.start()
    else:
        print("Couldn't find homepage.")