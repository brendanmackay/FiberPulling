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
        """Initialize the camera and set the global flag for camera connection."""
        global camera_connected
        global cap

        camera_connected = False
        cap = cv2.VideoCapture(1)  # attempt to capture video from the digital microscope

        if cap.isOpened():  # check if we successfully opened the camera
            camera_connected = True
        else:
            print("No camera found or unable to connect to camera!")

    def create_blank_image(self, width, height):
        """Create a blank white image of given dimensions."""
        blank_img = np.ones((height, width, 4), dtype=np.uint8) * 255  # 4 channels: RGBA
        return blank_img

    def show_feed(self):
        """Capture and display a frame from the camera (if connected),
        or display a white image if no camera is connected."""
        if camera_connected:
            _, frame = cap.read()
            frame = cv2.flip(frame, 0)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        else:
            cv2image = self.create_blank_image(500, 300)

        img = Image.fromarray(cv2image).resize((500, 300))
        imgtk = ImageTk.PhotoImage(image=img)
        video_frame = tk.Frame(root, width=10, height=10)  # frame for the digital microscope
        video_label = tk.Label(video_frame)  # label for the microscope
        video_label.imgtk = imgtk  # Shows frame for display 1
        video_label.configure(image=imgtk)
        root.after(10, self.show_feed)

    def save_power_meter_data(self):
        # Assuming x_vals and y_vals are defined elsewhere to create mw_time
        mw_time = np.array([self.x_vals, self.y_vals])

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

    def Clear(self):  # clears the plot
        plt.cla()
        self.x_vals.clear()
        self.y_vals.clear()

    def capture_frame(self):
        # Capture a frame from the camera
        print("hi")

    def display_frame(self):
        # Display the captured frame on the GUI
        print("hi")

class PowerMeterControl:

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.dev_name = 'USB0::0x1313::0x8078::P0032080::INSTR'
        self.power_meter = None
        self.connection_status = self.connect()

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
            return self.power_meter.read()
            #return float(self.power_meter.read())
        else:
            return None

    def animate(self, new_time):  # reads the powermeter and updates the graph
        self.x_vals.append(new_time)
        self.y_vals.append(power_meter.read * 1000)
        plt.cla()
        plt.title("Power [mW] as a function of Time[s]")
        plt.xlabel("Time [s]")
        plt.ylabel("Power [mW]")
        plt.grid()

        plt.plot(self.x_vals, self.y_vals)

    def save_power_meter_data(self, data):
        # Save power meter data to a file
        print("hi")

    def get_connection_status(self):
        return self.connection_status

class ArduinoControl:
    def __init__(self):
        self.arduino = None
        self.electrode_state = False  # Initialize the electrode state
        self.connection_status = "Not Connected"  # Initialize status as "Not Connected"
        self.auto_connect()

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

    def refresh_ports(self):
        # Get a list of all available COM ports using pyserial's list_ports method.
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports

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

    def read_from_arduino(self):
        if self.arduino:
            return self.arduino.readline().decode().strip()

    def get_connection_status(self):
        if self.connection_status.startswith("Connected"):
            return True
        else:
            return False

