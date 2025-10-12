import glob
import os
import traceback
from functools import partial

# matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button

import all_graphs
from CursorHoverInfo import CursorHoverInfo

H_PAD = 0.0125
V_PAD = 0.0125
V_SIZE_MIN = 0.04

colors = {
	"r": ("tab:red", "lightcoral"),
	"g": ("limegreen", "palegreen"),
	"c": ("turquoise", "paleturquoise"),
	"y": ("yellow", "lightgoldenrodyellow"),
	"b": ("deepskyblue", "lightskyblue"),
	"l": ("silver", "gainsboro"),
	"d": ("grey", "lightgrey"),
	"p": ("mediumorchid", "violet"),
	"o": ("sandybrown", "navajowhite"),
	"i": ("whitesmoke", "slategray"),
}

graph_introduction = """\

Welcome to the M&T sim graphing tool!

Select the graph you want to see below.
Use the buttons at the top right to change
graph option pages.
Refresh to read game.log again.
    """

cursor_hover_handler = None


def menu(msg=None):
	global cursor_hover_handler
	cursor_hover_handler = None  # Deactivate the old handler
	ax.clear()
	ax.set_title("Menu")
	ax.text(
		0.5,
		0.5,
		horizontalalignment="center",
		verticalalignment="center",
		s=graph_introduction.strip(),
	)
	if msg:
		ax.text(0.5, 0.5, msg)
	plt.draw()


def get_data(_, i):
	"""Read data"""
	lst = []
	loc = 0

	while True:
		loc = data.find(i, loc)

		if loc != -1:
			end = data.find("\n", loc)
			lst.append(float(data[loc:end].strip().split(":")[1].strip().split("£")[-1]))
			loc = end
		else:
			break

	return np.array(lst)


def read_all_logs():
	"""Read file(s)"""
	content_list = []
	files = glob.glob("game_*.log")
	files.sort(key=lambda x: int(x[5:-4]))
	for fn in files:
		with open(fn, "r") as f:
			content_list.append(f.read())
	logs = len(files)
	try:
		with open("game.log", "r") as f:
			content_list.append(f.read())
			logs += 1
	except FileNotFoundError:
		print("WARNING: Could not find game.log")
	print(f'Read {logs} log file{"" if logs == 1 else "s"}')
	if logs <= 0:
		pass  # raise ValueError("No logs found")
	return files, "".join(content_list)


def build_layout():
	"""Positioning of buttons and the like"""
	global pages, page, H_PAD, V_PAD, V_SIZE_MIN, max_rows, max_height
	pages = []
	with open("graph_pages.csv", "r") as f:
		page = []
		for line in f:
			line = line[:-1]
			if not line:
				continue
			if line.startswith(":"):
				if page:
					pages.append(page)
					page = []
			else:
				page.append([x.rstrip() for x in line.split(";")])
		if page:
			pages.append(page)
		del page

	max_rows = max((len(page) for page in pages))
	max_height = max_rows * V_SIZE_MIN + (max_rows + 1) * V_PAD
	if max_height + 0.04 > 0.45:
		raise ValueError("Too many rows/vsizemin too large!")
	plt.subplots_adjust(left=0.05, right=0.95, bottom=max_height + 0.04, top=0.925)

	return pages, max_rows, max_height


def plot_new(_, graph, title):
	global cursor_hover_handler  # Declare that we are modifying the global variable
	ax.clear()
	try:
		graph(data, ax)
		ax.legend(loc=2, ncol=2)
		# After plotting, create and attach the hover handler
		cursor_hover_handler = CursorHoverInfo(ax)
	except Exception as e:
		ax.text(0.5, 0.5, f"Error:\n{e}", horizontalalignment="center", verticalalignment="center")
		traceback.print_exc()

	ax.set_title(title)
	plt.draw()


def load_page(i):
	global cur_page

	# Deactivate and hide the buttons/axes on the old page
	for row in pages[cur_page - 1]:
		for slot in row:
			if slot:
				btn, pos = slot  # Unpack the button and its axes
				pos.set_visible(False)
				btn.active = False  # Deactivate the button widget

	cur_page = i

	# Activate and show the buttons/axes on the new page
	for row in pages[cur_page - 1]:
		for slot in row:
			if slot:
				btn, pos = slot  # Unpack the button and its axes
				pos.set_visible(True)
				btn.active = True  # Activate the button widget

	plt.draw()


