#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import tkinter as tk #tkinter packages
#from tkinter import ttk
from tkinter import *
import pyvisa  # for powermeter
from ThorlabsPM100 import ThorlabsPM100
import serial #serial packages
import serial.tools.list_ports
import time
import threading #threading
import cv2 #for video
import json
import math
from PIL import Image, ImageTk
import matplotlib #for graph
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
import random
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)
matplotlib.use('Agg')
#
class Database:
    def __init__(self, filename):
        self.filename = filename
        self.data = self.load_data()
        self.last_used_profile = None  # Initialize last_used_profile as None

        # Check if a last used profile exists in the loaded data
        if "last_used_profile" in self.data:
            self.last_used_profile = self.data["last_used_profile"]

    def load_data(self):
        try:
            with open(self.filename, 'r') as file:
                data = json.load(file)
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            # Handle the case when the file doesn't exist or is empty
            return {"profiles": []}

    def find_profile_by_name(self, profile_name):
        for profile in self.data["profiles"]:
            if profile.get("name") == profile_name:
                return profile
        return None  # Return None if the profile is not found

    def add_profile(self, profile):
        self.data["profiles"].append(profile)
        self.save_data()

    def delete_profile(self, profile_name):
        # Find the profile with the given name
        profile_to_delete = None
        for profile in self.data["profiles"]:
            if profile.get("name") == profile_name:
                profile_to_delete = profile
                break

        if profile_to_delete:
            # Remove the profile from the list
            self.data["profiles"].remove(profile_to_delete)

            # Save the updated data
            self.save_data()
            return True  # Deletion successful
        else:
            return False  # Profile not found or deletion failed


    def save_data(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)
            print("saved")

    def get_all_profiles(self):
        return self.data["profiles"]

    def get_last_used_profile(self):
        return self.last_used_profile

    def set_last_used_profile(self, profile_name):
        self.last_used_profile = profile_name

        # Store the last used profile in the data dictionary
        self.data["last_used_profile"] = profile_name
        self.save_data()

class CameraControl:
    def __init__(self):
        # Initialize camera here, if applicable
        self.init_camera()

    def init_camera(self):
        """Initialize the camera and set the global flag for camera connection."""
        self.camera_connected = False
        self.cap = cv2.VideoCapture(1)  # attempt to capture video from the digital microscope

        if self.cap.isOpened():  # check if we successfully opened the camera
            self.camera_connected = True
        else:
            print("No camera found or unable to connect to camera!")

    def get_frame(self):
        """Capture and return a frame from the camera (if connected) or a white image if no camera is connected."""
        if self.camera_connected:
            _, frame = self.cap.read()
            frame = cv2.flip(frame, 0)
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

class PowerMeterControl:

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.dev_name = 'USB0::0x1313::0x8078::P0032080::INSTR'
        self.power_meter = None
        self.connection_status = self.connect()
        self.time_data = []
        self.power_data = []

    def is_connected(self):
        res_avail = self.rm.list_resources()
        return self.dev_name in res_avail

    def connect(self):
        if self.is_connected():
            inst = self.rm.open_resource(self.dev_name)
            self.power_meter = ThorlabsPM100(inst=inst)
            init = self.power_meter.read
            print('initial value:', float(init))
            return True
        else:
            print("Power Meter not connected")
            return False

    def read_power(self):
        if self.power_meter and self.connection_status:
            return self.power_meter.read
        else:
            return None

    def save_power_meter_data(self):
        # Assuming x_vals and y_vals are defined elsewhere to create mw_time
        mw_time = np.array([self.time_data, self.power_data])

        # Check if mw_time is not empty
        if mw_time.size > 0:
            # Get the current date and time
            current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Construct the file name with the current date and time
            file_name = f"mW_f(t)_powermeter_electrode_1_{current_datetime}.npy"

            # Specify the directory path
            directory_path = r'C:\Users\brend\OneDrive - University of Calgary\Phys598\Fiber Data\Numpy Data'

            # Combine the directory path and file name to create the full file path
            file_path = directory_path + "\\" + file_name

            np.save(file_path, mw_time)
            print('Data saved.')
        else:
            print('mw_time is empty. Data not saved.')

    def clear_power_meter_data(self):
        self.time_data = []
        self.power_data = []

    def get_connection_status(self):
        return self.connection_status

class ArduinoControl:
    def __init__(self):
        self.arduino = None
        self.electrode_state = False  # Initialize the electrode state
        self.connection_status = "Not Connected"  # Initialize status as "Not Connected"
        self.auto_connect()

        #The following code can help trouble shoot arduino issues
        #self.data_thread = threading.Thread(target=self.read_data_from_arduino)
        #self.data_thread.daemon = True  # Set as daemon so it exits when the main program exits
        #self.data_thread.start()

    def toggle_electrodes_state(self):  # This function turns electrodes on and off
        if self.electrode_state:
            self.electrode_state = False
            self.send_command('RLY_OF\n')
        else:
            self.electrode_state = True
            self.send_command('RLY_ON\n')

        print(self.electrode_state)

    def emergency_stop(self):       # This function is the emergency stop button
        self.send_command('EMG_STP\n')
        self.send_command('RLY_OF\n')
        print("Emergency Stop Activated")

    def auto_connect(self):
        # Iterate through all available ports and try connecting
        for port in serial.tools.list_ports.comports():
            try:
                self.arduino = serial.Serial(port.device, 9600)
                self.connection_status = f"Connected to {port.device}"
                return  # If connection is successful, exit the function
            except:
                continue
        self.connection_status = "Auto-connect failed."

    def send_command(self, command):
        if self.arduino:
            self.arduino.write(command.encode())
            time.sleep(0.05)

    def read_from_arduino(self):
        if self.arduino:
            return self.arduino.readline().decode().strip()

    def read_data_from_arduino(self):
        while True:
            if self.arduino:
                try:
                    data = self.arduino.readline().decode().strip()
                    print(f"Arduino Data: {data}")
                except Exception as e:
                    print(f"Error reading from Arduino: {e}")
            time.sleep(0.1)  # Adjust the sleep interval as needed

    def fiber_broken(self):
        time.sleep(0.1)
        self.send_command('BROKEN\n')
        print("Fiber Broken")

    def get_connection_status(self):
        if self.connection_status.startswith("Connected"):
            return True
        else:
            return False

    def send_bezier_profile(self, bezier_profile):
        for profile_type, points in bezier_profile.items():
            for point in points:
                command = f"{profile_type}:{point[0]},{point[1]}\n"
                self.send_command(command)
                # Wait for an ack if implementing handshaking
        self.send_command("END\n")  # Signal the end of transmission


    def assign_parameters(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry,
                        enab_selection, Res1_selection, Res2_selection, prht_entry, waist_time,  dimple_speed, dimple_depth,
                        dimple_heat_time, tension_1, tension_2):
        print("Write Parameters to Arduino")
        Speed1 = 'SETSP_1' + str(Speed1_entry) + '\n'
        Speed2 = 'SETSP_2' + str(Speed2_entry) + '\n'
        Accel1 = 'SETAC_1' + str(Accel1_entry) + '\n'
        Accel2 = 'SETAC_2' + str(Accel2_entry) + '\n'
        # Calculate accel duration and taper steps (linear symmetrical acceleration profile)
        acc_duration = 'ACCDUR' + str(int(int(Speed2_entry)/int(Accel2_entry)*1000)) + '\n'
        taper_steps = 'TAPSTP' + str(int(2*int(Speed2_entry)**2/int(Accel2_entry))) + '\n'
        print(taper_steps)

        enab_val = str(enab_selection)
        enab1 = ''
        enab2=''
        if enab_val == "Yes":
            enab1 = 'ENABL_1\n'
            enab2 = 'ENABL_2\n'
        elif enab_val == "No":
            enab1 = 'DISAB_1\n'
            enab2 = 'DISAB_2\n'

        Res1_val = str(Res1_selection)
        Res2_val = str(Res2_selection)

        Res1 = ''
        Res2 = ''
        if Res1_val == "High Resolution":
            Res1 = 'RESHI_1\n'
        elif Res1_val == "Mid Resolution":
            Res1 = 'RESHA_1\n'
        elif Res1_val == "Low Resolution":
            Res1 = 'RESLO_1\n'

        if Res2_val == "High Resolution":
            Res2 = 'RESHI_2\n'
        elif Res2_val == "Mid Resolution":
            Res2 = 'RESHA_2\n'
        elif Res2_val == "Low Resolution":
            Res2 = 'RESLO_2\n'

        prht = 'prht' + str(prht_entry) + '\n'

        waist_time = "WAIST_T" + str(waist_time) + '\n'

        tension_2 = 'TEN2' + str(tension_2) + '\n'
        tension_1 = 'TEN1' + str(tension_1) + '\n'
        depth_val = 'DEPTH' + str(dimple_depth) + '\n'
        Speed3 = 'SETSP_3' + str(dimple_speed) + '\n'
        TimeD_s = 'TIME' + str(dimple_heat_time) + '\n'
        # Use your ArduinoControl object to send commands
        self.send_command(Speed1)
        time.sleep(0.1)
        self.send_command(Speed2)
        time.sleep(0.1)
        self.send_command(Accel1)
        time.sleep(0.1)
        self.send_command(Accel2)
        time.sleep(0.1)
        self.send_command(acc_duration)
        time.sleep(0.1)
        self.send_command(taper_steps)
        time.sleep(0.1)
        self.send_command(Res1)
        time.sleep(0.1)
        self.send_command(Res2)
        time.sleep(0.1)
        self.send_command(enab1)
        time.sleep(0.1)
        self.send_command(enab2)
        time.sleep(0.1)
        self.send_command(prht)
        time.sleep(0.1)
        self.send_command(waist_time)
        time.sleep(0.1)
        self.send_command(tension_2)
        time.sleep(0.1)
        self.send_command(tension_1)
        time.sleep(0.1)
        self.send_command(Speed3)  # Removed encode() here
        time.sleep(0.1)
        self.send_command('RESHI_1\n')
        time.sleep(0.1)
        self.send_command('RESHI_2\n')
        time.sleep(0.1)
        self.send_command('RESHI_3\n')
        time.sleep(0.1)
        self.send_command(TimeD_s)  # Removed encode() here
        time.sleep(0.1)
        self.send_command(depth_val)

