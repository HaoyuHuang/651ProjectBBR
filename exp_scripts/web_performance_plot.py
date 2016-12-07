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

		self.processlatency = {}

	def plot_PLT_CDF(self, config):
		for key in config:
			# print key
			# print len(config[key])
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
			# plt.yticks(np.array([0, 20, 40, 60, 80, 90, 95, 99, 100]))
			# plt.yscale('log', nonposy='clip')
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
				pp = []
				tt = []
				array = sorted(config[key][cc])
				for i in range(len(config[key][cc])):
					pp.append(array[i])
					tt.append(i)

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

		for file_name in os.listdir(self.archive):
			if "results" not in file_name or "0.2" in file_name:
				continue
			cc = file_name.split('-')[2]
			rtt = file_name.split('-')[4]
			loss = file_name.split('-')[6]
			bw = file_name.split('-')[8]

			print "{} {} {} {}".format(cc, rtt, loss, bw)
			for r in os.listdir(self.archive + '/' + file_name):
				with open(self.archive +'/' + file_name + '/' + r) as data_file:
					data = json.load(data_file)
					if r not in self.processlatency:
						self.processlatency[r] = []
					self.processlatency[r].append(min(int(data["processlatency"]), 30000))

		print len(self.processlatency["google.com.json"])
		latency = {}
		# latency = {}

		config = {}
		for file_name in os.listdir(self.archive):
			if "results" not in file_name:
				continue
			cc = file_name.split('-')[2]
			rtt = file_name.split('-')[4]
			loss = file_name.split('-')[6]
			bw = file_name.split('-')[8]
			config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)] = {}
			latency["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)] = {}
			
		for file_name in os.listdir(self.archive):
			if "results" not in file_name:
				continue
			cc = file_name.split('-')[2]
			rtt = file_name.split('-')[4]
			loss = file_name.split('-')[6]
			bw = file_name.split('-')[8]

			print "{} {} {} {}".format(cc, rtt, loss, bw)
			print "\n"
			config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc] = []
			latency["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc] = {}
			for r in os.listdir(self.archive + '/' + file_name):
				if is_json is True:
					with open(self.archive +'/' + file_name + '/' + r) as data_file:
						data = json.load(data_file)
						config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc].append(min(data[key], 30000))
						# print r
						latency["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc][r] = data[key]
						# if key == "totallatency":
						# 	config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc].append(min(int(data["networklatency"]) + (sum(self.processlatency[r]) / len(self.processlatency[r])), 30000))
						# else:
						# 	config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc].append(min(data[key], 30000))
				else:
					config["RTT-{}-Loss-{}-BW-{}".format(rtt, loss, bw)][cc].append(self.cal_plt(self.archive +'/' + file_name + '/' + r))

		for key in latency:
			if len(latency[key]) != 2:
				continue
			print key
			print
			diff = []
			for webpage in latency[key]['bbr']:
				# print webpage, latency[key]['bbr'][webpage], latency[key]['cubic'][webpage]
				# if latency[key]['bbr'][webpage]  latency[key]['cubic'][webpage]
				diff.append(latency[key]['bbr'][webpage] - latency[key]['cubic'][webpage])
			# print key
			# print sorted(diff)
			print sum(diff) / len(diff)


		self.plot_PLT_CDF(config)
		self.export_excel(config)

	def cal_elapsed_time(self, file_name):
		with open(file_name) as results:
			for line in results:
				# "trace file elapsed time: 0:00:26.880514"
				if "trace file elapsed time: " in line:
					time = line.split("trace file elapsed time: ")[1]
					# print time
					# print time
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

def cal_bytes(csv_file, file_dir, sender):
	conn = []
	avg_segm_size = []
	max_segm_size = []
	page_size = []
	page_connections = []
	page_index = -1
	initial_window_satis=0
	csv = open(csv_file, 'w')
	for file_name in os.listdir(file_dir):
		if "tcptrace" not in file_name:
			continue
		page_index += 1
		page_connections.append(0)
		page_size.append(0)
		
		with open(file_dir + '/' + file_name) as data:
			valid = True
			added = False
			for line in data:
				if "filename" in line:
					valid = True
					added = False
				if "actual data bytes" in line:
					# print line.split("actual data bytes:")[2][:-2]
					# print float(line.split("actual data bytes:")[2][:-2])
					sent = float(line.split("actual data bytes:")[1])
					rec = float(line.split("actual data bytes:")[2][:-2])
					if sent != 0 and rec != 0:
						conn.append(sent if sender else rec)
					else:
						valid = False
					page_size[page_index] += rec
				if valid and "avg segm size:" in line:
					sent = float(line.split("avg segm size:")[1].split('bytes')[0])
					rec = float(line.split("avg segm size:")[2].split('bytes')[0])
					if sent != 0 and rec != 0:
						avg_segm_size.append(sent if sender else rec)
					else:
						valid = False

				if valid and "max segm size:" in line:
					sent = float(line.split("max segm size:")[1].split('bytes')[0])
					rec = float(line.split("max segm size:")[2].split('bytes')[0])
					if sent != 0 and rec != 0:
						max_segm_size.append(sent if sender else rec)
					else:
						valid = False

				if valid and "initial window:" in line and "bytes" in line:
					# print line.split("initial window:")
					sent = float(line.split("initial window:")[1].split("bytes")[0])
					rec = float(line.split("initial window:")[2].split("bytes")[0])
					added = True
					# print sent, rec
					initial_window=sent if sender else rec
					if initial_window >= max_segm_size[-1]:
						initial_window_satis+=1

				if valid and added:
					page_connections[page_index] += 1
					added = False
	print "number of connections", len(conn)
	print ""
	print "actual data bytes:"
	csv.write("actual data bytes:\n")
	percentile_map(csv, [x for x in range(0, 101, 2)], conn)
	print ""
	print "average segment size"
	csv.write("average segment size:\n")
	percentile_map(csv, [x for x in range(0, 101, 2)], avg_segm_size)
	print ""
	print "max segment size"
	csv.write("max segment size:\n")
	percentile_map(csv, [x for x in range(0, 101, 2)], max_segm_size)
	print "page size"
	csv.write("page size:\n")
	percentile_map(csv, [x for x in range(0, 101, 2)], page_size)
	print "page connections"
	csv.write("page connection:\n")
	percentile_map(csv, [x for x in range(0, 101, 2)], page_connections)
	print ""
	print "% of connections that have initial window size >= max segment size"
	print float(initial_window_satis) / len(conn)

def percentile_map(csv, percentiles, array):
	array = sorted(array)
	for percentile in percentiles:
		csv.write(str(percentile) + ",")
	csv.write("\n")
	for percentile in percentiles:
		if percentile == 0:
			print "percentile {} data {} bytes".format(percentile, array[0])
			csv.write(str(array[0]) + ",")
		else:
			value = array[int((percentile * len(array) - 1) / 100)]
			print "percentile {} data {} bytes".format(percentile, value)
			csv.write(str(value) + ",")
	csv.write("\n\n")

if __name__ == "__main__":
	archive="/Users/haoyuh/Documents/PhdUSC/BBR/web-performance-top-100"
	for key in ["networklatency", "processlatency", "totallatency"]:
		pdf="{}/stats-{}.pdf".format(archive, key)
		csv="{}/stats-{}.csv".format(archive, key)
		stats = BBRWebStats(archive, pdf, csv)
		stats.plot_PLT(True, key)
	# cal_bytes("sender.csv", "/Users/haoyuh/Dropbox/results-cc-bbr-rtt-0-loss-0-bw-1G-selenium-Y", True)
	# cal_bytes("receiver.csv", "/Users/haoyuh/Dropbox/results-cc-bbr-rtt-0-loss-0-bw-1G-selenium-Y", False)



