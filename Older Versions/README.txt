//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
Hello, welcome to the fiber pulling readme. This code is meant to be used with the device I built for tapering optical fiber. Tapered and dimpled
fibers can be used for coupling, and thus are important around the lab. To taper the fiber, I have built a device to heat the fiber and stretch it. The
device requires 2 code packages. One is the arduino code for controlling 3 stepper motors and a pair of electrodes for arc discharge, the other is a python 
GUI that can be used to easily send commands to the arduino. For an in depth manual on how to use the device, view the Fiber Pulling section in the
Barzanjeh Group notebook. 
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
Dependancies:

You will need to ensure the following packages/drivers are installed on your laptop: 

Python 3

Arduino IDE

Matplotlib (pip install matplotlib)

tkinter 

numpy (pip install numpy)

Pyvisa(pip install pyvisa-py) 

Pyserial (pip install pyserial) 

Threading (pip install threaded) 

Opencv (pip install opencv-python) 

Pillow (pip install Pillow) 

Thorlabs PM100d (pip install ThorlabsPM100) 

Thorlabs PM100 driver (Thorlabs - PM100D Compact Power and Energy Meter Console, Digital 4" LCD) under software download 

NI VISA (NI-VISA Download - NI) 

Accelstepper Library for arduino


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
Installing:

You can use the installer in this package to get the GUI as an executable app. If you need to make modifications to the code, the python 
file can be downloaded from this GIT. The arduino code is also in this GIT.

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
Running:

Upload the arduino code to the arduino. Open the GUI. If you aren't connected to the arduino, the GUI will not run. If you aren't connected 
to the power meter, you will get a pop up window to warn you that the graph will not update. You can change the parameters for the speed
of the motors, acceleration, resolution, as well as preheat time, dimple depth and delay. When you click the 'run' button, the information
for the speed, acceleration, resolution, and preheat time will be sent to the arduino via serial port, as well as the command to begin 
pulling. The timer will start, and live graph will begin to update if the power meter is connected. Once the transmission begins to level out,
(usually after 6 seconds), click the decelerate command to tell the arduino to begin to decelerate to a stop. For the dimpling, ensure the 
center of the taper is between the electrodes. To do this, the 'center' button will command the motors to move till the taper is centered.
Enter the desired parameters for dimple depth, cooktime, and motor 3 speed. Setting the speed of motor 3 will automatically seta the speed
of motors 1 and 2 to half the speed of motor 3. Click the 'dimple' button, and the motors will execute the dimpling process. 

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