class MotorControl:
    def __init__(self, arduino_control, power_meter_control):
        self.arduino_control = arduino_control
        self.power_meter = power_meter_control
        self.knife_position = True          # True if knife is up

    def reset(self):
        time.sleep(0.1)
        self.arduino_control.send_command('HOME\n')
        print("Resetting")

    def calibrate_knife(self):
        if self.knife_position: # check if knife is down
            time.sleep(0.1)
            self.arduino_control.send_command('KNIFD\n')
            self.knife_position = False
            print("Knife Down")

        else:
            time.sleep(0.1)
            self.arduino_control.send_command('KNIFU\n')
            self.knife_position = True
            print("Knife Up")

    def calibrate_down_knife(self):
        if not self.knife_position: # check if knife is down
            time.sleep(0.1)
            self.arduino_control.send_command('KNDTH\n') # Knife Down Thousand Steps
            self.knife_position = False
            print("Knife Down 500")

    def calibrate_up_knife(self):
        if not self.knife_position: # check if knife is down
            time.sleep(0.1)
            self.arduino_control.send_command('KFUTH\n') # Knife Up Thousand Steps
            self.knife_position = False
            print("Knife Up 500")

    def move_to_home_position(self):
        time.sleep(0.1)
        self.arduino_control.send_command('EXIT\n')
        print("Returning to Home Position")

    def center_taper(self):
        time.sleep(0.1)
        # Logic for centering the taper between electrodes
        # Example: Send a command to the Arduino to center the taper
        self.arduino_control.send_command('CENTR\n')
        print('centering')
        while True:
            status = self.arduino_control.read_from_arduino()
            print(status)
            if status == "Centered":
                break
            time.sleep(1)
        print("woot woot")

    def dimple(self):
        # Implement the logic to dimple the taper using motor controls
        # You can use the 'speed', 'depth', and 'time_delay' parameters here

        self.power_meter.clear_power_meter_data()
        time.sleep(0.1)
        self.arduino_control.send_command("DIMPLE\n")  # Removed encode() here
        print("Dimpling")
        while True:
            status = self.arduino_control.read_from_arduino()
            if status == "Dimple complete":
                break
            time.sleep(1)
        self.power_meter.save_power_meter_data()

    def taper_and_dimple(self):

        self.power_meter.clear_power_meter_data()
        time.sleep(0.1)
        self.arduino_control.send_command('TAPER\n')
        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            if status == "Tapering Complete":
                break
            time.sleep(0.01)  # Wait for a short period before checking again
        self.power_meter.save_power_meter_data()

        self.center_taper()
        while True:
            status = self.arduino_control.read_from_arduino()
            if status == "Centered":
                break
            time.sleep(1)

        # Dimple the taper
        self.power_meter.clear_power_meter_data()
        time.sleep(0.1)
        self.arduino_control.send_command("DIMPLE\n")  # Removed encode() here
        print("Dimpling")
        while True:
            status = self.arduino_control.read_from_arduino()
            if status == "Dimple complete":
                break
            time.sleep(1)
        self.power_meter.save_power_meter_data()


    def automate_taper_bezier(self):
        time.sleep(0.1)
        self.arduino_control.send_command("TAPERB\n")
        print("Bezier Taper")
        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            if status == "Tapering Complete":
                break
            time.sleep(0.1)  # Wait for a short period before checking again
        self.power_meter.save_power_meter_data()

    def automate_taper(self):

        time.sleep(0.1)
        self.arduino_control.send_command("TAPER\n")
        print("Linear Taper")
        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            if status == "Tapering Complete":
                break
            time.sleep(0.1)  # Wait for a short period before checking again
        self.power_meter.save_power_meter_data()

    def move_motor_1(self, speed, steps):
        """
        Moves Motor 1 at the specified speed for a set number of steps.

        Parameters:
        - speed (int): Desired speed for Motor 1.
        - steps (int): Number of steps Motor 1 should move. Positive values for forward movement, negative for backward.
        """
        # Set the speed
        speed_cmd = f"SETSP1_{speed:05}\n"
        self.arduino_control.send_command(speed_cmd)
        time.sleep(0.1)
        print("move")
        # Set the movement direction and steps
        if steps >= 0:
            print("Move foward")
            move_cmd = f"MOVRF_1{steps:05}\n"
        else:
            print("Move back")
            steps = abs(steps)
            move_cmd = f"MOVRB_1{steps:05}\n"

        self.arduino_control.send_command(move_cmd)
        time.sleep(0.1)
        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            print(status)
            if status == "Done":
                break
            time.sleep(0.5)  # Wait for a short period before checking again

