import json
import argparse

def parseMe():
    parser = argparse.ArgumentParser(
        description="Export NetGovern Allow/Block lists and Attachment Blocking export for ClearSwift")
    parser.add_argument("-f", "--backup-file",
                        dest="backupFile",
                        required=True,
                        help="Path to the NetGovern Secure backup file (v6+ format)")
    return parser.parse_args()

parameters = parseMe()
backupFile = parameters.backupFile
count = 0
with open(backupFile) as bkp:
    for line in bkp:
        count += 1
        if not isinstance(line, str):
            print("Not a string at {0}".format(count))
        if isinstance(line, bytes):
            print("Unicode at {0}".format(count))
print("Processed {0}".format(count))

print("Trying to parse file as JSON")
with open(backupFile) as bkp:
    backupData = json.load(bkp)