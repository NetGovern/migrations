import json
import string
import re
import argparse
import os
import sys
import uuid
import subprocess
import urllib.parse
import zipfile
import shutil
from datetime import datetime
from lxml import etree

def parseMe():
    parser = argparse.ArgumentParser(
        description="Export NetGovern Allow/Block lists and Attachment Blocking export for ClearSwift")
    parser.add_argument("-f", "--backup-file",
                        dest="backupFile",
                        required=True,
                        help="Path to the NetGovern Secure backup file (v6+ format)")
    parser.add_argument("-t", "--export-templates",
                        action="store_true",
                        dest="exportTemplates",
                        help="enable Templates export")
    parser.add_argument("-l", "--export-ldap",
                        action="store_true",
                        dest="exportLdap",
                        help="enable Ldap export")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verboseOutput",
                        help="enable verbose output")
    return parser.parse_args()

def loadBackup(backupFilePath):
    if os.path.isfile(backupFilePath):
        with open(backupFilePath, 'r', encoding='utf-8') as jsonFile:
            try:
                backupData = json.load(jsonFile)
            except json.decoder.JSONDecodeError as e:
                sys.exit("Exception found while processing the backup file: {0} line {1} column {2} (char {3})".format(e.msg, e.lineno, e.colno, e.pos))
            except:
                sys.exit("The backup file has a problem in its JSON structure")
    else:
        sys.exit("Backup file not found")
    return backupData.get('objects.v2', {})

def getAttributeFromBackup(treePath, valueIfNone, toLower=False):
    treePath = treePath.split('|')
    attribute = backupData.get(treePath[0])
    for node in treePath[1:]:
        if attribute is None:
            break
        if not isinstance(attribute, dict):
            attribute = None
            break
        attribute = attribute.get(node)

    if attribute is None:
        return valueIfNone
    elif isinstance(attribute, list):
        sanitizedList = []
        for entry in attribute:
            if isinstance(entry, str):
                if toLower:
                    sanitizedList.append(entry.lower())
                else:
                    sanitizedList.append(entry)
            elif isinstance(entry, list):
                if toLower:
                    sanitizedList.append("".join(entry).lower())
                else:
                    sanitizedList.append("".join(entry))
        return sanitizedList
    else:
        if toLower:
            return attribute.lower()
        else:
            return attribute

def isValid(emailAddress):
    # Making sure that our aliases are a valid email address
    if not isinstance(emailAddress, str):
        validEmailAddress = False
    else:
        # In some systems, a path to an ldap object is found.
        # The following conditional and regex identify it as an error
        if re.match(r"(?!\\).*", emailAddress) and "@" in emailAddress:
            validEmailAddress = True
        else:
            validEmailAddress = False
    return validEmailAddress


