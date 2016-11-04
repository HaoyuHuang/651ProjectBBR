#!/bin/bash

# source ./exp_base_performance.sh

# cc, max bandwidth, base rtt, bg traffic, tcp dump? 

for cc in "cubic" "bbr"
do
	bash exp_base_performance.sh $cc '1G' 0 0 'N' '1' 'exp1'
	bash exp_base_performance.sh $cc '1G' 0 0 'N' '01' 'exp1'
	bash exp_base_performance.sh $cc '1M' 0 0 'N' '01' 'exp1'
done

for cc in "cubic" "bbr"
do
	bash exp_base_performance.sh $cc '1M' 0 0 'N' '1' 'exp2'
	bash exp_base_performance.sh $cc '1G' 0 0 'N' '01' 'exp2'
	bash exp_base_performance.sh $cc '1G' 5 0 'N' '1' 'exp2'
	bash exp_base_performance.sh $cc '1G' 5 '200M' 'N' '1' 'exp2'
done