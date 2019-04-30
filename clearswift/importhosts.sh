#!/bin/bash
# importhosts.sh v2.0
#
# Define Usage of the script:
usage() {
echo "Usage: $0 <'Connection Profile'> <List to Import>"
echo
echo " - 'Connection Profile' is the exact name of the Connection defined under System > SMTP Settings > Connections, to which you want to import hosts. Single quotes are required"
echo " - List to Import is the list of all IP addresses or ranges you want to import in the Connection. Ranges can only be wildcards. This tool does not accept the CIDR format."
echo
echo "For more information, please contact Clearswift Support"
exit 1
}

# Test if arguments were passed
if [ $# -lt 2  ]
 then usage
fi

DIR=/var/cs-gateway/uicfg/tls/endpoints
# Register arguments
PROFILE=$1
LIST=$2

# Get the Connection Profile UUID
CONNECTION_UUID=`xmlstarlet sel -t -m "/TLSEndPoint[@name='$PROFILE']" -v @uuid $DIR/*.xml`

# Import list of IP Addresses/Ranges in the xml file

for host in $(cat $LIST);
do
 xmlstarlet ed -L -s "/TLSEndPoint/HostList" -t elem -n Host -v "$host" $DIR/$CONNECTION_UUID.xml;
done

echo "Import complete. Now restart the user interface with 'cs-servicecontrol restart tomcat' and apply the configuration from the Web UI."