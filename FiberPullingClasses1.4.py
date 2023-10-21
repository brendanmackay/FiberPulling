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
        except FileNotFoundError:
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
            print(inst.query("*IDN?"))
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
        # Logic for centering the taper between electrodes
        # Example: Send a command to the Arduino to center the taper
        self.arduino_control.send_command('CENTR\n')
        print('centering')

    def initiate_pulling(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry,Decel2_entry,
                         enab_selection, Res1_selection, Res2_selection, prht_entry):
        Speed1 = 'SETSP_1' + str(Speed1_entry) + '\n'
        Speed2 = 'SETSP_2' + str(Speed2_entry) + '\n'
        Accel1 = 'SETAC_1' + str(Accel1_entry) + '\n'
        Accel2 = 'SETAC_2' + str(Accel2_entry) + '\n'
        Decel1 = 'SETDC_1' + str(Decel1_entry) + '\n'  # acquire deceleration
        Decel2 = 'SETDC_2' + str(Decel2_entry) + '\n'

        enab_val = str(enab_selection)
        if enab_val == "Yes":
            enab1 = 'ENABL_1\n'
            enab2 = 'ENABL_2\n'
            print("Enabled")
        elif enab_val == "No":
            enab1 = 'DISAB_1\n'
            enab2 = 'DISAB_2\n'
            print("Disabled")

        Res1_val = str(Res1_selection)
        Res2_val = str(Res2_selection)

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

        Time = 'GO'

        # Use your ArduinoControl object to send commands
        self.arduino_control.send_command(Speed1)
        time.sleep(0.1)
        self.arduino_control.send_command(Speed2)
        time.sleep(0.1)
        self.arduino_control.send_command(Accel1)
        time.sleep(0.1)
        self.arduino_control.send_command(Accel2)
        time.sleep(0.1)
        self.arduino_control.send_command(Decel1)
        time.sleep(0.1)
        self.arduino_control.send_command(Decel2)
        time.sleep(0.1)
        self.arduino_control.send_command(Res1)
        time.sleep(0.1)
        self.arduino_control.send_command(Res2)
        time.sleep(0.1)
        self.arduino_control.send_command(enab1)
        time.sleep(0.1)
        self.arduino_control.send_command(enab2)
        time.sleep(0.1)
        self.arduino_control.send_command(prht)
        time.sleep(0.1)
        self.arduino_control.send_command(Time)

    def decelerate(self):
        self.arduino_control.send_command('DECEL\n')  # electrodes
        print("Decelerating")

    def dimple(self, speed, depth, heat_time, tension1, tension2):
        # Implement the logic to dimple the taper using motor controls
        # You can use the 'speed', 'depth', and 'time_delay' parameters here
        tension_2 = 'TEN2' + str(tension2) + '\n'
        tension_1 = 'TEN1' + str(tension1) + '\n'
        Speed3 = 'SETSP_3' + str(speed) + '\n'
        Depth_val = 'DIMPL' + str(depth) + '\n'
        TimeD_s = 'TIME' + str(heat_time)+ '\n'
        self.arduino_control.send_command(tension_2)
        time.sleep(0.1)
        self.arduino_control.send_command(tension_1)
        time.sleep(0.1)
        self.arduino_control.send_command(Speed3)  # Removed encode() here
        time.sleep(0.5)
        self.arduino_control.send_command('RESHI_1\n')
        time.sleep(0.1)
        self.arduino_control.send_command('RESHI_2\n')
        time.sleep(0.1)
        self.arduino_control.send_command('RESHI_3\n')
        time.sleep(0.1)
        self.arduino_control.send_command(TimeD_s)  # Removed encode() here
        time.sleep(0.1)
        self.arduino_control.send_command(Depth_val)  # Removed encode() here
        print("Dimpling")


    def automate_dimple(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                        enab_selection, Res1_selection, Res2_selection, prht_entry, dimple_speed, dimple_depth,
                        dimple_heat_time, tension_1, tension_2):

        self.power_meter.clear_power_meter_data()

        # First, initiate the tapering process
        self.initiate_pulling(Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                              enab_selection, Res1_selection, Res2_selection, prht_entry)
        # Wait for 8 seconds
        time.sleep(8)
        self.decelerate()

        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            if status == "Pulling Complete":
                break
            time.sleep(0.1)  # Wait for a short period before checking again

        self.center_taper()

        while True:
            status = self.arduino_control.read_from_arduino()
            if status == "Centered":
                break
            time.sleep(1)

        # self.move_motor_1(speed=50, steps=-20)

        # Dimple the taper
        self.dimple(dimple_speed, dimple_depth, dimple_heat_time, tension_1, tension_2)
        while True:
            status = self.arduino_control.read_from_arduino()
            if status == "Dimple complete":
                break
            time.sleep(1)
        self.power_meter.save_power_meter_data()


    def automate_taper_2(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                     enab_selection, Res1_selection, Res2_selection, prht_entry, waist_time):

        self.power_meter.clear_power_meter_data()

        Speed1 = 'SETSP_1' + str(Speed1_entry) + '\n'
        Speed2 = 'SETSP_2' + str(Speed2_entry) + '\n'
        Accel1 = 'SETAC_1' + str(Accel1_entry) + '\n'
        Accel2 = 'SETAC_2' + str(Accel2_entry) + '\n'
        Decel1 = 'SETDC_1' + str(Decel1_entry) + '\n'  # acquire deceleration
        Decel2 = 'SETDC_2' + str(Decel2_entry) + '\n'

        enab_val = str(enab_selection)
        if enab_val == "Yes":
            enab1 = 'ENABL_1\n'
            enab2 = 'ENABL_2\n'
            print("Enabled")
        elif enab_val == "No":
            enab1 = 'DISAB_1\n'
            enab2 = 'DISAB_2\n'
            print("Disabled")

        Res1_val = str(Res1_selection)
        Res2_val = str(Res2_selection)

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

        perform_taper = 'TAPERL' # This is the linear taper function

        waist_time = "WAIST_T" +str(waist_time)+ '\n'

        # Use your ArduinoControl object to send commands
        self.arduino_control.send_command(Speed1)
        time.sleep(0.1)
        self.arduino_control.send_command(Speed2)
        time.sleep(0.1)
        self.arduino_control.send_command(Accel1)
        time.sleep(0.1)
        self.arduino_control.send_command(Accel2)
        time.sleep(0.1)
        self.arduino_control.send_command(Decel1)
        time.sleep(0.1)
        self.arduino_control.send_command(Decel2)
        time.sleep(0.1)
        self.arduino_control.send_command(Res1)
        time.sleep(0.1)
        self.arduino_control.send_command(Res2)
        time.sleep(0.1)
        self.arduino_control.send_command(enab1)
        time.sleep(0.1)
        self.arduino_control.send_command(enab2)
        time.sleep(0.1)
        self.arduino_control.send_command(prht)
        time.sleep(0.1)
        self.arduino_control.send_command(waist_time)
        time.sleep(0.1)
        self.arduino_control.send_command(perform_taper)

        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            print("Arduino (while loop): ", status)
            if status == "Tapering Complete":

                break
            time.sleep(0.01)  # Wait for a short period before checking again
        self.power_meter.save_power_meter_data()

    def automate_taper(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                     enab_selection, Res1_selection, Res2_selection, prht_entry):

        self.power_meter.clear_power_meter_data()


        # First, initiate the tapering process
        self.initiate_pulling(Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                              enab_selection, Res1_selection, Res2_selection, prht_entry)
        # Wait for 6 seconds
        time.sleep(9)
        self.decelerate()

        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            if status == "Pulling Complete":
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

    def move_motor_2(self, speed, steps):       # This function is broken for some reason
        """
        Moves Motor 1 at the specified speed for a set number of steps.
        Parameters:
        - speed (int): Desired speed for Motor 1.
        - steps (int): Number of steps Motor 1 should move. Positive values for forward movement, negative for backward.
        """
        # Set the speed
        speed_cmd = f"SETSP2_{speed:05}\n"
        self.arduino_control.send_command(speed_cmd)
        time.sleep(0.1)
        print("move")
        # Set the movement direction and steps
        if steps >= 0:
            print("Move forward")
            move_cmd = f"MOVRF_2{steps:05}\n"
        else:
            print("Move back")
            steps = abs(steps)
            move_cmd = f"MOVRB_2{steps:05}\n"

        self.arduino_control.send_command(move_cmd)
        time.sleep(0.1)
        while True:
            status = self.arduino_control.read_from_arduino()  # assuming you have such a method
            print(status)
            if status == "Done":
                break
            time.sleep(0.5)  # Wait for a short period before checking again

