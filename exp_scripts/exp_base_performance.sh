#!/bin/bash
# mahimahi http://mahimahi.mit.edu/
# iperf http://downloads.es.net/pub/iperf/iperf-3-current.tar.gz

server=10.0.2.15
base_port=10000
CC="$1"
max_bandwidth="$2"
base_rtt="$3"
bg_traffic="$4"
enable_tcp_dump="$5"
monitor_interval="$6"
output_dir="/tmp/$CC-maxb-$2-basertt-$3-BG-$4-tcpdump-$5-interval-$6-$7"

echo $output_dir

rm -rf $output_dir
mkdir $output_dir

start_flow_sync() {
	echo "flow number: $1 loss $2 rtt $3 port $4 start_time $5 output dir $6 remaining $7"

	start_time=`date +%s`

	if [ "$5" == "N" ]; then
		start_time="0"
	fi

	printf "flow:$1\nconfig-loss:$2\nconfig-rtt:$3\nstart_time:$start_time\nduration:$5\nremaining:$7\n" >> "$6.config"
	cmd=""
	loss=$2
	rtt=$3
	if [ "$rtt" == "0" ]; then
		rtt=$base_rtt
	fi

	if [ "$rtt" != "0" ]; then
		cmd+="mm-delay $rtt "
	fi

	if [ "$loss" != "0" ]; then
		cmd+="mm-loss uplink $loss mm-loss downlink $loss "
	fi

	cmd+="iperf3 -c $server -p $(($base_port + $4)) -b $max_bandwidth -i $monitor_interval -V -f k -J --logfile $6 $7"

	if [ "$CC" != "mix" ]; then
		cmd+=" -C $CC"
	fi

	echo $cmd

	eval $cmd
}

kill_all_iperfs() {
	ssh $server "ps -C iperf3 -o pid --sort=-start_time | grep -v PID > iperf3s.pid" 
	spid=`ssh $server "cat iperf3s.pid"`
	spid=`echo "$spid" | tr -d " "`
	printf '%s\n' "$spid" | while IFS= read -r line; 
	do
  		echo "kill " $line
    	ssh $server "kill -9 $line" &
    	sleep 2
	done
	sleep 5
	ssh $server "ps -C iperf3 -o pid --sort=-start_time | grep -v PID"
}

cleanup() {
	if [ $enable_tcp_dump == "Y" ]; then
		tcpdumppid=`sudo ps -C tcpdump -o pid --sort=-start_time | tr -d " "`
		echo $tcpdumppid
		printf '%s\n' "$tcpdumppid" | while IFS= read -r line; 
		do
	  		echo "kill " $line
	    	sudo kill -9 $line
		done
	fi

	kill_all_iperfs
}

start_iperfs() {
	for i in $(seq 1 $1);
	do 
		ssh $server "nohup iperf3 -s -p $(($base_port + $i - 1)) > /dev/null 2>&1 &" &
		sleep 2
	done
	sleep 5

	if [ $bg_traffic != "0" ]; then
		ssh $server "nohup iperf3 -s -p $(($base_port - 1)) > /dev/null 2>&1 &" &
		sleep 2
		iperf3 -c $server -p $(($base_port - 1)) -b $bg_traffic -u -i 1 -t 1000 -V -f k --logfile $2 &
	fi

	if [ $enable_tcp_dump == "Y" ]; then
		eval "sudo tcpdump -n tcp dst portrange $base_port-$(($base_port + $1)) -s 96 &"
	fi
}

run_exp1_loss() {
	name="exp1-vary-loss-RTT-$1"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=0
	for loss in $(seq 0.00 0.01 0.1);
	do
		echo "exp1 vary loss rate $loss, RTT $1, run cmd $2"
		kill_all_iperfs
		start_iperfs 1 "$output/udp-$flow_num"
		start_flow_sync $flow_num $loss $1 0 "N" "$output/flow-$flow_num" "-t 120"
		flow_num=$((flow_num+1))
		sleep 30
		cleanup
	done
	python plot.py $output $name $monitor_interval
}