def main():
    myData = {}
    systemAllowedList = []
    systemBlockedList = []
    smptModulesList = []
    internalMailServers = []
    filesWritten = {}
    filesWritten['addressesLists'] = []

    # Checking backup format
    if len(backupData) == 0:
        sys.exit("Invalid backup file")
    if "Internet Services\\NMsecure" in backupData.keys():
        sys.exit("Backup format < 6.0 version - Not supported")

    #Creating output folders
    outputFolderPath = "files_{0}".format(
        datetime.now().strftime("%Y%m%d-%H%M%S"))
    try:
        os.mkdir(outputFolderPath)
    except OSError:
        sys.exit("Cannot create {0}".format(outputFolderPath))

    try:
        os.mkdir("{0}/filenames".format(outputFolderPath))
    except OSError:
        sys.exit("Cannot create {0}/filenames".format(outputFolderPath))

    try:
        os.mkdir("{0}/rules".format(outputFolderPath))
    except OSError:
        sys.exit("Cannot create {0}/rules".format(outputFolderPath))

    try:
        os.mkdir("{0}/addresslists".format(outputFolderPath))
    except OSError:
        sys.exit("Cannot create {0}/addresslists".format(outputFolderPath))
    
    try:
        os.mkdir("{0}/alias".format(outputFolderPath))
    except OSError:
        sys.exit("Cannot create {0}/alias".format(outputFolderPath))

    # ldap-pull
    filesWritten['aliasList'] = []
    if exportLdap:
        externalCmdLog = []
        authPolicies = [
            maObject for maObject in backupData.keys()
            if 'security\\policies\\Authentication' in maObject and
                backupData.get(maObject, {}).get('class') == 'maAuthPolicy' ]
        for maObject in authPolicies:
            authRoute = "".join(getAttributeFromBackup(
                '{0}|attributes|maRouteURI'.format(maObject),[]))
            if "x-nm-ex" in authRoute or "ldap://" in authRoute:
                domainName = maObject.split('\\')[-1]
                splitAuthRoute = authRoute.split('@')
                if len(splitAuthRoute) != 2:
                    print("Cannot parse ldap Auth Route")
                    adminDn = input("Enter Admin DN, example: 'cn=admin,ou=administrators,dc=contoso,dc=com': ")
                    adminPassword = input("Enter Admin DN password: ")
                    ldapHost = input("Enter LDAP host: ")
                    ldapPort = input("Enter LDAP password: ")
                    baseDn = input("Enter Users Base DN, example: 'ou=users,dc=contoso,dc=com'")
                else:
                    adminDn = urllib.parse.unquote(splitAuthRoute[0].split(":")[1].replace("//",""))
                    if "::" in splitAuthRoute[0]:
                        adminPassword = input("Cannot parse admin password from backup file. Enter Admin DN password for {0}: ".format(adminDn))
                    else:
                        adminPassword = urllib.parse.unquote(splitAuthRoute[0].split(':')[2])
                    ldapHost = splitAuthRoute[1].split(':')[0]
                    ldapPort = splitAuthRoute[1].split(':')[1].split('/')[0]
                    baseDn = urllib.parse.unquote(splitAuthRoute[1].split(':')[1].split('/')[1].split('?')[0])
                if verboseOutput:
                    print("Authentication Route: {0}".format(domainName))
                    print("Admin DN: {0}".format(adminDn))
                    print("Password: {0}".format(adminPassword))
                    print("HOST: {0}".format(ldapHost))
                    print("PORT: {0}".format(ldapPort))
                    print("Base DN: {0}".format(baseDn))
                    input("Press [ENTER] to continue")
                externalCmdLog.append(authRoute)
                externalCmdLog.append("Authentication Route: {0}".format(domainName))
                externalCmdLog.append("Admin DN: {0}".format(adminDn))
                externalCmdLog.append("Password: {0}".format(adminPassword))
                externalCmdLog.append("HOST: {0}".format(ldapHost))
                externalCmdLog.append("PORT: {0}".format(ldapPort))
                externalCmdLog.append("Base DN: {0}".format(baseDn))
                externalCmd = ["./ldap-pull.sh",ldapHost,ldapPort,adminDn,adminPassword,baseDn,"{0}/alias/{1}.txt".format(outputFolderPath,domainName)]
                subprocess.call(externalCmd)
                filesWritten['aliasList'].append("{0}/alias/{1}.txt".format(outputFolderPath,domainName))
                #print(externalCmd)
        # Dumping log to file
        if len(externalCmdLog) > 0:
            with open("ldap-pull-log.txt", 'w') as externalCmdLogFile:
                externalCmdLogFile.write("\n".join(externalCmdLog))
    else:
        # Get aliases from NetGovern Secure Backup
        # Process domains
        aliasData = {}
        domainsList = getAttributeFromBackup(
            'security\\agents\\SMTP|attributes|maUserDomain', [])
        #print(domainsList)
        aliasData['PfAliases'] = {}
        # Get domain aliases
        for domain in domainsList:
            aliasData['PfAliases'][domain] = {}
            aliasData['PfAliases'][domain]['userEmailAddresses'] = []
            domainAliasesList = getAttributeFromBackup(
                'security\\domains\\{0}|attributes|maAliases'.format(domain), [], True)
            aliasData['PfAliases'][domain]['domainAliases'] = [
                alias for alias in domainAliasesList if alias != domain ]
            userObjectsList = [
                user for user in backupData.keys()
                if 'security\\domains\\{0}'.format(domain) in user and '@' in user ]
            userAliases = {}
            for user in userObjectsList:
                userPrimaryEmailAddress = user.rsplit('\\', 1)[1].lower()
                userAliases[userPrimaryEmailAddress] = []
                userAliasesList = getAttributeFromBackup(
                    '{0}|attributes|maAliases'.format(user), [], True)
                for userAlias in [userAlias for userAlias in userAliasesList if isValid(userAlias)]:
                    userAliases[userPrimaryEmailAddress].append(userAlias)
                userAliases[userPrimaryEmailAddress] = list(set(userAliases[userPrimaryEmailAddress]))
                aliasData['PfAliases'][domain]['userEmailAddresses'] = userAliases
        for domain in aliasData['PfAliases']:
            print("domain: {0}".format(domain))
            aliasesCsv = []
            for userEmailAddress in aliasData['PfAliases'][domain]['userEmailAddresses']:
                for userAlias in aliasData['PfAliases'][domain]['userEmailAddresses'][userEmailAddress]:
                    aliasesCsv.append("{0},{1}".format(userAlias,userEmailAddress))
                    for domainAlias in aliasData['PfAliases'][domain]['domainAliases']:
                        aliasesCsv.append("{0},{1}".format(userAlias.replace(domain,domainAlias),userEmailAddress))
                for domainAlias in aliasData['PfAliases'][domain]['domainAliases']:
                        aliasesCsv.append("{0},{1}".format(userEmailAddress.replace(domain,domainAlias),userEmailAddress))

            with open("{0}/alias/{1}.txt".format(outputFolderPath,domain)
                , 'w') as userAliasCsvFile:
                userAliasCsvFile.write("\n".join(aliasesCsv))
            filesWritten['aliasList'].append("{0}/alias/{1}.txt".format(outputFolderPath,domain))

    # Filtering Attachment Blocking policies
    if exportTemplates:
        attBlockPolicies = [
            maObject for maObject in backupData.keys()
            if 'security\\policies\\Attachment Blocking' in maObject and
                backupData.get(maObject, {}).get('class') == 'maATTBlockPolicy' ]
    else:
        attBlockPolicies = [
            maObject for maObject in backupData.keys()
            if 'security\\policies\\Attachment Blocking' in maObject and
                backupData.get(maObject, {}).get('class') == 'maATTBlockPolicy' and 
                backupData.get(maObject, {}).get('attributes', {}).get('maConfiguration') 
        ]

    for maObject in attBlockPolicies:
        attachmentNamesList = getAttributeFromBackup(
            '{0}|attributes|maAttachmentNames'.format(maObject),[], True)
        if len(attachmentNamesList) > 0:
            fileGroup = maObject.replace(
                "security\\policies\\Attachment Blocking\\", "")
            myData[fileGroup] = {}
            myData[fileGroup]['uuid'] = str(uuid.uuid4())
            myData[fileGroup]['fileList'] = []
            for extension in attachmentNamesList:
                if extension not in myData[fileGroup]['fileList']:
                    myData[fileGroup]['fileList'].append(
                        extension)
            configurationSettingsList = getAttributeFromBackup(
                '{0}|attributes|maConfiguration'.format(maObject),[])
            for configurationSetting in configurationSettingsList:
                if 'sizelimit:<' in configurationSetting:
                    myData[fileGroup]['sizeLimit'] = configurationSetting.split(':<')[1]

    for key in myData:
        filesWritten[key] = []
        print("Exporting policy: {0}".format(key))
        policyUuid = str(uuid.uuid4())
        xmlPolicy = "{0}/rules/{1}.xml".format(outputFolderPath,policyUuid)
        xmlFile = "{0}/filenames/{1}.xml".format(outputFolderPath,myData[key]['uuid'])
        filenameList = etree.Element("FilenameList", name="From Netgovern {0} policy".format(key),
                                     type="static", uuid=myData[key]['uuid'])
        for extension in myData[key]['fileList']:
            fileName = etree.SubElement(filenameList, "Filename")
            fileName.text = extension
        treeFile = etree.ElementTree(filenameList)
        treeFile.write(xmlFile, encoding='utf-8',
                       xml_declaration=True, pretty_print=True)
        filesWritten[key].append(xmlFile)

        policyRule = etree.Element("PolicyRule", name="From Netgovern {0} policy".format(key),
                                   siteSpecific="false", template="e8758788-e62f-484b-857d-10d10ef72504",
                                   uuid=policyUuid)
        whatToFind = etree.SubElement(policyRule, "WhatToFind")
        etree.SubElement(whatToFind, "MediaTypes", selection="all",
                         uuid="6e5493bb-7472-4950-b1cf-626c159b5a4d", visible="false")

        sizeLimit = myData[key].get('sizeLimit')
        if sizeLimit:
            etree.SubElement(whatToFind, "SizeLimit", enabled="true", limit="{0}".format(sizeLimit), threshold="0",
                         uuid="60a3c050-16e9-40b7-932a-ca8a8bb3a02c", visible="false")
        else:
            etree.SubElement(whatToFind, "SizeLimit", enabled="false", limit="unknown", threshold="0",
                         uuid="60a3c050-16e9-40b7-932a-ca8a8bb3a02c", visible="false")

        fileNames = etree.SubElement(whatToFind, "Filenames", exclusive="false",
                                     uuid="5e8dcb6d-b90c-477e-9971-8d62d5f75736")

        fileNamesList = etree.SubElement(fileNames, "List")
        fileNamesList.text = myData[key]['uuid']

        etree.SubElement(whatToFind, "Direction", direction="either",
                         uuid="cc062337-3ef6-464f-b046-5d7005c75d9b")

        whatToDo = etree.SubElement(policyRule, "WhatToDo")
        etree.SubElement(whatToDo, "Disposal", disposal="6490eae4-cb03-45d0-85de-38f96d9a8a55",
                         primaryCrypto="UNDEFINED", secondary="95d778e0-4baa-4266-b572-db1a8bd12333",
                         secondaryCrypto="UNDEFINED", uuid="21a72369-6963-4b9f-b35a-93cf0455c5be")

        whatToDoWeb = etree.SubElement(policyRule, "WhatToDoWeb")
        etree.SubElement(whatToDoWeb, "PrimaryWebAction", editable="true", type="none",
                         uuid="343a71c2-ecc5-4e8b-bca2-339dcc506c08")

        etree.SubElement(policyRule, "WhatElseToDo")

        treeFile = etree.ElementTree(policyRule)
        treeFile.write(xmlPolicy, encoding='utf-8',
                       xml_declaration=True, pretty_print=True)
        filesWritten[key].append(xmlPolicy)

    if len(filesWritten) == 0:
        print("No attachment blocking policies were found")

    ### Allow / Block Lists

    # Get system allowed addresses from SMTP Modules
    smptModulesList = getAttributeFromBackup(
        'security\\smtp modules|attributes|maAdministrator',[])

    for module in smptModulesList:
        if 'Lists' in module or 'Limits' in module:
            allowedAddressesList = getAttributeFromBackup(
                '{0}|attributes|maAllowedAddress'.format(module),[], True)
        else:
            moduleConfig = getAttributeFromBackup(
                '{0}|attributes|maConfiguration'.format(module),[])
            allowedAddressesList = [
                config.replace("allowed:", "") for config in moduleConfig
                if 'allowed:' in config ]

        systemAllowedList.extend(allowedAddressesList)

    # Process domains
    domainsList = getAttributeFromBackup(
        'security\\agents\\SMTP|attributes|maUserDomain', [])

    myData['Users'] = {}
    for domain in domainsList:
        myData[domain] = {}
        # Whitelist servers present in the delivery routes
        deliveryPolicyList = [
            maObject for maObject in backupData.keys()
            if 'security\\policies\\Delivery' in maObject and
                backupData.get(maObject, {}).get('class') == 'maDeliveryPolicy' ]
        #deliveryPolicyList = getAttributeFromBackup(
        #    'security\\domains\\{0}|attributes|maRoutePolicy'.format(domain), [])
        for policy in deliveryPolicyList:
            deliveryRoutesList = getAttributeFromBackup(
                '{0}|attributes|maRouteURI'.format(policy), [])
            for route in deliveryRoutesList:
                matchWithPort = re.search(r'//(.*):',route)
                matchWithoutPort = re.search(r'//(.*)\?',route)
                if matchWithPort:
                    internalMailServers.append(matchWithPort.group(1))
                elif matchWithoutPort:
                    internalMailServers.append(matchWithoutPort.group(1))


        # Get Allowed/Blocked by domain
        myData[domain]['Allowed'] = list(set(getAttributeFromBackup(
            'security\\domains\\{0}|attributes|maAllowAddress'.format(domain), [], True)))
        systemAllowedList.extend(myData[domain]['Allowed'])
        myData[domain]['Blocked'] = list(set(getAttributeFromBackup(
            'security\\domains\\{0}|attributes|maBlockAddress'.format(domain), [], True)))
        systemBlockedList.extend(myData[domain]['Blocked'])

        # Get domain aliases
        domainsList = getAttributeFromBackup(
            'security\\domains\\{0}|attributes|maAliases'.format(domain), [], True)
        myData[domain]['domainAliases'] = [
            alias for alias in domainsList if alias != domain ]

        emailAddressesErrors = []
        # Get Users, aliases and allowed lists
        userObjectsList = [
            user for user in backupData.keys()
            if 'security\\domains' in user and '@' in user ]
        for user in userObjectsList:
            allowedList = getAttributeFromBackup(
                '{0}|attributes|maAllowAddress'.format(user), [], True)
            allowedList = list(set(allowedList))
            if len(allowedList) > 0:
                userEmailAddressesList = []
                userEmailAddressesList.append(user.rsplit('\\', 1)[1].lower())
                userAliasesList = getAttributeFromBackup(
                    '{0}|attributes|maAliases'.format(user), [], True)
                for userAlias in [userAlias for userAlias in userAliasesList if isValid(userAlias)]:
                    if verboseOutput:
                        print("Parsing alias: {0} from backup file for user: {1}".format(userAlias,user))
                    userEmailAddressesList.append(userAlias)
                userEmailAddressesList = list(set(userEmailAddressesList))
                for userEmailAddress in userEmailAddressesList:
                    if isValid(userEmailAddress):
                        if verboseOutput:
                            print("Adding email address: {0} for user: {1}".format(
                                userEmailAddress, user))

                        if userEmailAddress not in myData['Users']:
                            myData['Users'][userEmailAddress] = {}
                        myData['Users'][userEmailAddress]['Allowed'] = allowedList

                        for domainAlias in myData[domain]['domainAliases']:
                            aliasedEmailAddress = userEmailAddress.replace(
                                domain, domainAlias)
                            if aliasedEmailAddress not in myData['Users']:
                                if verboseOutput:
                                    print("Adding email address: {0} for user: {1}".format(
                                        aliasedEmailAddress, user))
                                myData['Users'][aliasedEmailAddress] = {}
                            myData['Users'][aliasedEmailAddress]['Allowed'] = allowedList
                    else:
                        emailAddressesErrors.append(userEmailAddress)

        # Dumping to files
        if len(emailAddressesErrors) > 0:
            with open("{0}/addresslists/aliases_errors_{1}.txt".format(outputFolderPath, domain), 'w') as errorsFile:
                filesWritten['addressesLists'].append(
                    "{0}/addresslists/aliases_errors_{1}.txt".format(outputFolderPath, domain))
                errorsFile.write("\n".join(emailAddressesErrors))

    pmmwdbusers = []
    pmmwdbsenders = []

    # Processing users allowed lists
    userID = 0
    senderID = 0
    for user in myData['Users'].keys():
        userID += 1
        crtDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
        userAllowedAddressesList = myData.get('Users',{}
            ).get(user,{}
            ).get('Allowed',[])
        pmmwdbusers.append("{0},{1},{2},{3},{2}".format(
            userID,
            user,
            crtDate,
            "false"))
        if verboseOutput:
            print("Processing user {0} with id: {1} - Allowed list size: {2}".format(user,userID,len(userAllowedAddressesList)))
        for userAllowedAddress in userAllowedAddressesList:
            senderID += 1
            if '@' not in userAllowedAddress:
                userAllowedAddress = "*@{0}".format(userAllowedAddress)
            pmmwdbsenders.append("{0},{1},{2},{3},{4}".format(
                senderID,
                userAllowedAddress,
                userID,
                crtDate,
                "false"))

    if len(pmmwdbusers) > 0 and len(pmmwdbsenders) > 0:
        with open("{0}/addresslists/pmmwdbusers.csv".format(outputFolderPath), 'w') as csvFile:
            filesWritten['addressesLists'].append(
                "{0}/addresslists/pmmwdbusers.csv".format(outputFolderPath))
            # Fixes wildcard as per clearSwift wildcard style
            csvFile.write("\n".join(pmmwdbusers))
        with open("{0}/addresslists/pmmwdbsenders.csv".format(outputFolderPath), 'w') as csvFile:
            filesWritten['addressesLists'].append(
                "{0}/addresslists/pmmwdbsenders.csv".format(outputFolderPath))
            # Fixes wildcard as per clearSwift wildcard style
            csvFile.write("\n".join(pmmwdbsenders).replace(",@", ",*@"))

    # Generate system whitelists files
    if len(systemAllowedList) > 0:
        sanitizedsystemAllowedList = []
        for entry in systemAllowedList:
            # @domain.com type wildcards are not accepted
            # replacing with *@domain.com
            if re.match(r"(^@).*", entry):
                sanitizedsystemAllowedList.append(entry.replace("@","*@"))
            else:
                sanitizedsystemAllowedList.append(entry)
        # removing duplicates
        sortedSystemAllowedList = list(set(sanitizedsystemAllowedList))
        sortedSystemAllowedList.sort()

        emailAddressesAllowList = [ emailAddress for emailAddress in sortedSystemAllowedList if '@' in emailAddress ]
        if len(emailAddressesAllowList) > 0:
            with open("{0}/addresslists/allow_list_email_addresses.txt".format(outputFolderPath), 'w') as textFile:
                filesWritten['addressesLists'].append(
                    "{0}/addresslists/allow_list_email_addresses.txt".format(outputFolderPath))
                textFile.write("\n".join(emailAddressesAllowList))

        ipAddressesAllowList = [
            ipAddress for ipAddress in sortedSystemAllowedList if '@' not in ipAddress]
        if len(ipAddressesAllowList) > 0:
            with open("{0}/addresslists/allow_list_ip_addresses.txt".format(outputFolderPath), 'w') as textFile:
                filesWritten['addressesLists'].append(
                    "{0}/addresslists/allow_list_ip_addresses.txt".format(outputFolderPath))
                textFile.write("\n".join(ipAddressesAllowList))
        
    if len(systemBlockedList) > 0:
        sanitizedsystemBlockedList = []
        for entry in systemBlockedList:
            # @domain.com type wildcards are not accepted
            # replacing with *@domain.com
            if re.match(r"(^@).*", entry):
                sanitizedsystemBlockedList.append(entry.replace("@", "*@"))
            else:
                sanitizedsystemBlockedList.append(entry)
        # removing duplicates
        sortedSystemBlockedList = list(set(sanitizedsystemBlockedList))
        sortedSystemBlockedList.sort()

        emailAddressesBlockList = [ emailAddress for emailAddress in sortedSystemBlockedList if '@' in emailAddress ]
        if len(emailAddressesBlockList) > 0:
            with open("{0}/addresslists/block_list_email_addresses.txt".format(outputFolderPath), 'w') as textFile:
                filesWritten['addressesLists'].append(
                    "{0}/addresslists/block_list_email_addresses.txt".format(outputFolderPath))
                textFile.write("\n".join(emailAddressesBlockList))
        
        ipAddressesBlockList = [ emailAddress for emailAddress in sortedSystemBlockedList if '@' not in emailAddress ]
        if len(ipAddressesBlockList) > 0:
            with open("{0}/addresslists/block_list_ip_addresses.txt".format(outputFolderPath), 'w') as textFile:
                filesWritten['addressesLists'].append(
                    "{0}/addresslists/block_list_ip_addresses.txt".format(outputFolderPath))
                textFile.write("\n".join(ipAddressesBlockList))
    
    if len(internalMailServers) > 0:
        sortedInternalMailServers = list(set(internalMailServers)) #Unique values
        sortedInternalMailServers.sort()
        with open("{0}/addresslists/internal_mail_servers.txt".format(outputFolderPath), 'w') as textFile:
            filesWritten['addressesLists'].append("{0}/addresslists/internal_mail_servers.txt".format(outputFolderPath))
            textFile.write("\n".join(sortedInternalMailServers))

    print("The following files were created:")
    print(json.dumps(filesWritten,indent=2))
    
    #Uncomment to debug
    #with open('./myData.json', 'w') as outfile:
    #    json.dump(myData, outfile, indent=2)

    shutil.make_archive(outputFolderPath, 'zip', "./{0}/".format(outputFolderPath))


if __name__ == '__main__':
    parameters = parseMe()
    # Globals
    backupData = loadBackup(parameters.backupFile)
    exportTemplates = parameters.exportTemplates
    verboseOutput = parameters.verboseOutput
    exportLdap = parameters.exportLdap
    main()