class SetupGUI:
    def __init__(self, root, motor_control, arduino_control, power_meter, camera_control, database):
        self.root = root
        self.root.title("Fiber Pulling App")

        # Store references to the motor control, Arduino control, power meter, camera, database
        self.motor_control = motor_control
        self.arduino_control = arduino_control
        self.power_meter = power_meter
        self.camera_control = camera_control
        self.database = database

        # Setup the frames in the GUI
        self.setup_frames()

        # Set up the protocol for handling window closure
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create and place buttons on GUI
        self.setup_gui()

        # Show camera feed
        self.show_camera_feed()

    def setup_gui(self):
        root.title('Fiber Pulling')
        self.tapering_setup()
        self.dynamic_button_setup()
        self.dimpling_setup()
        self.update_electrode_status()
        self.power_meter_plot_setup()
        self.connection_status_setup()
        self.profile_setup()
        self.live_info_setup()
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
        self.profile_frame = tk.Frame(column_frame_1)
        self.profile_frame.grid(row=0, column=0, sticky="nsew")

        self.tapering_frame = tk.Frame(column_frame_1)
        self.tapering_frame.grid(row=1, column=0, sticky="nsew")

        self.dimpling_frame = tk.Frame(column_frame_1)
        self.dimpling_frame.grid(row=2, column=0, sticky="nsew")

        self.live_info_frame = tk.Frame(column_frame_1)
        self.live_info_frame.grid(row=3, column=0, sticky="nsew")

        # Second Column Frame
        self.dynamic_button_frame = tk.Frame(column_frame_2)
        self.dynamic_button_frame.grid(row=0, column=0, sticky="nsew")

        self.power_meter_frame = tk.Frame(column_frame_3, width=400, height=300, bg="grey80")
        self.power_meter_frame.grid(row=0, column=0, sticky="nsew")

        self.camera_frame = tk.Frame(column_frame_3, width=400, height=300, bg="grey90")
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

        # deceleration 1 labels and entry widgets
        Decel1_label = tk.Label(self.tapering_frame, text="Deceleration Motor 1: ", font=("Arial", 10))
        Decel1_units = tk.Label(self.tapering_frame, text="Steps/s\u00b2", font=("Arial", 10))
        self.Decel1_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        # Acceleration 1 labels and entry widgets
        Accel2_label = tk.Label(self.tapering_frame, text="Acceleration Motor 2: ", font=("Arial", 10))
        Accel2_units = tk.Label(self.tapering_frame, text="Steps/s\u00b2", font=("Arial", 10))
        self.Accel2_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

        # deceleration 1 labels and entry widgets
        Decel2_label = tk.Label(self.tapering_frame, text="Deceleration Motor 2: ", font=("Arial", 10))
        Decel2_units = tk.Label(self.tapering_frame, text="Steps/s\u00b2", font=("Arial", 10))
        self.Decel2_entry = tk.Entry(self.tapering_frame, width=6, font=("Arial", 10))

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

        Decel1_label.grid(row=5, column=0, pady=2)  # Deceleration 1 widget placements
        Decel1_units.grid(row=5, column=2)
        self.Decel1_entry.grid(row=5, column=1, pady=2)

        Decel2_label.grid(row=6, column=0, pady=2)  # Acceleration 2 widget placements
        Decel2_units.grid(row=6, column=2)
        self.Decel2_entry.grid(row=6, column=1, pady=2)

        prht_label.grid(row=7, column=0, pady=2)  # preheat widgets placements
        self.prht_entry.grid(row=7, column=1, pady=2)
        prht_units.grid(row=7, column=2, pady=2)

        max_speed_time.grid(row=8, column=0, pady=2)  # preheat widgets placements
        self.max_speed_time_entry.grid(row=8, column=1, pady=2)
        max_speed_time_units.grid(row=8, column=2, pady=2)

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
        self.Automate_dimple_button = tk.Button(self.dynamic_button_frame, text="Automate Dimple", font=("Arial", 10),
                                                command=self.automate_dimple_button_pressed, pady=10)
        self.Automate_taper_button = tk.Button(self.dynamic_button_frame, text="Automate Taper 1", font=("Arial", 10),
                                               command=self.automate_taper_button_pressed, pady=10)
        self.Automate_taper_2_button = tk.Button(self.dynamic_button_frame, text="Automate Taper 2", font=("Arial", 10),
                                               command=self.automate_taper_2_button_pressed, pady=10)

        self.Emg_button = tk.Button(self.dynamic_button_frame, text="EMERGENCY STOP", command=self.arduino_control.emergency_stop,
                                    bg="red", fg="white", activebackground="green", pady=20)
        self.elec_toggle_button = tk.Button(self.dynamic_button_frame, text="electrodes on/off", command=self.toggle_electrode_state_button_pressed
                                            , font=("Arial", 10), activebackground = "cyan", pady=20)

        self.Tension_button = tk.Button(self.dynamic_button_frame, text="Tension Fiber", font=("Arial", 10),
                                        command=self.tension_button_pressed, pady=10)

        self.Fiber_broken_button = tk.Button(self.dynamic_button_frame, text ="Fiber Broken", font = ("Arial", 10),
                                             command =self.arduino_control.fiber_broken, pady=10)
        # Dynamic Button Frame placement
        self.Automate_dimple_button.grid(row=1, column=0, pady=5, sticky="nsew")
        self.Automate_taper_button.grid(row=2, column=0, pady=5,  sticky="nsew")
        self.Tension_button.grid(row=3, column=0, pady=5, sticky="nsew")
        self.Fiber_broken_button.grid(row=4, column=0, pady=5, sticky="nsew")
        self.Automate_taper_2_button.grid(row=7, column=0, pady=5, sticky="nsew")

        self.elec_toggle_button.grid(row=5, column=0, pady=5,  sticky="nsew")
        self.Emg_button.grid(row=6, column=0, pady=5, sticky="nsew")

        # Dimpling Frame Buttons
        self.Reset_button = tk.Button(self.dimpling_frame, text="Reset", command=self.motor_control.reset, font=("Arial", 10)
                                      , padx=10, pady=2)
        self.Center_button = tk.Button(self.dimpling_frame, text="Center", command=self.motor_control.center_taper,
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

    def profile_setup(self):
        # prepare the widgets of the GUI for dimpling
        dimpling_label = tk.Label(self.profile_frame, text="Profiles:", font=(15))
        dimpling_label.grid(row=0, column=0, pady=7)

        # Create a listbox to display profiles
        self.profile_listbox = tk.Listbox(self.profile_frame, width=30, height=5, selectmode=tk.SINGLE)
        self.profile_listbox.grid(row=0, column=0, rowspan=3, padx=10)

        # Load profiles from the database and populate the listbox
        self.load_profiles()

        # Buttons for profile management
        self.load_button = tk.Button(self.profile_frame, text="Load Profile", command=self.load_selected_profile)
        self.load_button.grid(row=0, column=1, padx=10, pady=5)

        self.add_button = tk.Button(self.profile_frame, text="Add Profile", command=self.add_profile)
        self.add_button.grid(row=1, column=1, padx=10, pady=5)

        self.delete_button = tk.Button(self.profile_frame, text="Delete Profile", command=self.delete_profile)
        self.delete_button.grid(row=2, column=1, padx=10, pady=5)

        # Load the last used profile on startup
        last_used_profile = database.get_last_used_profile()
        if last_used_profile:
            self.load_selected_profile(last_used_profile)

    def load_profiles(self):
        # Clear the listbox
        self.profile_listbox.delete(0, tk.END)

        # Get all profiles from the database and add them to the listbox
        profiles = self.database.get_all_profiles()
        for profile in profiles:
            self.profile_listbox.insert(tk.END, profile["name"])

    def load_selected_profile(self, profile_name=None):
        if profile_name is None:
            # Get the selected profile name from the listbox
            selected_profile_name = self.profile_listbox.get(tk.ACTIVE)
        else:
            selected_profile_name = profile_name

        # Update the last used profile and save it to the database
        self.database.set_last_used_profile(selected_profile_name)

        # Find the profile in the database by name
        selected_profile = self.database.find_profile_by_name(selected_profile_name)

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
            self.Decel1_entry.delete(0, tk.END)
            self.Decel1_entry.insert(0, selected_profile["motor_decelerations"][0])
            # Repeat this for other Entry widgets and parameters
            self.Decel2_entry.delete(0, tk.END)
            self.Decel2_entry.insert(0, selected_profile["motor_decelerations"][1])
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

    def add_profile(self):
        # Implement a dialog to add a new profile with parameters and store it in the database
        # After adding, call load_profiles to refresh the listbox
        print("Initiate Code Here")
        pass

    def delete_profile(self):
        # Get the selected profile name from the listbox
        selected_index = self.profile_listbox.curselection()
        if selected_index:
            selected_index = selected_index[0]
            selected_profile_name = self.profile_listbox.get(selected_index)

            # Implement logic to delete the selected profile from the database
            # After deleting, call load_profiles to refresh the listbox

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

    def dimple_button_pressed(self):
        tension_1 = self.Tension_1_entry.get()
        tension_2 = self.Tension_2_entry.get()
        speed = self.Speed3_entry.get()
        depth = self.Dimple_depth_entry.get()
        time_delay = self.Heat_time_entry.get()
        print(type(time_delay), "time delay")
        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return

        thread = threading.Thread(target=self.motor_control.dimple, args=(
            speed, depth, time_delay, tension_1, tension_2))
        thread.start()

    def initiate_pulling_button_pressed(self):
        Speed1_entry = self.Speed1_entry.get()
        Speed2_entry = self.Speed2_entry.get()
        Accel1_entry = self.Accel1_entry.get()
        Accel2_entry = self.Accel2_entry.get()
        Decel1_entry = self.Decel1_entry.get()
        Decel2_entry = self.Decel2_entry.get()
        enab_selection = self.enab_selection.get()
        Res1_selection = self.Res1_selection.get()
        Res2_selection = self.Res2_selection.get()
        prht_entry = self.prht_entry.get()

        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return

        thread = threading.Thread(target=self.motor_control.initiate_pulling, args=(
        Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry, enab_selection,
        Res1_selection, Res2_selection, prht_entry))
        thread.start()

    def automate_dimple_button_pressed(self):
        # begin updating the power meter
        self.update_power_meter_plot_periodically()
        self.update_fiber_loss_periodically()

        """This function performs the entire tapering and dimpling process with the parameters found below."""
        Speed1_entry = self.Speed1_entry.get()
        Speed2_entry = self.Speed2_entry.get()
        Accel1_entry = self.Accel1_entry.get()
        Accel2_entry = self.Accel2_entry.get()
        Decel1_entry = self.Decel1_entry.get()
        Decel2_entry = self.Decel2_entry.get()
        enab_selection = self.enab_selection.get()
        Res1_selection = self.Res1_selection.get()
        Res2_selection = self.Res2_selection.get()
        prht_entry = self.prht_entry.get()

        dimple_speed = self.Speed3_entry.get()
        dimple_depth = self.Dimple_depth_entry.get()
        dimple_heat_time = self.Heat_time_entry.get()

        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return


        thread = threading.Thread(target=self.motor_control.automate_dimple, args=(Speed1_entry, Speed2_entry, Accel1_entry,
                                    Accel2_entry, Decel1_entry, Decel2_entry, enab_selection, Res1_selection,
                                    Res2_selection, prht_entry, dimple_speed, dimple_depth, dimple_heat_time))
        thread.start()

    def automate_taper_button_pressed(self):
        # Update the power meter
        self.update_power_meter_plot_periodically()


        Speed1_entry = self.Speed1_entry.get()
        Speed2_entry = self.Speed2_entry.get()
        Accel1_entry = self.Accel1_entry.get()
        Accel2_entry = self.Accel2_entry.get()
        Decel1_entry = self.Decel1_entry.get()
        Decel2_entry = self.Decel2_entry.get()
        enab_selection = self.enab_selection.get()
        Res1_selection = self.Res1_selection.get()
        Res2_selection = self.Res2_selection.get()
        prht_entry = self.prht_entry.get()


        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return

        thread = threading.Thread(target=self.motor_control.automate_taper, args=(Speed1_entry, Speed2_entry, Accel1_entry,
                                                                            Accel2_entry, Decel1_entry, Decel2_entry,
                                                                            enab_selection, Res1_selection,
                                                                            Res2_selection, prht_entry))
        thread.start()

    def automate_taper_2_button_pressed(self):
        # Update the power meter
        self.update_power_meter_plot_periodically()

        Speed1_entry = self.Speed1_entry.get()
        Speed2_entry = self.Speed2_entry.get()
        Accel1_entry = self.Accel1_entry.get()
        Accel2_entry = self.Accel2_entry.get()
        Decel1_entry = self.Decel1_entry.get()
        Decel2_entry = self.Decel2_entry.get()
        enab_selection = self.enab_selection.get()
        Res1_selection = self.Res1_selection.get()
        Res2_selection = self.Res2_selection.get()
        prht_entry = self.prht_entry.get()
        waist_time = self.max_speed_time_entry.get()

        print("Taper 2 Pressed")
        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return

        thread = threading.Thread(target=self.motor_control.automate_taper_2,
                                  args=(Speed1_entry, Speed2_entry, Accel1_entry,
                                        Accel2_entry, Decel1_entry, Decel2_entry,
                                        enab_selection, Res1_selection,
                                        Res2_selection, prht_entry, waist_time))
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

if __name__ == "__main__":
    root = tk.Tk()

    # Create instances of the MotorControl and ArduinoControl classes
    database = Database("database.json")
    camera_control = CameraControl()
    arduino_control = ArduinoControl()
    power_meter = PowerMeterControl()
    motor_control = MotorControl(arduino_control, power_meter)

    app = SetupGUI(root, motor_control, arduino_control, power_meter, camera_control, database)
    root.mainloop()


