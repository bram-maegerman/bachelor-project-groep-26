import os, subprocess
from pathlib import Path

current_dir = Path(__file__).parent

def find_subdirectory(target_name, search_path=current_dir):
    for root, dirs, _ in os.walk(search_path):
        if target_name in dirs:
            return Path(root) / target_name
    return None

def find_file(target_name, search_path=current_dir):
    for root, _, files in os.walk(search_path):
        if target_name in files:
            return Path(root) / target_name
    return None

scripts_dir = find_subdirectory('scripts')
if scripts_dir is None:
    raise FileNotFoundError("The 'scripts' directory was not found in the current directory or its subdirectories.")
else:
    gui = find_file('gui.py', scripts_dir)
    if gui is None:
        raise FileNotFoundError("The 'gui.py' file was not found in the 'scripts' directory.")
    else:
        print(f"Found 'gui.py' at: {gui}")
        subprocess.run(['python', gui], check=True)