import os
import sys
import subprocess
import importlib
import time
import shutil
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog

# -------------------------------
# auto install package
# -------------------------------
required = ["psutil"]

for p in required:
    try:
        importlib.import_module(p)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", p])

import psutil

# -------------------------------
# constants
# -------------------------------
REPORT_FILE = "testo 184 measurement report.pdf"
CONFIG_FILE = "testo-184-T3-configuration_data.xml"
WHOAMI_FILE = "whoami.txt"

ARCHIVE_FOLDER = "reports_archive"
CONFIG_FOLDER = "config_templates"

SCAN_INTERVAL = 3

os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

CONFIG_TEMPLATE = os.path.join(CONFIG_FOLDER, CONFIG_FILE)

# -------------------------------
# device detection
# -------------------------------
def find_testo_device():

    for p in psutil.disk_partitions():

        try:
            if os.path.exists(os.path.join(p.mountpoint, REPORT_FILE)):
                return p.mountpoint
        except:
            pass

    return None


# -------------------------------
# read whoami
# -------------------------------
def read_whoami(device):

    path = os.path.join(device, WHOAMI_FILE)

    if not os.path.exists(path):
        return None, None

    device_id = "Unknown"
    location = "Unknown"

    with open(path) as f:

        for line in f:

            line = line.strip()

            if line.lower().startswith("device"):
                device_id = line.split(":")[1].strip()

            elif line.lower().startswith("location"):
                location = line.split(":")[1].strip()

    return device_id, location


# -------------------------------
# archive report
# -------------------------------
def archive_report(device, device_id, location):

    src = os.path.join(device, REPORT_FILE)

    if not os.path.exists(src):
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    name = f"{timestamp}_{device_id}_{location}_Testo184_Report.pdf"

    dst = os.path.join(ARCHIVE_FOLDER, name)

    shutil.copy(src, dst)

    print("Archived:", dst)


# -------------------------------
# copy config
# -------------------------------
def copy_config(device):

    dst = os.path.join(device, CONFIG_FILE)

    shutil.copy(CONFIG_TEMPLATE, dst)

    print("Configuration copied")


# -------------------------------
# GUI app
# -------------------------------
class App:

    def __init__(self, root):

        self.root = root
        self.device_connected = False
        self.current_device = None

        root.title("Testo 184 Auto Manager")
        root.geometry("520x250")

        self.status = tk.StringVar()
        self.status.set("Waiting for logger...")

        tk.Label(root,
                 text="Testo 184 Logger Manager",
                 font=("Arial",16)).pack(pady=10)

        tk.Label(root,
                 textvariable=self.status,
                 font=("Arial",12)).pack(pady=10)

        tk.Label(root,
                 text="Reports archived automatically").pack()

        tk.Label(root,
                 text="Configuration applied automatically").pack()

        tk.Label(root,
                 text="whoami.txt created if missing").pack()

        threading.Thread(target=self.monitor, daemon=True).start()

        self.update_status()


    # -----------------------
    # background monitor
    # -----------------------
    def monitor(self):

        while True:

            device = find_testo_device()

            if device and not self.device_connected:

                self.device_connected = True
                self.current_device = device

                self.root.after(0, self.handle_device)

            elif not device:

                self.device_connected = False

            time.sleep(SCAN_INTERVAL)


    # -----------------------
    # handle device in GUI
    # -----------------------
    def handle_device(self):

        device = self.current_device

        device_id, location = read_whoami(device)

        if device_id is None:

            messagebox.showinfo(
                "Device Setup",
                "whoami.txt not found.\nPlease enter device information."
            )

            device_id = simpledialog.askstring(
                "Device ID",
                "Enter Device ID: (e.g. Freezer1, Fridge2, etc.)"
            )

            location = simpledialog.askstring(
                "Location",
                "Enter Location: (e.g. Acid, Caustic, Solvent etc.)"
            )

            if not device_id:
                device_id = "Unknown"

            if not location:
                location = "Unknown"

            path = os.path.join(device, WHOAMI_FILE)

            with open(path, "w") as f:

                f.write(f"Device: {device_id}\n")
                f.write(f"Location: {location}\n")

        archive_report(device, device_id, location)

        copy_config(device)

        messagebox.showinfo(
            "Complete",
            "Report archived and configuration applied.\n\nPlease unplug the USB logger."
        )


    # -----------------------
    # status display
    # -----------------------
    def update_status(self):

        device = find_testo_device()

        if device:
            self.status.set(f"Logger detected: {device}")
        else:
            self.status.set("Waiting for logger...")

        self.root.after(2000, self.update_status)


# -------------------------------
# start program
# -------------------------------
root = tk.Tk()

app = App(root)

root.mainloop()
