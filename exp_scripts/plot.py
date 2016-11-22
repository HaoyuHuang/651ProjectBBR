import os
import sys
import json
import re

import numpy as np
import matplotlib
# lab machine supports agg display
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as lines
import matplotlib.transforms as mtransforms
import matplotlib.text as mtext
import collections
import matplotlib.lines as mlines
from os import listdir
from os.path import isfile, join
import datetime

from matplotlib.backends.backend_pdf import PdfPages
import subprocess

class BBRStats():
	def __init__(self, time_interval):
		self.resolution = 1
		if time_interval == ".1":
			self.resolution = 10
		# print self.resolution

	def plot_flow(self, archive):
		flow_time_table = {}
		# read configuration
		for file_name in os.listdir(archive):

			if "config" not in file_name:
				continue
			flow_num = int(file_name[5:-7])

			flow_time_table[flow_num] = {}
			flow_time_table[flow_num]["thpt_timeline"] = []
			flow_time_table[flow_num]["cwnd_timeline"] = []
			flow_time_table[flow_num]["retr_timeline"] = []
			flow_time_table[flow_num]["rtt_timeline"] = []

			with open(archive + '/' + file_name) as log_file:
				for line in log_file:
					line = line[:-1]
					flow_time_table[flow_num][line.split(":")[0]] = line.split(":")[1]

		# read flow timeline
		for file_name in os.listdir(archive):

			if "flow" not in file_name or "config" in file_name:
				continue
			flow_num = int(file_name[5:])

			with open(archive + '/' + file_name) as data_file:
				data = json.load(data_file)
				flow_time_table[flow_num]["duration"] = data["start"]["test_start"]["duration"]

				for key in data["end"]["streams"][0]["sender"]:
					flow_time_table[flow_num][key] = data["end"]["streams"][0]["sender"][key]

				for interval in data["intervals"]:
					flow_time_table[flow_num]["thpt_timeline"].append(interval["streams"][0]["bits_per_second"])
					flow_time_table[flow_num]["cwnd_timeline"].append(interval["streams"][0]["snd_cwnd"])
					flow_time_table[flow_num]["retr_timeline"].append(interval["streams"][0]["retransmits"])
					flow_time_table[flow_num]["rtt_timeline"].append(interval["streams"][0]["rtt"])

		# print json.dumps(flow_time_table, indent=4)

		# process relative start time
		min_start_time = 99999999999
		for flow in flow_time_table:
			min_start_time = min(int(flow_time_table[flow]["start_time"]), min_start_time)

		for flow in flow_time_table:
			flow_time_table[flow]["start_time"] = int(flow_time_table[flow]["start_time"]) - min_start_time

		return flow_time_table

	def export_excel(self, exp_folder, export_file, plot_time_line):

		flow_time_table = self.plot_flow(exp_folder)
		csv = exp_folder + "/{}.csv".format(export_file)
		print csv
		pdffile = exp_folder + "/{}.pdf".format(export_file)

		export_file = open(csv, 'w')
		print pdffile
		pdf=PdfPages(pdffile)

		max_time = 0
		for stat in flow_time_table.values():
			max_time = max(max_time, stat['duration'] + int(stat['start_time']))
		print "max time ", max_time, "s"
		config_line = "flow,config-rtt,config-loss,start_time,duration,mean_rtt,min_rtt,max_rtt,bits_per_second,retransmits"
		export_file.write(config_line + "\n")
		data = ""
		for flow in sorted(flow_time_table):
			line = ""
			for config in config_line.split(","):
				line += str(flow_time_table[flow][config]) + ","
			data += line[:-1] + "\n"
		export_file.write(data)

		for field in ["bits_per_second", "mean_rtt", "retransmits"]:
			self.plot_overall_timeline(pdf, field, flow_time_table)

		if plot_time_line:
			for field in ["thpt_timeline", "cwnd_timeline", "retr_timeline", "rtt_timeline"]:
				export_file.write("\n")
				self.export_excel_timeline(export_file, field, max_time, flow_time_table)
				self.plot_pdf_timeline(pdf, field, max_time, flow_time_table)

		export_file.close()
		pdf.close()

	def plot_overall_timeline(self, pdf, field, flow_time_table):
		x = [flow_num for flow_num in sorted(flow_time_table)]
		y = [flow_time_table[flow_num][field] for flow_num in sorted(flow_time_table)]
		print x
		print y

		fig, ax = plt.subplots()
		ax.plot(np.array(x), np.array(y))
		ax.set_xlabel('flow #')
		plt.legend()
		ax.set_title('Overall ' + field)
		plt.savefig(pdf, format='pdf')

	def plot_pdf_timeline(self, pdf, field, max_time, flow_time_table):
		max_time = max_time * self.resolution
		x = []
		for i in range(0, max_time):
			x.append(i)
		
		fig, ax = plt.subplots()

		# print x

		for flow in sorted(flow_time_table):
			y = []
			for i in range(0, self.resolution*int(flow_time_table[flow]["start_time"])):
				y.append(0)
			for dp in flow_time_table[flow][field]:
				y.append(int(dp))
			for i in range(len(flow_time_table[flow][field]) + self.resolution*int(flow_time_table[flow]["start_time"]), max_time):
				y.append(0)
			# print y

			ax.plot(np.array(x), np.array(y), label=flow)

		ax.set_xlabel('time ({}second)'.format(1/ self.resolution))
		# ax.set_ylabel('latency (us)')

		plt.legend()
		# fig.suptitle(self.title, fontweight='bold', fontsize=12)
		ax.set_title(field)
		plt.savefig(pdf, format='pdf')

	def export_excel_timeline(self, export_file, field, max_time, flow_time_table):
		timeline = "flow,"
		max_time = max_time * self.resolution
		for i in range(0, max_time):
			timeline += str(i) + ","
		export_file.write(timeline[:-1] + "\n")
		for flow in sorted(flow_time_table):
			line = flow_time_table[flow]["flow"] + ","
			for i in range(0, self.resolution*int(flow_time_table[flow]["start_time"])):
				line += "0,"
			for dp in flow_time_table[flow][field]:
				line += str(dp) + ","
			for i in range(len(flow_time_table[flow][field]) + self.resolution*int(flow_time_table[flow]["start_time"]), max_time):
				line += "0,"
			export_file.write(line[:-1] + "\n")

	

if __name__ == "__main__":
	# plot_flow("/Users/haoyuh/Documents/PhdUSC/BBR/exp_scripts")
	exp_folder = sys.argv[1]
	result_file = sys.argv[2]
	time_resolution = sys.argv[3]
	print "exp folder ", exp_folder, "result", result_file, "resolution", time_resolution
	# exp_folder="/Users/haoyuh/Documents/PhdUSC/BBR/bbr-exp/bbr-maxb-1G-basertt-0-BG-0-tcpdump-N/exp1-vary-rtt-loss-0"
	# result_file="/Users/haoyuh/Documents/PhdUSC/BBR/bbr-exp/bbr-maxb-1G-basertt-0-BG-0-tcpdump-N/exp1-vary-rtt-loss-0/run.txt"
	stats = BBRStats(time_resolution)
	stats.export_excel(exp_folder, result_file, True)