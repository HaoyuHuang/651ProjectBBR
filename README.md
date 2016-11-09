# 651ProjectBBR
## Install kernel sources with BBR
1. Follow steps in https://github.com/google/bbr/blob/master/Documentation/bbr-quick-start.md
2. If you don't have a Google compute engine, follow the following steps:
3. Install lilo https://linux.die.net/man/8/lilo
4. Obtain kernel source with BBR

```
git clone git://git.kernel.org/pub/scm/linux/kernel/git/davem/net-next.git
cd net-next/
make olddefconfig
```
### Make Install
1. Make sure CONFIG_BBR is set to true and FQ modules are enabled. Here is the .config file I used to successfully install the kernel. 
2. Install kernel
3. change /etc/lilo.conf to include the installed kernal
```
make -j 8 && make -j 8 modules_install && make install
change /etc/lilo.conf to include the installed kernal
/sbin/lilo
```
### Reboot

2. reboot
3. confirm fq qdisc is installed and that BBR is avaiable:
```
tc qdisc show
cat /proc/sys/net/ipv4/tcp_available_congestion_control
```

### Install Mahimahi
```
Follow steps in http://mahimahi.mit.edu/
```
### Install iperf3
```
wget http://downloads.es.net/pub/iperf/iperf-3-current.tar.gz
```
### Install Python
1. Install python 2.7
2. Install python matplotlib http://matplotlib.org/

## Experiments
A simple dumebell topology is used where two nodes connected with a 1Gbits/sec link. Each node is an off-the-shelf PC configured with 4 (8 hyper-threaded) Core Intel i7-3770 3.40 GHz CPU with 16GB of memory.

Change the server Ip adderss to be your server Ip address. 

### Section 3.1 Experimenting with single-flow
Run following commands and view results in /tmp/$cc-maxb-1G-basertt-0-BG-0-tcpdump-N-interval-.1-exp1/
```
for cc in "cubic" "bbr"
do
	bash exp_base_performance.sh $cc '1G' 0 0 'N' '.1' 'exp1'
done
```

### Section 3.2 Experimenting with multiple-flow
Run following commands and view results in /tmp/$cc-maxb-1G-basertt-0-BG-0-tcpdump-N-interval-.1-exp2/
```
for cc in "cubic" "bbr"
do
	bash exp_base_performance.sh $cc '1G' 0 0 'N' '.1' 'exp2'
done
```
#### Background traffic
Run following commands and view results in /tmp/$cc-maxb-1G-basertt-0-BG-200M-tcpdump-N-interval-.1-$exp/
```
for exp in "exp1" "exp2"
do
	for cc in "cubic" "bbr"
	do
		bash exp_base_performance.sh $cc '1G' 0 '200M' 'N' '.1' $exp
	done
done
```
#### Mix flow
Run following commands and view results in /tmp/mix-maxb-1G-basertt-0-BG-0-tcpdump-N-interval-.1-mix/
```
bash exp_base_performance.sh 'mix' '1G' 0 '' 'N' '.1' 'mix'
```


