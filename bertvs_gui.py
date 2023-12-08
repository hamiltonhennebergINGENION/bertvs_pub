###############################################
#				TVS Test GUI	v3			  #
###############################################
# Author: 		Matthaeus Gebauer			  #
# References: 	guiv2						  #
# Ingenion, LLC								  #
###############################################

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import pandas as pd
import numpy as np
import datetime
import threading 
import time 
import glob
import os

from richtext import *
from signal_map import *
from bertvs import *
from log_manager import *
from multiplatform_opener import *


class GUI():
	def __init__(self):
		# Initial Window
		self.device = FP_API()
		self.window = Tk()
		self.window.geometry('450x350')
		self.window.title('TVS Test')

		self.pm = signal_map("BER_TVS_pm.txt")
		self.connectors = self.pm.get_connector_list()
		self.signals = self.pm.get_signals_per_connector()
		self.pass_fail  = False
		self.test_state = np.zeros(len(self.device.ber_test)).astype(bool).tolist()

		self.multientry = False
		self.hasStart = 0

		# Entry Strings
		self.entryU = ''
		self.entryS = ''

		self.log = log_manager("TVS_Logs/TVS_Current_Log.txt")

		#---------------Labels---------------------
		labels = [  
			('TVS Model XEM7310-A200 Test ', 0, 1, 2, 12, 'w'),
			('Test not started', 14, 1, 1, 10, ''),
			('Test Time', 15, 1, 1, 10, '', 'disabled'),
			('Inspector/Conductor:', 10, 2, 1, 10, 'w'),
			('TVS Serial Number:', 12, 2, 1, 10, 'w'),
			('Additional Notes:', 14, 2, 1, 10, 'w'),
			('Test Result', 18, 2, 2, 14, '', 'disabled')
		]

		displayTxt = [] # holds the labels for future reference

		# applys a format to all lables
		for label in labels:
			text = label[0]		# 'TVS test label'
			row  = label[1]		# 0-15
			col  = label[2]		# 0-3
			colspan = label[3]	# 1-2 width in columns
			font = 'Arial Bold'
			size  = label[4]	# size in points 10 is standard
			side  = label[5]	# side hugging text 'n', 'e', 's', 'w', like a compass or '' for center
			state = label[6] if len(label) > 6 else None # enabled or disabled
			txt = ttk.Label(self.window, text=text, font=(font,size), state=state, background='light sky blue')
			txt.grid(row=row, column=col, columnspan=colspan, sticky=side)
			displayTxt.append(txt)

		# reassign the labels to attributes
		self.title		= displayTxt[0]
		self.testStatus = displayTxt[1]
		self.testTime	= displayTxt[2]
		self.cond		= displayTxt[3]
		self.tvsSerial	= displayTxt[4]
		self.tvsNotes	= displayTxt[5]
		self.result		= displayTxt[6]

		#---------------Text Entry------------------
		# Inspector Entry
		self.enterU = StringVar()
		self.userEntry = ttk.Entry(self.window, textvariable=self.enterU, width=25)
		self.userEntry.grid(row=11, column=2)
		# TVS Serial Entry
		self.enterSer = StringVar()
		self.serialEntry = ttk.Entry(self.window, textvariable=self.enterSer,width=10)
		self.serialEntry.grid(row=13, column=2, sticky='w')
		# TVS Notes Entry 
		self.noteEntry = Text(self.window,width=35, height=5, wrap='word', relief='flat', padx=3)
		self.noteEntry.grid(row=15, column=2, columnspan=2, sticky='w')

		#---------------Buttons-------------------
		button_config = [
			('Start Test', self.clicked_start, 10, 1),
			('Connect', self.clicked_connect, 11, 1),
			('Open File', self.clicked_file, 12, 1),
			('Save Log', self.save_log, 10, 3),
			('Reset', self.clicked_reset, 11, 3),
			('User Info', self.open_info, 13, 1)
		]

		self.button = []
		# applies a format to all buttons
		for text, command, row, column in button_config:
			btn = Button(self.window, text=text, command=command, activebackground='orange1', relief='flat', width=10, bg='white')
			btn.grid(row=row, column=column, pady=2, padx=25 if column == 3 else 0)
			self.button.append(btn)

		if (self.device.connected == True):
			self.button[1].configure(text='Disconnect', command=self.clicked_disconnect)

		#---------------Device Call---------------
		#Find information on connected device
		self.window.configure(background = 'light sky blue')
		self.show_device_info()
		# Set up the second window
		self.test_window()
		# Precheck failsafe pins
		self.failsafe_check()

	
	'''
	################################################################################
	#                                 test_window                                   #
	#                        initializes the test window                           #
	################################################################################
	'''
	def test_window(self):
		# Second window for test progress
		self.window2 = Toplevel(self.window)
		self.window2.geometry('885x230')
		self.window2.title('Progress')
		# Puts TVS front panal image for progress 
		self.frontTVS = PhotoImage(file='TVS_Front.GIF')
		self.front = ttk.Label(self.window2, image=self.frontTVS)
		self.front.image = self.frontTVS
		self.front.grid(row=0,column=0)
		#Color
		self.window2.configure(background= 'light sky blue')
		#self.window.iconbitmap('ingenion.ico')

		# LEDs
		self.canvas = Canvas(self.window2, height=150,width=885)

		self.leds  = []
		self.ratio = []

		# J1 and J2
		self.leds.append(self.canvas.create_oval(85,10,105,30,fill=''))
		self.leds.append(self.canvas.create_oval(85,50,105,70,fill=''))
		# J3 and J4
		self.leds.append(self.canvas.create_oval(190,10,210,30,fill=''))
		self.leds.append(self.canvas.create_oval(190,50,210,70,fill=''))
		# J5
		self.leds.append(self.canvas.create_oval(317,30,337,50,fill=''))
		# J6 and J7
		self.leds.append(self.canvas.create_oval(395,50,415,70,fill=''))
		self.leds.append(self.canvas.create_oval(395,10,415,30,fill=''))
		# J8 and J9
		self.leds.append(self.canvas.create_oval(455,50,475,70,fill=''))
		self.leds.append(self.canvas.create_oval(455,10,475,30,fill=''))
		# J10 and J11
		self.leds.append(self.canvas.create_oval(510,50,530,70,fill=''))
		self.leds.append(self.canvas.create_oval(510,10,530,30,fill=''))
		# J12 and J13
		self.leds.append(self.canvas.create_oval(605,50,625,70,fill=''))
		self.leds.append(self.canvas.create_oval(605,10,625,30,fill=''))

		# loop through the list of circle IDs
		for circle_id in self.leds:
			# get the coordinates of the circle
			x1, y1, x2, y2 = self.canvas.coords(circle_id)
			# calculate the position of the text based on the circle's coordinates
			text_x = x2 + 17  # 10 pixels to the right of the circle
			text_y = (y1 + y2) / 2  # vertically centered with the circle
			# create the text object
			self.ratio.append(self.canvas.create_text(text_x, text_y, text='0%'))
		
		self.canvas.grid(row=2,column=0)
		return self.window2


	'''
	################################################################################
	#                            show_device_info                                  #
	#                  shows the device info found in the TVS                      #
	################################################################################
	'''
	def show_device_info(self):
		if(self.device.connected == False):
			messagebox.showwarning(title='TVS Disconnected', message='The TVS was disconnected')
			self.infoErr = ttk.Label(self.window, text ='Unable to retrieve info.',background='light sky blue')
			self.infoErr.grid(row=16,column=1)
			try:
				self.Product.destroy()
				self.firmware.destroy()
				self.sn.destroy()
				self.id.destroy()
			except:
				pass
		else:
			self.Product = ttk.Label(self.window, text='Product: '+ self.device.productName, background='light sky blue')
			self.Product.grid(row=17,column=1)
			self.firmware = ttk.Label(self.window, text='Firmware Version: '+ self.device.deviceVersion, background='light sky blue')
			self.firmware.grid(row=18,column=1)		
			self.sn = ttk.Label(self.window, text='Device SN: '+ self.device.serialNumber, background='light sky blue')
			self.sn.grid(row=19,column=1)
			self.id = ttk.Label(self.window, text='Device ID: '+ self.device.deviceID, background='light sky blue')
			self.id.grid(row=20,column=1)
			self.lspace = ttk.Label(self.window, text=''.ljust(50), background='light sky blue')
			self.lspace.grid(row=21,column=1)
			try:
				self.infoErr.destroy()
			except:
				pass


	'''
	################################################################################
	#                              show_fsPopup                                    #
	#       opens a new popup that warns the user about failsafe errors            #
	################################################################################
	'''
	def show_fsPopup(self):
		fsPopup = Toplevel(self.window)
		fsPopup.title('Failsafe Check')
		# centers the popup
		fsPopup.geometry('250x200+{0}+{1}'.format(int(fsPopup.winfo_screenwidth()/2 - 125), int(fsPopup.winfo_screenheight()/2 - 100)))
		fsPopup.lift(aboveThis=self.window2)
		fsPopup.lift(aboveThis=self.window)
		# makes the popup take all inputs
		fsPopup.grab_set()
		fsPopup_label1 = ttk.Label(fsPopup, text='Errors Detected')
		fsPopup_label1.pack(pady=10)
		fsPopup_label2 = ttk.Label(fsPopup, text='Make sure nothing is plugged in')
		fsPopup_label2.pack(pady=10)
		fsPopup_close = ttk.Button(fsPopup, text='See Log', command=self.clicked_file)
		fsPopup_close.pack(pady=10,padx=5)
		fsPopup_open = ttk.Button(fsPopup, text='Close', command=fsPopup.destroy)
		fsPopup_open.pack(padx=5)
		return fsPopup
	

	'''
	################################################################################
	#                               clicked_start                                  #
	#            starts a new test and a new test window if necessary              #
	################################################################################
	'''
	def clicked_start(self):
		# Disables the button until all actions are complete
		if self.multientry:
			return
		
		self.multientry = True

		# Brings the test window back if closed
		if (self.window2.winfo_exists() == 0):
			self.test_window()

		if (self.device.connected == False):
			# Error message if no XEM connection 
			messagebox.showinfo('Error','No device found. Please connect the TVS.')
			self.window.update()
		elif (self.hasStart==0):
			self.button[0].configure(text='Stop Test', command=self.clicked_stop, relief='sunken', bg='orange1')
			self.testStatus.configure(text='Test Started...',background='light sky blue')
			now = datetime.datetime.now()
			self.testTime.configure(text=now.strftime('%m/%d/%Y\n%I:%M:%S'))
			for led in self.leds:
				self.canvas.itemconfigure(led,fill='red')

			# Starts the test
			self.hasStart = 1

			# Creates new thread to run scanner
			self.testing = threading.Thread(target=self.callback)
			self.testing.daemon = True
			self.testing.start()

		time.sleep(0.5)
		self.multientry = False
		
		
	# Callback to loop TVS scanning 
	def callback(self):	
		try:
			while(self.hasStart==1):
				# Check in the TVS is still connected
				# Updates window to keep GUI Thread from freezing
				self.window.update()
				self.window2.update()
				# Calls scanner and checks progress
				self.read_progress()
				time.sleep(0.1)

		except Exception as e:
			print('Error Running Test')
			print(e)
			messagebox.showwarning(title='Test', message='Error Running Test')
			self.button[0].configure(text='Start Test', command=self.clicked_start, relief='flat', bg='white')
			self.hasStart=0

		else:
			print("Test Stopped")


	'''
	################################################################################
	#                                clicked_stop                                  #
	#                      stops the current running test                          #
	################################################################################
	'''
	def clicked_stop(self):
		# switches the button state
		self.button[0].configure(text='Start Test', command=self.clicked_start, relief='flat', bg='white')
	
		# Will stop test once pressed, along with stop time 
		self.testStatus.configure(text='Test Stopped at:',background='light sky blue')
		now = datetime.datetime.now()
		self.testTime.configure(text=now.strftime('%m/%d/%Y\n%I:%M:%S'))
		self.hasStart = 0
		# self.testing.join()

		# gets the user entries
		self.entryU    = self.enterU.get()
		self.entryS    = self.enterSer.get() if len(self.enterSer.get()) != 0 else 'xxxx'
		self.enterNote = self.noteEntry.get('1.0', 'end')	

		# enters the user and device info to a file via log manager
		dev_info = [self.device.productName,  self.device.deviceVersion, 
				    self.device.serialNumber, self.device.deviceID]
		
		self.log.log_info(dev_info, self.entryU, self.entryS)
		if (len(self.enterNote) > 1): self.log.log_note(self.enterNote)
		self.log.log_test(self.device.ber_test, self.test_state, self.pass_fail)
		self.log.log_end(self.testTime.cget('text'))

		if self.pass_fail == 1: self.result.configure(text='Test Passed', state='normal')
		else: self.result.configure(text='Test Failed', state='normal')



	'''
	################################################################################
	#                              clicked_connect                                 #
	#                    connects the TVS if it's available                        #
	################################################################################
	'''
	def clicked_connect(self):
		# attempts to connect the TVS
		self.device.connect_TVS(10)				

		if self.device.connected == True:
			self.device.device_reset()
			self.show_device_info()
			self.button[1].configure(text='Disconnect', command=self.clicked_disconnect)
		else:
			messagebox.showinfo('Error','No device found. Please connect the FPGA.')

	'''
	################################################################################
	#                             clicked_disconnect                               #
	#                            disconnects the TVS                               #
	################################################################################
	'''
	def clicked_disconnect(self):
		# disconnects the TVS
		self.device.disconnect_TVS()				
		self.show_device_info()
		if self.device.connected == False:
			self.button[1].configure(text='Connect', command=self.clicked_connect)


	'''
	################################################################################
	#                                clicked_file                                  #
	#           opens the most recently edited file if one exists                  #
	################################################################################
	'''
	def clicked_file(self): 
		# gets the log directory
		directory = self.log.get_log_directory()

		# finds and opens the file last edited
		if len(os.listdir(directory)) > 0:
			list_of_files = glob.glob(directory+'/*') # * means all if need specific format then *.csv

			latest_file = max(list_of_files, key=os.path.getmtime)

			subprocess_opener(latest_file)


	'''
	################################################################################
	#                               clicked_reset                                  #
	#       resets the TVS and all temporary information about the last test       #
	################################################################################
	'''
	def clicked_reset(self):
		# lets you know to save your log before resetting
		answer = messagebox.askokcancel(title='Reset', message='This will overwrite unsaved logs')
		if answer == False:
			return

		# checks if the test window exists
		if (self.window2.winfo_exists() == 0): 
			self.test_window()

		# checks for errors and starts
		if (self.device.connected == False):
			# Error message if no XEM connection 
			messagebox.showinfo('Error','No device found. Please connect the FPGA.')
			self.window.update()
			return
		
		if (self.hasStart == 1):
			self.clicked_stop()
		
		self.testStatus.configure(text='Test Reset',background='light sky blue')
		self.testTime.configure(text='Test Time')
		self.result.configure(text='Test Result', state='disabled')

		# Resets the device
		self.device.reset_ber_test()
		self.resetLEDs()

		# Updates window
		self.window.update()
		self.window2.update()

		# Logs the event
		self.log.log_reset()
		self.failsafe_check()
	

	def resetLEDs(self):
		for led in self.leds:
			self.canvas.itemconfigure(led,fill='')
		for ratio in self.ratio:
			self.canvas.itemconfigure(ratio,text='0%')


	'''
	################################################################################
	#                                  save_log                                    #
	#        Enters the current test to the log file and finalizes the entry       #
	################################################################################
	'''
	def save_log(self):
		# gets the entry time
		now = datetime.datetime.now().strftime('%m%d%y_%H%M')

		# renames the temporary file
		try:
			self.log.enter_log(self.entryS, now)	
		except Exception as e:
			messagebox.showinfo(title='Log Manager', message='No file to save')
			# print(e)
			print('No File to Save')


	'''
	################################################################################
	#                                open_info                                     #
	#            opens a new window containing a basic user guide                  #
	################################################################################
	'''
	def open_info(self):
		# Third Window for user information
		self.window3 = Toplevel(self.window)
		self.window3.geometry('740x400')
		self.window3.title('User Information')
		
		info_box = RichText(self.window3, font=('Arial', 11))

		# Add the Ingenion logo at the bottom
		self.logo = PhotoImage(file='ingenion.png')
		self.front = ttk.Label(self.window3, image=self.logo)
		self.front.lift()
		self.front.pack(side='bottom')

		# info_box = ttk.Text(self.window3, font=('Arial Bold', 10))
		info_box.insert('end', 'TVS Testing Information' + '\n', 'h1')

		info_box.insert('end', '\tStart by entering your name into the Inspector box\n\t', 'bold')
		info_box.insert_bullet('end', '    Enter a serial number before hitting start\n\t')
		info_box.insert_bullet('end', '    Notes are not required but can be helpful\n\n')

		info_box.insert('end', '\tAfter starting the test the 2nd window should activate\n\t', 'bold')
		info_box.insert_bullet('end', '    Each port is given a percent change indicator, when this hits 100% the test is complete\n\t')
		info_box.insert_bullet('end', '    If an LED does not light up or complete, refer to log file to see which pin is malfunctioning\n\t')
		info_box.insert_bullet('end', '    For each successful loopback the color should progress	1: orange    2: yellow    3: green\n\n\n')

		info_box.insert('end', '\tAuthors: Albert DiCroce, Matthaeus Gebauer\n')
		info_box.insert('end', '\tProperty of Ingenion, LLC')

		info_box.config(bg='white', border=0)
		info_box.pack(expand=True, fill='both')


	'''
	################################################################################
	#                              failsafe_check                                  #
	#              checks for failsafe violations on the device                    #
	################################################################################
	'''
	def failsafe_check(self):
		if (self.device.connected == False):
			print("Cannot check failsafe, TVS not connected.")
			return
		# Get a list of signals that don't have a failsafe
		low_failsafes = self.device.failsafe_status()

		if len(low_failsafes) == 0:
			print("No failsafe errors")
			return
		
		info = []

		# Loop through the list of signals with no failsafe
		for signal in low_failsafes:
			# Get information about the signal failure
			info.append(self.pm.get_debug_info(signal))

		self.log.log_failsafe_violations(info)
		self.show_fsPopup()



	'''
	################################################################################
	#                               read_progress                                  #
	#    checks the progress of the BER test and updates the leds on window 2      #
	################################################################################
	'''
	def read_progress(self):
		# checks if the device is still connected
		if (self.device.connected == False):
			raise Exception('Device was disconnected during test')

		# calls the most recent register bridge state
		self.device.read_test_registers()
		
		# alias for the signal test registers
		test  = self.device.ber_test

		# gets the connection bit from the test registers and creates a mask
		test_state = test[:,0] == 0 & test[:,2].astype(bool)
		mask = test_state.tolist()

		# This gets all the successfully found signals and divides them by connector 'J--'
		success = self.pm.signals_per_connector(self.pm.map.iloc[mask])

		def set_led(ratio, n):
			if (ratio == 1):
				self.canvas.itemconfigure(self.leds[n],fill='green')
			elif (ratio > 0.5):
				self.canvas.itemconfigure(self.leds[n],fill='yellow')
			elif (ratio > 0):
				self.canvas.itemconfigure(self.leds[n],fill='orange')
			else:
				self.canvas.itemconfigure(self.leds[n],fill='red')


		for i in range(len(self.signals)):
			# set the LED color based on the number of successful connections for the current connector
			completion = success[i] / self.signals[i]
			self.canvas.itemconfigure(self.ratio[i],text=f'{100*completion:.0f}%')
			set_led(completion,i)
			if i == 11:
				self.canvas.itemconfigure(self.ratio[12],text=f'{100*completion:.0f}%')
				set_led(completion,12)

		# updates the list of successful connections
		self.pass_fail  = np.sum(success) == np.sum(self.signals)
		self.test_state = test_state



app = GUI()
app.window.mainloop()