import matplotlib.pyplot as plt
import matplotlib.patches as mpatch

def exp2_timeline():
	fig, ax = plt.subplots()
	rectangles = {'flow0' : mpatch.Rectangle((0,0), 180, 5, color='#0099FF', ec='black'),
	              'flow1' : mpatch.Rectangle((10,5), 30, 5, color='#0099FF', ec='black'),
	              'flow2' : mpatch.Rectangle((70,5), 30, 5, color='#0099FF', ec='black'),
	              'flow3' : mpatch.Rectangle((130,5), 30, 5, color='#0099FF', ec='black'),
	              'flow4' : mpatch.Rectangle((145,10), 30, 5, color='#0099FF', ec='black')
	              }

	for r in rectangles:
	    ax.add_artist(rectangles[r])
	    rx, ry = rectangles[r].get_xy()
	    cx = rx + rectangles[r].get_width()/2.0
	    cy = ry + rectangles[r].get_height()/2.0

	    ax.annotate(r, (cx, cy), fontsize=10, ha='center', va='center')
	ax.set_xlabel('simulation time (second) ')
	ax.set_xlim((0, 200))
	ax.set_ylim((0, 50))
	ax.set_aspect('equal')
	ax.set_yticklabels([])
	fig.savefig('exp2-timeline.eps', format='eps', dpi=10000)   # save the figure to file
	plt.close(fig)

def exp3_timeline():

# 0	60
# 10	60
# 20	60
# 30	60
# 40	60
# 110	60
# 120	60
# 130	60
# 140	60
# 150	60
	fig, ax = plt.subplots()
	time=60
	rectangles = {'flow0' : mpatch.Rectangle((0,0), time, 5, color='#0099FF', ec='black'),
	              'flow1' : mpatch.Rectangle((10,5), time, 5, color='#0099FF', ec='black'),
	              'flow2' : mpatch.Rectangle((20,10), time, 5, color='#0099FF', ec='black'),
	              'flow3' : mpatch.Rectangle((30,15), time, 5, color='#0099FF', ec='black'),
	              'flow4' : mpatch.Rectangle((40,20), time, 5, color='#0099FF', ec='black'),
	              'flow5' : mpatch.Rectangle((110,0), time, 5, color='#0099FF', ec='black'),
	              'flow6' : mpatch.Rectangle((120,5), time, 5, color='#0099FF', ec='black'),
	              'flow7' : mpatch.Rectangle((130,10), time, 5, color='#0099FF', ec='black'),
	              'flow8' : mpatch.Rectangle((140,15), time, 5, color='#0099FF', ec='black'),
	              'flow9' : mpatch.Rectangle((150,20), time, 5, color='#0099FF', ec='black')
	              }

	for r in rectangles:
	    ax.add_artist(rectangles[r])
	    rx, ry = rectangles[r].get_xy()
	    cx = rx + rectangles[r].get_width()/2.0
	    cy = ry + rectangles[r].get_height()/2.0

	    ax.annotate(r, (cx, cy), fontsize=10, ha='center', va='center')
	ax.set_xlabel('simulation time (second) ')
	ax.set_xlim((0, 220))
	ax.set_ylim((0, 50))
	ax.set_yticklabels([])
	ax.set_aspect('equal')
	fig.savefig('exp3-timeline.eps', format='eps', dpi=10000)   # save the figure to file
	plt.close(fig)

if __name__ == '__main__':
	exp2_timeline()

