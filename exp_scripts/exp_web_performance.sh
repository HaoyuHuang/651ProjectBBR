#!/bin/bash

output="/tmp/web-performance"
recorddir="/tmp/web-record"
selenium="$2"
CC="$3"
base_rtt="$4"
loss="$5"
bw="$6"

dumpdir="$output/dump-cc-$CC-rtt-$base_rtt-loss-$loss-bw-$bw-selenium-$selenium"
resultdir="$output/results-cc-$CC-rtt-$base_rtt-loss-$loss-bw-$bw-selenium-$selenium/"
input="/home/haoyuhua/Dropbox/BBR/BBR/alexa/alexa.txt"
chromedriver="/home/haoyuhua/chromedriver"
tries=5
# input="/home/haoyuhua/BBR/alexa/alexa.txt"

# rm -rf $output
mkdir $output
rm -rf $dumpdir
rm -rf $resultdir
mkdir $dumpdir
mkdir $resultdir

record() {
	rm -rf $recorddir
	mkdir $recorddir
	
	while IFS= read -r site
	do
  		sitename="www.$site"
  		echo $sitename
      cmd="mm-webrecord $recorddir/$site "
      if [ $selenium == "Y" ]; then
        cmd+="java -jar selenium.jar record $chromedriver http://$sitename"
        eval $cmd
        sleep 2
      fi
      if [ $selenium == "N" ]; then
        cmd+="chromium-browser --incognito --ignore-certificate-errors --user-data-dir=/tmp/nonexistent$(date +%s%N) $sitename"
        eval $cmd  &
        sleep 30
      fi
      echo $cmd

      killprogram "mm-webrecord"
      killprogram "apache2"
      killprogram "chromedriver"
      killprogram "chromium-browser"
	done < "$input"
}

killprogram() {
	replaypid=`sudo ps -C $1 -o pid --sort=-start_time | tr -d " "`
	echo $replaypid
	printf '%s\n' "$replaypid" | while IFS= read -r line; 
	do
  		echo "kill " $line
    	sudo kill -9 $line
	done
}

replay() {
	echo "loss $loss RTT $base_rtt"

	while IFS= read -r site
	do
  		loss=$loss
  		rtt=$base_rtt
  		sitename="www.$site"

  		cmd="mm-webreplay $recorddir/$site "
  		if [ $loss != "0" ]; then
  			cmd+="mm-loss uplink $loss mm-loss downlink $loss "
  		fi
      cmd+="mm-delay $rtt "
  		
      inner_cmd=""

      if [ $bw == "10M" ]; then
         inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 10mbit burst 10000 limit 10000; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
      fi

      if [ $bw == "1M" ]; then
         inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 1mbit burst 1000 limit 1000; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
      fi

      if [ $selenium == "Y" ]; then
        inner_cmd+="java -jar selenium.jar replay $chromedriver $input $tries $resultdir/result.json"
      fi
      if [ $selenium == "N" ]; then
        inner_cmd+="sudo tcpdump -i any -w $dumpdir/$site & chromium-browser --incognito --ignore-certificate-errors --user-data-dir=/tmp/nonexistent$(date +%s%N) $sitename"
      fi

  		cmd+="bash -c '$inner_cmd'"
  		echo "cmd $cmd"
      if [ $selenium == "Y" ]; then
        eval $cmd
        sleep 2
      fi

      if [ $selenium == "Y" ]; then
        eval $cmd &
        sleep 30;
        tcptrace -r -l $dumpdir/$site > $resultdir/result-$site
      fi

  		killprogram "dnsmasq"
  		killprogram "mm-webreplay"
  		killprogram "mm-delay"
  		killprogram "mm-loss"
  		killprogram "mm-link"
  		killprogram "tcpdump"
  		killprogram "apache2"
      killprogram "chromedriver"
  		killprogram "chromium-browser"
	done < "$input"
}

killprogram "tcpdump"
killprogram "dnsmasq"
killprogram "mm-webreplay"
killprogram "mm-delay"
killprogram "mm-loss"
killprogram "mm-link"
killprogram "apache2"
killprogram "chromedriver"
killprogram "chromium-browser"

if [ "$1" == "record" ]; then
	record
fi

if [ "$1" == "replay" ]; then
	sudo sysctl -w net.ipv4.tcp_congestion_control=$CC
	replay
fi