import os
import shutil
import psutil
import time
from datetime import datetime
import threading
import tkinter as tk
from tkinter import messagebox

# -----------------------------
# Constants
# -----------------------------
REPORT_FILE = "testo 184 measurement report.pdf"
CONFIG_FILE = "testo-184-T3-configuration_data.xml"

# Folder containing pre-generated XML templates
CONFIG_TEMPLATE_FOLDER = "config_templates"

# Folder where reports will be archived
ARCHIVE_FOLDER = "reports_archive"

# Background scan interval (seconds)
SCAN_INTERVAL = 5

# -----------------------------
# Ensure folders exist
# -----------------------------
os.makedirs(CONFIG_TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

# Pick one XML template (you can have multiple for different presets)
TEMPLATE_XML = os.path.join(CONFIG_TEMPLATE_FOLDER, CONFIG_FILE)

if not os.path.exists(TEMPLATE_XML):
    print(f"Error: Please place a valid pre-generated XML in {TEMPLATE_XML}")
    exit(1)

# -----------------------------
# Detect logger USB
# -----------------------------
def find_testo_device():
    for p in psutil.disk_partitions():
        if os.path.exists(os.path.join(p.mountpoint, REPORT_FILE)):
            return p.mountpoint
    return None

# -----------------------------
# Archive report with timestamp
# -----------------------------
def archive_report(device):
    src = os.path.join(device, REPORT_FILE)
    if os.path.exists(src):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst_name = f"{timestamp}_Testo184_Report.pdf"
        dst = os.path.join(ARCHIVE_FOLDER, dst_name)
        shutil.copy(src, dst)
        print(f"[INFO] Report archived: {dst}")

# -----------------------------
# Copy XML config to logger
# -----------------------------
def copy_config_to_logger(device):
    dst = os.path.join(device, CONFIG_FILE)
    shutil.copy(TEMPLATE_XML, dst)
    print(f"[INFO] Configuration copied to logger: {dst}")

# -----------------------------
# Background scanner
# -----------------------------
device_connected = False

def background_scan():
    global device_connected
    while True:
        device = find_testo_device()
        if device and not device_connected:
            print(f"[INFO] Logger detected at {device}")
            device_connected = True

            # Archive report
            archive_report(device)

            # Copy XML config
            copy_config_to_logger(device)

            # Prompt user to remove USB
            messagebox.showinfo(
                "Configuration Applied",
                "Logger configured and report archived.\nPlease safely remove/unplug the USB device."
            )

        elif not device:
            device_connected = False
        time.sleep(SCAN_INTERVAL)

# -----------------------------
# Simple GUI for status
# -----------------------------
root = tk.Tk()
root.title("Testo 184 T3 Auto Manager")
root.geometry("500x220")

status_var = tk.StringVar()
status_var.set("Waiting for logger...")

def update_status():
    device = find_testo_device()
    if device:
        status_var.set(f"Logger detected: {device}")
    else:
        status_var.set("Waiting for logger...")
    root.after(2000, update_status)

tk.Label(root, textvariable=status_var, font=("Arial", 14)).pack(pady=20)
tk.Label(root, text="Reports archived in 'reports_archive'", font=("Arial", 10)).pack()
tk.Label(root, text="Configuration copied automatically", font=("Arial", 10)).pack()
tk.Label(root, text="You will be prompted to remove USB after configuration", font=("Arial", 10)).pack(pady=10)

# -----------------------------
# Start background scanner in thread
# -----------------------------
threading.Thread(target=background_scan, daemon=True).start()
update_status()

root.mainloop()
