import os, sys

if len(sys.argv) < 2:
    print("Error: pipeline.py expects at least one argument")
    sys.exit(1)

pdf_paths = sys.argv[1:]

for pdf_path in pdf_paths:
    # TODO: change this to use the rust script instead of test.py
    os.system(f"py test.py {pdf_path} | py flagger.py")