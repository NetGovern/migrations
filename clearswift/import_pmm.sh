#!/usr/bin/bash
EXPORTED_ZIP_FILE="$1"
unzip $EXPORTED_ZIP_FILE
cp addresslists/pmm*.csv .
touch pmmpdbaccount.csv pmmpdbadopter.csv pmmpdbrcptlink.csv && tar cfj pmmwdb.gz pmm*.csv
psql -d pmi_operations -U postgres -c "delete from pmmw_whitelist; delete from pmmp_adopters; delete from pmmp_recipient_links; delete from pmmw_users; delete from pmmp_accounts;"
cp pmmwdb.gz /var/cs-gateway/pmm/awl/remote
