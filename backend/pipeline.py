import os
# TODO: change this to use the rust script instead of test.py
os.system("py test.py | py flagger.py")