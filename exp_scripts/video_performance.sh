#!/bin/bash

output="/tmp/video-performance"
CC="$1"
base_rtt="$2"
loss="$3"
bw="$4"
video="$5"
result_file="cc-$CC-rtt-$base_rtt-loss-$loss-bw-$bw-$video.json"
dumpdir="$output/dump-cc-$CC-rtt-$base_rtt-loss-$loss-bw-$bw-$video"
resultdir="$output/results-cc-$CC-rtt-$base_rtt-loss-$loss-bw-$bw-$video"
# input="/home/haoyuhua/Dropbox/BBR/BBR/alexa/alexa.txt"
# chromedriver="/home/haoyuhua/chromedriver"
# tries=3
# input="/home/haoyuhua/BBR/alexa/alexa.txt"

# rm -rf $output
mkdir $output
rm -rf $dumpdir
rm -rf $resultdir
mkdir $dumpdir
mkdir $resultdir

killprogram() {
	replaypid=`sudo ps -C $1 -o pid --sort=-start_time | tr -d " "`
	echo $replaypid
	printf '%s\n' "$replaypid" | while IFS= read -r line; 
	do
  		echo "kill " $line
    	sudo kill -9 $line
	done
}

play() {
	echo "loss $loss RTT $base_rtt"
	cmd=""
  if [ $loss != "0" ]; then
    cmd+="mm-loss uplink $loss mm-loss downlink $loss "
  fi
  cmd="mm-delay $base_rtt "
  inner_cmd=""

  if [ $bw == "10M" ]; then
     inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 10mbit burst 10000 limit 10000; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
  fi

  if [ $bw == "1M" ]; then
     inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 1mbit burst 1200 limit 1200; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
  fi

  if [ $bw == "5M" ]; then
     inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 5mbit burst 5000 limit 5000; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
  fi

  if [ $bw == "3M" ]; then
     inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 3mbit burst 5000 limit 5000; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
  fi

  if [ $bw == "100K" ]; then
     inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 100kbit burst 1200 limit 1200; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
  fi

  if [ $bw == "10K" ]; then
     inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 10kbit burst 1200 limit 1200; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
  fi

  if [ $bw == "50K" ]; then
     inner_cmd+="sudo /sbin/tc qdisc add dev ingress handle 10: root tbf rate 50kbit burst 1200 limit 1200; sudo /sbin/tc qdisc add dev ingress parent 10:1 handle 100: fq; /sbin/tc qdisc show; "
  fi

  inner_cmd+="sudo tcpdump -i any -w $dumpdir/$video & chromium-browser --incognito --user-data-dir=/tmp/nonexistent$(date +%s%N) $video"

  cmd+="bash -c '$inner_cmd'"
  echo "cmd $cmd"
  eval $cmd &
  if [ "cat.html" == $video ]; then
    sleep 1200;
  fi
  if [ "fantastic-beasts.html" == $video ]; then
    sleep 420;
  fi
  mv ~/Downloads/test.txt $resultdir/$result_file
  tcptrace -r -l $dumpdir/$video > $dumpdir/tcptrace-$video
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

sudo sysctl -w net.ipv4.tcp_congestion_control=$CC
play