class GUIcontrol:
    def __init__(self, root, motor_control, arduino_control, power_meter, camera_control, database_linear, database_bezier):
        self.root = root
        self.root.title("Fiber Pulling App")

        # Store references to the motor control, Arduino control, power meter, camera, database
        self.motor_control = motor_control
        self.arduino_control = arduino_control
        self.power_meter = power_meter
        self.camera_control = camera_control
        self.database_lin = database_linear
        self.database_bez = database_bezier

        # Setup the frames in the GUI
        self.setup_frames()

        # Set up the protocol for handling window closure
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create and place buttons on GUI
        self.setup_gui()

        # Show camera feed
        self.show_camera_feed()

    def setup_gui(self):
        root.title('Fiber Pulling Controller')
        self.tapering_setup()
        self.dynamic_button_setup()
        self.dimpling_setup()
        self.update_electrode_status()
        self.power_meter_plot_setup()
        self.connection_status_setup()
        self.linear_profile_setup()
        self.live_info_setup()
        self.bezier_profile_setup()
        if self.arduino_control.get_connection_status():
            self.connection_status_frame.configure(bg="green")

    def setup_frames(self):
        # Create and configure the main frame
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Create Frame for Connection Status and other important info
        self.connection_status_frame = tk.Frame(main_frame, bg= "red")
        self.connection_status_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Create three vertical sub frames
        column_frame_1 = tk.Frame(main_frame)
        column_frame_1.grid(row=1, column=0, sticky="nsew")

        column_frame_2 = tk.Frame(main_frame)
        column_frame_2.grid(row=1, column=1, sticky="nsew")

        column_frame_3 = tk.Frame(main_frame)
        column_frame_3.grid(row=1, column=2, sticky="nsew")


        # Create subframes in the first column frame
        self.profile_frame = tk.Frame(column_frame_1, highlightbackground="black", highlightthickness=2)
        self.profile_frame.grid(row=0, column=0, sticky="nsew")

        self.tapering_frame = tk.Frame(column_frame_1, highlightbackground="black", highlightthickness=2)
        self.tapering_frame.grid(row=1, column=0, sticky="nsew")

        self.dimpling_frame = tk.Frame(column_frame_1, highlightbackground="black", highlightthickness=2)
        self.dimpling_frame.grid(row=2, column=0, sticky="nsew")

        self.live_info_frame = tk.Frame(column_frame_2, highlightbackground="black", highlightthickness=2)
        self.live_info_frame.grid(row=1, column=0, sticky="nsew")

        # Second Column Frame
        self.dynamic_button_frame = tk.Frame(column_frame_2)
        self.dynamic_button_frame.columnconfigure(0, weight=1)
        self.dynamic_button_frame.grid(row=0, column=0, sticky="nsew")

        self.power_meter_frame = tk.Frame(column_frame_3, highlightbackground="black", highlightthickness=1,
                                          width=400, height=300, bg="grey80")
        self.power_meter_frame.grid(row=0, column=0, sticky="nsew")

        self.camera_frame = tk.Frame(column_frame_3, highlightbackground="black", highlightthickness=1,
                                     width=400, height=300, bg="grey80")
        self.camera_frame.grid(row=1, column=0, sticky="nsew")

        # Configure column and row weights to make subframes expand with window resizing
        main_frame.columnconfigure((0, 1), weight=1)
        main_frame.rowconfigure((0, 1), weight=1)

    def live_info_setup(self):
        # Prepare GUI for Tapering
        live_info_label = tk.Label(self.live_info_frame, text="Live Data:", font=(15))
        live_info_label.grid(row=0, column=0, pady=7)

        self.fiber_loss_label = tk.Label(self.live_info_frame, text="Fiber Transmission: 0.0 Percent")
        self.fiber_loss_label.grid(row=1, column=0, pady=7)

    def tapering_setup(self):
        # Prepare GUI for Tapering
        tapering_label = tk.Label(self.tapering_frame, text="Tapering:", font=(15))

        # resoution 1 labels and option menu
        Res_options = ["High Resolution", "Mid Resolution", "Low Resolution"]
        self.Res1_selection = tk.StringVar()
        self.Res1_selection.set(Res_options[0])
        Res1_label = tk.Label(self.tapering_frame, text="Resolution Motor 1: ", font=("Arial", 10))
        self.Res1_entry = tk.OptionMenu(self.tapering_frame, self.Res1_selection, *Res_options)
        self.Res1_entry['menu'].configure(font=('Arial', 10))

        # resolution 2 labels and option menu
        self.Res2_selection = tk.StringVar()
        self.Res2_selection.set(Res_options[1])
        Res2_label = tk.Label(self.tapering_frame, text="Resolution Motor 2: ", font=("Arial", 10))
        self.Res2_entry = tk.OptionMenu(self.tapering_frame, self.Res2_selection, *Res_options)
        self.Res2_entry['menu'].configure(font=('Arial', 10))

        # Enable Motors Widgets and Dropdown Menu
        enab_options = ["Yes", "No"]  # enable options
        self.enab_selection = tk.StringVar()  # enable label and option menu
        self.enab_selection.set(enab_options[0])
        enab_label = tk.Label(self.tapering_frame, text="Enable Motors?: ", font=("Arial", 10))
        self.enab_entry = tk.OptionMenu(self.tapering_frame, self.enab_selection, *enab_options)

        # Speed 1 labels and entry widgets
        Speed1_label = tk.Label(self.tapering_frame, text="Speed Motor 1: ", font=("Arial", 10))
        Speed1_units = tk.Label(self.tapering_frame, text="Steps/s", font=("Arial", 10))
        self.Speed1_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        # Speed 2 Labels and entry widgets
        Speed2_label = tk.Label(self.tapering_frame, text="Speed Motor 2: ", font=("Arial", 10))
        Speed2_units = tk.Label(self.tapering_frame, text="Steps/s", font=("Arial", 10))
        self.Speed2_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        Accel1_label = tk.Label(self.tapering_frame, text="Acceleration Motor 1: ", font=("Arial", 10))
        Accel1_units = tk.Label(self.tapering_frame, text="Steps/s\u00b2", font=("Arial", 10))
        self.Accel1_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        # Acceleration 1 labels and entry widgets
        Accel2_label = tk.Label(self.tapering_frame, text="Acceleration Motor 2: ", font=("Arial", 10))
        Accel2_units = tk.Label(self.tapering_frame, text="Steps/s\u00b2", font=("Arial", 10))
        self.Accel2_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        # preheat labels and entry widgets
        prht_label = tk.Label(self.tapering_frame, text="Preheat time:", font=("Arial", 10))
        prht_units = tk.Label(self.tapering_frame, text="ms", font=("Arial", 10))
        self.prht_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        # preheat labels and entry widgets
        max_speed_time = tk.Label(self.tapering_frame, text="Max Speed Time:", font=("Arial", 10))
        max_speed_time_units = tk.Label(self.tapering_frame, text="ms", font=("Arial", 10))
        self.max_speed_time_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        tapering_label.grid(row=0, column=0, padx=5, pady=2)

        Res1_label.grid(row=1, column=3, padx=5, pady=2)  # resolution 1 widget placements
        self.Res1_entry.grid(row=2, column=3, padx=5, pady=2)

        Res2_label.grid(row=3, column=3, padx=5, pady=2)  # resolution 2 widget placements
        self.Res2_entry.grid(row=4, column=3, padx=5, pady=2)

        enab_label.grid(row=5, column=3, padx=5, pady=2)  # enable 1 widget placements
        self.enab_entry.grid(row=6, column=3, padx=5, pady=2)


        Speed1_label.grid(row=1, column=0, pady=2)  # Speed 1 widget placements
        Speed1_units.grid(row=1, column=2, pady=2)
        self.Speed1_entry.grid(row=1, column=1, pady=2)

        Speed2_label.grid(row=2, column=0, pady=2)  # Speed 2 widget placements
        Speed2_units.grid(row=2, column=2, pady=2)
        self.Speed2_entry.grid(row=2, column=1, pady=2)

        Accel1_label.grid(row=3, column=0, pady=2)  # acceleration 1 widget placements
        Accel1_units.grid(row=3, column=2)
        self.Accel1_entry.grid(row=3, column=1, pady=2)

        Accel2_label.grid(row=4, column=0, pady=2)  # Acceleration 2 widget placements
        Accel2_units.grid(row=4, column=2)
        self.Accel2_entry.grid(row=4, column=1, pady=2)

        prht_label.grid(row=5, column=0, pady=2)  # preheat widgets placements
        self.prht_entry.grid(row=5, column=1, pady=2)
        prht_units.grid(row=5, column=2, pady=2)

        max_speed_time.grid(row=6, column=0, pady=2)  # preheat widgets placements
        self.max_speed_time_entry.grid(row=6, column=1, pady=2)
        max_speed_time_units.grid(row=6, column=2, pady=2)

    def dimpling_setup(self):
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # prepare the widgets of the GUI for dimpling
        dimpling_label = tk.Label(self.dimpling_frame, text="Dimpling:", font=(15))
        dimpling_label.grid(row=0, column=0, pady=7)

        # Speed 3 labels and entry widgets
        Speed3_label = tk.Label(self.dimpling_frame, text="Speed Motor 3: ", font=("Arial", 10))
        Speed3_units = tk.Label(self.dimpling_frame, text="Steps/s", font=("Arial", 10))
        self.Speed3_entry = tk.Entry(self.dimpling_frame, width=6, font=("Arial", 10))

        # resolution 3 labels and option menu widgets
        Depth_label = tk.Label(self.dimpling_frame, text="Dimple depth: ", font=("Arial", 10))
        self.Dimple_depth_entry = tk.Entry(self.dimpling_frame, width=6, font=("Arial", 10))
        Depth_units = tk.Label(self.dimpling_frame, text="Steps", font=("Arial", 10))

        # Heating Time label and entry options during dimpling
        Heat_time_label = tk.Label(self.dimpling_frame, text="Heat Time:", font=("Arial", 10))  # time delay labels and entry widgets
        Heat_time_units = tk.Label(self.dimpling_frame, text="ms", font=("Arial", 10))
        self.Heat_time_entry = tk.Entry(self.dimpling_frame, width=6, font=("Arial", 10))

        # Tension label and entry widgets
        Tension_1_label = tk.Label(self.dimpling_frame, text="Tension Motor 1:", font=("Arial", 10))
        Tension_1_units = tk.Label(self.dimpling_frame, text="steps", font=("Arial", 10))
        self.Tension_1_entry = tk.Entry(self.dimpling_frame, width=6, font=("Arial", 10))
        Tension_2_label = tk.Label(self.dimpling_frame, text="Tension Motor 2:", font=("Arial", 10))
        Tension_2_units = tk.Label(self.dimpling_frame, text="steps", font=("Arial", 10))
        self.Tension_2_entry = tk.Entry(self.dimpling_frame, width=6, font=("Arial", 10))

        # Speed 3 widget placements
        Speed3_label.grid(row=1, column=0, pady=2)
        Speed3_units.grid(row=1, column=2, pady=2)
        self.Speed3_entry.grid(row=1, column=1, pady=2)

        Depth_label.grid(row=2, column=0, padx=5, pady=2)  # resolution 1 widget placements
        self.Dimple_depth_entry.grid(row=2, column=1, padx=5, pady=2)
        Depth_units.grid(row=2, column=2, padx=5, pady=2)


        Heat_time_label.grid(row=3, column=0, pady=2)  # time delay dimple widgets placements
        Heat_time_units.grid(row=3, column=2)
        self.Heat_time_entry.grid(row=3, column=1, pady=2)

        Tension_1_label.grid(row=4, column=0, pady=2)  # Tension dimple widgets placements
        Tension_1_units.grid(row=4, column=2)
        self.Tension_1_entry.grid(row=4, column=1, pady=2)
        Tension_2_label.grid(row=5, column=0, pady=2)
        Tension_2_units.grid(row=5, column=2)
        self.Tension_2_entry.grid(row=5, column=1, pady=2)

    def dynamic_button_setup(self):
        self.Automate_taper_bezier_button = tk.Button(self.dynamic_button_frame, text="Taper Bezier", font=("Arial", 10),
                                                command=self.taper_bezier_button_pressed, pady=10)
        self.Automate_dimple_button = tk.Button(self.dynamic_button_frame, text="Taper & Dimple", font=("Arial", 10),
                                                command=self.taper_dimple_button_pressed, pady=10)
        self.Automate_taper_button = tk.Button(self.dynamic_button_frame, text="Taper Linear", font=("Arial", 10),
                                               command=self.automate_taper_button_pressed, pady=10)

        self.Emg_button = tk.Button(self.dynamic_button_frame, text="EMERGENCY STOP", command=self.arduino_control.emergency_stop,
                                    bg="red", fg="white", activebackground="green", pady=20)
        self.elec_toggle_button = tk.Button(self.dynamic_button_frame, text="electrodes on/off", command=self.toggle_electrode_state_button_pressed
                                            , font=("Arial", 10), activebackground = "cyan", pady=20)

        self.Tension_button = tk.Button(self.dynamic_button_frame, text="Tension Fiber", font=("Arial", 10),
                                        command=self.tension_button_pressed, pady=10)

        self.Fiber_broken_button = tk.Button(self.dynamic_button_frame, text ="Fiber Broken", font = ("Arial", 10),
                                             command =self.arduino_control.fiber_broken, pady=10)

        self.send_parameters_button = tk.Button(self.dynamic_button_frame, text="Send GUI Parameters",
                                                font =("Arial", 10), command=self.assign_gui_parameters, pady=10)


        # Dynamic Button Frame placement

        self.send_parameters_button.grid(row=0, column=0, pady=5, sticky="nsew")
        self.Automate_taper_bezier_button.grid(row=1, column=0, pady=5, sticky="nsew")
        self.Automate_taper_button.grid(row=2, column=0, pady=5,  sticky="nsew")
        self.Automate_dimple_button.grid(row=3, column=0, pady=5, sticky="nsew")
        self.Tension_button.grid(row=4, column=0, pady=5, sticky="nsew")
        self.Fiber_broken_button.grid(row=5, column=0, pady=5, sticky="nsew")
        self.elec_toggle_button.grid(row=6, column=0, pady=5,  sticky="nsew")
        self.Emg_button.grid(row=7, column=0, pady=5, sticky="nsew")

        # Dimpling Frame Buttons
        self.Reset_button = tk.Button(self.dimpling_frame, text="Reset", command=self.motor_control.reset, font=("Arial", 10)
                                      , padx=10, pady=2)
        self.Center_button = tk.Button(self.dimpling_frame, text="Center", command=self.center_button_pressed,
                                       font=("Arial", 10), padx=10, pady=2)
        self.Dimple_button = tk.Button(self.dimpling_frame, text="Dimple", font=("Arial", 10),
                                       command=self.dimple_button_pressed, padx=10, pady=2)

        self.Calibrate_button = tk.Button(self.dimpling_frame, text="Calibrate Knife", font=("Arial", 10),
                                          command=self.motor_control.calibrate_knife, pady=2)
        self.Calibrate_up_button = tk.Button(self.dimpling_frame, text="Knife Up 500 steps", font=("Arial", 8),
                                             command=self.motor_control.calibrate_up_knife, pady=2)
        self.Calibrate_down_button = tk.Button(self.dimpling_frame, text="Knife Down 500 steps", font=("Arial", 8),
                                               command=self.motor_control.calibrate_down_knife, pady=2)

        # Dimple Button placement in seperate subframe
        self.Dimple_button.grid(row=1, column=3, sticky="nsew")
        self.Center_button.grid(row=2, column=3, sticky="nsew")
        self.Reset_button.grid(row=3, column=3, sticky="nsew")
        self.Calibrate_button.grid(row=1, column=4,  sticky="nsew")
        self.Calibrate_up_button.grid(row=2, column=4, sticky="nsew")
        self.Calibrate_down_button.grid(row=3, column=4, sticky="nsew")

    def connection_status_setup(self):
        # Check the connection status of Arduino and update the background color accordingly
        if self.arduino_control.get_connection_status():
            arduino_bg = "green"
            self.arduino_connection = "Arduino Connected"
        else:
            arduino_bg = "red"
            self.arduino_connection = "Arduino Not Connected"

        # Check the connection status of the power meter and update the background color accordingly
        if self.power_meter.get_connection_status():
            power_meter_bg = "green"
            self.power_meter_connection = "Power Meter Connected"
        else:
            power_meter_bg = "red"
            self.power_meter_connection = "Power Meter Not Connected"

        if self.camera_control.camera_connected:
            microscope_bg= "green"
            self.microscope_connection = "Microscope Connected"
        else:
            microscope_bg ="red"
            self.microscope_connection = "Microscope Not Connected"

        # Create and place labels for connection status directly in the main frame
        arduino_status_label = Label(self.connection_status_frame, text=self.arduino_connection, bg=arduino_bg)
        arduino_status_label.grid(row=0, column=0, padx=100)

        power_meter_status_label = Label(self.connection_status_frame, text=self.power_meter_connection, bg=power_meter_bg)
        power_meter_status_label.grid(row=0, column=1, columnspan=2, padx=100)

        microscope_status_label = Label(self.connection_status_frame, text=self.microscope_connection, bg=microscope_bg)
        microscope_status_label.grid(row=0, column=3, columnspan=2, padx=100)

    def power_meter_plot_setup(self):
        if self.power_meter.get_connection_status():
            # Setup Matplotlib Plot
            self.fig, self.ax = plt.subplots(figsize=(5, 3))
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.power_meter_frame)
            self.canvas.get_tk_widget().grid(row=0, column=0)

            # Add a title to the plot
            self.ax.set_title("Power Meter Plot")
            self.ax.grid()

            # Optionally, if you want to set labels for x and y axes:
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Voltage (mW)")

            self.line, = self.ax.plot(self.power_meter.power_data, self.power_meter.time_data, label='Power')  # Define 'line' here
            print("line")
            # Call animation method (You can adjust the interval as needed)
            self.update_power_meter_plot()

    def linear_profile_setup(self):
        # prepare the widgets of the GUI for dimpling
        #as
        dimpling_label = tk.Label(self.profile_frame, text="Linear Profiles", font=("Arial", 15))
        dimpling_label.grid(row=0, column=0, columnspan=2)

        # Create a listbox to display profiles
        self.linear_listbox = tk.Listbox(self.profile_frame, width=30, height=8, selectmode=tk.SINGLE)
        self.linear_listbox.grid(row=3, column=0, rowspan=3, columnspan=2)

        # Load profiles from the database and populate the listbox
        self.refresh_profiles(self.database_lin, self.linear_listbox)

        self.profile_name_entry = tk.Entry(self.profile_frame, width=10, font=("Arial", 10))
        self.profile_name_entry.grid(row=1, column=1)

        # Buttons for profile management
        self.load_button = tk.Button(self.profile_frame, text="Load Profile", command=self.load_lin_profile)
        self.load_button.grid(row=2, column=0, pady=5)

        self.add_button = tk.Button(self.profile_frame, text="Add Profile", command=self.add_lin_profile)
        self.add_button.grid(row=1, column=0, pady=5)

        self.delete_button = tk.Button(self.profile_frame, text="Delete Profile", command=self.delete_lin_profile)
        self.delete_button.grid(row=2, column=1, pady=5)

        # Load the last used profile on startup
        last_used_profile = database_linear.get_last_used_profile()
        if last_used_profile:
            self.load_lin_profile(last_used_profile)

    def bezier_profile_setup(self):
        # prepare the widgets of the GUI for dimpling
        bezier_label = tk.Label(self.profile_frame, text="Bezier Profiles", font=("Arial", 15))
        bezier_label.grid(row=0, column=3, columnspan=2)

        # Create a listbox to display profiles
        self.bezier_listbox = tk.Listbox(self.profile_frame, width=30, height=8, selectmode=tk.SINGLE)
        self.bezier_listbox.grid(row=3, column=3, rowspan=3, columnspan=2)

        # To load Bezier profiles
        self.refresh_profiles(self.database_bez, self.bezier_listbox)

        self.new_button = tk.Button(self.profile_frame, text="Create Profile", width=10, command=self.open_bezier_window)
        self.new_button.grid(row=1, column=3, pady=5, columnspan=1)

        self.delete_button = tk.Button(self.profile_frame, text="Delete Profile", width=10, command=self.delete_bez_profile)
        self.delete_button.grid(row=1, column=4, pady=5, columnspan=1)

        self.send_profile_button = tk.Button(self.profile_frame, text = "Send Profile", width=15, command=self.send_bez_profile)
        self.send_profile_button.grid(row=2, column=3, pady=5, columnspan=2)

    def refresh_profiles(self, database, listbox):
        # Clear the listbox
        listbox.delete(0, tk.END)

        # Get all profiles from the specified database and add them to the listbox
        profiles = database.get_all_profiles()
        for profile in profiles:
            listbox.insert(tk.END, profile["name"])

    def load_lin_profile(self, profile_name=None):
        if profile_name is None:
            # Get the selected profile name from the listbox
            selected_profile_name = self.linear_listbox.get(tk.ACTIVE)
        else:
            selected_profile_name = profile_name

        # Update the last used profile and save it to the database
        self.database_lin.set_last_used_profile(selected_profile_name)

        # Find the profile in the database by name
        selected_profile = self.database_lin.find_profile_by_name(selected_profile_name)

        # Check if the selected_profile exists
        if selected_profile:
            # Populate the Entry widgets with the profile data
            self.Speed1_entry.delete(0, tk.END)
            self.Speed1_entry.insert(0, selected_profile["motor_speeds"][0])
            # Repeat this for other Entry widgets and parameters
            self.Speed2_entry.delete(0, tk.END)
            self.Speed2_entry.insert(0, selected_profile["motor_speeds"][1])
            # Repeat this for other Entry widgets and parameters
            self.Speed3_entry.delete(0, tk.END)
            self.Speed3_entry.insert(0, selected_profile["motor_speeds"][2])
            # Repeat this for other Entry widgets and parameters
            self.Accel1_entry.delete(0, tk.END)
            self.Accel1_entry.insert(0, selected_profile["motor_accelerations"][0])
            # Repeat this for other Entry widgets and parameters
            self.Accel2_entry.delete(0, tk.END)
            self.Accel2_entry.insert(0, selected_profile["motor_accelerations"][1])
            # Repeat this for other Entry widgets and parameters
            self.max_speed_time_entry.delete(0, tk.END)
            self.max_speed_time_entry.insert(0, selected_profile["max_speed_time"])
            # Repeat this for other Entry widgets and parameters
            self.prht_entry.delete(0, tk.END)
            self.prht_entry.insert(0, selected_profile["preheat_time"])
            # Repeat this for other Entry widgets and parameters
            self.Heat_time_entry.delete(0, tk.END)
            self.Heat_time_entry.insert(0, selected_profile["dimple_heat_time"])
            # Repeat this for other Entry widgets and parameters
            self.Dimple_depth_entry.delete(0, tk.END)
            self.Dimple_depth_entry.insert(0, selected_profile["dimple_depth"])
            # Repeat this for other Entry widgets and parameters
            self.Tension_1_entry.delete(0, tk.END)
            self.Tension_1_entry.insert(0, selected_profile["tension_steps"][0])
            # Repeat this for other Entry widgets and parameters
            self.Tension_2_entry.delete(0, tk.END)
            self.Tension_2_entry.insert(0, selected_profile["tension_steps"][1])

    def add_lin_profile(self):

        # Collect data from entry boxes
        profile_name = self.profile_name_entry.get()
        if profile_name == "":
            print("Enter a name")
            return
        print("Adding profile")
        motor_speeds = [int(self.Speed1_entry.get()), int(self.Speed2_entry.get()), int(self.Speed3_entry.get())]
        motor_accelerations = [int(self.Accel1_entry.get()), int(self.Accel2_entry.get()), 0]  # Assuming 0 for now
        max_speed_time = float(self.max_speed_time_entry.get())
        preheat_time = float(self.prht_entry.get())
        dimple_depth = int(self.Dimple_depth_entry.get())
        dimple_heat_time = float(self.Heat_time_entry.get())
        motor_resolution = [self.Res1_selection.get(), self.Res2_selection.get(), "low"]  # Assuming "low" for now
        tension_steps = [float(self.Tension_1_entry.get()), float(self.Tension_2_entry.get())]  # Assuming 0.0 for now

        # Create a profile dictionary with the collected data
        new_profile = {
            "name": profile_name,
            "motor_speeds": motor_speeds,
            "motor_accelerations": motor_accelerations,
            "max_speed_time": max_speed_time,
            "preheat_time": preheat_time,
            "dimple_depth": dimple_depth,
            "dimple_heat_time": dimple_heat_time,
            "motor_resolution": motor_resolution,
            "knife_calibration_height": 87900,
            "tension_steps": tension_steps
        }

        # Add the new profile to the database
        self.database_lin.add_profile(new_profile)

        # To load linear profiles
        self.refresh_profiles(self.database_lin, self.linear_listbox)

    def delete_lin_profile(self):
        # Get the selected profile name from your listbox or other widget
        selected_profile = self.linear_listbox.get(tk.ACTIVE)

        # Call the delete_profile function from the Database object
        deletion_result = self.database_lin.delete_profile(selected_profile)

        # Check if the deletion was successful
        if deletion_result:
            print(f"Profile '{selected_profile}' deleted successfully.")
            # Refresh your list of profiles in the GUI if needed
            # To load linear profiles
            self.refresh_profiles(self.database_lin, self.linear_listbox)
        else:
            print(f"Profile '{selected_profile}' not found or deletion failed.")

    def delete_bez_profile(self):
        # Get the selected profile name from your listbox or other widget
        selected_profile = self.bezier_listbox.get(tk.ACTIVE)

        # Call the delete_profile function from the Database object
        deletion_result = self.database_bez.delete_profile(selected_profile)

        # Check if the deletion was successful
        if deletion_result:
            print(f"Profile '{selected_profile}' deleted successfully.")
            # Refresh your list of profiles in the GUI if needed
            # To load linear profiles
            self.refresh_profiles(self.database_bez, self.bezier_listbox)
        else:
            print(f"Profile '{selected_profile}' not found or deletion failed.")

    def send_bez_profile(self):
        selected_profile_name = self.bezier_listbox.get(tk.ACTIVE)
        bezier_profile = self.database_bez.find_profile_by_name(selected_profile_name)
        print(bezier_profile)
        self.arduino_control.send_bezier_profile(bezier_profile)

    def update_electrode_status(self):
        state = self.arduino_control.electrode_state
        if state:
            self.elec_toggle_button.config(text="Electrode On", bg="red")
        else:
            self.elec_toggle_button.config(text="Electrode Off", bg="green")

    def tension_button_pressed(self):
        self.motor_control.move_motor_1(speed=50, steps=-100)
        pass

    def toggle_electrode_state_button_pressed(self):
        self.arduino_control.toggle_electrodes_state()
        self.update_electrode_status()

    def assign_gui_parameters(self):
        Speed1_entry = self.Speed1_entry.get()
        Speed2_entry = self.Speed2_entry.get()
        Accel1_entry = self.Accel1_entry.get()
        Accel2_entry = self.Accel2_entry.get()
        enab_selection = self.enab_selection.get()
        Res1_selection = self.Res1_selection.get()
        Res2_selection = self.Res2_selection.get()
        prht_entry = self.prht_entry.get()
        waist_time = self.max_speed_time_entry.get()
        dimple_speed = self.Speed3_entry.get()
        dimple_depth = self.Dimple_depth_entry.get()
        dimple_heat_time = self.Heat_time_entry.get()
        tension_1 = self.Tension_1_entry.get()
        tension_2 = self.Tension_2_entry.get()
        self.arduino_control.assign_parameters(Speed1_entry, Speed2_entry,
                                                Accel1_entry, Accel2_entry,enab_selection, Res1_selection, Res2_selection,
                                                prht_entry, waist_time,  dimple_speed, dimple_depth,
                                                dimple_heat_time, tension_1, tension_2)

    def dimple_button_pressed(self):
        # begin updating the power meter
        self.update_power_meter_plot_periodically()
        self.update_fiber_loss_periodically()
        thread = threading.Thread(target=self.motor_control.dimple, args=())
        thread.start()

    def center_button_pressed(self):
        thread = threading.Thread(target=self.motor_control.center_taper, args=())
        thread.start()

    def taper_dimple_button_pressed(self):
        # begin updating the power meter
        self.update_power_meter_plot_periodically()
        self.update_fiber_loss_periodically()
        thread = threading.Thread(target=self.motor_control.taper_and_dimple, args=())
        thread.start()

    def taper_bezier_button_pressed(self):
        # begin updating the power meter
        self.update_power_meter_plot_periodically()
        self.update_fiber_loss_periodically()
        thread = threading.Thread(target=self.motor_control.automate_taper_bezier, args=())
        thread.start()

    def automate_taper_button_pressed(self):
        # begin updating the power meter
        self.update_power_meter_plot_periodically()
        self.update_fiber_loss_periodically()
        thread = threading.Thread(target=self.motor_control.automate_taper, args=())
        thread.start()

    def show_camera_feed(self):
        if self.camera_control.camera_connected:
            """Display the camera feed within the GUI."""
            frame = self.camera_control.get_frame()

            img = Image.fromarray(frame).resize((500, 300))
            imgtk = ImageTk.PhotoImage(image=img)

            if not hasattr(self, "camera_label"):
                # Create a label for the camera feed if it doesn't exist
                self.camera_label = tk.Label(self.camera_frame, image=imgtk)
                self.camera_label.imgtk = imgtk  # Store a reference to prevent garbage collection
                self.camera_label.grid(row=0, column=0, sticky="nsew")
            else:
                # Update the existing label with the new image
                self.camera_label.configure(image=imgtk)
                self.camera_label.imgtk = imgtk  # Store a reference to prevent garbage collection

        # Schedule the next frame update
        self.root.after(10, self.show_camera_feed)

    def update_power_meter_plot_periodically(self):
        if self.power_meter.get_connection_status():
            # Call the function to update the power meter plot
            self.update_power_meter_plot()

            # Schedule the next update using the 'after' method
            self.root.after(100, self.update_power_meter_plot_periodically)

    def update_power_meter_plot(self):
        if self.power_meter.get_connection_status():
            # Call the read_power method from your PowerMeterControl instance
            power = self.power_meter.read_power()

            if power is not None:
                self.power_meter.time_data.append(time.time())  # Replace with how you're getting the time
                self.power_meter.power_data.append(power)

                # Update the plot with the new data
                self.line.set_xdata(self.power_meter.time_data)
                self.line.set_ydata(self.power_meter.power_data)

                # Adjust the plot limits if needed
                self.ax.relim()
                self.ax.autoscale_view()

                # Redraw the canvas
                self.canvas.draw()

    def on_closing(self):
        try:
            #self.motor_control.move_to_home_position()
            self.root.destroy()
            print("Good work")
        except Exception as e:
            # Handle the exception gracefully, e.g., print an error message
            print(f"An error occurred during closing: {str(e)}")

    def update_fiber_loss(self):
        # Input power (initial power level)
        power_in = self.power_meter.power_data[1]

        # Output power (final power level)
        power_out = self.power_meter.read_power() # Replace with your actual output power value

        # Calculate loss in decibels
        transmission_percent = 100*(power_out/power_in)
        #loss_percent = 10 * math.log10(P_in / P_out)
        self.fiber_loss_label.config(text=f"Fiber Transmission: {transmission_percent:.2f} Percent")

    def update_fiber_loss_periodically(self):
        if self.power_meter.get_connection_status():
            # Update the label with the latest value
            self.update_fiber_loss()

            # Schedule the next update after a specific interval (e.g., 1000 milliseconds)
            self.root.after(500, self.update_fiber_loss_periodically)

    def open_bezier_window(self):
        bezier_window = tk.Toplevel(root)
        bezier_app = BezierCurveApp(bezier_window, self.database_bez)

        def on_close():
            bezier_window.destroy()
            self.database_bez.data = self.database_bez.load_data()  # Reload data
            self.refresh_profiles(self.database_bez, self.bezier_listbox)

        bezier_window.protocol("WM_DELETE_WINDOW", on_close)


