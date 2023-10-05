#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#live updating graph works in this one, opens power meter
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

class CameraControl:
    def __init__(self):
        # Initialize camera here, if applicable
        print("HI")

    def init_camera(self):
        # Initialize camera and set up configurations
        print("hi")

    def capture_frame(self):
        # Capture a frame from the camera
        print("hi")

    def display_frame(self):
        # Display the captured frame on the GUI
        print("hi")

class PowerMeterControl:
    def __init__(self):
        # Initialize power meter connection here, if applicable
        print("hi")
    def connect_power_meter(self):
        # Establish a connection to the power meter
        print("hi")


    def read_power_meter(self):
        # Read power meter data
        print("hi")

    def save_power_meter_data(self, data):
        # Save power meter data to a file
        print("hi")

class ArduinoControl:
    def __init__(self):
        self.arduino = None
        self.electrode_state = False  # Initialize the electrode state
        self.connection_status = "Not Connected"  # Initialize status as "Not Connected"
        self.auto_connect()

    def toggle_electrodes_state(self):
        if self.electrode_state:
            self.electrode_state = False
            self.send_command('RLY_OF\n')
        else:
            self.electrode_state = True
            self.send_command('RLY_ON\n')

        print(self.electrode_state)


    def connect_arduino(self, selected_port):
        if selected_port != 'Select port':
            try:
                self.arduino = serial.Serial(selected_port, 9600)
                self.connection_status = f"Connected to {selected_port}"
            except Exception as e:
                self.connection_status = "Select a valid port"
        else:
            self.connection_status = "Select a valid port"

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

    def read_data(self):
        if self.arduino:
            return self.arduino.readline().decode().strip()

    def get_connection_status(self):
        return self.connection_status

class MotorControl:
    def __init__(self, arduino_control):
        self.arduino_control = arduino_control

    def move_motors(self, motor_speed, motor_acceleration):
        # Logic for moving motors with specified speed and acceleration
        # Example: Send a command to the Arduino to control motors
        command = f"MOVE {motor_speed} {motor_acceleration}\n"
        self.arduino_control.send_command(command)

    def stop_motors(self):
        # Logic for stopping the motors
        # Example: Send a command to the Arduino to stop motors
        command = "STOP\n"
        self.arduino_control.send_command(command)


    def center_taper(self):
        # Logic for centering the taper between electrodes
        # Example: Send a command to the Arduino to center the taper
        command = "CENTER_TAPER\n"
        self.arduino_control.send_command(command)

    def initiate_pulling(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, enab_selection,
                                            Res1_selection, Res2_selection, prht_entry):
        Speed1 = 'SETSP_1' + str(Speed1_entry) + '\n'
        Speed2 = 'SETSP_2' + str(Speed2_entry) + '\n'
        Accel1 = 'SETAC_1' + str(Accel1_entry) + '\n'
        Accel2 = 'SETAC_2' + str(Accel2_entry) + '\n'

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

        prht_s = float(str(prht_entry))
        prht = 'prht' + str(int(prht_s * 1000)) + '\n'

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

    def dimple_taper(self, speed, depth, time_delay):
        # Implement the logic to dimple the taper using motor controls
        # You can use the 'speed', 'depth', and 'time_delay' parameters here
        Speed3 = 'SETSP_3' + str(speed) + '\n'
        Depth_val = 'DIMPL' + str(depth) + '\n'
        TimeD_s = 'TIME' + str(time_delay * 1000) + '\n'

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


