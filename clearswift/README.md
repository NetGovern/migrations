# NetGovern Secure export scripts to Clearswift

The following python scripts process a 6.0+ secure backup file in order to export:

1. System and user defined whitelisted addresses
2. Custom Attachment blocking policies based on filenames and file extensions

## Pre-requisites

Python 3+ with the following modules:

* argparse
* lxml
* uuid

```bash
python3 -m pip install argparse lxml uuid
```

---

## secureExport.py

```bash
python3 ./secureExport.py -h
usage: secureExport.py [-h] -f BACKUPFILEPATH [-t]

Export NetGovern Allow/Block lists and Attachment Blocking exportfor ClearSwift

optional arguments:
  -h, --help            show this help message and exit
  -f BACKUPFILEPATH, --backup-file BACKUPFILEPATH
                        Path to the NetGovern Secure backup file (v6+ format)
  -t, --export-templates
                        enable Templates export

```

It exports custom Attachment Blocking policies or policies that were modified from the default ones provided by the NetGovern.  
Using the option --export-templates will output all of the policies (Default templates and custom/modified)
The output is 2 XML files per policy, ready to be used by Clearswift.

It also exports system whitelists, internal mail servers and user whitelists.
In the case of user whitelists, it will produce output for each alias of the domain.
The output is a set of csv and txt files ready to be used by Clearswift.

---

## Example

```bash
python3 .\secureExport.py -f .\netmail.wbackup
Exporting policy: datcard\iso-qt
Exporting policy: Policy Templates\Executables and Scripts\Deliver to Mailbox
The following files were created:
{
  "addressesLists": [
    "files_20190429-103454/addresslists/pmmwdbusers.csv",
    "files_20190429-103454/addresslists/pmmwdbsenders.csv",
    "files_20190429-103454/addresslists/sec01ca-client_allow_list_email_addresses.txt",
    "files_20190429-103454/addresslists/sec01ca-client_allow_list_ip_addresses.txt",
    "files_20190429-103454/addresslists/sec01ca-client_block_list_email_addresses.txt",
    "files_20190429-103454/addresslists/sec01ca-client_internal_mail_servers.txt"
  ],
  "datcard\\iso-qt": [
    "files_20190429-103454/filenames/86e4cb1b-368b-4e81-b106-ad85f116c601.xml",
    "files_20190429-103454/rules/4305dae2-1597-4af6-bc88-0a83d4b81177.xml"
  ],
  "Policy Templates\\Executables and Scripts\\Deliver to Mailbox": [
    "files_20190429-103454/filenames/c8158f5f-069d-4c4e-8d93-9847e27eb95a.xml",
    "files_20190429-103454/rules/b6ee4228-529d-47b4-8ee5-8b453ac88e01.xml"
  ]
}
```

```bash
cat 332a056a-3ba9-49f6-a719-c313f67335d3.xml
<?xml version='1.0' encoding='UTF-8'?>
<FilenameList name="From Netgovern zip_files Custom policy" type="static" uuid="332a056a-3ba9-49f6-a719-c313f67335d3">
  <FileName>*.zip</FileName>
</FilenameList>
```

```bash
cat 95bc36c7-e024-401a-bb1a-e239c99b93aa.xml
<?xml version='1.0' encoding='UTF-8'?>
<PolicyRule name="From Netgovern zip_files Custom policy" siteSpecific="false" template="e8758788-e62f-484b-857d-10d10ef72504" uuid="95bc36c7-e024-401a-bb1a-e239c99b93aa">
  <WhatToFind>
    <MediaTypes selection="all" uuid="6e5493bb-7472-4950-b1cf-626c159b5a4d" visible="false"/>
    <SizeLimit enabled="false" limit="unknown" threshold="0" uuid="60a3c050-16e9-40b7-932a-ca8a8bb3a02c" visible="false"/>
    <Filenames exclusive="false" uuid="5e8dcb6d-b90c-477e-9971-8d62d5f75736">
      <List>332a056a-3ba9-49f6-a719-c313f67335d3</List>
    </Filenames>
    <Direction direction="either" uuid="cc062337-3ef6-464f-b046-5d7005c75d9b"/>
  </WhatToFind>
  <WhatToDo>
    <Disposal disposal="6490eae4-cb03-45d0-85de-38f96d9a8a55" primaryCrypto="UNDEFINED" secondary="95d778e0-4baa-4266-b572-db1a8bd12333" secondaryCrypto="UNDEFINED" uuid="21a72369-6963-4b9f-b35a-93cf0455c5be"/>
  </WhatToDo>
  <WhatToDoWeb>
    <PrimaryWebAction editable="true" type="none" uuid="343a71c2-ecc5-4e8b-bca2-339dcc506c08"/>
  </WhatToDoWeb>
  <WhatElseToDo/>
</PolicyRule>
```

