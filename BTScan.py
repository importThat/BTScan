import os
import time
import pandas as pd
import customtkinter as ctk
import matplotlib.pyplot as plt
from threading import Thread
from gi.repository import GLib
from pydbus import SystemBus
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from AntennaGUI import AntennaGUI
from SignalGUI import SignalGUI
from WaterfallGUI import WaterfallGUI


class ctkApp:
    def __init__(self):
        # Constants
        global x
        self.WIDTH=1200
        self.HEIGHT=900
        self.QUIT = False

        # GUI particulars
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.geometry("1200x900+200x200")
        self.root.title("BTScan")
        self.root.update()
        self.swap_view_toggle = False

        # The display for the antenna view
        self.hud = AntennaGUI(
            self.root, x,
            quit=self.quit,
            toggle_update=self.toggle_update,
            toggle_view=self.toggle_view,
            reset=self.reset_data,
            save=self.save_data
        )

        self.current_hud = 'antenna' # 'antenna', 'signal' or 'waterfall'

    def run(self):
        # Loop
        self.update_window()
        self.root.mainloop()

    def update_window(self):
        # Update the hud, repeats every 100ms
        self.root.update()

        if self.hud.UPDATE:
            self.hud.update(x)

        if self.swap_view_toggle:
            self.swap_view()
            self.swap_view_toggle = False

        if not self.QUIT:
            if self.current_hud == 'antenna':
                self.root.after(100, self.update_window)
            elif self.current_hud == 'signal':
                self.root.after(4, self.update_window)
            elif self.current_hud == 'waterfall':
                self.root.after(4, self.update_window)
        else:
            self.root.quit()
            self.root.destroy()

    def toggle_update(self):
        if self.hud.UPDATE:
            self.hud.UPDATE = False
        else:
            self.hud.UPDATE = True

    def toggle_view(self, selection):
        self.swap_view_toggle = True
        self.current_hud = selection

    def swap_view(self):
        self.hud.destroy()

        if self.current_hud == 'antenna':
            self.hud = AntennaGUI(
                self.root, x,
                quit=self.quit,
                toggle_update=self.toggle_update,
                toggle_view=self.toggle_view,
                reset=self.reset_data
            )

        elif self.current_hud == 'signal':
            self.hud = SignalGUI(
                self.root, x,
                quit=self.quit,
                toggle_update=self.toggle_update,
                toggle_view=self.toggle_view
            )

        elif self.current_hud == 'waterfall':
            self.hud = WaterfallGUI(
                self.root, x,
                quit=self.quit,
                toggle_view=self.toggle_view
            )

    def optionmenu_callback(self, choice):
        print("optionmenu dropdown clicked:", choice)

    def quit(self):
        self.QUIT = True

    def reset_data(self):
        global x

        x = pd.DataFrame({
            "MACID": [],
            "RSSI": [],
            "Time": []
        })

    def save_data(self):
        now = time.time()
        filename = "BTScan_log_" + str(now) + ".csv"
        x.to_csv(filename, index=False)

        print(f"Data saved as {os.getcwd() + '/' + filename}")


# ****************** SCANNER *************************


SCAN_TIME = 20
DEVICE_INTERFACE = 'org.bluez.Device1'
NULL = None

remove_list = set()

x = pd.DataFrame({
    "MACID": [],
    "RSSI": [],
    "Time": []
})


def stop_scan():
    adapter.StopDiscovery()
    mainloop.quit()


def clean_device(rm_dev):
    try:
        adapter.RemoveDevice(rm_dev)
    except GLib.Error as err:
        pass


def on_iface_added(path, interfaces):
    if DEVICE_INTERFACE in interfaces:
        on_device_found(path, interfaces[DEVICE_INTERFACE])


def on_device_found(device_path, device_props):
    global x
    address = device_props.get('Address')
    rssi = device_props.get('RSSI')
    ts = time.time()

    # Stick the data in to our DF
    x = pd.concat([x,
                   pd.Series(
                       {"MACID":address, "RSSI":rssi, "Time":ts}
                   ).to_frame().T],
                  ignore_index=True)

    clean_device(device_path)

# *********************** ADAPTER SETUP **************************************

bus = SystemBus()
adapter = bus.get('org.bluez', '/org/bluez/hci0')

mngr = bus.get('org.bluez', '/')
mngr.onInterfacesAdded = on_iface_added

mainloop = GLib.MainLoop()


# Change the default scan options
adapter.SetDiscoveryFilter(
    {
        'Transport': GLib.Variant.new_string("le"),
        'DuplicateData': GLib.Variant.new_boolean(True),
        'RSSI': GLib.Variant.new_int16(-120)
    }
)

# ***************************** MAIN PROGRAM **********************************

if __name__ == "__main__":
    adapter.StartDiscovery()
    time.sleep(0.5)
    CTK_Window = ctkApp()

    data = Thread(target=mainloop.run, daemon=True)

    data.start()
    CTK_Window.run()
    plt.close()
    GLib.timeout_add_seconds(0.1, stop_scan)
    data.join()



