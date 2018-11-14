
#Imports
import pandas as pd
import subprocess
import time
from ib_insync import *
import argparse
import sys 
import os
from datetime import datetime as dt
from modules.nyse_calendar import get_nyse_calender
from modules.timeit import timeit


#Global variables to be adjusted
MY_GATEWAY_LOCATION = 'C:/IBC/StartGateway.bat'
MY_GATEWAY_PORT = 4002


def open_gateway(): 

	'''Called if -nogateway unspecified'''

	subprocess.call([MY_GATEWAY_LOCATION])
	time.sleep(30)


def connect_ib():
	
	'''Starts Gateway and Connects to IB API'''

	ib = IB()
	ib.connect('127.0.0.1', MY_GATEWAY_PORT, clientId=126)
	print("Connected to Gateway.") 
	return ib



class FileGenerator: 

	'''One FileGenerator object per batch, 
	contains file-generating logic'''

	def __init__(self, batch, ib, m="NYSE"):

		self.batch = batch
		self.ib = ib
		self.output_path = ("csv/files_low" 
			if self.batch.startswith("l") 
			else "csv/files_high")
		self.m = m


	def request_contract(self, c, end_date): 

		'''Requests individual contracts'''
		
		contract = Stock(c, 'SMART', 'USD')
		end_date = end_date.replace("-", "")
		bars = self.ib.reqHistoricalData(
				contract,
				durationStr='14 D',  #get 3D pre- & +10D post drop date
				endDateTime="{}".format(end_date), #preformatted
				barSizeSetting='30 secs',
				whatToShow='TRADES',
				useRTH=True,
				formatDate=1)
		df = util.df(bars)
		return df


	@timeit
	def generate_files(self): 

		'''File gnererating logic'''

		trading_days = get_nyse_calender()

		master_df = pd.read_csv("csv/master/master-{}.csv"
			.format(self.batch), header=None)

		for row in master_df.itertuples(): 
			
			file = "-".join([row[1],row[2],row[3]])+".csv" 

			#Enter only if not exists (integrity)
			if not os.path.exists("{}/{}".format(self.output_path,file)):

				print("Working on {}, {}.".format(row[3],row[1]))
				end_date = str(dt.strptime(row[1], "%Y-%m-%d") 
					+ 11*trading_days)
				df = self.request_contract(row[3],end_date)

				#Save csv
				try: 
					df.to_csv("{}/{}".format(self.output_path,file))
				except AttributeError: 
					pass

			else: pass



class BatchHandler: 

	''' Contains all user-defined batches and handles program logic'''

	def __init__(self):

		self.batches = self.parse_arguments()
		print(self.batches)
		self.ib = connect_ib()


	def parse_arguments(self): 

		''' Parses command line args '''

		parser = argparse.ArgumentParser(
			description='Mover Shares Data Generator: +/-4%')
		parser.add_argument('batchcodes', 
			type=str, nargs='+', default='',
			help=('Enter batchcode(s) (e.g. "l-1" for low batch 1,'
				'"h-2" for high batch 2 etc). Refer to "csv/master/" '
				'directory for available batches.'))
		parser.add_argument('-nogateway', action='store_true',
			help=('If specified, IB Gateway will not be opened on startup.'))
		args = parser.parse_args()

		if not args.nogateway: 
			open_gateway()

		return args.batchcodes 


	@timeit
	def main(self): 

		''' Program Logic '''

		for batch in self.batches:

			print("---------- Working on Batch {} ----------".format(batch))
			FileGenerator(batch, self.ib).generate_files()

		ib.disconnect()



#Main 
if __name__ == "__main__":

	BatchHandler().main()