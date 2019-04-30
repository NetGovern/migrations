#!/bin/bash

CONFIG=$1
RULES=$2

while read line;
do
FROM=$(echo $line | cut -d ',' -f 1)
TO=$(echo $line | cut -d ',' -f 2)
xmlstarlet ed -L -s "/RewriteRules" -t elem -n 'Rewrite' -v '' \
-s "/RewriteRules/Rewrite[last()]" -t attr -n 'from' -v "$FROM" \
-s "/RewriteRules/Rewrite[last()]" -t attr -n 'to' -v "$TO" \
$CONFIG
done < $RULES
