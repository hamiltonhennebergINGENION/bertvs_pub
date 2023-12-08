###############################################
#				Bit-Error Testing	v4		  #
#				   API Control				  #
###############################################
# Author: 		Matthaeus Gebauer			  #
# References: 	berv2.py					  #
###############################################

import ok 
import numpy as np
import time


class FP_API:
	def __init__(self):
		# Initialize the Frontpanel API
		self._diff_a = 0
		self._diff_b = 0
		self._diff_c = 0
		self._single = 0
		self._ber_test_offset = 0
		self._diff_a_offset = 0
		self._diff_b_offset = 0
		self._diff_c_offset = 0
		self._single_offset = 0
		self._address_space = 0
		self.connected = 0

		self._productName   = None
		self._deviceVersion = None
		self._serialNumber  = None
		self._deviceID      = None

		self.xem = ok.okCFrontPanel()
		self.devInfo = ok.okTDeviceInfo()
		self.ber_test = np.empty([1, 3], dtype=float)

		#Try and detect a connected device
		self.connect_TVS(5)				
		self.device_reset() 



	def connect_TVS(self, attempts=1):
		try:
			self._connect_TVS()		
			self.connected = 1

		except ConnectionError as e:
			time.sleep(1)
			if (attempts == 0): 
				print(e)
				print('Connection Timeout')
				self.connected = 0
				return
			self.connect_TVS(attempts-1)

		except Exception as e:
			print(e)
			self.connected = 0

		
	def _connect_TVS(self):
		#Try and detect a connected device
		opn = self.xem.OpenBySerial("")
		if (opn == self.xem.NoError):
			print("Device Found.")

		elif (opn == self.xem.DeviceNotOpen):
			raise ConnectionError("Device Not Found")
		
		config = self.xem.ConfigureFPGA("ber_tvs_fpga.bit")
		if (config == self.xem.NoError): 
			print("Xem 7310 bit file loaded.")

		elif (config == self.xem.DeviceNotOpen):
			raise ConnectionError("Device is not open. Please disconnect other instances.")
		
		elif (config == self.xem.FileError):
			raise ConnectionError("File error occurred during open or read.")
		
		elif (config == self.xem.InvalidBitstream):
			raise ConnectionError("The bitstream is not properly formatted.")
		
		elif (config == self.xem.DoneNotHigh):
			raise ConnectionError("FPGA DONE signal did not assert after configuration.")
		
		elif (config == self.xem.TransferError):
			raise ConnectionError("USB error has occurred during download.")
		
		elif (config == self.xem.CommunicationError):
			raise ConnectionError("Communication error with the firmware.")
		
		elif (config == self.xem.UnsupportedFeature):
			raise ConnectionError("Configuration call not supported on this device or in this configuration.")
		
		#Find information on connected device
		if (self.xem.NoError != self.get_device_info()):
			raise ConnectionError("Unable to retrieve information.")
		
		# Loads bit file and configures XEM 
		self.xem.LoadDefaultPLLConfiguration()
		if self.devInfo.productName != "XEM7310-A200":
			raise Exception("XEM7310-A200 was not detected")
		
		# Checks for FrontPanel and if device is open 
		if (self.xem.IsFrontPanelEnabled() == False):
			raise Exception("Front Panel support is unavailable.")
		print("Front Panel support is available.")
		print(f'Serial Number: {self.serialNumber}\n')
		

	def disconnect_TVS(self):
		#disconnect the device
		if self.connected:
			self.xem.Close()
			self.connected = 0
			print("TVS disconnected")
		else:
			print("Failed to disconnect, TVS is not connected.")
		return
	

	def get_version(self):
		if self.connected:
			return self.xem.ReadRegister(0x0000)
		else:
			print("TVS is not connected")
			return 0
	

	def get_device_info(self):
		# Get device information
		code = self.xem.GetDeviceInfo(self.devInfo)

		self._productName   = self.devInfo.productName
		self._deviceVersion = self.devInfo.deviceMajorVersion,self.devInfo.deviceMinorVersion
		self._serialNumber  = self.devInfo.serialNumber
		self._deviceID      = self.devInfo.deviceID
		return code
	
	@property
	def productName(self):
		return f"{self._productName}"
	
	@property
	def deviceVersion(self):
		return f"{self._deviceVersion[0]}.{self._deviceVersion[1]}"
	
	@property
	def serialNumber(self):
		return f"{self._serialNumber}"
	
	@property
	def deviceID(self):
		return f"{self._deviceID}"


	def reset_ber_test(self):
		# Reset the logic
		if self.connected:
			self.xem.SetWireInValue(0,0,0xffff_ffff)
			self.xem.UpdateWireIns()
			time.sleep(0.1) # pauses for 1/10 sec
			self.xem.SetWireInValue(0,1,0xffff_ffff)
			self.xem.UpdateWireIns()
		return


	def device_reset(self):
		# Reset the device
		if self.connected:
			self.xem.ResetFPGA()
			self.reset_ber_test()
			self.init_test_registers()
		return
	

	def init_test_registers(self):
		rel_offsets = self.xem.ReadRegister(0x0001)

		self._diff_a = (rel_offsets >> 0)  & 0x3f
		self._diff_b = (rel_offsets >> 6)  & 0x3f
		self._diff_c = (rel_offsets >> 12) & 0x3f
		self._single = (rel_offsets >> 18) & 0x3f

		self._ber_test_offset = 0x0008

		self._diff_a_offset = 0
		self._diff_b_offset = self._diff_a + self._diff_a_offset
		self._diff_c_offset = self._diff_b + self._diff_b_offset 
		self._single_offset = self._diff_c + self._diff_c_offset

		self._address_space = self._diff_a + self._diff_b + self._diff_c + self._single
		self.ber_test = np.empty([self._address_space, 3], dtype=float) 
		return


	def failsafe_status(self):
		self.reset_ber_test()
		# Check for device failures and create a list of failed pins
		regs = ok.okTRegisterEntries(4)

		for i in range(4):
			regs[i].address = 4 + i

		self.xem.ReadRegisters(regs)

		check_signals = []

		for i in range(4):
			status_bits = bin(regs[i].data)[2:].zfill(32)
			position = len(status_bits)*(i+1)

			for bit in status_bits:
				if bit != '1':
					check_signals.append(position-1)
				position -= 1
    
		check_signals.sort()
		return check_signals
	

	def read_test_registers(self):
		# reads the BER test registers
		regs = ok.okTRegisterEntries(self._address_space)

		for i in range(self._address_space):
			regs[i].address = self._ber_test_offset + i
			# print(regs[i].address)

		self.xem.ReadRegisters(regs)

		for i in range(self._address_space):

			error_count = (regs[i].data >> 0)   & 0x03ff_ffff
			delay_count = (regs[i].data >> 26)  & 0x001f

			# Theses are fixed values based on the TVS clock period
			if (i >= self._single_offset):
				divisor = 100_000
				period_ns = 200
			elif (i >= self._diff_c_offset):
				divisor = 7_500_000
				period_ns = 6.666
			else:
				divisor = 1_500_000
				period_ns = 6.666

			ber = error_count/divisor
			ns  = delay_count*period_ns

			self.ber_test[i][0] = ber if ber < 1 else 1.0
			self.ber_test[i][1] = ns
			self.ber_test[i][2] = (regs[i].data >> 31)  & 0x0001


	def print_offsets(self):
		try:
			print(f'Diff ep offset A: {self._diff_a_offset}')
			print(f'Diff ep offset B: {self._diff_b_offset}')
			print(f'Diff ep offset C: {self._diff_c_offset}')
			print(f'Single ep offset: {self._single_offset}\n')
			print(f'Test Address Space: {self._address_space}\n')
		except:
			print("Register offsets were not found")
	
	
	def print_test_registers(self):

		self.read_test_registers()
		
		print('')
		for i in range(self._diff_a_offset, self._diff_b_offset):
			ber =   self.ber_test[i][0]
			delay = self.ber_test[i][1]
			print(f'RS422 {i} ber: {ber:.3f}     delay: {delay:.0f}')

		print('')
		for i in range(self._diff_b_offset, self._diff_c_offset):
			ber =   self.ber_test[i][0]
			delay = self.ber_test[i][1]
			print(f'Uart  {i} ber: {ber:.3f}     delay: {delay:.0f}')

		print('')
		for i in range(self._diff_c_offset, self._single_offset):
			ber =   self.ber_test[i][0]
			delay = self.ber_test[i][1]
			print(f'LVDS  {i} ber: {ber:.3f}     delay: {delay:.0f}')

		print('')
		for i in range(self._single_offset, self._address_space):
			ber =   self.ber_test[i][0]
			delay = self.ber_test[i][1]
			print(f'TTL   {i} ber: {ber:.3f}     delay: {delay:.0f}')

	

if __name__ == "__main__":
	fp = FP_API()
	fp.get_device_info()

	print('')
	print(f'Product: {fp.productName}')
	print(f'Firmware Version: {fp.deviceVersion}')
	print(f'Serial Number: {fp.serialNumber}')
	print(f'Device ID: {fp.deviceID}')
	print(f'BER TVS version: {fp.get_version()}\n')

	fp.print_offsets()

	if (len(fp.failsafe_status()) != 0):
		print("Failsafe errors at signals:")
		print(fp.failsafe_status())
	else:
		print("Passed Faisafe Check")

	fp.print_test_registers()
	
	time.sleep(5)
	fp.disconnect_TVS()
	time.sleep(5)
	fp.connect_TVS(30)

	time.sleep(5)

