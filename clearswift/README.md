# NetGovern Secure export scripts to Clearswift

The following set of scripts process a 6.0+ secure backup file and pulls email addresses from a LDAP backend in order to export:

1. System and user defined whitelisted addresses
2. Custom Attachment blocking policies based on filenames and file extensions
3. A list of emails with the active aliases

## Pre-requisites

You can run the following oneliner in your netgovern secure to clone this repository:
```bash
sudo yum install git -y && git clone https://bitbucket.netmail.com/scm/pub/migrations.git
```

The following files need to be copied to the same location in the netgovern secure server:

Run the following script to prepare the environment:  [export_prep.sh](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/export_prep.sh)

```bash
chmod +x export_prep.sh
./export_prep.sh

....
....
....

  Downloading https://files.pythonhosted.org/packages/35/8a/5e066949f2b40caac32c7b2a77da63ad304b5fbe869036cc3fe4a198f724/lxml-4.3.3-cp36-cp36m-manylinux1_x86_64.whl (5.7MB)
     |################################| 5.7MB 2.1MB/s 
Collecting uuid
  Downloading https://files.pythonhosted.org/packages/ce/63/f42f5aa951ebf2c8dac81f77a8edcc1c218640a2a35a03b9ff2d4aa64c3d/uuid-1.30.tar.gz
Installing collected packages: argparse, lxml, uuid
  Running setup.py install for uuid ... done
Successfully installed argparse-1.4.0 lxml-4.3.3 uuid-1.30

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
  -l, --export-ldap
                        enable Ldap export
  -t, --export-templates
                        enable Templates export

```

*NOTE: Locales have to be UTF-8.  DO NOT RUN THE SCRIPT AS root, IT WILL BREAK THE JSON PARSER.*

A full system backup needs to be taken before running the script!
After taking a full backup from the UI, the new file is written at: /opt/ma/netmail/var/dbf/mplus.directory.backup/
Look at the latest *.backup

It exports custom Attachment Blocking policies or policies that were modified from the default ones provided by the NetGovern.  
Using the option --export-templates will output all of the policies (Default templates and custom/modified)
The output is 2 XML files per policy, ready to be used by Clearswift.

If the -l option is used, it exports the aliases to map the primary SMTP address into a csv file calling the script ldap-pull.sh with credentials parsed from the backup file.  
The csv structure is: rcpt-email, primary-smtp.

It also exports system whitelists, internal mail servers and user whitelists.
In the case of user whitelists, it will produce output for each alias of the domain.
The output is a zip file containing a set of csv and txt files ready to be used by Clearswift.

---

## Example

