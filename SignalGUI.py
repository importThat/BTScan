import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import numpy as np


class SignalGUI:
    def __init__(self, root, x, **callbacks):
        self.root = root
        self.UPDATE = True
        self.COLOURS = ["#e50494", "#f77aff", "#7789e1", "#007bc9", "#9dead0",
                        "#7de1ac", "#03b751", "#e9f947", "#cdc90f", "#c5a709"]
        self.update_counter = 1
        self.max_graph_time = 120

        # Get the strongest signal to start with for our plotting
        strongest_sig = x.groupby('MACID').mean().sort_values(by="RSSI", ascending=False)
        strongest_sig = strongest_sig.index[0]
        self.MACID = strongest_sig
        self.create_signal_hud(x, **callbacks)

    def create_signal_hud(self, x, **callbacks):
        # Put the plot in
        self.create_line(x, new=True)

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
        self.selected_view = ctk.StringVar(value='signal')

        self.view_dropdown = ctk.CTkOptionMenu(
            master=self.root,
            values=['antenna', 'signal', 'waterfall'],
            variable=self.selected_view,
            command=callbacks['toggle_view'])
        self.view_dropdown.place(relx=0.02, rely=0.1)

        # Quit Button
        quit_button = ctk.CTkButton(
            master=self.root,
            width=150,
            height=50,
            text="Quit",
            command=callbacks['quit'])

        quit_button.place(relx=0.02, rely=0.18)

        # Dropdown Selector
        self.selected_option = ctk.StringVar(value=self.MACID)

        self.dropdown = ctk.CTkOptionMenu(
            master=self.root,
            values=[],
            variable=self.selected_option,
            command=self.select_MACID)
        self.dropdown.place(relx=0.025, rely=0.3)

        # Total Signal count textbox
        self.device_name = ctk.CTkLabel(
            master=self.root,
            text=f"Device\n{self.MACID}",
            width=200,
            height=100,
            font=("Roboto",18)
        )
        self.device_name.place(relx=0.2, rely=0.02)

        # Active Signal count textbox
        self.device_signal_count = ctk.CTkLabel(
            master=self.root,
            text=f"Device Signal Count\n{x[x.MACID==self.MACID].shape[0]}",
            width=200,
            height=100,
            font=("Roboto",18)
        )
        self.device_signal_count.place(relx=0.2, rely=0.1)

        # Average Signal Strength
        self.av_rssi = ctk.CTkLabel(
            master=self.root,
            text=f"Av. Device RSSI\n{round(x[x.MACID==self.MACID].RSSI.mean(), 1)}",
            width=200,
            height=100,
            font=("Roboto",18))
        self.av_rssi.place(relx=0.2, rely=0.18)

        # Average Signal Strength
        self.av_signals = ctk.CTkLabel(
            master=self.root,
            text=f"Av. Signals per Second\n{round(x[(x.Time - time.time()) < 5].shape[0], 1)}",
            width=200,
            height=100,
            font=("Roboto",18))
        self.av_signals.place(relx=0.19, rely=0.26)

    def update(self, x):
        cutoff = 25

        self.device_signal_count.configure(text=f"Device Signal Count\n{x[x.MACID==self.MACID].shape[0]}")

        av_rssi = round(x[x.MACID==self.MACID].RSSI[(time.time() - x.Time) < cutoff].mean(), 1)
        av_sig = round(x[x.MACID==self.MACID][(time.time() - x.Time) < cutoff].shape[0] / cutoff, 1)
        self.av_rssi.configure(text=f"Av. Device RSSI\n{av_rssi}")
        self.av_signals.configure(text=f"Av. Signals per Second\n{av_sig}")

        # Do this every 10 cycles
        if (self.update_counter % 10) == 0:
            now = time.time()

            counts = x[(now - x.Time) < cutoff]
            counts = counts.groupby('MACID').count()
            counts.RSSI = counts.RSSI / cutoff
            counts = counts.sort_values(by="RSSI", ascending=False)
            counts = counts.iloc[0:30, :]

            self.dropdown.configure(values=counts.index.tolist())

        self.create_line(x, new=False)

        self.update_counter += 1

    def select_MACID(self, selection):
        self.MACID = selection
        self.device_name.configure(text=f"Device\n{self.MACID}")

    def create_line(self, x, new=True):
        now = time.time()

        m1 = x.MACID == self.MACID
        m2 = now - x.Time <= self.max_graph_time
        m3 = m1 & m2

        if new:
            # Create the graph and set the parameters
            self.figl, self.axl = plt.subplots()
            self.figl.set_size_inches(11.5, 5)
            self.canvasl = FigureCanvasTkAgg(self.figl, master=self.root)

            self.axl.set_title("RSSI Over Time")
            self.axl.set_xlabel("Time")
            self.axl.set_ylabel("RSSI")

            self.graph, = self.axl.plot((np.array(x.Time[m3] - now)), np.array(x.RSSI[m3]))

            # Draw and place the graph
            self.canvasl.get_tk_widget().place(relx=0.02, rely=0.4)
            self.canvasl.draw()

        else:
            # Update the graph
            self.graph.set_ydata(x.RSSI[m3])
            self.graph.set_xdata(x.Time[m3])
            self.axl.relim()
            self.axl.autoscale_view()

            self.figl.canvas.draw_idle()


    def destroy(self):
        plt.close('all')

        for widget in self.root.winfo_children():
            widget.destroy()