class SetupGUI:
    def __init__(self, root, motor_control, arduino_control):
        self.root = root
        self.root.title("Fiber Pulling App")

        # Store references to the motor control and Arduino control instances
        self.motor_control = motor_control
        self.arduino_control = arduino_control


        # Create and configure the main frame
        main_frame = Frame(self.root)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Configure the grid layout
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Create and place buttons on GUI
        self.old_GUI()

    def old_GUI(self):
        root.title('Fiber Pulling')

        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # prepare the widgets of the GUI for tapering
        Res_options = ["High Resolution",
                       "Mid Resolution",  # resolution options
                       "Low Resolution"]

        self.text1 = tk.Label(root, text="Tapering:", font=(15))

        self.timer_Label = tk.Label(root, text="Time Elapsed:")  # timer
        self.timer_time = tk.Label(root, text="0.0s")

        self.Res1_selection = tk.StringVar()  # resoution 1 labels and option menu
        self.Res1_selection.set(Res_options[0])
        self.Res1_label = tk.Label(root, text="Resolution Motor 1: ", font=("Arial", 10))
        self.Res1_entry = tk.OptionMenu(root, self.Res1_selection, *Res_options)
        self.Res1_entry['menu'].configure(font=('Arial', 10))

        self.Res2_selection = tk.StringVar()  # resolution 2 labels and option menu
        self.Res2_selection.set(Res_options[1])
        self.Res2_label = tk.Label(root, text="Resolution Motor 2: ", font=("Arial", 10))
        self.Res2_entry = tk.OptionMenu(root, self.Res2_selection, *Res_options)
        self.Res2_entry['menu'].configure(font=('Arial', 10))

        self.enab_options = ["Yes", "No"]  # enable options

        self.enab_selection = tk.StringVar()  # enable label and option menu
        self.enab_selection.set(self.enab_options[0])
        self.enab_label = tk.Label(root, text="Enable Motors?: ", font=("Arial", 10))
        self.enab_entry = tk.OptionMenu(root, self.enab_selection, *self.enab_options)

        self.Speed1_label = tk.Label(root, text="Speed Motor 1: ", font=("Arial", 10))  # Speed 1 labels and entry widgets
        self.s1_def = IntVar()
        self.Speed1_units = tk.Label(root, text="Steps/s", font=("Arial", 10))
        self.Speed1_entry = tk.Entry(root, text=self.s1_def, font=("Arial", 10))
        self.s1_def.set(38)

        self.Speed2_label = tk.Label(root, text="Speed Motor 2: ", font=("Arial", 10))  # Speed 2 Labels and entry widgets
        self.s2_def = IntVar()
        self.Speed2_units = tk.Label(root, text="Steps/s", font=("Arial", 10))
        self.Speed2_entry = tk.Entry(root, text=self.s2_def, font=("Arial", 10))
        self.s2_def.set(930)

        self.Accel1_label = tk.Label(root, text="Acceleration Motor 1: ",
                                font=("Arial", 10))  # acceleration 1 labels and entry widgets
        self.Accel1_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.A1_def = IntVar()
        self.Accel1_entry = tk.Entry(root, text=self.A1_def, font=("Arial", 10))
        self.A1_def.set(6)

        self.Decel1_label = tk.Label(root, text="Deceleration Motor 1: ",
                                font=("Arial", 10))  # deceleration 1 labels and entry widgets
        self.Decel1_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.D1_def = IntVar()
        self.Decel1_entry = tk.Entry(root, text=self.D1_def, font=("Arial", 10))
        self.D1_def.set(6)

        self.Accel2_label = tk.Label(root, text="Acceleration Motor 2: ",
                                font=("Arial", 10))  # acceleration 2 labels and entry widgets
        self.Accel2_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.A2_def = IntVar()
        self.Accel2_entry = tk.Entry(root, text=self.A2_def, font=("Arial", 10))
        self.A2_def.set(160)

        self.Decel2_label = tk.Label(root, text="Deceleration Motor 2: ",
                                font=("Arial", 10))  # deceleration 1 labels and entry widgets
        self.Decel2_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.D2_def = IntVar()
        self.Decel2_entry = tk.Entry(root, text=self.D2_def, font=("Arial", 10))
        self.D2_def.set(160)

        self.prht_label = tk.Label(root, text="Preheat time:", font=("Arial", 10))  # preheat labels and entry widgets
        self.prht_units = tk.Label(root, text="s", font=("Arial", 10))
        self.prht_def = IntVar()
        self.prht_entry = tk.Entry(root, text=self.prht_def, font=("Arial", 10))
        self.prht_def.set(0.8)

        self.TimeD_label = tk.Label(root, text="Time Delay:", font=("Arial", 10))  # time delay labels and entry widgets
        self.TimeD_units = tk.Label(root, text="s", font=("Arial", 10))
        self.TD_def = IntVar()
        self.TimeD_entry = tk.Entry(root, text=self.TD_def, font=("Arial", 10))
        self.TD_def.set(1)

        self.elec_toggle = tk.Button(text="electrodes on/off", command=lambda: arduino_control.toggle_electrodes_state(),
            font=("Arial", 10))

        self.Automate_button = tk.Button(text="Automate Dimple", font=("Arial", 10))

        self.Run_button = tk.Button(text="Run",font=("Arial", 10), command=self.initiate_pulling_button_pressed)
        self.Emg_button = tk.Button(text="EMERGENCY STOP",)
        self.Reset_button = tk.Button(text="Reset",
                                 font=("Arial", 10))
        self.decel_button = tk.Button(text="Decelerate")

        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # prepare the widgets of the GUI for dimpling

        self.text2 = tk.Label(root, text="Dimpling:", font=(15))

        self.Speed3_label = tk.Label(root, text="Speed Motor 3: ", font=("Arial", 10))  # Speed 1 labels and entry widgets
        self.s3_def = IntVar()
        self.Speed3_units = tk.Label(root, text="Steps/s", font=("Arial", 10))
        self.Speed3_entry = tk.Entry(root, text=self.s3_def, font=("Arial", 10))
        self.s3_def.set(1000)

        self.Depth_selection = IntVar()  # resolution 3 labels and option menu widgets
        self.Depth_selection.set(20)
        self.Depth_label = tk.Label(root, text="Dimple depth: ", font=("Arial", 10))
        self.Depth_entry = tk.Entry(root, text=self.Depth_selection, font=("Arial", 10))
        self.Depth_units = tk.Label(root, text="Steps", font=("Arial", 10))

        self.Center_button = tk.Button(text="Center",
                                  font=("Arial", 10))
        self.Dimple_button = tk.Button(root, text="Dimple", font=("Arial", 10), command=self.dimple_taper_button_pressed)


        # Create buttons for connecting to arduino
        self.refresh_button = tk.Button(root, text="Refresh Ports")
        self.connection_status_label = tk.Label(root)
        self.connect_button = tk.Button(root, text="Connect to Arduino")
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # grid spacing for all the widgets

        self.text1.grid(row=0, column=0, padx=10, pady=7)
        self.text2.grid(row=10, column=0, pady=7)

        self.Speed1_label.grid(row=1, column=0, pady=7)  # Speed 1 widget placements
        self.Speed1_units.grid(row=1, column=2, pady=7)
        self.Speed1_entry.grid(row=1, column=1, pady=7)

        self.Speed2_label.grid(row=2, column=0, pady=7)  # Speed 2 widget placements
        self.Speed2_units.grid(row=2, column=2, pady=7)
        self.Speed2_entry.grid(row=2, column=1, pady=7)

        self.Speed3_label.grid(row=11, column=0, pady=7)  # Speed 3 widget placements
        self.Speed3_units.grid(row=11, column=2, pady=7)
        self.Speed3_entry.grid(row=11, column=1, pady=7)

        self.Accel1_label.grid(row=3, column=0, pady=7)  # acceleration 1 widget placements
        self.Accel1_units.grid(row=3, column=2)
        self.Accel1_entry.grid(row=3, column=1, pady=7)

        self.Accel2_label.grid(row=4, column=0, pady=7)  # Acceleration 2 widget placements
        self.Accel2_units.grid(row=4, column=2)
        self.Accel2_entry.grid(row=4, column=1, pady=7)

        self.Decel1_label.grid(row=5, column=0, pady=7)  # Deceleration 1 widget placements
        self.Decel1_units.grid(row=5, column=2)
        self.Decel1_entry.grid(row=5, column=1, pady=7)

        self.Decel2_label.grid(row=6, column=0, pady=7)  # Acceleration 2 widget placements
        self.Decel2_units.grid(row=6, column=2)
        self.Decel2_entry.grid(row=6, column=1, pady=7)

        self.Res1_label.grid(row=1, column=3, padx=5, pady=7)  # resolution 1 widget placements
        self.Res1_entry.grid(row=1, column=4, padx=5, pady=7)

        self.Res2_label.grid(row=2, column=3, padx=5, pady=7)  # resolution 2 widget placements
        self.Res2_entry.grid(row=2, column=4, padx=5, pady=7)

        self.Depth_label.grid(row=12, column=0, padx=5, pady=7)  # resolution 1 widget placements
        self.Depth_entry.grid(row=12, column=1, padx=5, pady=7)
        self.Depth_units.grid(row=12, column=2, padx=5, pady=7)

        self.enab_label.grid(row=3, column=3, padx=5, pady=7)  # enable 1 widget placements
        self.enab_entry.grid(row=3, column=4, padx=5, pady=7)

        self.timer_Label.grid(row=7, column=3)  # timer widget placements
        self.timer_time.grid(row=7, column=4)

        self.TimeD_label.grid(row=13, column=0, pady=7)  # time delay dimple widgets placements
        self.TimeD_units.grid(row=13, column=2)
        self.TimeD_entry.grid(row=13, column=1, pady=7)

        self.prht_label.grid(row=7, column=0, pady=7)  # preheat widgets placements
        self.prht_entry.grid(row=7, column=1, pady=7)
        self.prht_units.grid(row=7, column=2, pady=7)

        self.connect_button.grid(row=4, column=5, padx=5, pady=7)
        self.refresh_button.grid(row=5, column=4, padx=5, pady=7)
        self.connection_status_label.grid(row=5, column=5, padx=5, pady=7)

        self.Run_button.grid(row=9, column=1, padx=15, pady=7)  # button widget placements
        self.Emg_button.grid(row=10, column=4, rowspan=3, columnspan=2, padx=10, pady=7)
        self.Reset_button.grid(row=9, column=0, padx=15, pady=7)
        self.elec_toggle.grid(row=6, column=4)
        self.Center_button.grid(row=14, column=1, pady=7)
        self.Dimple_button.grid(row=14, column=3, pady=7)
        self.Automate_button.grid(row=14, column=5, pady=7)
        self.decel_button.grid(row=9, column=3, pady=7)

    def dimple_taper_button_pressed(self):
        speed = self.s3_def.get()
        depth = self.Depth_selection.get()
        time_delay = self.TD_def.get()

        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return

        # Call the dimple_taper method in MotorControl
        self.motor_control.dimple_taper(speed, depth, time_delay)

    def initiate_pulling_button_pressed(self):
        Speed1_entry = self.Speed1_entry.get()
        Speed2_entry = self.Speed2_entry.get()
        Accel1_entry = self.Accel1_entry.get()
        Accel2_entry = self.Accel2_entry.get()
        enab_selection = self.enab_selection.get()
        Res1_selection = self.Res1_selection.get()
        Res2_selection = self.Res2_selection.get()
        prht_entry = self.prht_entry.get()

        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return
        self.motor_control.initiate_pulling(Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, enab_selection, Res1_selection, Res2_selection, prht_entry)
    # Define other methods related to motor control GUI elements


if __name__ == "__main__":
    root = tk.Tk()

    # Create instances of the MotorControl and ArduinoControl classes
    arduino_control = ArduinoControl()
    motor_control = MotorControl(arduino_control)

    app = SetupGUI(root, motor_control, arduino_control)
    root.mainloop()