class BezierCurveApp:
    def __init__(self, root, database):

        self.database = database


        # Define constant for the frame size
        self.padding_y = 80
        self.padding_x = 80
        self.frame_size_x = 1000
        self.frame_size_y = 500
        self.y_lower_bound = 0
        self.x_lower_bound = 0
        self.y_upper_bound = self.frame_size_y - 2 * self.padding_y
        self.x_upper_bound = self.frame_size_x - 2 * self.padding_x

        # Create initial control points
        self.accel_points_1 = [(self.x_lower_bound, self.y_lower_bound), (self.x_lower_bound, self.y_upper_bound/6),
                               (self.x_upper_bound*4/10,  self.y_lower_bound/4), (self.x_upper_bound*9/20, self.y_upper_bound)]
        self.decel_points_1 = [(self.x_upper_bound * 11 / 20, self.y_upper_bound), (self.x_upper_bound*6/10,  self.y_lower_bound/4),
                               (self.x_upper_bound, self.y_upper_bound/6), (self.x_upper_bound, self.y_lower_bound)]

        # Copy of the points which will be scaled and saved to the JSON file
        self.display_accel_points_1 = self.accel_points_1.copy()
        self.display_decel_points_1 = self.decel_points_1.copy()

        self.accel_points_2 = [(self.x_lower_bound, self.y_upper_bound*0.1), (self.x_upper_bound / 8, self.y_lower_bound),
                               (self.x_upper_bound / 4,  self.y_lower_bound), (self.x_upper_bound*9/20, self.y_lower_bound)]
        self.decel_points_2 = [(self.x_upper_bound * 11 / 20, self.y_lower_bound), (self.x_upper_bound * 3 / 4, self.y_lower_bound),
                               (self.x_upper_bound*5/6, self.y_lower_bound), (self.x_upper_bound, self.y_upper_bound*0.1)]

        # Copy of the points which will be scaled and saved to the JSON file
        self.display_accel_points_2 = self.accel_points_2.copy()
        self.display_decel_points_2 = self.decel_points_2.copy()

        #Set Maximum speeds for initialization
        self.initial_max_velocity = 900
        self.initial_max_time = 5000


        # Create the control panel
        self.control_panel = tk.Frame(root)
        self.control_panel.pack(pady=10)

        # Add widgets to the control panel
        tk.Label(self.control_panel, text="Max Time (ms):").grid(row=0, column=0, padx=10)
        self.last_x_entry = tk.Entry(self.control_panel, width=5)
        self.last_x_entry.grid(row=0, column=1)
        self.last_x_entry.insert(0, str(self.initial_max_time))

        tk.Label(self.control_panel, text="Max Velocity (step/s):").grid(row=1, column=0, padx=10)
        self.last_y_entry = tk.Entry(self.control_panel, width=5)
        self.last_y_entry.grid(row=1, column=1)
        self.last_y_entry.insert(0, str(self.initial_max_velocity))

        self.update_button = tk.Button(self.control_panel, text="Update Final Conditions", command=self.update_display_control_points)
        self.update_button.grid(row=2, columnspan=3)


        # Button and entry box for saving a new profile with name entered in entry box
        self.save_profile = tk.Button(self.control_panel, text="Save Points to Database", command=self.save_profile)
        self.save_profile.grid(row=3, columnspan=3)
        self.profile_name = tk.Entry(self.control_panel, width=18, font=("Arial", 10))
        self.profile_name.grid(row=4, columnspan=3)

        self.canvas = Canvas(root, bg="white", width=self.frame_size_x, height=self.frame_size_y)
        self.canvas.pack()

        self.draw_grid()

        # Initialize control points on the screen with distinct tags
        self.init_control_points()

        # Initialize functionality for grabbing and dragging points
        self.canvas.tag_bind("point", "<Button-1>", self.on_point_click)
        self.canvas.tag_bind("point", "<B1-Motion>", self.on_point_drag)

        # Add a StringVar to hold the text for the label
        self.accel_points_1_text = tk.StringVar()
        self.decel_points_1_text = tk.StringVar()
        self.accel_points_2_text = tk.StringVar()
        self.decel_points_2_text = tk.StringVar()
        self.update_point_position_text()

        # Create labels for displaying acceleration points
        self.accel_points_label_1 = tk.Label(self.control_panel, textvariable=self.accel_points_1_text,
                                             font=("Arial", 10, "bold"), width=60)
        self.accel_points_label_2 = tk.Label(self.control_panel, textvariable=self.accel_points_2_text,
                                             font=("Arial", 10, "bold"), width=60)


        # Create labels for displaying deceleration points
        self.decel_points_label_1 = tk.Label(self.control_panel, textvariable=self.decel_points_1_text,
                                             font=("Arial", 10, "bold"), width=60)
        self.decel_points_label_2 = tk.Label(self.control_panel, textvariable=self.decel_points_2_text,
                                             font=("Arial", 10, "bold"), width=60)
        self.accel_points_label_1.grid(row=0, column=4, padx=40, pady=5)
        self.decel_points_label_1.grid(row=1, column=4, padx=40, pady=5)
        self.accel_points_label_2.grid(row=2, column=4, padx=40, pady=5)
        self.decel_points_label_2.grid(row=3, column=4, padx=40, pady=5)

        # Appropriately scale points
        self.update_display_control_points()
        self.update_display_control_points()

        # Draw the initial Bezier curves
        self.draw_curve(self.accel_points_1, "acc_curve1", "blue")

        # Draw the deceleration curve 1
        self.draw_curve(self.decel_points_1, "dec_curve1", "blue")

        # Draw the acceleration curve 2
        self.draw_curve(self.accel_points_2, "acc_curve2", "purple")

        # Draw the deceleration curve 2
        self.draw_curve(self.decel_points_2, "dec_curve2", "purple")

        # Add this in the __init__ method
        self.line_between_curves_1 = self.canvas.create_line(0, 0, 0, 0, fill="blue", width=4)

        # Add this in the __init__ method
        self.line_between_curves_2 = self.canvas.create_line(0, 0, 0, 0, fill="purple", width=4)

        # Usage example for draw_line_between_curves_1
        self.draw_line_between_curves(self.accel_points_1, self.decel_points_1, self.line_between_curves_1)

        # Usage example for draw_line_between_curves_2
        self.draw_line_between_curves(self.accel_points_2, self.decel_points_2, self.line_between_curves_2)

    def init_control_points(self):
        # Initialize control points for acceleration curve (curve1)
        for idx, point in enumerate(self.accel_points_1):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="blue",
                                    tags=(f"acc_curve1_{idx}", "point"))

        # Initialize control points for deceleration curve (curve2)
        for idx, point in enumerate(self.decel_points_1):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="blue",
                                    tags=(f"dec_curve1_{idx}", "point"))

        for idx, point in enumerate(self.accel_points_2):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="purple",
                                    tags=(f"acc_curve2_{idx}", "point"))

        # Initialize control points for deceleration curve (curve2)
        for idx, point in enumerate(self.decel_points_2):
            canvas_y = self.adjust_y(point[1])
            canvas_x = self.adjust_x(point[0])
            self.canvas.create_oval(canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10, fill="purple",
                                    tags=(f"dec_curve2_{idx}", "point"))

    def update_point_position_text(self):
        # Update the StringVar with the current positions of the display_accel_points
        accel_positions_1 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_accel_points_1])
        self.accel_points_1_text.set(f"Accel Points Blue: {accel_positions_1}")

        # Update the StringVar with the current positions of the display_decel_points
        decel_positions_1 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_decel_points_1])
        self.decel_points_1_text.set(f"Decel Points Blue: {decel_positions_1}")

        # Update the StringVar with the current positions of the display_accel_points
        accel_positions_2 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_accel_points_2])
        self.accel_points_2_text.set(f"Accel Points Purple: {accel_positions_2}")

        # Update the StringVar with the current positions of the display_decel_points
        decel_positions_2 = ', '.join([f"({x:.1f}, {y:.1f})" for x, y in self.display_decel_points_2])
        self.decel_points_2_text.set(f"Decel Points Purple: {decel_positions_2}")

    def update_display_control_points(self):
        # Calculate the scaling factor based on the change in the final point's values
        x_scale_factor = int(self.last_x_entry.get()) / self.x_upper_bound if self.x_upper_bound != 0 else 1
        y_scale_factor = int(self.last_y_entry.get()) / self.y_upper_bound if self.y_upper_bound != 0 else 1

        # Apply the scaling factor to the internal control points
        self.display_accel_points_1 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.accel_points_1]
        self.display_decel_points_1 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.decel_points_1]
        self.display_accel_points_2 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.accel_points_2]
        self.display_decel_points_2 = [(x * x_scale_factor, y * y_scale_factor) for x, y in self.decel_points_2]


        # Update the label text to display the new scaled control points
        self.update_point_position_text()

    def adjust_y(self, v):
        return self.frame_size_y - v - self.padding_y # Assuming canvas height is 600

    def adjust_x(self, t):
        return t+self.padding_x

    def on_point_click(self, event):
        # Get the closest point to the click
        self.selected_point = self.canvas.find_closest(event.x, event.y)
        # Determine which curve the point belongs to based on tags
        tags = self.canvas.gettags(self.selected_point)
        if "acc_curve1" in tags:
            self.selected_curve = "acc_curve1"
        elif "dec_curve1" in tags:
            self.selected_curve = "dec_curve1"
        if "acc_curve2" in tags:
            self.selected_curve = "acc_curve2"
        elif "dec_curve2" in tags:
            self.selected_curve = "dec_curve2"
        else:
            self.selected_curve = None

    def on_point_drag(self, event):
        # Get the tags for the selected point
        tags = self.canvas.gettags(self.selected_point)

        # Check if any of the tags indicate which curve the point belongs to
        selected_curve = None
        for tag in tags:
            if tag.startswith("acc_curve1_"):
                selected_curve = "acc_curve1"
                break
            elif tag.startswith("dec_curve1_"):
                selected_curve = "dec_curve1"
                break
            elif tag.startswith("acc_curve2_"):
                selected_curve = "acc_curve2"
                break
            elif tag.startswith("dec_curve2_"):
                selected_curve = "dec_curve2"
                break

        # If selected_curve is still None, exit the method
        if selected_curve is None:
            return

        # Extract the index from the tag
        index = int(tags[0].split('_')[2])

        if index == 0 or index == 3:
            if (event.x - self.padding_x < self.y_lower_bound or self.adjust_y(event.y) < self.x_lower_bound
                    or event.x - self.padding_y > self.x_upper_bound or self.adjust_y(event.y) > self.y_upper_bound):
                return

        # Handle dragging for the specific curve
        if selected_curve == "acc_curve1":
            # Logic for updating acceleration points
            self.update_points(event, index, self.accel_points_1, "acc_curve1", "blue", self.draw_line_between_curves_1)
            self.draw_curve(self.accel_points_1, "acc_curve1", "blue")
            self.draw_line_between_curves(self.accel_points_1, self.decel_points_1, self.line_between_curves_1)
            self.update_display_control_points()
        elif selected_curve == "dec_curve1":
            # Logic for updating deceleration points
            self.update_points(event, index, self.decel_points_1, "dec_curve1", "blue", self.draw_line_between_curves_1)
            self.draw_curve(self.decel_points_1, "dec_curve1", "blue")
            self.draw_line_between_curves(self.accel_points_1, self.decel_points_1, self.line_between_curves_1)
            self.update_display_control_points()
        elif selected_curve == "acc_curve2":
            # Logic for updating deceleration points
            self.update_points(event, index, self.accel_points_2, "acc_curve2", "purple",
                               self.draw_line_between_curves_2)
            self.draw_curve(self.accel_points_2, "acc_curve2", "purple")
            self.draw_line_between_curves(self.accel_points_2, self.decel_points_2, self.line_between_curves_2)
            self.update_display_control_points()
        elif selected_curve == "dec_curve2":
            # Logic for updating deceleration points
            self.update_points(event, index, self.decel_points_2, "dec_curve2", "purple",
                               self.draw_line_between_curves_2)
            self.draw_curve(self.decel_points_2, "dec_curve2", "purple")
            self.draw_line_between_curves(self.accel_points_2, self.decel_points_2, self.line_between_curves_2)
            self.update_display_control_points()

    def draw_line_between_curves(self, accel_points, decel_points, line_between):
        # Get the last point of the acceleration curve
        last_accel_point = accel_points[-1]
        # Get the first point of the deceleration curve
        first_decel_point = decel_points[0]

        # Convert coordinates to canvas coordinates
        last_accel_canvas = (self.adjust_x(last_accel_point[0]), self.adjust_y(last_accel_point[1]))
        first_decel_canvas = (self.adjust_x(first_decel_point[0]), self.adjust_y(first_decel_point[1]))

        # Update the line's coordinates
        self.canvas.coords(line_between, last_accel_canvas[0], last_accel_canvas[1], first_decel_canvas[0],
                           first_decel_canvas[1])

    def draw_line_between_curves_1(self):
        # Get the last point of the acceleration curve (curve1)
        last_accel_point = self.accel_points_1[-1]
        # Get the first point of the deceleration curve (curve2)
        first_decel_point = self.decel_points_1[0]

        # Convert coordinates to canvas coordinates
        last_accel_canvas = (self.adjust_x(last_accel_point[0]), self.adjust_y(last_accel_point[1]))
        first_decel_canvas = (self.adjust_x(first_decel_point[0]), self.adjust_y(first_decel_point[1]))

        # Update the line's coordinates
        self.canvas.coords(self.line_between_curves_1, last_accel_canvas[0], last_accel_canvas[1], first_decel_canvas[0],
                           first_decel_canvas[1])

    def draw_line_between_curves_2(self):
        # Get the last point of the acceleration curve (curve1)
        last_accel_point = self.accel_points_2[-1]
        # Get the first point of the deceleration curve (curve2)
        first_decel_point = self.decel_points_2[0]

        # Convert coordinates to canvas coordinates
        last_accel_canvas = (self.adjust_x(last_accel_point[0]), self.adjust_y(last_accel_point[1]))
        first_decel_canvas = (self.adjust_x(first_decel_point[0]), self.adjust_y(first_decel_point[1]))

        # Update the line's coordinates
        self.canvas.coords(self.line_between_curves_2, last_accel_canvas[0], last_accel_canvas[1], first_decel_canvas[0],
                           first_decel_canvas[1])

    def update_points(self, event, index, points, curve_tag, color, line_between_func):
        if 0 <= index < len(points):
            adjusted_y = self.adjust_y(event.y)
            points[index] = (event.x - self.padding_x, adjusted_y)
            # Update the visual representation of the control point
            self.canvas.coords(f"{curve_tag}_{index}", event.x - 10, event.y - 10, event.x + 10, event.y + 10)
        self.draw_curve(points, curve_tag, color)
        line_between_func()

    def draw_curve(self, points, curve_tag, color):
        self.canvas.delete(curve_tag)  # Delete the old curve

        # Drawing logic for the curve
        curve_points = []
        for i in range(0, 1001, 5):
            t = i / 1000
            x, y = self.calculate_bezier(t, points)  # Pass points
            curve_points.extend([self.adjust_x(x), self.adjust_y(y)])

        # Draw the new Bezier curve with the specified tag and color
        self.canvas.create_line(*curve_points, fill=color, tags=curve_tag, width=4)

    def calculate_bezier_points(self, control_points):
        curve_points = []
        for t in self.frange(0, 1, 0.01):
            x, y = self.calculate_bezier_point(t, control_points)
            curve_points.append((self.adjust_x(x), self.adjust_y(y)))
        return curve_points

    def binomial_coefficient(self, n, k):
        # Calculate the binomial coefficient
        return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))

    def calculate_bezier(self, t, points):
        # points is either self.accel_points or self.decel_points
        x = 0
        y = 0
        n = len(points) - 1
        for i, point in enumerate(points):
            B = (pow(1 - t, n - i) * pow(t, i)) * self.combination(n, i)
            x += point[0] * B
            y += point[1] * B
        return x, y

    def combination(self, n, k):
        from math import factorial
        return factorial(n) / (factorial(k) * factorial(n - k))

    def draw_grid(self, spacing=50):
        # Draw horizontal grid lines
        for i in range(2*spacing, self.frame_size_y-spacing, spacing):
            self.canvas.create_line(self.padding_x, i, self.frame_size_x - self.padding_x, i, fill="#ddd")

        # Draw vertical grid lines
        for i in range(2*spacing, self.frame_size_x-spacing, spacing):
            self.canvas.create_line(i, self.padding_y, i, self.frame_size_y - self.padding_y, fill="#ddd")

        # Draw horizontal grid lines at the upper and lower bounds
        #self.canvas.create_line(self.padding_x, self.padding_y, self.frame_size_x - self.padding_x, self.padding_y, fill="#ddd")
        #self.canvas.create_line(self.padding_x, self.frame_size_y - self.padding_y, self.frame_size_x - self.padding_x, self.frame_size_y - self.padding_y, fill="#ddd")

        # Draw the x and y axes
        self.canvas.create_line(self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_lower_bound),
                                self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_lower_bound), width=4)  # x-axis
        self.canvas.create_line(self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_upper_bound),
                                self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_upper_bound), width=4)  # x-axis
        self.canvas.create_line(self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_lower_bound),
                                self.adjust_x(self.x_lower_bound), self.adjust_y(self.y_upper_bound), width=4)  # y-axis
        self.canvas.create_line(self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_lower_bound),
                                self.adjust_x(self.x_upper_bound), self.adjust_y(self.y_upper_bound), width=4)  # y-axis
        # Label the x and y axes
        self.canvas.create_text(self.adjust_x(self.x_upper_bound/2), self.adjust_y(-20),
                                text="Time (ms)", font=("Arial", 20, "bold"))
        self.canvas.create_text(self.adjust_x(-20), self.adjust_y(self.y_upper_bound/2),
                                angle=90, text="Velocity (Step/s)", font=("Arial", 20, "bold"))

    def save_profile(self):
        # Step 1: Collect and Structure the Data
        profile_data = {
            "name": self.profile_name.get().strip(),
            "accel_points_1": self.display_accel_points_1,
            "decel_points_1": self.display_decel_points_1,
            "accel_points_2": self.display_accel_points_2,
            "decel_points_2": self.display_decel_points_2,
        }
        if not profile_data["name"]:
            print("Profile name is empty. Please enter a valid name.")
            return
        self.database.add_profile(profile_data)  # Use the add_profile method of Database
        print(f"Profile '{profile_data['name']}' saved successfully.")


if __name__ == "__main__":
    root = tk.Tk()

    # Create instances of the MotorControl and ArduinoControl classes
    database_linear = Database("database_linear.json")
    database_bezier = Database("database_bezier.json")
    camera_control = CameraControl()
    arduino_control = ArduinoControl()
    power_meter = PowerMeterControl()
    motor_control = MotorControl(arduino_control, power_meter)

    app = GUIcontrol(root, motor_control, arduino_control, power_meter, camera_control, database_linear, database_bezier)
    root.mainloop()


