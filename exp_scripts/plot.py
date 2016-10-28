import os
import sys
import json
import re

def plot_flow(archive):
	# read flow time table 
	# read each flow file and then plot throughput graph according to time table
	flow_time_table = {}
	for file_name in os.listdir(archive):

		if "flow" not in file_name:
			continue

		flow_time_table[file_name] = {}
		flow_time_table[file_name]["thpt"] = []
		flow_time_table[file_name]["cwnd"] = []
		flow_time_table[file_name]["retr"] = []
		flow_time_table[file_name]["avg_thpt"] = ""
		flow_time_table[file_name]["total_retr"] = ""
		with open(archive + '/' + file_name) as log_file:
			timeline_start = False
			summary_start = False
			for line in log_file:
				# print line
				if "flowtimeline" in line:
					timeline_start = True
					continue

				if summary_start:
					if "sender" in line:
						ems = filter(lambda a: a != '' and a != '\n', line.split(" "))
						print ems
						flow_time_table[file_name]["avg_thpt"] = ems[-4] + ems[-3]
						flow_time_table[file_name]["total_retr"] = ems[-2]
				elif timeline_start:
					if "- - - - - - - - - - - - - - - - - - - - - - - - -" in line:
						summary_start = True
						continue
					if "sec" in line:
						ems = filter(lambda a: a != '' and a != '\n', line.split(" "))
						flow_time_table[file_name]["thpt"].append(ems[-5] + ems[-4])
						flow_time_table[file_name]["retr"].append(ems[-3])
						flow_time_table[file_name]["cwnd"].append(ems[-2] + ems[-1])

				else:
					# remove \n 
					line = line[:-1]
					flow_time_table[file_name][line.split(":")[0]] = line.split(":")[1]
	print json.dumps(flow_time_table, indent=4)
	return flow_time_table

def export_excel(export_file, flow_time_table, plot_time_line):
	export_file = open(export_file, 'w')
	max_time = 0
	for stat in flow_time_table.values():
		max_time = max(max_time, len(stat['thpt']) + int(stat['start_time']))
	print "max time ", max_time, "s"
	config_line = "flow,rtt,loss,start_time,duration,avg_thpt,total_retr"
	export_file.write(config_line + "\n")
	data = ""
	for flow in flow_time_table:
		line = ""
		for config in config_line.split(","):
			line += flow_time_table[flow][config] + ","
		data += line[:-1] + "\n"
	export_file.write(data)

	if plot_time_line:
		for field in ["thpt", "cwnd", "retr"]:
			export_file.write("\n")
			export_excel_timeline(export_file, field, max_time, flow_time_table)
	export_file.close()

def export_excel_timeline(export_file, field, max_time, flow_time_table):
	timeline = "flow,"
	for i in range(0, max_time):
		timeline += str(i) + ","
	export_file.write(timeline[:-1] + "\n")
	for flow in flow_time_table:
		line = flow_time_table[flow]["flow"] + ","
		for i in range(0, int(flow_time_table[flow]["start_time"])):
			line += "0,"
		for dp in flow_time_table[flow][field]:
			line += dp + ","
		for i in range(len(flow_time_table[flow][field]) + int(flow_time_table[flow]["start_time"]), max_time):
			line += "0,"
		export_file.write(line[:-1] + "\n")

if __name__ == "__main__":
	# plot_flow("/Users/haoyuh/Documents/PhdUSC/BBR/exp_scripts/exp2-1-loss-0-RTT-N")
	exp_folder = sys.argv[1]
	result_file = sys.argv[2]
	print "exp folder ", exp_folder, "result", result_file
	flow_table = plot_flow(exp_folder)
	export_excel(result_file, flow_table, True)
	