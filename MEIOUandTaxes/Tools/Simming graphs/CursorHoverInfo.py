import numpy as np


class CursorHoverInfo:
	"""
	Creates a hover annotation for a Matplotlib axes that shows the
	Y-values of all lines at the current X-position of the cursor.
	"""

	def __init__(self, ax):
		self.ax = ax
		self.fig = ax.figure
		self.lines = [line for line in ax.get_lines() if not line.get_label().startswith('_')]

		self.last_integer_x = None
		self.closest_line = None

		# Create an annotation object, initially invisible
		self.annot = self.ax.annotate(
			"",
			xy=(0, 0),
			xytext=(15, 15),
			textcoords="offset points",
			bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.75),
			arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
			fontfamily='monospace',
		)
		self.annot.set_visible(False)

		# Connect the event handlers
		self.fig.canvas.mpl_connect("motion_notify_event", self.on_hover)
		self.fig.canvas.mpl_connect("axes_leave_event", self.on_leave)

	def on_hover(self, event):
		# Exit if the cursor is not in our axes or has no valid x-data
		if event.inaxes != self.ax or event.xdata is None:
			return

		# Get the current integer X position (the "year")
		current_integer_x = int(event.xdata)

		# --- The rest of the logic now uses `current_integer_x` instead of `event.xdata` ---
		line_data = []
		min_vertical_dist = float('inf')
		closest_line_label = None
		closest_point_on_line = None

		# Find the closest point on each line
		for line in self.lines:
			x_data, y_data = line.get_data()

			# Find the index for the current integer year
			idx = np.searchsorted(x_data, current_integer_x)

			# Guard against the index being out of bounds
			if idx >= len(x_data) or x_data[idx] != current_integer_x:
				continue # This year doesn't exist in this line's data

			point_x, point_y = x_data[idx], y_data[idx]

			# Calculate the vertical distance in screen pixels to find the closest line
			vertical_dist_pixels = abs(self.ax.transData.transform((point_x, point_y))[1] - event.y)

			# Check if this line is the new closest
			if vertical_dist_pixels < min_vertical_dist:
				min_vertical_dist = vertical_dist_pixels
				closest_line_label = line.get_label()
				closest_point_on_line = (point_x, point_y)

			line_data.append({'label': line.get_label(), 'y_val': point_y})

		if current_integer_x == self.last_integer_x and self.closest_line == closest_line_label:
			return
		self.last_integer_x = current_integer_x
		self.closest_line = closest_line_label

		# --- CORE CHANGE: LOOKUP PRE-CALCULATED DATA ---
		sorted_data = self.tooltip_cache.get(current_integer_x)
		if not sorted_data:
			if self.annot.get_visible(): self.annot.set_visible(False); self.fig.canvas.draw_idle()
			return

		if not closest_point_on_line:
			if self.annot.get_visible(): self.annot.set_visible(False); self.fig.canvas.draw_idle()
			return

		# --- TABLE FORMATTING LOGIC ---
		# Sort data by Y-value before formatting
		line_data.sort(key=lambda item: item['y_val'], reverse=True)

		# Calculate the required width for each column to align them
		max_label_len = max(len(d['label']) for d in line_data) if line_data else 0
		max_val_len = max(len(f"{d['y_val']:,.2f}") for d in line_data) if line_data else 0

		# Display the integer year in the tooltip
		info_texts = [f"{'Year':>{max_val_len}} : {current_integer_x:>3} ({current_integer_x + 1357})"]
		info_texts.append('')
		for item in sorted_data:
			label_str = f"{item['label']:<{max_label_len}}"
			val_str = f"{item['y_val']:>{max_val_len},.2f}"

			char_reveal = '*' if item['label'] == closest_line_label else ' '
			info_texts.append(f"{val_str} : {char_reveal}{label_str}")

		# --- DYNAMIC POSITIONING LOGIC ---
		y_min, y_max = self.ax.get_ylim()
		y_mid = (y_min + y_max) / 2

		# If cursor is in the top half, move the annotation below it
		if event.ydata > y_mid:
			# The y-offset is negative, and we make it larger for more lines of text
			y_offset = -15 - (12 * len(line_data))
			self.annot.xytext = (15, -200)
		else:
			# Default position: above and to the right
			self.annot.xytext = (15, 15)

		# --- UPDATE ANNOTATION ---
		self.annot.set_visible(True)
		self.annot.set_text("\n".join(info_texts))
		self.annot.xy = closest_point_on_line

		# Redraw the canvas
		self.fig.canvas.draw_idle()

	def on_leave(self, event):
		# Hide the annotation when the mouse leaves the axes
		if self.annot.get_visible():
			self.annot.set_visible(False)
			self.fig.canvas.draw_idle()
