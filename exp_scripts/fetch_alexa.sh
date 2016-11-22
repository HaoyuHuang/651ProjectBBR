#!/bin/bash

rm alexa.txt
for i in {0..7..1}
do
	curl "http://www.alexa.com/topsites/global;$i" | grep "/siteinfo/[a-zA-Z0-9\.]*\"" -o | cut -d "/" -f3 | tr -d "\" " >> alexa.txt
done
sed -i '/^$/d' alexa.txt
sort -u alexa.txt -o alexa.txt