```bash
python3 ./secureExport.py -f ./netmail.wbackup -l
Exporting policy: datcard\iso-qt
Exporting policy: Policy Templates\Executables and Scripts\Deliver to Mailbox
The following files were created:
{
  "addressesLists": [
    "files_20190429-103454/addresslists/pmmwdbusers.csv",
    "files_20190429-103454/addresslists/pmmwdbsenders.csv",
    "files_20190429-103454/addresslists/allow_list_email_addresses.txt",
    "files_20190429-103454/addresslists/allow_list_ip_addresses.txt",
    "files_20190429-103454/addresslists/block_list_email_addresses.txt",
    "files_20190429-103454/addresslists/internal_mail_servers.txt"
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

Login to the Gateway Linux console using the cs-admin credentials.
Select Open Terminal Session and login using the cs-admin credentials.
Assume root.

The zip file created byt the export script needs to be copied to the clearswift gateway server.  
In addition, the following files and scripts need to be copied as well:

* [import_pmm.sh](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/import_pmm.sh)
* [import_att.sh](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/import_att.sh)
* [templates.zip](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/templates.zip)
* [importhosts.sh](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/importhosts.sh)
* [import_rewrite_rules.sh](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/import_rewrite_rules.sh)

Note: SSH is locked down, but once logged in to the console, it will allow to pull files from another location.

Note: You must enable SSH and whitelist your source IP (or range) in System > System Settings > SSH Access.
Note: All Tests were run on 4.10.0.20.

## __Adding Internal Email Servers__

The file name that is created by the export script is: **internal_mail_servers.txt**
The Gateway initial policy wizard asks you to supply an internal email server. If the customer’s configuration contains additional email servers, they can be manually added to System > SMTP Settings > Connections > Internal Email Servers.

## __Adding Customer Email Domains__

The Gateway initial policy wizard asks you to supply up to 6 hosted email domains. If the customer has additional email domains that they wish to protect, they can be manually added to System > SMTP Settings > Mail Domains and Routing
•	Use the Hosted Domains tab to add those email domains that the customer wishes to protect
•	Use the Email Routing tab to configure any custom routing for the customer’s email domains that you have just added
•	Use the MTA Groups tab to configure any required failover/load-balancing between the servers in the group, to ensure that mail traffic continues to be routed without interruption

### __User Allow lists__

THIS HAS TO BE DONE BEFORE ANY USER LOGS IN.

NEEDS TO BE DONE AGAINST AN EMPTY PMM DATABASE.

With the zip file from the export process, run the script [import_pmm.sh](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/import_pmm.sh)
After the script runs, the internal import process should kick in and your dropped files will disappear.  You can query the tables with the following commands to verify that it has finished:

```bash
psql -d pmi_operations -U postgres -c "select * from pmmw_users;"
psql -d pmi_operations -U postgres -c "select * from pmmw_whitelist;"
```
You can verify the successful import in the Gateway UI under System > PMM Settings > Manage Users.

## __Import Attachment Blocking policies and MediaType Templates rules__

Run the script [import_att.sh](https://bitbucket.netmail.com/projects/PUB/repos/migrations/raw/clearswift/import_att.sh)
It will copy the policy files and restart tomcat.
After the script runs, the new policies need to be applied/confirmed from the UI. Disposal actions need to be configured from the UI as the ones set in the templates may not be existing in the SEG you are importing these rules.

## __Import system WL__

The file name that is created by the export script is: **allow_list_ip_addresses.txt**
To import this file into the Clearswift UI:
1.	Navigate to Policy > SpamLogic Settings
2.	Click on Import white list on the left of the UI
3.	In the Import SpamLogic White List dialog
	a.	Click on Choose File and select the allow_list_ip_addresses.txt file
	b.	Ensure that the Replace existing matching entries? check box is not ticked
	c.	Select the Mail Server radio button
	d.	Tick the appropriate check boxes for the spam checks that you wish to bypass
	e.	Click on Import
4.	If there are any errors in the file to be imported, a warning dialog box will be displayed. You will need to correct the errors in the source file before you can proceed with the import
5.	Click on the White List tab to verify that the appropriate entries have been imported

Use Clearswift UI to import it

## __Import Domain WL - email addresses only__

The file name that is created by the export script is: **allow_list_email_addresses.txt**

If the requirements is to bypass Spam policy only:
To import this file into the Clearswift UI:
1.	Navigate to Policy > SpamLogic Settings
2.	Click on Import white list on the left of the UI
3.	In the Import SpamLogic White List dialog
	a.	Click on Choose File and select the allow_list_email_addresses.txt file
	b.	Ensure that the Replace existing matching entries? check box is not ticked
	c.	Select the Email radio button
	d.	Tick the appropriate check boxes for the spam checks that you wish to bypass
	e.	Click on Import
4.	If there are any errors in the file to be imported (e.g. wildcards are not supported in the following format: example@*.salesforce.com), a warning dialog box will be displayed. You will need to correct the errors in the source file before you can proceed with the import
5.	Click on the White List tab to verify that the appropriate entries have been imported

If other elements of the policy need bypassed (i.e. block attachments)
Using the Clearswift UI:

* Create a new email address list
* Import the text file
* Use the newly created email address list in the Content Policy configuration

## __Import system BL - email addreses__

The file name that is created by the export script is: **block_list_email_addresses.txt**

To import this file into the Clearswift UI:
1.	Navigate to Policy > Email Addresses
2.	Click on New
3.	In the Choose Address List Type? dialog
	a.	Select the Static Address List radio button
	b.	Click on Create
4.	Use the Overview section to rename the address list to: Blacklisted Email Addresses
5.	Click on Import address list on the left of the UI
6.	In the Import Addresses to “Blacklisted Email Addresses” dialog
	a.	Click on Choose File and select the block_list_email_addresses.txt file
	b.	Ensure that the Delete and replace the current addresses in the address list? check box is not ticked
	c.	Click on Import
7.	Navigate to Policy > SpamLogic Settings
8.	In the Reject messages from the following pane, click on Click here to change these settings
9.	Tick the Blacklisted Email Addresses check box
10.	Click on Save

## __Import system BL - IPs__

Run this step only if the export script discovered blocked IP addresses.
Using the Clearswift UI:

1.	Navigate to System > SMTP Settings > Connections
2.	Click on New
3.	Use the Overview section to rename the address list to: Blacklisted IP Addresses
4.	Click on the Relay tab
5.	In the Inbound Relay Control pane, click on Click here to change these settings
6.	Select the Blocked radio button
7.	Click on Save

Now access the Clearswift command line to run the import script:

1.	Login to the Gateway Linux console using the cs-admin credentials
2.	Select Open Terminal Session and login using the cs-admin credentials
3.	Assume root
4.	Run the following script:

```bash
chmod +x importhosts.sh
./importhosts.sh '<connection_name>' addresslists/block_list_ip_addresses.txt
```

restart the tomcat web server

```bash
cs-servicecontrol restart tomcat
```

## __Import system trusted IPs__

Using the Clearswift UI:
1.	Navigate to System > SMTP Settings > Connections
2.	Click on New
3.	Use the Overview section to rename the address list to: Trusted IP Addresses
4.	Click on the Relay tab
5.	In the Inbound Relay Control pane, click on Click here to change these settings
6.	Select the Restricted Internal radio button
7.	Click on Save

Now access the Clearswift command line to run the import script:

1.	Login to the Gateway Linux console using the cs-admin credentials
2.	Select Open Terminal Session and login using the cs-admin credentials
3.	Assume root
4.	Run the following script:

```bash
chmod +x importhosts.sh
./importhosts.sh <new_connection_name> addresslists/client_allow_list_ip_addresses.txt
```

Restart the tomcat web server

```bash
cs-servicecontrol restart tomcat
```

## __Aliasing__

Aliasing is supported using the PostFix config (if there's no need to retain the original rcpt address):

Using the Clearswift UI,
1.	Navigate to System > SMTP Settings > Email Address Rewriting
2.	Click on New
3.	In the Options pane, click on Click here to change these settings
4.	Select the type of rewriting required:
	•	Rewrite addresses of the sender and recipients in the message envelope and content
	•	Rewrite addresses of recipients within the message envelope only
5.	Click on Save

Now access the Clearswift command line to run the import script:

1.	Login to the Gateway Linux console using the cs-admin credentials
2.	Select Open Terminal Session and login using the cs-admin credentials
3.	Assume root
4.	Copy the csv file (outfile.csv ) previously exported
5.	Run the following command selecting the file wanted from the unzipped csv. This step will need to be repeated per each csv 

```bash
chmod +x import_rewrite_rules.sh
./import_rewrite_rules.sh /var/cs-gateway/uicfg/policy/alias.xml alias/<csv_filename>
```