run_exp1_rtt() {
	name="exp1-vary-rtt-loss-$1"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=0
	for rtt in {0..100..10}
	do
		echo "exp1 vary RTT $rtt, loss rate $1, run cmd $2"
		kill_all_iperfs
		start_iperfs 1 "$output/udp-$flow_num"
		start_flow_sync $flow_num $1 $rtt 0 "N" "$output/flow-$flow_num" "-t 120"
		flow_num=$((flow_num+1))
		sleep 30
		cleanup
	done
	python plot.py $output $name $monitor_interval
}

run_exp2_1() {
	echo "exp2.1 loss rate $1, RTT $2"

	kill_all_iperfs
	name="exp2-1-loss-$1-RTT-$2"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=0
	start_iperfs 5 "$output/udp"
	declare -a RTT=("100" "25" "50" "25" "50")

	if [ "$2" == "N" ]; then
		RTT=("0" "0" "0" "0" "0")
	fi

	# start a long flow with RTT = 100
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 180" &
	sleep 5
	# start two short flows with 10 second
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30"
	sleep 10
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30"
	sleep 10
	# start two overlap short flows
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30" &
	sleep 10
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30" &
	# wait for experiment to finish
	sleep 120
	cleanup
	python plot.py $output $name $monitor_interval
}

run_exp2_2() {
	echo "exp2.2 loss rate $1, RTT $2"

	kill_all_iperfs
	name="exp2-2-loss-$1-RTT-$2"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=0
	start_iperfs 10 "$output/udp"
	declare -a RTT=("250" "200" "150" "100" "50")

	if [ "$2" == "N" ]; then
		RTT=("0" "0" "0" "0" "0")
	fi
	# make sure the 5th flow overlap with all other 4 flows
	for flow_num in {0..4}
	do
		start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 60" &
		sleep 10
	done
	# make sure all flows exit
	sleep 60

	# introduce flows in reverse order
	for flow_num in {5..9}
	do
		index=$((9 - $flow_num))
		start_flow_sync $flow_num $1 ${RTT[$index]} $flow_num "Y" "$output/flow-$flow_num" "-t 60" &
		sleep 10
	done
	sleep 60
	cleanup
	python plot.py $output $name $monitor_interval
}

run_exp2_3fairness() {
	echo "exp2.3 loss rate $1, RTT $2"

	kill_all_iperfs
	name="exp2-3-loss-$1-RTT-$2"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=0
	start_iperfs 10 "$output/udp"
	
	for flow_num in {0..4}
	do
		start_flow_sync $flow_num $1 $2 $flow_num "Y" "$output/flow-$flow_num" "-t 120" &
	done
	# make sure all flows exit
	sleep 150
	cleanup
	python plot.py $output $name $monitor_interval
}

run_mix_exp2_1() {
	declare -a ccs=("cubic" "bbr")
	echo "mix exp2.1 loss rate $1, RTT $2, start ${ccs[$3]}"

	kill_all_iperfs
	name="mix-exp2-1-loss-$1-RTT-$2-${ccs[$3]}"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=$3
	start_iperfs 5 "$output/udp"
	declare -a RTT=("100" "25" "50" "25" "50")

	if [ "$2" == "N" ]; then
		RTT=("0" "0" "0" "0" "0")
	fi

	# start a long flow with RTT = 100
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 180 -C ${ccs[$((flow_num%2))]}" &
	sleep 5
	# start two short flows with 10 second
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30 -C ${ccs[$((flow_num%2))]}"
	sleep 10
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30 -C ${ccs[$((flow_num%2))]}"
	sleep 10
	# start two overlap short flows
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30 -C ${ccs[$((flow_num%2))]}" &
	sleep 10
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 30 -C ${ccs[$((flow_num%2))]}" &
	# wait for experiment to finish
	sleep 120
	cleanup
	python plot.py $output $name $monitor_interval
}