class MotorControl:
    def __init__(self, arduino_control):
        self.arduino_control = arduino_control
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
            print("Knife Down 1000")

    def calibrate_up_knife(self):
        if not self.knife_position: # check if knife is down
            time.sleep(0.1)
            self.arduino_control.send_command('KFUTH\n') # Knife Up Thousand Steps
            self.knife_position = False
            print("Knife Up 1000")

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

    def dimple(self, speed, depth, time_delay):
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


    def automate_dimple(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                     enab_selection, Res1_selection, Res2_selection, prht_entry, dimple_speed, dimple_depth,
                     dimple_time_delay):
        # First, initiate the tapering process
        self.initiate_pulling(Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                              enab_selection, Res1_selection, Res2_selection, prht_entry)
        # Wait for 6 seconds
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
        self.dimple(dimple_speed, dimple_depth, dimple_time_delay)
        while True:
            status = self.arduino_control.read_from_arduino()
            if status == "Dimple complete":
                break
            time.sleep(1)

    def automate_taper(self, Speed1_entry, Speed2_entry, Accel1_entry, Accel2_entry, Decel1_entry, Decel2_entry,
                     enab_selection, Res1_selection, Res2_selection, prht_entry):
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
    def __init__(self, root, motor_control, arduino_control, power_meter):
        self.root = root
        self.root.title("Fiber Pulling App")

        # Store references to the motor control, Arduino control, and power meter instances
        self.motor_control = motor_control
        self.arduino_control = arduino_control
        self.power_meter = power_meter

        # Create and configure the main frame
        main_frame = Frame(self.root)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Set up the protocol for handling window closure
        # self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create and place buttons on GUI
        self.setup_gui()

    def setup_gui(self):
        root.title('Fiber Pulling')
        self.tapering_setup()
        self.dynamic_button_setup()
        self.dimpling_setup()
        self.update_electrode_status()
        self.power_meter_plot_setup()
        self.connection_status_setup()

    def power_meter_plot_setup(self):
        # Setup Matplotlib Plot
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row= 0, column=6, rowspan=10, columnspan=10)

        # Add a title to the plot
        self.ax.set_title("Power Meter Plot")

        # Optionally, if you want to set labels for x and y axes:
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Voltage (mW)")

        # Initial data setup
        self.x_data = np.linspace(0, 10, 100)  # replace with your X axis range
        self.y_data = np.zeros(100)
        self.line, = self.ax.plot(self.x_data, self.y_data)

        # Call animation method (You can adjust the interval as needed)
        self.update_power_meter_plot()

    def update_power_meter_plot(self):
        # Get new data from the power meter
        power = self.power_meter.read_power()
        if power is not None:
            # Shift old data to the left
            self.y_data[:-1] = self.y_data[1:]
            # Append new data to the rightmost side
            self.y_data[-1] = power
            self.line.set_ydata(self.y_data)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()

    def tapering_setup(self):
        # Prepare GUI for Tapering
        Res_options = ["High Resolution", "Mid Resolution", "Low Resolution"]
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

        self.Speed1_label = tk.Label(root, text="Speed Motor 1: ",
                                     font=("Arial", 10))  # Speed 1 labels and entry widgets
        self.s1_def = IntVar()
        self.Speed1_units = tk.Label(root, text="Steps/s", font=("Arial", 10))
        self.Speed1_entry = tk.Entry(root, width=6, text=self.s1_def, font=("Arial", 10))
        self.s1_def.set(38)

        self.Speed2_label = tk.Label(root, text="Speed Motor 2: ",
                                     font=("Arial", 10))  # Speed 2 Labels and entry widgets
        self.s2_def = IntVar()
        self.Speed2_units = tk.Label(root, text="Steps/s", font=("Arial", 10))
        self.Speed2_entry = tk.Entry(root,width=6, text=self.s2_def, font=("Arial", 10))
        self.s2_def.set(930)

        self.Accel1_label = tk.Label(root, text="Acceleration Motor 1: ",
                                     font=("Arial", 10))  # acceleration 1 labels and entry widgets
        self.Accel1_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.A1_def = IntVar()
        self.Accel1_entry = tk.Entry(root, width=6, text=self.A1_def, font=("Arial", 10))
        self.A1_def.set(6)

        self.Decel1_label = tk.Label(root, text="Deceleration Motor 1: ",
                                     font=("Arial", 10))  # deceleration 1 labels and entry widgets
        self.Decel1_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.D1_def = IntVar()
        self.Decel1_entry = tk.Entry(root, width=6, text=self.D1_def, font=("Arial", 10))
        self.D1_def.set(6)

        self.Accel2_label = tk.Label(root, text="Acceleration Motor 2: ",
                                     font=("Arial", 10))  # acceleration 2 labels and entry widgets
        self.Accel2_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.A2_def = IntVar()
        self.Accel2_entry = tk.Entry(root, width=6, text=self.A2_def, font=("Arial", 10))
        self.A2_def.set(160)

        self.Decel2_label = tk.Label(root, text="Deceleration Motor 2: ",
                                     font=("Arial", 10))  # deceleration 1 labels and entry widgets
        self.Decel2_units = tk.Label(root, text="Steps/s\u00b2", font=("Arial", 10))
        self.D2_def = IntVar()
        self.Decel2_entry = tk.Entry(root, width=6, text=self.D2_def, font=("Arial", 10))
        self.D2_def.set(160)

        self.prht_label = tk.Label(root, text="Preheat time:", font=("Arial", 10))  # preheat labels and entry widgets
        self.prht_units = tk.Label(root, text="s", font=("Arial", 10))
        self.prht_def = IntVar()
        self.prht_entry = tk.Entry(root, width=6, text=self.prht_def, font=("Arial", 10))
        self.prht_def.set(0.5)

        self.TimeD_label = tk.Label(root, text="Time Delay:", font=("Arial", 10))  # time delay labels and entry widgets
        self.TimeD_units = tk.Label(root, text="s", font=("Arial", 10))
        self.TD_def = IntVar()
        self.TimeD_entry = tk.Entry(root, width=6, text=self.TD_def, font=("Arial", 10))
        self.TD_def.set(1)

        self.Res1_label.grid(row=1, column=3, padx=5, pady=7)  # resolution 1 widget placements
        self.Res1_entry.grid(row=2, column=3, padx=5, pady=7)

        self.Res2_label.grid(row=3, column=3, padx=5, pady=7)  # resolution 2 widget placements
        self.Res2_entry.grid(row=4, column=3, padx=5, pady=7)

        self.enab_label.grid(row=5, column=3, padx=5, pady=7)  # enable 1 widget placements
        self.enab_entry.grid(row=6, column=3, padx=5, pady=7)


        self.Speed1_label.grid(row=1, column=0, pady=7)  # Speed 1 widget placements
        self.Speed1_units.grid(row=1, column=2, pady=7)
        self.Speed1_entry.grid(row=1, column=1, pady=7)

        self.Speed2_label.grid(row=2, column=0, pady=7)  # Speed 2 widget placements
        self.Speed2_units.grid(row=2, column=2, pady=7)
        self.Speed2_entry.grid(row=2, column=1, pady=7)

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

        self.prht_label.grid(row=7, column=0, pady=7)  # preheat widgets placements
        self.prht_entry.grid(row=7, column=1, pady=7)
        self.prht_units.grid(row=7, column=2, pady=7)

        self.TimeD_label.grid(row=11, column=0, pady=7)  # time delay dimple widgets placements
        self.TimeD_units.grid(row=11, column=2)
        self.TimeD_entry.grid(row=11, column=1, pady=7)

    def dynamic_button_setup(self):
        self.Automate_dimple_button = tk.Button(text="Automate Dimple", font=("Arial", 10),
                                         command=self.automate_dimple_button_pressed)
        self.Automate_taper_button = tk.Button(text="Automate Dimple", font=("Arial", 10),
                                         command=self.automate_taper_button_pressed)
        self.Automate_taper_button = tk.Button(text="Automate Taper", font=("Arial", 10),
                                         command=self.automate_taper_button_pressed)
        self.Run_button = tk.Button(text="Run", font=("Arial", 10), command=self.initiate_pulling_button_pressed)
        self.Emg_button = tk.Button(text="EMERGENCY STOP", command=self.arduino_control.emergency_stop,
                                     bg="red", fg="white",  activebackground="green")
        self.elec_toggle_button = tk.Button(text="electrodes on/off", command=self.toggle_electrode_state_button_pressed
                                            , font=("Arial", 10), activebackground = "cyan")

        self.Reset_button = tk.Button(text="Reset", command=self.motor_control.reset, font=("Arial", 10))
        self.decel_button = tk.Button(text="Decelerate", command=self.motor_control.decelerate)

        self.Center_button = tk.Button(text="Center", command=self.motor_control.center_taper,
                                       font=("Arial", 10))
        self.Dimple_button = tk.Button(text="Dimple", font=("Arial", 10),
                                       command=self.dimple_button_pressed)

        self.Calibrate_button = tk.Button(text="Calibrate Knife", font=("Arial", 10),
                                          command=self.motor_control.calibrate_knife)

        self.Calibrate_up_button = tk.Button(text="Move Knife Up", font=("Arial", 10),
                                          command=self.motor_control.calibrate_up_knife)
        self.Calibrate_down_button = tk.Button(text="Move Knife Down", font=("Arial", 10),
                                             command=self.motor_control.calibrate_down_knife)
        self.Tension_button = tk.Button(text="Tension Fiber", font=("Arial", 10),
                                             command=self.tension_button_pressed)
        # Button placement on GUI
        self.Automate_dimple_button.grid(row=1, column=4)
        self.Automate_taper_button.grid(row=2, column=4)
        self.Center_button.grid(row=3, column=4)
        self.Dimple_button.grid(row=4, column=4)
        self.Reset_button.grid(row=5, column=4)
        self.Tension_button.grid(row=6, column=4)
        self.Calibrate_button.grid(row=7, column=4)
        self.Calibrate_up_button.grid(row=8, column=4)
        self.Calibrate_down_button.grid(row=9, column=4)
        self.Run_button.grid(row=10, column=4)
        self.decel_button.grid(row=11, column=4)

        self.elec_toggle_button.grid(row=9, column=3)
        self.Emg_button.grid(row=8, column=3)

    def dimpling_setup(self):
        # ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # prepare the widgets of the GUI for dimpling
        self.text2 = tk.Label(root, text="Dimpling:", font=(15))
        self.text2.grid(row=8, column=0, pady=7)


        self.Speed3_label = tk.Label(root, text="Speed Motor 3: ",
                                     font=("Arial", 10))  # Speed 3 labels and entry widgets
        self.s3_def = IntVar()
        self.Speed3_units = tk.Label(root, text="Steps/s", font=("Arial", 10))
        self.Speed3_entry = tk.Entry(root, width=6, text=self.s3_def, font=("Arial", 10))
        self.s3_def.set(1000)

        self.Speed3_label.grid(row=9, column=0, pady=7)  # Speed 3 widget placements
        self.Speed3_units.grid(row=9, column=2, pady=7)
        self.Speed3_entry.grid(row=9, column=1, pady=7)

        self.Depth_selection = IntVar()  # resolution 3 labels and option menu widgets
        self.Depth_selection.set(20)
        self.Depth_label = tk.Label(root, text="Dimple depth: ", font=("Arial", 10))
        self.Depth_entry = tk.Entry(root, width=6, text=self.Depth_selection, font=("Arial", 10))
        self.Depth_units = tk.Label(root, text="Steps", font=("Arial", 10))



        self.Depth_label.grid(row=10, column=0, padx=5, pady=7)  # resolution 1 widget placements
        self.Depth_entry.grid(row=10, column=1, padx=5, pady=7)
        self.Depth_units.grid(row=10, column=2, padx=5, pady=7)

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

        self.microscope_connection = "Microscope Not Connected"

        # Create and place labels for connection status directly in the main frame
        arduino_status_label = Label(self.root, text=self.arduino_connection, bg=arduino_bg)
        arduino_status_label.grid(row=0, column=0)

        power_meter_status_label = Label(self.root, text=self.power_meter_connection, bg=power_meter_bg)
        power_meter_status_label.grid(row=0, column=1, columnspan=2)

        microscope_status_label = Label(self.root, text=self.microscope_connection, bg="red")
        microscope_status_label.grid(row=0, column=3, columnspan=2)

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
        speed = self.s3_def.get()
        depth = self.Depth_selection.get()
        time_delay = self.TD_def.get()

        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return

        thread = threading.Thread(target=self.motor_control.dimple, args=(
            speed, depth, time_delay))
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

        dimple_speed = self.s3_def.get()
        dimple_depth = self.Depth_selection.get()
        dimple_time_delay = self.TD_def.get()

        # Check if Arduino is connected before performing dimple
        if self.arduino_control.get_connection_status() == "Not Connected":
            print("Error", "Arduino is not connected.")
            return

        thread = threading.Thread(target=self.motor_control.automate_dimple, args=(Speed1_entry, Speed2_entry, Accel1_entry,
                                    Accel2_entry, Decel1_entry, Decel2_entry, enab_selection, Res1_selection,
                                    Res2_selection, prht_entry, dimple_speed, dimple_depth, dimple_time_delay))
        thread.start()

    def automate_taper_button_pressed(self):
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

    def refresh_ports(self):
        # Call the ArduinoControl's refresh_ports method to get the list of ports
        ports = self.arduino_control.refresh_ports()

        # Reset the default value of the dropdown menu to 'Select port'.
        self.port_var.set('Select port')

        # Clear all current options in the dropdown menu.
        self.port_dropdown["menu"].delete(0, "end")

        # For each available port, add it as an option in the dropdown menu.
        for p in ports:
            self.port_dropdown["menu"].add_command(label=p, command=tk._setit(self.port_var, p))


    '''def on_closing(self):
        try:
            self.motor_control.move_to_home_position()
            self.arduino_control.send_command('EXIT\n')
            self.root.destroy()
        except Exception as e:
            # Handle the exception gracefully, e.g., print an error message
            print(f"An error occurred during closing: {str(e)}")
            ''' # Resets to home when closed

if __name__ == "__main__":
    root = tk.Tk()

    # Create instances of the MotorControl and ArduinoControl classes
    arduino_control = ArduinoControl()
    motor_control = MotorControl(arduino_control)
    power_meter = PowerMeterControl()

    app = SetupGUI(root, motor_control, arduino_control, power_meter)
    root.mainloop()


