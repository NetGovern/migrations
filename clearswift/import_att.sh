#!/bin/bash

# Argument: zip file with at least the templates, filenames, and rules directory at the top level.
# Usage: ./import_pmm.sh file.zip

# Check if running as root
if [ $EUID -ne 0 ]; then
        echo "[!] This script must be run as root"
        echo "[-] Exiting the script."
        exit 1
fi

echo "Processing Media type templates" 
# Define variables from the argument
EXPORTED_ZIP_FILE="$1"
UI_RESTART=0

unzip $EXPORTED_ZIP_FILE
# Test if the templates directory is present in the current directory. Otherwise ignore and move on.
if [ -d templates ]; then
	cp templates/*.xml /var/cs-gateway/uicfg/policy/rules/
    UI_RESTART=1
    else echo "No templates directory. Ignoring"
fi

echo "Processing Attachment blocking rules and file lists"
if [[ -d filenames && -d rules ]]; then
	cp filenames/*.xml /var/cs-gateway/uicfg/policy/filenames/
	cp rules/*.xml /var/cs-gateway/uicfg/policy/rules/
    UI_RESTART=1
    else echo "No filenames or rules directory. Ignoring"
fi

if [ $UI_RESTART -eq 1 ]; then
	echo "Changes made. Restart tomcat"
	cs-servicecontrol restart tomcat
    echo "Please login to Clearswift UI to apply the configuration"
fi
