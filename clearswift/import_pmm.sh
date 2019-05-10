#!/bin/bash

# Argument: zip file with at least the addresslists directory at the top level.
# Usage: ./import_pmm.sh file.zip

# Check if running as root
if [ $EUID -ne 0 ]; then
	echo "[!] This script must be run as root"
	echo "[-] Exiting the script."
	exit 1
fi

# Define variables from the argument
EXPORTED_ZIP_FILE="$1"

# Import PMM
unzip $EXPORTED_ZIP_FILE

# Test if the addresslists directory is present in the current directory
if [ ! -d addresslists ]; then
	echo "Could not find addresslists directory, is it at the top level of the zip file?"
    exit 2
fi

cp addresslists/pmm*.csv .
touch pmmpdbaccount.csv pmmpdbadopter.csv pmmpdbrcptlink.csv && tar cfj pmmwdb.gz pmm*.csv
psql -d pmi_operations -U postgres -c "delete from pmmw_whitelist; delete from pmmp_adopters; delete from pmmp_recipient_links; delete from pmmw_users; delete from pmmp_accounts;"
cp pmmwdb.gz /var/cs-gateway/pmm/awl/remote
