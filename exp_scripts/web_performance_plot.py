import os
import sys
import json
import re
import datetime
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
from datetime import datetime

from matplotlib.backends.backend_pdf import PdfPages
import subprocess
import json

def cdf(array):
	cdf_map = {}
	array = sorted(array)
	# print array
	i = 0
	while i < len(array):
		while i < len(array) - 1 and array[i] == array[i+1]:
			i+=1
		p = float(i) * 100 / float(len(array))
		cdf_map[p] = array[i]
		i += 1
	return cdf_map


class BBRWebStats():
	def __init__(self, archive, pdf, csv):
		self.archive = 	archive
		self.pdf = PdfPages(pdf)
		self.csv = open(csv, 'w')

	def plot_PLT_CDF(self, config):
		for key in config:
			print key
			print len(config[key])
			if len(config[key]) != 2:
				continue

			fig, ax = plt.subplots()
			max_x = 0

			for cc in config[key]:
				cdf_map = cdf(config[key][cc])
				pp = []
				tt = []
				for p in sorted(cdf_map):
					pp.append(p)
					tt.append(cdf_map[p])
					max_x = max(max_x, cdf_map[p])

				ax.plot(np.array(tt), np.array(pp), label=cc)
			ax.set_xlabel('time (ms)')
			ax.set_ylabel('CDF (%)')
			max_x = int(max_x / 1000)

			plt.legend()
			ax.set_title(key)
			# plt.yticks(np.arange(0, max_x+1, 1.0))
			plt.savefig(self.pdf, format='pdf')
		self.pdf.close()

	def export_excel(self, config):
		for key in config:
			if len(config[key]) != 2:
				continue
			for cc in config[key]:
				self.csv.write(key + '-' + cc + '\n')
				cdf_map = cdf(config[key][cc])
				pp = []
				tt = []
				for p in sorted(cdf_map):
					pp.append(cdf_map[p])
					tt.append(p)

				xstr = ""
				for x in pp:
					xstr += str(x) + ","
				self.csv.write(xstr + '\n')
				xstr = ""
				for y in tt:
					xstr += str(y) + ","
				self.csv.write(xstr + '\n')

		self.csv.close()


	def plot_PLT(self, is_json, key):
		config = {}
		for file_name in os.listdir(self.archive):
			if "results" not in file_name:
				continue
			cc = file_name.split('-')[2]
			rtt = file_name.split('-')[4]
			loss = file_name.split('-')[6]
			bw = file_name.split('-')[8]
			config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)] = {}
			
		for file_name in os.listdir(self.archive):
			if "results" not in file_name:
				continue
			cc = file_name.split('-')[2]
			rtt = file_name.split('-')[4]
			loss = file_name.split('-')[6]
			bw = file_name.split('-')[8]

			print "{} {} {} {}".format(cc, rtt, loss, bw)
			config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc] = []

			if is_json is True:
				with open('data.json') as data_file:    
    				data = json.load(data_file)
    				for website in data:
    					config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc].append(data[website][key])
    		else:
				for r in os.listdir(self.archive + '/' + file_name):
					config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc].append(self.cal_plt(self.archive +'/' + file_name + '/' + r))

		self.plot_PLT_CDF(config)
		self.export_excel(config)

	def cal_elapsed_time(self, file_name):
		with open(file_name) as results:
			for line in results:
				# "trace file elapsed time: 0:00:26.880514"
				if "trace file elapsed time: " in line:
					time = line.split("trace file elapsed time: ")[1]
					# print time
					print time
					return float(time.split(":")[2].split(".")[0]) * 1000 + float(time.split(":")[2].split(".")[1]) / 1000

	def cal_plt(self, file_name):
		conns = {}
		# convert to ms
		with open(file_name) as results:
			new_conn = False
			cur_conn_time = None
			for line in results:
				if "TCP connection info" in line:
					continue
				if "TCP connection " in line:
					new_conn = True
				if "=========" in line:
					new_conn = False

				if new_conn == False:
					continue

				if "first packet: " in line:
					# Sat Nov 19 12:11:02.088443 2016
					# print line
					# print line.split("\tfirst packet:  ")[1][:-1]
					cur_conn_time = datetime.strptime(line.split("\tfirst packet:  ")[1][:-1], "%a %b %d %H:%M:%S.%f %Y")
					conns[cur_conn_time] = 0
				if "elapsed time: " in line:
					#  0:00:00.004,984
					time = line.split("elapsed time:  ")[1][:-1]
					if int(time.split(":")[0]) > 0:
						print "BUG!!!", line
					elif int(time.split(":")[1]) > 0:
						print "BUG!!!", line

					# print 
					conns[cur_conn_time] = float(time.split(":")[2].split(".")[0]) * 1000 + float(time.split(":")[2].split(".")[1]) / 1000
				if "idletime max: " in line:
					# print line
					# print float([x for x in line.split("idletime max:")[1].split(" ") if x][0])
					#  2.1 ms
					idletime = float([x for x in line.split("idletime max:")[1].split(" ") if x][0])
					if idletime < conns[cur_conn_time]:
						conns[cur_conn_time] = conns[cur_conn_time] - int(idletime)
					else:
						print "ERROR!!! idle {} elasped {}".format(idletime, conns[cur_conn_time])

		sorted_start_time = sorted(conns)
		start = 0
		end = conns[sorted_start_time[0]]
		i = 1
		for i in range(1, len(sorted_start_time), 1):
			i_start = (sorted_start_time[i] - sorted_start_time[0]).total_seconds() * 1000
			# print i_start

			if i_start < end or i_start - end < 2000:
				end = i_start + conns[sorted_start_time[i]]
			else:
				break
		# print file_name, end-start
		# print "%s %f".format(file_name, end-start)
		return int(end - start)

if __name__ == "__main__":
	archive="/Users/haoyuh/Dropbox/BBR/web-performance"
	for key in ["networklatency", "processlatency", "totallatency"]:
		pdf="/Users/haoyuh/Dropbox/BBR/web-performance/stats-{}.pdf".format(key)
		csv="/Users/haoyuh/Dropbox/BBR/web-performance/stats-{}.csv".format(key)
		stats = BBRWebStats(archive, pdf, csv)
		stats.plot_PLT(True, key)