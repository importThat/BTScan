import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import numpy as np

# Waterfall Plot of signal strengths vs MACIDs


class AntennaGUI:
    def __init__(self, root, x, **callbacks):
        print(x)
        self.root = root
        self.UPDATE = True
        self.COLOURS = ["#e50494", "#f77aff", "#7789e1", "#007bc9", "#9dead0",
                        "#7de1ac", "#03b751", "#e9f947", "#cdc90f", "#c5a709"]
        self.create_antenna_hud(x, **callbacks)
        self.update_counter = 1

    def create_antenna_hud(self, x, **callbacks):
        # Put the plot in
        self.create_av_bar(x, new=True)
        self.create_hist(x)
        self.create_update_bar(x)

        # Add buttons
        # Scan on/off button
        scan_button = ctk.CTkButton(
            master=self.root,
            width=150,
            height=50,
            text="Scan On/Off",
            command=callbacks['toggle_update'])

        scan_button.place(relx=0.020, rely=0.02)

        # View Selector
        self.selected_view = ctk.StringVar(value='antenna')

        self.dropdown = ctk.CTkOptionMenu(
            master=self.root,
            values=['antenna', 'signal', 'waterfall'],
            variable=self.selected_view,
            command=callbacks['toggle_view'])
        self.dropdown.place(relx=0.02, rely=0.1)

        # Quit Button
        quit_button = ctk.CTkButton(
            master=self.root,
            width=150,
            height=50,
            text="Quit",
            command=callbacks['quit'])

        quit_button.place(relx=0.02, rely=0.18)

        # Save data button
        reset_button = ctk.CTkButton(
            master=self.root,
            width=150,
            height=50,
            text="Save Data",
            command=callbacks['save'])

        reset_button.place(relx=0.02, rely=0.25)


        # Data Reset Button
        reset_button = ctk.CTkButton(
            master=self.root,
            width=150,
            height=50,
            text="Reset Data",
            command=callbacks['reset'])

        reset_button.place(relx=0.02, rely=0.32)

        # D

        # Total Signal count textbox
        self.total_device_count = ctk.CTkLabel(
            master=self.root,
            text=f"Total Device Count\n{len(x.MACID.unique())}",
            width=200,
            height=100,
            font=("Roboto",18)
        )
        self.total_device_count.place(relx=0.2, rely=0.02)

        # Active Signal count textbox
        self.total_signal_count = ctk.CTkLabel(
            master=self.root,
            text=f"Total Signal Count\n{x.shape[0]}",
            width=200,
            height=100,
            font=("Roboto",18)
        )
        self.total_signal_count.place(relx=0.2, rely=0.1)

        # Average Signal Strength
        self.av_rssi = ctk.CTkLabel(
            master=self.root,
            text=f"Av. RSSI\n{round(x.RSSI.mean(), 1)}",
            width=200,
            height=100,
            font=("Roboto",18))
        self.av_rssi.place(relx=0.2, rely=0.18)

        # Average Signals per second
        self.av_signals = ctk.CTkLabel(
            master=self.root,
            text=f"Av. Signals per Second\n{round(x[(x.Time - time.time()) < 5].shape[0], 1)}",
            width=200,
            height=100,
            font=("Roboto",18))
        self.av_signals.place(relx=0.19, rely=0.26)

    def update(self, x):
        self.total_device_count.configure(text=f"Total Device Count\n{len(x.MACID.unique())}")
        self.total_signal_count.configure(text=f"Total Signal Count\n{x.shape[0]}")

        cutoff = 5

        av_rssi = round(x.RSSI[(time.time() - x.Time) < cutoff].mean(), 1)
        av_sig = round(x[(time.time() - x.Time) < cutoff].shape[0] / cutoff, 1)
        self.av_rssi.configure(text=f"Average RSSI\n{av_rssi}")
        self.av_signals.configure(text=f"Average Signals per Second\n{av_sig}")

        self.create_update_bar(x, new=False)

        if self.update_counter % 5 == 0:
            self.create_hist(x, new=False)
            self.create_av_bar(x, new=False)

        self.update_counter += 1

    def create_av_bar(self, x, new=True):
        '''
        Creates or updates a bar graph of average RSSI values
        '''
        if not new:
            self.ax.clear()

        now = time.time()
        cutoff=10
        mask = (now - x.Time) <= cutoff

        avs = x[mask].groupby('MACID').mean().sort_values(by="RSSI", ascending=True)
        avs.index = [i[0:5] for i in avs.index]
        avs = avs.iloc[avs.shape[0]-25:, ]

        if new:
            self.fig, self.ax = plt.subplots()
            self.fig.set_size_inches(5.75, 4.5)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        self.ax.hlines(y=avs.index, xmin=-100, xmax=avs['RSSI'], color='skyblue')
        self.ax.plot(np.array(avs['RSSI']), np.array(avs.index), "o")

        self.ax.set_title(f'Average RSSI (t={cutoff})')
        self.ax.set_xlabel("Av. RSSI")

        self.canvas.draw()

        if new:
            self.canvas.get_tk_widget().place(relx=0.02, rely=0.48)

    def create_update_bar(self, x, new=True):
        '''
        Creates or updates a bar graph of average signals received per second over the last 5 seconds
        '''
        plt.close()
        now = time.time()
        cutoff=10
        mask = (now - x.Time) <= cutoff
        counts = x[mask]
        counts = counts.groupby('MACID').count()

        counts.RSSI = counts.RSSI/cutoff

        counts = counts.sort_values(by="RSSI", ascending=False)
        counts = counts.iloc[0:8, :]
        counts.index = [i[0:5] for i in counts.index]

        if new:
            self.figup, self.axup = plt.subplots()
            plt.subplots_adjust(bottom=0.15)
            self.figup.set_size_inches(5.75, 4.5)
            self.canvasup = FigureCanvasTkAgg(self.figup, master=self.root)

        self.axup.bar(counts.index, height=counts.RSSI, label=counts.index, color=self.COLOURS)
        self.axup.set_title(f'Av. Signals per Second (t={cutoff})')
        self.axup.set_xticklabels(counts.index, rotation=90, fontsize=10)

        self.canvasup.draw()

        if new:
            self.canvasup.get_tk_widget().place(relx=0.5, rely=0.48)
        else:
            self.axup.clear()

    def create_hist(self, x, new=True):
        now = time.time()
        cutoff = 10
        mask = (now - x.Time) <= cutoff

        counts = x[mask]
        counts = counts.groupby('MACID').count().sort_values(by='MACID')
        counts.RSSI = counts.RSSI/cutoff

        avs = x[mask].groupby('MACID').mean().sort_values(by='MACID')

        if new:
            self.figh, self.axh = plt.subplots()
            self.figh.set_size_inches(6.95, 4)
            self.canvash = FigureCanvasTkAgg(self.figh, master=self.root)

            self.graph = self.axh.scatter(avs.RSSI, counts.RSSI, 140, color="#7789e1", alpha=0.4)
            self.axh.set_xlim(-80, -30)
            self.axh.set_ylim(0, 16)
            self.axh.set_title(f"Av. RSSI vs Av. Signals Received (t={cutoff})")
            self.axh.set_xlabel("Av. RSSI")
            self.axh.set_ylabel("Av. Signals Received")
            self.canvash.draw()
            self.canvash.get_tk_widget().place(relx=0.4, rely=0.025)

        else:
            self.graph.set_offsets(
                np.array([i for i in zip(avs.RSSI, counts.RSSI)])
            )

            self.figh.canvas.draw_idle()


    def destroy(self):
        plt.close('all')

        for widget in self.root.winfo_children():
            widget.destroy()
