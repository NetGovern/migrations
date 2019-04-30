#!/usr/bin/bash

echo "Processing Media type templates" 
EXPORTED_ZIP_FILE="$1"
mkdir templates
cp $EXPORTED_ZIP_FILE templates/
cd templates
unzip $EXPORTED_ZIP_FILE
cp *.xml /var/cs-gateway/uicfg/policy/rules/

echo "Processing Attachment blocking rules and file lists"
cd ../
cp filenames/*.xml /var/cs-gateway/uicfg/policy/filenames/
cp rules/*.xml /var/cs-gateway/uicfg/policy/rules/

cs-servicecontrol restart tomcat

echo "Please login to Clearswift UI to apply the configuration"