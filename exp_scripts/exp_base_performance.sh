#!/bin/bash
# mahimahi http://mahimahi.mit.edu/
# iperf http://downloads.es.net/pub/iperf/iperf-3-current.tar.gz

server=10.0.2.15
output_dir="/tmp"
base_port=10000

start_flow_sync() {
	echo "flow number: $1 loss $2 rtt $3 start_time $4 time $5 output dir $6"
	printf "flow:$1\nloss:$2\nrtt:$3\nstart_time:$4\nduration:$5\nflowtimeline\n" >> $6
	if [ "$1" == "0" ]; then
		iperf3 -c $server -p $(($base_port + $1)) -i 1 -t $5 >> $6
	elif [ "$2" == "0" ]; then
		mm-delay $3 iperf3 -c $server -p $(($base_port + $1)) -i 1 -t $5 >> $6
	else
		mm-delay $3 mm-loss uplink $2 mm-loss downlink $2 iperf3 -c $server -p $(($base_port + $1)) -i 1 -t $5 >> $6
	fi
}

kill_all_iperfs() {
	ssh $server "ps -C iperf3 -o pid --sort=-start_time | grep -v PID > iperf3s.pid" 
	spid=`ssh $server "cat iperf3s.pid"`
	spid=`echo "$spid" | tr -d " "`
	printf '%s\n' "$spid" | while IFS= read -r line; 
	do
  		echo "kill " $line
    	ssh $server "kill -9 $line" &
	done
	sleep 5
	ssh $server "ps -C iperf3 -o pid --sort=-start_time | grep -v PID"
}

start_iperfs() {
	for i in $(seq 1 $1); 
	do 
		ssh $server "nohup iperf3 -s -p $(($base_port + $i - 1)) > /dev/null 2>&1 &" &
	done
	sleep 5
}

run_exp1_loss() {
	output="$output_dir/exp1-vary-loss-RTT-$1-runtime-$2"
	rm -rf $output
	mkdir $output
	flow_num=0
	for loss in $(seq 0.00 0.01 0.1);
	do
		echo "exp1 vary loss rate $loss, RTT $1, runtime $2"
		kill_all_iperfs
		start_iperfs 1
		start_flow_sync 0 $loss $1 0 $2 "$output/flow-loss-$loss"
		flow_num=$((flow_num+1))
	done
	python plot.py $output "$output_dir/exp1-vary-loss-RTT-$1.txt"
}

run_exp1_rtt() {
	output="$output_dir/exp1-vary-rtt-loss-$1-runtime-$2"
	rm -rf $output
	mkdir $output
	flow_num=0
	for rtt in {0..100..10}
	do
		echo "exp1 vary RTT $rtt, loss rate $1, runtime $2"
		kill_all_iperfs
		start_iperfs 1
		start_flow_sync 0 $1 $rtt 0 $2 "$output/flow-rtt-$rtt"
		flow_num=$((flow_num+1))
	done
	python plot.py $output "$output_dir/exp1-vary-rtt-loss-$1.txt"
}

run_exp2_1() {
	echo "exp2.1 loss rate $1, RTT $2"

	kill_all_iperfs
	output="$output_dir/exp2-1-loss-$1-RTT-$2"
	rm -rf $output
	mkdir $output
	flow_num=0
	start_iperfs 5
	declare -a RTT=("100" "25" "50" "25" "50")

	if [ "$2" == "N" ]; then
		RTT=("0" "0" "0" "0" "0")
	fi

	# start a long flow with RTT = 100
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} 0 120 "$output/flow-$flow_num" &
	sleep 5
	# start two short flows with 10 second
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} 5 10 "$output/flow-$flow_num"
	sleep 5
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} 20 10 "$output/flow-$flow_num"
	sleep 5
	# start two overlap short flows
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} 35 10 "$output/flow-$flow_num" &
	sleep 5
	flow_num=$((flow_num+1))
	start_flow_sync $flow_num $1 ${RTT[$flow_num]} 40 10 "$output/flow-$flow_num" &
	# wait for experiment to finish
	sleep 120
	python plot.py $output "$output_dir/exp2-1-loss-$1-RTT-$2.txt"
}

run_exp2_2() {
	echo "exp2.2 loss rate $1, RTT $2"

	kill_all_iperfs
	output="$output_dir/exp2-2-loss-$1-RTT-$2"
	rm -rf $output
	mkdir $output
	flow_num=0
	start_iperfs 10
	declare -a RTT=("250" "200" "150" "100" "50")

	if [ "$2" == "N" ]; then
		RTT=("0" "0" "0" "0" "0")
	fi
	# make sure the 5th flow overlap with all other 4 flows
	start_time=0
	for flow_num in {0..4}
	do
		start_flow_sync $flow_num $1 ${RTT[$flow_num]} $start_time 25 "$output/flow-$flow_num" &
		sleep 5
		start_time=$((start_time+5))
	done
	# make sure all flows exit
	sleep 30
	start_time=$((start_time+30))

	# introduce flows in reverse order
	for flow_num in {5..9}
	do
		index=$((9 - $flow_num))
		start_flow_sync $flow_num $1 ${RTT[$index]} $start_time 25 "$output/flow-$flow_num" &
		sleep 5
		start_time=$((start_time+5))
	done
	sleep 30
	python plot.py $output "$output_dir/exp2-2-loss-$1-RTT-$2.txt"
}

run_exp1_rtt 0 120
run_exp1_rtt 10 120
run_exp1_loss 0 120
run_exp1_loss 0.02 120

for loss_rate in 0 0.02
do
	for rtt in "Y" "N"
	do
		run_exp2_1 $loss_rate $rtt
	done
done

for loss_rate in 0 0.02
do
	for rtt in "Y" "N"
	do
		run_exp2_2 $loss_rate $rtt
	done
done