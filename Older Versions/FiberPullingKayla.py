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
matplotlib.use('Agg')
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import random
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)


def Timer_Stop():  # sets the event, which causes the timer to stop, and returns the run button to it's original colour
    event_2.set()
    Run_button.config(bg=defaultbg)


def Reset():  # sends command to arduino to return motors to home position
    time.sleep(0.1)
    serCom1.write(b'HOME\n')
    print("Reseting")


def Emg_stop():  # emergency stop, commands all motors to stop, turns of electrodes
    Timer_Stop()
    serCom1.write(b'EMG_STP\n')
    app = tk.Tk()
    app.title("Emergency Stop")

    app_label = tk.Label(app, text="Emergency Stop Activated")
    app_label.pack()

    app_button = tk.Button(app, text="ok", command=app.destroy)
    app_button.pack()

    print("Stop")


def Decel():  # sends command to arduino to bring the motors to a stop with the given parameters and turn off the
    serCom1.write(b'DECEL\n')  # electrodes
    print("decelerating")


def elec_state():  # write command to serial port to turn electrodes on/off toggle state
    global electrode_state
    if elecState == True:
        elecState = False
        elec_toggle.config(bg=defaultbg)
        serCom1.write(b'RLY_OF\n')

    else:
        elecState = True
        elec_toggle.config(bg="Green")
        serCom1.write(b'RLY_ON\n')

    print(elecState)


def Center():  # write command to serial port to center the taper between the electrodes
    serCom1.write(b'CENTR\n')
    print('centering')


def Dimple():  # write command to serial port to dimple the taper
    Speed3 = 'SETSP_3' + Speed3_entry.get() + '\n'  # acquire speed
    Depth_val = 'DIMPL' + str(float(Depth_entry.get())) + '\n'  # get the depth input
    TimeD_s = 'TIME' + str(float(TimeD_entry.get()) * 1000) + '\n'  # get time input

    time.sleep(0.1)
    serCom1.write(Speed3.encode())
    time.sleep(0.5)
    print(Speed3.encode())
    serCom1.write(b'RESHI_1\n')
    time.sleep(0.1)
    serCom1.write(b'RESHI_2\n')
    time.sleep(0.1)
    serCom1.write(b'RESHI_3\n')
    time.sleep(0.1)
    serCom1.write(TimeD_s.encode())
    time.sleep(0.1)
    serCom1.write(Depth_val.encode())
    print(Depth_val.encode())
    print("dimpling")


def Readline():  # read lines from the arduino to see when to turn off the live updating graph and timer
    print("Readline activated")
    while 1:
        line = serCom1.read_until('\n').decode('utf-8')
        print('line: ', line)
        print('bool:', line.startswith("P"))
        if len(line) > 0:
            result = line.startswith("P")
            print(result)
            if result == True:
                # Run_button.config(bg = defaultbg)
                Timer_Stop()
                print("done")
                break