run_mix_exp2_2() {
	declare -a ccs=("cubic" "bbr")
	echo "mix exp2.2 loss rate $1, RTT $2, start ${ccs[$3]}"

	kill_all_iperfs
	name="mix-exp2-2-loss-$1-RTT-$2-${ccs[$3]}"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=0
	start_iperfs 10 "$output/udp"
	declare -a RTT=("250" "200" "150" "100" "50")

	if [ "$2" == "N" ]; then
		RTT=("0" "0" "0" "0" "0")
	fi
	# make sure the 5th flow overlap with all other 4 flows
	for flow_num in {0..4}
	do
		start_flow_sync $flow_num $1 ${RTT[$flow_num]} $flow_num "Y" "$output/flow-$flow_num" "-t 60 -C ${ccs[$((flow_num%2))]}" &
		sleep 10
	done
	# make sure all flows exit
	sleep 60

	# introduce flows in reverse order
	for flow_num in {5..9}
	do
		index=$((9 - $flow_num))
		start_flow_sync $flow_num $1 ${RTT[$index]} $flow_num "Y" "$output/flow-$flow_num" "-t 60 -C ${ccs[$((flow_num%2))]}" &
		sleep 10
	done
	sleep 60
	cleanup
	python plot.py $output $name $monitor_interval
}

run_mix_exp3_6_flows() {
	declare -a ccs=("cubic" "bbr")
	echo "mix exp3 loss rate $1, first $2 first index $3"

	kill_all_iperfs
	name="mix-exp3-loss-$1-${ccs[$3]}-$2"
	output="$output_dir/$name"
	rm -rf $output
	mkdir $output
	flow_num=0
	index=$3
	start_iperfs 6 "$output/udp"

	runtime=180
	while [ $flow_num -lt $2 ]
	do
		start_flow_sync $flow_num $1 0 $flow_num "Y" "$output/flow-$flow_num" "-t $(($runtime - $flow_num * 10)) -C ${ccs[$index]}" &
		sleep 20
		flow_num=$((flow_num+1))
	done

	index=$(((index+1)%2))
	while [ $flow_num -lt 6 ]
	do
		start_flow_sync $flow_num $1 0 $flow_num "Y" "$output/flow-$flow_num" "-t $(($runtime - $flow_num * 10)) -C ${ccs[$index]}" &
		sleep 20
		flow_num=$((flow_num+1))
	done

	sleep 60
	
	cleanup
	python plot.py $output $name $monitor_interval
}

run_mix() {
	for loss_rate in 0 0.02
	do
		for index in {0..1}
		do
			for first in {1..5}
			do
				run_mix_exp3_6_flows $loss_rate $first $index
			done
		done
	done

	for loss_rate in 0 0.02
	do
		for rtt in "N" #"Y"
		do
			for start in "0" "1"
			do
				run_mix_exp2_1 $loss_rate $rtt $start
			done
		done
	done

	for loss_rate in 0 0.02
	do
		for rtt in "N" #"Y"
		do
			for start in "0" "1"
			do
				run_mix_exp2_2 $loss_rate $rtt $start
			done
		done
	done
}

run_exp2() {
	

	for loss_rate in 0 0.02
	do
		for rtt in "N" #"Y"
		do
			run_exp2_1 $loss_rate $rtt
		done
	done

	for loss_rate in 0 0.02
	do
		for rtt in "N" #"Y"
		do
			run_exp2_2 $loss_rate $rtt
		done
	done

	for loss_rate in 0 0.02
	do
		for rtt in 0 10
		do
			run_exp2_3fairness $loss_rate $rtt
		done
	done
}

if [ "$7" == "mix" ]; then
	run_mix
fi

if [ "$7" == "exp1" ]; then
	run_exp1_rtt 0
	run_exp1_rtt 0.02
	run_exp1_loss 0
	run_exp1_loss 10
fi

if [ "$7" == "exp2" ]; then
	run_exp2
fi
