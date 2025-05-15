# Scan-Checker: Script to check to completeness of a scanned PDF
This script takes a PDF scan as an input, and outputs different messages based on different scenarios

### Different types of messages
- "INFO" : These messages are there to give the user as much detail as possible, but do not necessarily indicate a problem.
- "SUCCESS" : These messages indicate that a certain page is the expected next page.
- "WARNING" : These messages indicate a problem with a certain page, e.g. no page number was found on that page or the expected page number is missing.
- messages without a prefix are purely informative and can be ignored.

#### Purpose of output
This output is used to inform the user when something is wrong with a certain page, so the user can do a more specific manual check.
The output will later be displayed in a GUI to the user.

### How to use

<b> Make sure python and packages used in this script are correctly installed.</b>

Open the command line and make sure you navigate to the folder where the script is located.
Inside this command line, type `py main.py <absolute path to scanned pdf>` and press enter. Make sure to replace `<absolute path to scanned pdf>` with the absolute path of the scanned PDF on your machine.