def Run():  # send all the important data to the serial command, run motors and electrodes
    Run_button.config(bg="green")
    event_2.clear()
    Speed1 = 'SETSP_1' + Speed1_entry.get() + '\n'  # acquire speed and set to proper format
    Speed2 = 'SETSP_2' + Speed2_entry.get() + '\n'

    Accel1 = 'SETAC_1' + Accel1_entry.get() + '\n'  # acquire acceleration
    Accel2 = 'SETAC_2' + Accel2_entry.get() + '\n'

    Decel1 = 'SETDC_1' + Decel1_entry.get() + '\n'  # acquire deceleration
    Decel2 = 'SETDC_2' + Decel2_entry.get() + '\n'

    enab_val = enab_selection.get()  # value of enable

    if enab_val == "Yes":  # prepare to send to arduino based on input
        enab1 = 'ENABL_1\n'
        enab2 = 'ENABL_2\n'
        print("Enabled")

    elif enab_val == "No":
        enab1 = 'DISAB_1\n'
        enab2 = 'DISAB_2\n'
        print("Disabled")

    Res1_val = Res1_selection.get()  # get resolution value
    Res2_val = Res2_selection.get()

    if Res1_val == "High Resolution":  # prepare to send to arduino resolution value
        Res1 = 'RESHI_1\n'

    elif Res1_val == "Mid Resolution":
        Res1 = 'RESHA_1\n'

    elif Res1_val == "Low Resolution":
        Res1 = 'RESLO_1\n'

    if Res2_val == "High Resolution":  # resolution for second motor, high
        Res2 = 'RESHI_2\n'

    elif Res2_val == "Mid Resolution":  # medium
        Res2 = 'RESHA_2\n'

    elif Res2_val == "Low Resolution":  # Low
        Res2 = 'RESLO_2\n'

    global Time

    prht_s = float(prht_entry.get())

    prht = 'prht' + str(int(prht_s * 1000)) + '\n'

    Time = 'GO'

    serCom1.write(Speed1.encode())  # encode everything and send to the arduino
    time.sleep(0.1)
    serCom1.write(Speed2.encode())
    time.sleep(0.1)
    serCom1.write(Accel1.encode())
    time.sleep(0.1)
    serCom1.write(Accel2.encode())
    time.sleep(0.1)
    serCom1.write(Decel1.encode())
    time.sleep(0.1)
    serCom1.write(Decel2.encode())
    time.sleep(0.1)
    serCom1.write(Res1.encode())
    time.sleep(0.1)
    serCom1.write(Res2.encode())
    time.sleep(0.1)
    serCom1.write(enab1.encode())
    time.sleep(0.1)
    serCom1.write(enab2.encode())
    time.sleep(0.1)
    serCom1.write(prht.encode())
    time.sleep(0.1)
    serCom1.write(Time.encode())

    running = True
    global start
    Clear()  # clear the graph
    start = time.time()  # get start time
    while running == True:
        timer_time.after(100, update)  # update timer every 100 ms
        time_new = time.time() - start
        if pm == True:  # pm True if powermeter is connected
            animate(time_new)
            fig.canvas.draw()
            fig.canvas.flush_events()
        if event_2.is_set():
            Run_button.config(bg=defaultbg)
            break  # break out of loop
        root.update_idletasks()


def Clear():  # clears the plot
    plt.cla()
    x_vals.clear()
    y_vals.clear()


def update():  # updates the timer
    global start
    timer_time.config(text=str(round(time.time() - start, 2)) + 's')
    root.update_idletasks()


def show_frame():
    _, frame = cap.read()
    frame = cv2.flip(frame, 0)
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image).resize((500,300))
    imgtk = ImageTk.PhotoImage(image=img)
    display1.imgtk = imgtk #Shows frame for display 1
    display1.configure(image=imgtk)
    root.after(10, show_frame)


def animate(new_time):  # reads the powermeter and updates the graph
    x_vals.append(new_time)
    y_vals.append(power_meter.read * 1000)
    plt.cla()
    plt.title("Power [mW] as a function of Time[s]")
    plt.xlabel("Time [s]")
    plt.ylabel("Power [mW]")
    plt.grid()

    plt.plot(x_vals, y_vals)



root = tk.Tk()
#root.geometry("1000x1000+300+300")
root.title('Fiber Pulling')



defaultbg = root.cget('bg')

ports = list(serial.tools.list_ports.comports()) #gets available ports
ports_selection = tk.StringVar()  #allows you to select your port
ports_selection.set(ports[0])
ports_label = tk.Label(root, text="Select Port: ", font = ("Arial", 10))
ports_entry = tk.OptionMenu(root, ports_selection, *ports)

global pm
pm = False
rm = pyvisa.ResourceManager()  # majid PM code
res_avail = rm.list_resources()
print("resources:",res_avail)
print(type(res_avail[0]))
dev_name = 'USB0::0x1313::0x8078::P0032080::INSTR'
print(dev_name in res_avail)
if dev_name in res_avail:  #if the device is connected, it will run this code and read from the powermeter
    inst = rm.open_resource('USB0::0x1313::0x8078::P0032080::INSTR')
    power_meter = ThorlabsPM100(inst=inst)
    print(inst.query("*IDN?"))
    init = power_meter.read
    pm = True
    print('initial value:', float(init))