def backup_log(_):
	last_log_num = int(logs[-1][5:-4])
	try:
		os.rename("game.log", f"game_{last_log_num + 1}.log")
	except FileNotFoundError:
		pass
	menu()


def page_change(_, is_next):
	global cur_page
	if is_next:
		load_page(cur_page + 1 if cur_page < len(pages) else 1)
	else:
		load_page(cur_page - 1 if cur_page > 1 else len(pages))


def reload_log(_):
	global logs, data
	logs, data = read_all_logs()
	menu()


def plotting_evil_deeds():
	"""Plotting evil deeds"""

	global max_height, H_PAD, V_PAD, V_SIZE_MIN, max_rows, color
	done = set()
	color = None
	for pi, page in enumerate(pages):
		height_page = (max_height - V_PAD * (len(page) + 1)) / len(page)
		for ri, row in enumerate(page):
			width_row = (1 - H_PAD * (len(row) + 1)) / len(row)
			vpos = (len(page) - ri - 1) * (height_page + V_PAD) + V_PAD
			for si, slot in enumerate(row):
				if not slot:
					continue
				if slot[-2] == ":":
					color = slot[-1]
					slot = slot[:-2]
				if slot not in graphs:
					raise ValueError(
						f'Unknown entry: "{slot}"\nCould not find function "graph{slot.replace(" ", "_")}"')
				if slot in done:
					raise ValueError(f'Duplicate entry: "{slot}"\nSecond occurrence in page {pi + 1}')
				pos = plt.axes((si * width_row + H_PAD * (si + 1), vpos, width_row, height_page))
				pos.set_visible(False)
				if color:
					try:
						btn = Button(pos, slot, None, *colors[color])
					except KeyError:
						print(f"WARNING: Unknown color {color} used for {slot}")
						btn = Button(pos, slot, None, *colors["l"])
					color = None
				else:
					btn = Button(pos, slot, None, *colors["l"])
				btn.on_clicked(partial(plot_new, title=graphs[slot][0], graph=graphs[slot][1]))
				pages[pi][ri][si] = (btn, pos)  # type:ignore
				done.add(slot)
	del H_PAD, V_PAD, V_SIZE_MIN, max_rows, max_height, color

	done = set(graphs) - done
	if done:
		print('WARNING\nMissing: "', '", "'.join(done), '"', sep="")
	del done


def on_scroll(event):
	"""
	Handles mouse wheel scroll events to cycle through pages.
	"""
	# Check if the scroll event happened over the main axes (the graph area)
	# This prevents scrolling from triggering page changes when over a button or other widget
	if event.inaxes != ax:
		return

	page_change(event, event.step > 0)


if __name__ == '__main__':
	try:
		os.chdir(os.path.dirname(__file__))
		fig, ax = plt.subplots(num="MEIOU and Taxes - Sim graphs", figsize=(16, 9))

		# Connect the mouse wheel handler to the figure
		fig.canvas.mpl_connect('scroll_event', on_scroll)

		ax.show = lambda: None  # type:ignore

		menu()

		# Highly cursed
		all_graphs.get_data = get_data
		graphs = {
			getattr(all_graphs, name).__name__[5:].replace("_", " "): (getattr(all_graphs, name).__doc__,
																	   getattr(all_graphs, name))
			for name in dir(all_graphs)
			if getattr(all_graphs, name) and name.lower().startswith("graph")
		}

		logs, data = read_all_logs()
		pages, max_rows, max_height = build_layout()

		plotting_evil_deeds()

		# Other buttons
		cur_page = 1
		load_page(1)

		next_button = Button(plt.axes((0.825, 0.9375, 0.15, 0.05)), "Next", None, *reversed(colors["c"]))
		next_button.on_clicked(partial(page_change, is_next=True))

		prev_button = Button(plt.axes((0.65, 0.9375, 0.15, 0.05)), "Prev", None, *reversed(colors["c"]))
		prev_button.on_clicked(partial(page_change, is_next=False))

		reload_button = Button(plt.axes((0.025, 0.9375, 0.2, 0.05)), "Refresh data", None, *reversed(colors["g"]))
		reload_button.on_clicked(reload_log)

		backup_button = Button(plt.axes((0.25, 0.9375, 0.1, 0.05)), "Backup game.log", None, *reversed(colors["r"]))
		backup_button.on_clicked(backup_log)

		plt.show()

	except Exception as e:
		print(e)
		traceback.print_exc()
		input("\nPress enter to close...")
