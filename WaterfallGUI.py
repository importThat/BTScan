import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
from time import time
from random import sample


class WaterfallGUI:
    def __init__(self, root, x, **callbacks):
        self.start = time()
        self.root = root
        self.UPDATE = True
        self.MACS_SAMPLED = False
        self.WATERFALL_LENGTH = 100
        self.Y_AXIS = np.arange(self.WATERFALL_LENGTH)
        self.labs_set = True

        self.CMAPS = [
            'CMRmap', 'Spectral', 'hot', 'jet',
            'plasma', 'viridis', 'winter_r']

        self.CMAP = 'viridis'

        self.sample_macs(x)
        self.create_waterfall_hud(x, **callbacks)

    def sample_macs(self, x):
        N = min(50, len(x.MACID.unique()))
        # Sample N random MACIDs
        self.MACIDS = sample([i for i in x.MACID.unique()], N)

        self.waterfall_container = np.zeros((self.WATERFALL_LENGTH, len(self.MACIDS)))
        self.waterfall_container.fill(-100)
        self.waterfall_container = pd.DataFrame(self.waterfall_container)
        self.waterfall_container.columns = self.MACIDS
        self.labels = [i[0:5] for i in self.MACIDS]
        self.MACS_SAMPLED = True

    def create_waterfall_hud(self, x, **callbacks):
        # Put the plot in
        self.create_waterfall(x, new=True)

        # Dropdown Selector
        self.selected_option = ctk.StringVar(value=self.CMAP)

        self.dropdown = ctk.CTkOptionMenu(
            master=self.root,
            values=self.CMAPS,
            variable=self.selected_option,
            command=self.select_CMAP)

        self.dropdown.place(relx=0.25, rely=0.01)

        # View Selector
        self.selected_view = ctk.StringVar(value='waterfall')

        self.dropdown = ctk.CTkOptionMenu(
            master=self.root,
            values=['antenna', 'signal', 'waterfall'],
            variable=self.selected_view,
            command=callbacks['toggle_view'])
        self.dropdown.place(relx=0.01, rely=0.01)

    def select_CMAP(self, selection):
        self.CMAP = selection
        self.ax.clear()
        self.graph = self.ax.pcolormesh(self.MACIDS,
                                        self.Y_AXIS,
                                        self.waterfall_container.to_numpy(dtype='float'),
                                        vmin=-90, vmax=-20, cmap=self.CMAP)

        self.ax.set_xticklabels(self.labels, rotation=90, fontsize=12, color='white')

    def update(self, x):
        if not self.MACS_SAMPLED:
            self.sample_macs(x)

        else:
            self.create_waterfall(x, new=False)

    def create_waterfall(self, x, new=True):

        if new:
            self.fig, self.ax = plt.subplots()
            self.fig.set_size_inches(11.5, 8.5)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.ax.get_yaxis().set_visible(False)
            self.fig.subplots_adjust(left=0,right=1,bottom=0.1,top=1)
            self.ax.margins(x=0, y=0., tight=True)
            self.fig.set_facecolor("#3B3B3B")
            self.last_scan = x.Time.max() - 0.1



        # Subset the data
        data = x[x.Time >= self.last_scan]

        # Store the final scan time for the next iteration
        self.last_scan = x.Time.max()

        # Subset the data
        #if len(self.MACIDS) >= 1:
        data = data[data.MACID.isin(self.MACIDS)]

        # Collapse the data to MACID and add it in to the plot df
        grouped_df = data[["MACID", "RSSI"]].groupby(["MACID"])
        grouped_df = grouped_df.mean().T

        # Add it in
        self.waterfall_container = pd.concat([self.waterfall_container, grouped_df], ignore_index=True)

        self.waterfall_container.fillna(-100, inplace=True)

        # Drop the first row (which is the oldest reading)
        self.waterfall_container = self.waterfall_container.iloc[1:, :]

        if new:
            if len(self.MACIDS) > 0:
                self.graph = self.ax.pcolormesh(self.MACIDS,
                                    self.Y_AXIS,
                                    self.waterfall_container.to_numpy(dtype='float'),
                                    vmin=-90, vmax=-20, cmap=self.CMAP)

                self.ax.set_xticklabels(self.labels, rotation=90, fontsize=12, color='white')

            self.canvas.get_tk_widget().place(relx=0.02, rely=0.02)
            self.canvas.draw()
        else:
            self.graph.set_array(self.waterfall_container.to_numpy(dtype='float'))
            self.fig.canvas.draw_idle()


    def destroy(self):
        plt.close('all')

        for widget in self.root.winfo_children():
            widget.destroy()