else:#if device is not connected, a warning window will pop up
    res_not_avail = tk.Tk()
    res_not_avail.title("Error")
    error_label = tk.Label(res_not_avail, text = "Power meter not connected. Graph will not display").pack()
    ok_button =tk.Button(res_not_avail, text = "OK", command = res_not_avail.destroy).pack()
    print("Power Meter not connected")

port = ports_selection.get()
com = port.split(' ')
print(com[0])
global serCom1
serCom1 = serial.Serial(com[0],9600,timeout=2) #connects to the selected port via pyserial


# In[1]:


cap = cv2.VideoCapture(1) #captures video from the digital microscope
imageFrame = tk.Frame(root, width=10, height=10) #frame for the digital microscope
imageFrame.grid(row=0, column= 6, rowspan = 6, padx=10, pady=20)



display1 = tk.Label(imageFrame)
display1.grid(row=0, column=2, columnspan = 10, padx=20, pady=2)  #Display 1

show_frame()

# the next few lines make a canvas to embed the updating graph in the GUI
fig = plt.figure(figsize = (5,2))
ax = fig.add_subplot(111)
plt.title("Power [mW] as a function of Time[s]") #title
plt.xlabel("Time [s]") #x label
plt.ylabel("Power [mW]") #y label
plt.grid()

canvas = FigureCanvasTkAgg(fig, master = root)
canvas.draw()

x_vals = []
y_vals = []

# placing the canvas on the Tkinter
canvas.get_tk_widget().grid(row = 6, column = 6, columnspan = 5, rowspan = 8)

toolbar_frame = tk.Frame(root) #tool bar for the graph, allows it to be saved
toolbar_frame.grid(row=14,column=6)
toolbar = NavigationToolbar2Tk( canvas, toolbar_frame )
toolbar.update()

event_2 =threading.Event() #creates thread



global electrode_state
electrode_state = True



# In[ ]:


#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# prepare the widgets of the GUI for tapering
Res_options = [ "High Resolution",
                "Mid Resolution", #resolution options
                "Low Resolution"]

text1 = tk.Label(root, text = "Tapering:", font = (15))

timer_Label = tk.Label(root, text = "Time Elapsed:") #timer
timer_time = tk.Label(root, text="0.0s")


Res1_selection = tk.StringVar() #resoution 1 labels and option menu
Res1_selection.set(Res_options[0])
Res1_label = tk.Label(root, text="Resolution Motor 1: ", font = ("Arial", 10))
Res1_entry = tk.OptionMenu(root, Res1_selection, *Res_options)
Res1_entry['menu'].configure(font=('Arial',10))

Res2_selection = tk.StringVar() #resolution 2 labels and option menu
Res2_selection.set(Res_options[1])
Res2_label = tk.Label(root, text="Resolution Motor 2: ", font = ("Arial", 10))
Res2_entry = tk.OptionMenu(root, Res2_selection, *Res_options)
Res2_entry['menu'].configure(font=('Arial',10))

enab_options = ["Yes", "No"] #enable options

enab_selection = tk.StringVar() #enable label and option menu
enab_selection.set(enab_options[0])
enab_label = tk.Label(root, text="Enable Motors?: ", font = ("Arial", 10))
enab_entry = tk.OptionMenu(root, enab_selection, *enab_options)


Speed1_label = tk.Label(root, text="Speed Motor 1: ", font = ("Arial", 10)) #Speed 1 labels and entry widgets
s1_def = IntVar()
Speed1_units = tk.Label(root, text = "Steps/s", font = ("Arial", 10))
Speed1_entry = tk.Entry(root,text = s1_def, font = ("Arial", 10) )
s1_def.set(38)

Speed2_label = tk.Label(root, text="Speed Motor 2: ", font = ("Arial", 10)) #Speed 2 Labels and entry widgets
s2_def = IntVar()
Speed2_units = tk.Label(root, text = "Steps/s", font = ("Arial", 10))
Speed2_entry = tk.Entry(root, text = s2_def, font = ("Arial", 10))
s2_def.set(930)

