###############################################
#				TVS Pin Map					  #
###############################################
# Author: 	 	Matthaeus Gebauer			  #
# References: 	BER Hardwear Specification	  #
# Ingenion, LLC								  #
###############################################

import pandas as pd

class signal_map():
	def __init__(self, filePath="BER_TVS_pm.txt"):
		self.map = self.load_signal_map(filePath)
		

	def load_signal_map(self, file="BER_TVS_pm.txt"):
		# Opens a csv file and creates a dataframe
		pm = pd.read_csv(file, header=[3], delim_whitespace=True)
		pm = pm.infer_objects()
		pm['Info'] = pm['Info'].apply(lambda x: x[1:-1].split('|'))
		return pm
	

	def signals_per_connector(self, pin_map):
		# This method returns the total number of signals on each connector
		conn_list = self.get_connector_list()
		num_signals = []
		for item in conn_list:
			num_signals.append(len(pin_map[pin_map['Connector'] == item]))
		return num_signals
	

	def get_signals_per_connector(self):
		return self.signals_per_connector(self.map)


	def get_connector_list(self):
		# This method returns a sorted list of all connectors in the pin map
		connectorList = list(set(self.map['Connector']))
		connectorList.sort(key=lambda x: int(x.replace("J", "")))
		return connectorList
	

	def get_debug_info(self, signal):
		# This method returns the debug info associated with each signal
		info = self.map['Info'].iloc[signal]
		return info


if __name__ == "__main__":
	sm = signal_map()
	print(sm.map)

	print(sm.get_connector_list())
	print(sm.get_debug_info(5))
	print(sm.get_signals_per_connector())
