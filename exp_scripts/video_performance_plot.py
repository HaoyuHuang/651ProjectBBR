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
import pprint 
pp = pprint.PrettyPrinter(indent=4)
# import matplotlib as mpl
# label_size = 8
# mpl.rcParams['xtick.labelsize'] = label_size

def process(data):
	out = {}
	out["duration"] = int(data["0"][0]) - int(data["-1"][0])
	out["join"] = int(data["1"][0]) - int(data["-1"][0])
	out["pause"] = process_pause("2", data)
	out["buffering"] = process_pause("3", data)
	out["quality"] = process_quality(data)
	out["pause_count"] = len(data["2"])
	out["buffering_count"] = len(data["3"])
	return out

def process_pause(target, data):
	if len(data[target]) <= 0:
		return 0
	# print data 
	timeline = {}
	timeline[data["0"][0]] = "end"
	for key in [target, "1"]:
		for time in data[key]:
			timeline[time] = key
	time = 0
	sorted_timeline = sorted(timeline)
	# if consecutive events are the same, it is bogus data.
	for i in range(len(sorted_timeline) - 1):
		if timeline[sorted_timeline[i]] == timeline[sorted_timeline[i+1]]:
			print "Bogus ", data
			print "Bogus data", sorted_timeline
			return 9999999999999


	for i in range(len(sorted_timeline) - 1):
		if timeline[sorted_timeline[i]] == target:
			time += sorted_timeline[i+1] - sorted_timeline[i]
	return time

def process_quality(data):
	quality_timeline = {}
	quality_timeline[data["0"][0]] = "end"
	for key in data:
		if key in ["small", "medium", "large", "hd720", "hd1080"]:
			for time in data[key]:
				quality_timeline[time] = key
	timeline = sorted(quality_timeline)
	quality = {}
	for key in ["small", "medium", "large", "hd720", "hd1080"]:
		quality[key] = 0
	for i in range(1, len(timeline)):
		key = quality_timeline[timeline[i-1]]
		quality[key] += timeline[i] - timeline[i-1]

	# score
	score_map = {}
	score_map["small"] = 240.0 / 1080.0
	score_map["medium"] = 360.0 / 1080.0
	score_map["large"] = 480.0 / 1080.0
	score_map["hd720"] = 720.0 / 1080.0
	score_map["hd1080"] = 1.00
	score = 0
	duration = int(data["0"][0]) - int(data["-1"][0])
	for key in ["small", "medium", "large", "hd720", "hd1080"]:
		score += float(score_map[key]) * float(quality[key]) / float(duration)
	return score