Accel1_label = tk.Label(root, text="Acceleration Motor 1: ", font = ("Arial", 10)) #acceleration 1 labels and entry widgets
Accel1_units = tk.Label(root, text = "Steps/s\u00b2", font = ("Arial", 10))
A1_def = IntVar()
Accel1_entry = tk.Entry(root, text = A1_def, font = ("Arial", 10))
A1_def.set(6)

Decel1_label = tk.Label(root, text="Deceleration Motor 1: ", font = ("Arial", 10)) #deceleration 1 labels and entry widgets
Decel1_units = tk.Label(root, text = "Steps/s\u00b2", font = ("Arial", 10))
D1_def = IntVar()
Decel1_entry = tk.Entry(root, text = D1_def, font = ("Arial", 10))
D1_def.set(6)

Accel2_label = tk.Label(root, text="Acceleration Motor 2: ", font = ("Arial", 10)) #acceleration 2 labels and entry widgets
Accel2_units = tk.Label(root, text = "Steps/s\u00b2", font = ("Arial", 10))
A2_def = IntVar()
Accel2_entry = tk.Entry(root, text = A2_def, font = ("Arial", 10))
A2_def.set(160)

Decel2_label = tk.Label(root, text="Deceleration Motor 2: ", font = ("Arial", 10)) #deceleration 1 labels and entry widgets
Decel2_units = tk.Label(root, text = "Steps/s\u00b2", font = ("Arial", 10))
D2_def = IntVar()
Decel2_entry = tk.Entry(root, text = D2_def, font = ("Arial", 10))
D2_def.set(160)

prht_label = tk.Label(root, text = "Preheat time:", font = ("Arial", 10)) #preheat labels and entry widgets
prht_units = tk.Label(root, text = "s", font = ("Arial", 10))
prht_def = IntVar()
prht_entry = tk.Entry(root, text = prht_def, font = ("Arial", 10))
prht_def.set(0.8)


TimeD_label = tk.Label(root, text = "Time Delay:", font = ("Arial", 10)) #time delay labels and entry widgets
TimeD_units = tk.Label(root, text = "s", font = ("Arial", 10))
TD_def = IntVar()
TimeD_entry = tk.Entry(root, text = TD_def, font = ("Arial", 10))
TD_def.set(1)

elec_toggle = tk.Button(text ="electrodes on/off", command = elec_state, font = ("Arial", 10)  ) #electrodes button widget

Run_button = tk.Button(text="Run",
                       command = lambda: [threading.Thread(target = Run).start(),
                       threading.Thread(target = Readline).start()], font = ("Arial", 10)) #run button widget
Emg_button = tk.Button(text = "EMERGENCY STOP",  #emergency stop button widget
                        command = Emg_stop,
                        background = 'Red',
                        font = 15,
                        height = 2,
                        width = 17)
Reset_button = tk.Button(text = "Reset", #reset button widget
                         command = lambda: threading.Thread(target = Reset).start(),
                         font = ("Arial", 10))
decel_button = tk.Button(text = "Decelerate",  #decelerate button widget
                         command = lambda: threading.Thread(target = Decel).start(),
                         font = ("Arial, 10"),
                         activebackground='green')

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#prepare the widgets of the GUI for dimpling

text2 = tk.Label(root, text = "Dimpling:", font = ( 15))

Speed3_label = tk.Label(root, text="Speed Motor 3: ", font = ("Arial", 10)) #Speed 1 labels and entry widgets
s3_def = IntVar()
Speed3_units = tk.Label(root, text = "Steps/s", font = ("Arial", 10))
Speed3_entry = tk.Entry(root,text = s3_def, font = ("Arial", 10) )
s3_def.set(1000)

Depth_selection = IntVar() #resolution 3 labels and option menu widgets
Depth_selection.set(20)
Depth_label = tk.Label(root, text ="Dimple depth: ", font = ("Arial", 10))
Depth_entry = tk.Entry(root, text = Depth_selection, font = ("Arial", 10))
Depth_units = tk.Label(root, text = "Steps", font = ("Arial", 10))

