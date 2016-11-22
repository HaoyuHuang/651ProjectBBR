#!/bin/bash

# source ./exp_base_performance.sh

eval_base_performance() {
	# cc, max bandwidth, base rtt, bg traffic, tcp dump? 
	for cc in "cubic" "bbr"
	do
		# bash exp_base_performance.sh $cc '1G' 0 0 'N' '1' 'exp1'
		bash exp_base_performance.sh $cc '1G' 0 0 'N' '.1' 'exp1'
		bash exp_base_performance.sh $cc '10M' 0 0 'N' '1' 'exp1'
	done

	for cc in "cubic" "bbr"
	do
		bash exp_base_performance.sh $cc '10M' 0 0 'N' '1' 'exp2'
		bash exp_base_performance.sh $cc '1G' 0 0 'N' '.1' 'exp2'
		bash exp_base_performance.sh $cc '1G' 5 0 'N' '1' 'exp2'
		bash exp_base_performance.sh $cc '1G' 5 '200M' 'N' '1' 'exp2'
	done
}

eval_web_performance() {
	bash exp_web_performance.sh "record" "Y"
	bash exp_web_performance.sh "replay" 'Y' 'bbr' '50' '0.02' '1G'

	for bw in "1G" "10M" "1M"
	do
		for cc in "cubic" "bbr"
		do
			for rtt in "0" "50"
			do
				for loss in "0" "0.02"
				do
					bash exp_web_performance.sh "replay" 'Y' $cc $rtt $loss $bw
				done
			done
		done
	done
}
eval_web_performance
# bash exp_web_performance.sh "replay" "bbr" "50" "0.02" "1G"