def plot_PLT(archive):
	"""
	  // -1 (unstarted)
      // 0 (ended)
      // 1 (playing)
      // 2 (paused)
      // 3 (buffering)
      // 5 (video cued).
      Join time
      Buffering time
      video quality, % of time spent on each quality.
	"""
	config = {}
	for file_name in os.listdir(archive):
		if "results" not in file_name:
			continue
		cc = file_name.split('-')[2]
		rtt = file_name.split('-')[4]
		loss = file_name.split('-')[6]
		bw = file_name.split('-')[8]
		html = file_name.split('-')[9]
		config["CC-{}-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(cc, rtt, loss, bw, html)] = {}
		
	for file_name in os.listdir(archive):
		if "results" not in file_name:
			continue
		cc = file_name.split('-')[2]
		rtt = file_name.split('-')[4]
		loss = file_name.split('-')[6]
		bw = file_name.split('-')[8]
		html = file_name.split('-')[9]

		print "{} {} {} {} {}".format(cc, rtt, loss, bw, html)
		# config["CC-{}-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(rtt, loss, bw, html)][cc] = []
		for r in os.listdir(archive + '/' + file_name):
			with open(archive +'/' + file_name + '/' + r) as data_file:
				data = json.load(data_file)
				for event in ["-1", "0", "1"]:
					if event not in data:
						print "Bogus data ", data
						return
				for event in ["-1", "0", "1", "2", "3", "5"]:
					if event not in data:
						data[event] = []
				config["CC-{}-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(cc, rtt, loss, bw, html)] = process(data)
	pp.pprint(config)
	return config

def export_csv(archive, csv_file):
	ccs = ["bbr", "cubic"]
	rtts = ["0", "50", "100"]
	losses = ["0", "0.02"]
	bws = ["0.02M", "1M", "10M", "1G"]
	videos = ["cat.html", "fantastic"]
	metrics = ["buffering", "buffering_count", "join", "quality"]

	config = plot_PLT(archive)
	csv = open(csv_file, 'w')

	for video in videos:
		for metric in metrics:
			for rtt in rtts:
				# combine bw and loss
				csv.write("Video-{}-Metric-{}-RTT-{}\n".format(video, metric, rtt))
				csv.write("BW-Loss,BBR,Cubic\n")
				for bw in bws:
					for loss in losses:
						print config["CC-bbr-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(rtt, loss, bw, video)]
						bbr = config["CC-bbr-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(rtt, loss, bw, video)][metric]
						cubic = config["CC-cubic-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(rtt, loss, bw, video)][metric]
						csv.write("{}-{},{},{}\n".format(bw, loss, bbr, cubic))
				csv.write("\n\n")
	csv.close()

def plot_graph(archive, pdf_file):
	ccs = ["bbr", "cubic"]
	rtts = ["0", "50", "100"]
	losses = ["0", "0.02"]
	bws = ["100K", "1M", "10M", "1G"]
	videos = ["cat.html", "fantastic"]
	metrics = ["buffering", "buffering_count", "join", "quality"]

	config = plot_PLT(archive)
	pdf = PdfPages(pdf_file)

	for video in videos:
		for rtt in rtts:
			f, axarr = plt.subplots(2, 2)
			index = 0
			for metric in metrics:
				# combine bw and loss
				i = index / 2
				j = index % 2
				index += 1
				ax = axarr[i, j]
				x_ticks = []
				bbrs = []
				cubics = []
				for bw in bws:
					for loss in losses:
						bbr_tag = "CC-bbr-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(rtt, loss, bw, video)
						cubic_tag = "CC-cubic-RTT-{}-Loss-{}-BW-{}-HTML-{}".format(rtt, loss, bw, video)
						bbr = 0
						cubic = 0
						if metric not in config[bbr_tag]:
							print "Missing", bbr_tag
						else:
							bbr = config[bbr_tag][metric]	
						if metric not in config[cubic_tag]:
							print "Missing", cubic_tag
						else:
							cubic = config[cubic_tag][metric]
						bbrs.append(bbr)
						cubics.append(cubic)
						x_ticks.append("{}-{}".format(bw, loss))
				ind = np.arange(len(bws) * len(losses))  # the x locations for the groups
				width = 0.35       # the width of the bars
				rects1 = ax.bar(ind, bbrs, width, color='r')
				rects2 = ax.bar(ind + width, cubics, width, color='b')

				# add some text for labels, title and axes ticks
				ax.set_ylabel(metric)
				# ax.set_title('Metrics-{}-Video-{}-RTT-{}'.format(metric, video, rtt))
				ax.set_xticks(ind + width)
				ax.set_xticklabels(np.array(x_ticks))
				for tick in ax.xaxis.get_major_ticks():
					tick.label.set_fontsize(6) 
					tick.label.set_rotation(45)
				ax.tick_params(axis='both', which='major', labelsize=6)
				ax.tick_params(axis='both', which='minor', labelsize=6)

				ax.legend((rects1[0], rects2[0]), ('BBR', 'Cubic'))
			# Fine-tune figure; hide x ticks for top plots and y ticks for right plots
			plt.suptitle('Video-{}-RTT-{}'.format(video, rtt))
			# plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
			# plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)


			plt.savefig(pdf, format='pdf')
	pdf.close()

if __name__ == "__main__":
	archive="/Users/haoyuh/Dropbox/BBR/video-performance2"
	file=archive + "/" + "stats.csv"
	# export_csv(archive, file)
	plot_graph(archive, archive + "/" + "stats.pdf")