Center_button = tk.Button(text = "Center", command = lambda: threading.Thread(target = Center).start(), font = ("Arial", 10))
Dimple_button =tk.Button(text = "Dimple", command = lambda: threading.Thread(target=Dimple).start(), font = ("Arial", 10))



# In[ ]:


#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#grid spacing for all the widgets

text1.grid(row = 0, column = 0, padx = 10, pady = 7)
text2.grid(row = 10, column = 0, pady =7)

Speed1_label.grid(row = 1, column = 0, pady = 7) #Speed 1 widget placements
Speed1_units.grid(row = 1, column = 2, pady = 7)
Speed1_entry.grid(row = 1, column = 1, pady = 7)

Speed2_label.grid(row = 2, column = 0, pady = 7) #Speed 2 widget placements
Speed2_units.grid(row = 2, column = 2, pady = 7)
Speed2_entry.grid(row = 2, column = 1, pady= 7)

Speed3_label.grid(row = 11, column = 0, pady = 7) #Speed 3 widget placements
Speed3_units.grid(row = 11, column = 2, pady = 7)
Speed3_entry.grid(row = 11, column = 1, pady = 7)

Accel1_label.grid(row = 3, column = 0, pady = 7) #acceleration 1 widget placements
Accel1_units.grid(row = 3, column = 2)
Accel1_entry.grid(row = 3, column = 1, pady = 7)

Accel2_label.grid(row = 4, column = 0, pady = 7) #Acceleration 2 widget placements
Accel2_units.grid(row = 4, column = 2)
Accel2_entry.grid(row = 4, column = 1,  pady = 7)

Decel1_label.grid(row = 5, column = 0, pady = 7) #Deceleration 1 widget placements
Decel1_units.grid(row = 5, column = 2)
Decel1_entry.grid(row = 5, column = 1, pady = 7)

Decel2_label.grid(row = 6, column = 0, pady = 7) #Acceleration 2 widget placements
Decel2_units.grid(row = 6, column = 2)
Decel2_entry.grid(row = 6, column = 1,  pady = 7)

Res1_label.grid(row = 1, column = 3, padx = 5, pady = 7) #resolution 1 widget placements
Res1_entry.grid(row = 1, column = 4, padx = 5, pady = 7)

Res2_label.grid(row = 2, column = 3, padx = 5, pady = 7) #resolution 2 widget placements
Res2_entry.grid(row = 2, column = 4, padx = 5, pady = 7)

Depth_label.grid(row = 12, column = 0, padx = 5, pady = 7) #resolution 1 widget placements
Depth_entry.grid(row = 12, column = 1, padx = 5, pady = 7)
Depth_units.grid(row = 12, column = 2, padx = 5, pady = 7)

enab_label.grid(row=3, column=3, padx=5, pady= 7) #enable 1 widget placements
enab_entry.grid(row=3, column=4, padx=5, pady= 7)

timer_Label.grid(row = 6, column =3) #timer widget placements
timer_time.grid(row = 6, column =4)

TimeD_label.grid(row =13, column = 0, pady= 7) #time delay dimple widgets placements
TimeD_units.grid(row = 13, column = 2)
TimeD_entry.grid(row = 13, column = 1, pady= 7)

prht_label.grid(row = 7, column = 0, pady= 7) #preheat widgets placements
prht_entry.grid(row = 7, column = 1, pady = 7)
prht_units.grid(row = 7, column = 2, pady = 7)

ports_label.grid(row = 4, column = 3, padx = 5, pady = 7) #ports widgets placements
ports_entry.grid(row = 4, column = 4, padx = 5, pady = 7)

Run_button.grid( row=9, column=1, padx=15, pady= 7) #button widget placements
Emg_button.grid( row  = 10, column = 4, rowspan = 3, columnspan =2, padx =10, pady = 7)
Reset_button.grid( row =9, column = 0, padx= 15, pady = 7)
elec_toggle.grid(row = 5, column = 4)
Center_button.grid(row = 14, column =1, pady = 7)
Dimple_button.grid(row = 14, column  = 3, pady = 7)
decel_button.grid(row = 9, column = 3 , pady = 7)




root.mainloop()