---

## @ Clearswift

The set of files from the output should be copied to the clearswift gateway server.  SSH is locked down, but once logged in to the console, it will allow to pull files from another location.

Note: You must enable SSH and whitelist your source IP (or range) in System > SSH Access.
Note: All Tests were run on 4.10.0.20.

### __User Allow lists__

THIS HAS TO BE DONE BEFORE ANY USER LOGS IN.

NEEDS TO BE DONE AGAINST AN EMPTY PMM DATABASE.

With the zip file from the export process, run the script [import_pmm.sh](./import_pmm.sh)
After the script runs, the internal import process should kick in and your dropped files will disappear.  You can query the tables with the following commands to verify that it has finished:

```bash
psql -d pmi_operations -U postgres -c "select * from pmmw_users;"
psql -d pmi_operations -U postgres -c "select * from pmmw_whitelist;"
```

## __Import Attachment Blocking policy__

Copy the exported XML files to eacf of their respective folders:

```bash
/var/cs-gateway/uicfg/policy/filenames/<file_containing_list_of_filenames>
```

And

```bash
/var/cs-gateway/uicfg/policy/rules/<file_containing_policy>
```

Restart the tomcat server:

```bash
cs-servicecontrol restart tomcat
```

## __Import of MediaType Templates Rules__

There's a predefined set of templates from NetGovern.  copy the xml files to: /var/cs-gateway/uicfg/policy/rules

Restart the tomcat server:

```bash
cs-servicecontrol restart tomcat
```

Go back to the UI and configure the disposition action for the imported rules

## __Import system WL__

The file name that is created by the export script is:

```bash
<secure host name>_allow_list_ip_addresses.txt
```

Use Clearswift UI to import it

## __Import Domain WL - email addresses only__

The file name that is created by the export script is:

```bash
<secure host name>_allow_list_ip_addresses.txt
```

Using the Clearswift UI:

* Create a new email address list
* Import the text file
* Use the newly created email address list in the Content Policy configuration

## __Import system BL - email addreses__

The file name that is created by the export script is:

```bash
<secure host name>_block_list_email_addresses.txt
```

Using the Clearswift UI:

* Create a new email address list
* Import the text file
* Use the newly created email address list in the SPAM configuration section

## __Import system BL - IPs__

Using the Clearswift UI:

* Go to system/smtp settings/connections
* Create a connection (blocked types (relay tab))

run script from command line:

```bash
cd /var/cs-gateway/uicfg/tls/endpoints
run importhosts.sh '<connection_name>' <file_name>
```

where <file_name> is the previously exported: \<host name>_block_list_ip_addresses.txt

restart the tomcat web server

```bash
cs-servicecontrol restart tomcat
```

## __Import system trusted IPs__

Using the Clearswift UI:

* Go to system/smtp settings/connections
* Create a connection, go to the relay tab and select the type: "Restricted Internal"

Run script the script provided by Clearswift from command line:

```bash
cd /var/cs-gateway/uicfg/tls/endpoints
run importhosts.sh <new_connection_name> <file_name_from_export_script>
```

Restart the tomcat web server

```bash
cs-servicecontrol restart tomcat
```

## __Aliasing__

Aliasing is supported using the PostFix config (if there's no need to retain the original rcpt address):

From the secure server:
Export the aliases to map the primary SMTP address into a csv file using the script ldap-pull.sh.  The csv structure is: rcpt-email, primary-smtp.

Using the Clearswift UI, Go to system/smtp settings/email address rewriting/ and configure the type of aliasing wanted.

From the Clearswift console:

* Copy the csv file previously exported
* run the following command

```bash
import_rewrite_rules.sh /var/cs-gateway/uicfg/policy/alias.xml <cvs_filename>
```
