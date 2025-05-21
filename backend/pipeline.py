import os, sys

if len(sys.argv) != 2:
    print("Error: pipeline.py expects 1 argument")
    sys.exit(1)

pdf_path = sys.argv[1]

# TODO: change this to use the rust script instead of test.py
os.system(f"py test.py {pdf_path} | py flagger.py")