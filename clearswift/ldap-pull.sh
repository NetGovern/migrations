#!/bin/bash

LDAPHOST="$1"
LDAPPORT="$2"
LDAPUSER="$3"
LDAPPASS="$4"
LDAPDN="$5"
LDAPCMD="`which ldapsearch` -LLL -x -H ldap://$LDAPHOST:$LDAPPORT -D $LDAPUSER -w $LDAPPASS -b $LDAPDN "
USERFILE="/tmp/userfile"
OUTFILE="$6"

#rm $USERFILE $OUTFILE

#Get users
$LDAPCMD "(&(!(objectClass=contact))(|(objectClass=Person)(objectClass=group)(objectClass=msExchDynamicDistributionList))(proxyaddresses=*smtp*))" cn | awk -F : '/cn/ {print $2}' | \
grep -Eiv 'healthmailbox|discoverysearchmailbox|federatedemail|lyncenterprise|migration|sharepointenterprise|systemmailbox|msexchangeapproval|msexchdiscovery|extest' > $USERFILE
`which sort` -o $USERFILE $USERFILE

while read USER; do
    PRIMARY=`$LDAPCMD "(&(!(objectClass=contact))(|(objectClass=Person)(objectClass=group)(objectClass=msExchDynamicDistributionList))(proxyaddresses=*smtp*)(cn=$USER))" proxyaddresses | awk -F : '/SMTP/ {print tolower($3)}'`
    ALIASES="`$LDAPCMD "(&(!(objectClass=contact))(|(objectClass=Person)(objectClass=group)(objectClass=msExchDynamicDistributionList))(proxyaddresses=*smtp*)(cn=$USER))" proxyaddresses | awk -F : '/smtp/ {print tolower($3)}'`"
    echo "User: $USER"
    for ALIAS in $ALIASES; do
        echo "Alias: $ALIAS"
        echo "Primary: $PRIMARY"
        printf "%s,%s\r\n" $ALIAS $PRIMARY >> $OUTFILE
    done
    echo ""
done <"$USERFILE"

`which sort` -u -o $OUTFILE $OUTFILE