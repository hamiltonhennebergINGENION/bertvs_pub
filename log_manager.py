###############################################
#			TVS Test Log Manager		      #
###############################################
# Author: 	 		Matthaeus Gebauer		  #
# References: 		log.py				      #
# Ingenion, LLC								  #
###############################################

import pandas as pd
import numpy as np
import os

from signal_map import *

class log_manager():
	def __init__(self, filePath="TVS_Logs/TVS_Current_Log.txt"):
		# Stores the Report in a Temporary file
		self.log_file = filePath
		self.pass_fail = "fail"

		self.pm = signal_map()
		self.p_map = self.pm.map
		self.connectors = self.pm.get_connector_list()
		self.signals = self.pm.get_signals_per_connector()

		# replaces the temporary file
		if os.path.exists(filePath):
			os.remove(filePath)
			return

		directory = os.path.dirname(filePath)
		# creates a local directory if one does not exist
		if not os.path.exists(directory):
			os.mkdir(directory)


	# Logs Developer Information into File
	def log_info(self, deviceInfo, entryU, entryS):

		action = 'a' if os.path.exists(self.log_file) else 'w'
		TVSfile = open(self.log_file,action)
		
		# Title
		title = "-+-+-TVS Information-+-+-"
		TVSfile.write(f"\n\n{title.center(62,' ')}\n")
		TVSfile.write("\n")
		TVSfile.write(f"Inspector/Conductor: {entryU} \n")
		TVSfile.write(f"  TVS Serial Number: {entryS} \n")
		TVSfile.write("\n")
		
		# Device and Test Information
		TVSfile.write(f"--------------------------------------------------------------\n")
		TVSfile.write(f"         Product: {deviceInfo[0]}\n")
		TVSfile.write(f"Firmware version: {deviceInfo[1]}\n")
		TVSfile.write(f"   Serial Number: {deviceInfo[2]}\n")
		TVSfile.write(f"       Device ID: {deviceInfo[3]}\n")
		TVSfile.write(f"--------------------------------------------------------------\n")
		TVSfile.close()


	def log_note(self,tvsNotes):
		# Check if the log file exists and open it in append mode if it does, otherwise open it in write mode
		action = 'a' if os.path.exists(self.log_file) else 'w'
		TVSfile = open(self.log_file, action)

		# Write a header and the notes to the file
		TVSfile.write("Additional Notes".center(40, "=") +"\n")
		tvsNotes = "\n   ".join(tvsNotes[i:i+34] for i in range(0, len(tvsNotes), 34)).replace("\t", " ")
		TVSfile.write("   "+ tvsNotes)
		TVSfile.write("".center(40, "=") +"\n")
		TVSfile.close()


	def log_test(self, status=np.array(0), test_state=list, pass_fail=0):
		# Check if the log file exists and open it in append mode if it does, otherwise open it in write mode
		action = 'a' if os.path.exists(self.log_file) else 'w'
		TVSfile = open(self.log_file, action)

		TVSfile.write("**If all tests are completed they should say passed. \n")
		TVSfile.write("\n")
		TVSfile.write("  If errors do occur during a loopback test, or a test case was\n")
		TVSfile.write("  found unsuccessful for any reason, a debug string will be\n")
		TVSfile.write("  presented with the format shown below:\n")
		TVSfile.write("\n")
		TVSfile.write("  Driver| driver pins   Receiver| receiver pins   |Loopback pins   driver[polarity] -> receiver[polarity]\n\n")

		for connector in self.connectors:
			connector_signals = self.p_map[self.p_map['Connector'] == connector]
			TVSfile.write("\n"+ connector.center(40,"-") +"\n")

			for signal in connector_signals.itertuples():
				# Each signal in the connector signal dataframe contains this information:
				# 0 	Index=0,
				# 1 	Test=0, 
				# 2 	Connector='J1', 
				# 3 	Loopback='A', 
				# 4 	Signal_Pair='RS422[0,2]', 
				# 5 	Standard='RS422', 
				# 6 	Info=['U600', '9,10,11', 'U601', '3,2,1', '9p->17p', '10n->4n']
				io_type = self.delay_to_type(status[signal[1],1])

				debug_format = lambda y,x: "".join(s.ljust(y) for s in x)

				driver   = signal[6][0]
				receiver = signal[6][2]
				driver_pins   = debug_format(4,signal[6][1].split(','))
				receiver_pins = debug_format(4,signal[6][3].split(','))
				loopbacks = debug_format(10,signal[6][4:])

				debug_string = f"debug info: \t{driver}| {driver_pins}  {receiver}| {receiver_pins}  |{loopbacks}" 

				if status[signal[1],2] == 0:
					TVSfile.write(f"   {signal[4]}" + "\t Fail".ljust(15)   + "No test"
				   				+ f"\t\t{debug_string}\n")

				elif (io_type == signal[5]) and (test_state[signal[0]] == True):
					TVSfile.write(f"   {signal[4]}" + "\t Passed".ljust(15) 
				   			    + f"{io_type}\t{status[signal[1],0]:.4f}\n")
					
				else:
					TVSfile.write(f"   {signal[4]}" + "\t Fail".ljust(15)   
								+ f"expected {signal[5]}, got {io_type}\t{status[signal[1],0]:.4f}"
								+ f"\t\t{debug_string}\n")

		TVSfile.close()

		# If the number of successful pins equals the total number of pins tested, set pass_fail to "pass"
		if pass_fail == 1:
			self.pass_fail = "pass"


	def log_end(self,time):
		# Check if the log file exists and open it in append mode if it does, otherwise open it in write mode
		action = 'a' if os.path.exists(self.log_file) else 'w'
		TVSfile = open(self.log_file, action)

		# Write the end time to the file
		TVSfile.write("\nTest Ended at: %s \n" %time.replace("\n", " "))
		TVSfile.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")
		TVSfile.close()
    

	def log_failsafe_violations(self, low_failsafes):
		# Open log file in 'w' mode to overwrite any existing content
		TVSfile = open(self.log_file, 'w')
		TVSfile.write("\nTVS Failsafe Failures Detected: \n\n")
		# Write header for table with column names
		TVSfile.write(f"{'Driver':<12} {'Receiver':<12} \n")
		# Loop through each pin in the DataFrame and write its information to the log
		for signal in low_failsafes:
			# Write information for the current pin to the log in a formatted string
			TVSfile.write(f"{signal[0]:<12} {signal[1]:<12} \n")

		TVSfile.write('\n')
		TVSfile.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")
		TVSfile.close()


	def log_reset(self):
		# Reset the pass_fail status
		self.pass_fail = "fail"
		# Open log file in 'w' mode to overwrite any existing content
		TVSfile = open(self.log_file, 'w')
		# Write DEVICE RESET message to log with centered formatting
		TVSfile.write("\n\n" + "DEVICE RESET".center(62," ") + "\n\n")
		TVSfile.write("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||\n")
		TVSfile.close()


	def enter_log(self, serial, time):
		# Construct the new name for the log file using the device serial number, test end time, and pass/fail status
		newName = "TVS_Logs/TVS_" + serial + "_" + time + "_" + self.pass_fail + ".txt"
		# Rename the current log file with the new name
		os.rename(self.log_file, newName)


	def delay_to_type(self, delay):
		io_type = "none"
		if delay <  30:     io_type = "LVDS"
		if delay >= 30:     io_type = "RS422"
		if delay >= 100:    io_type = "TTL"
		return io_type


	def get_log_directory(self):
		# Return the directory of the current log file
		return os.path.dirname(self.log_file)
	