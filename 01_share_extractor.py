
#Imports
import pandas as pd
import subprocess
import time
from ib_insync import *
import sys 
import argparse
import os
import datetime as dt
from modules.timeit import timeit


#Global variables to be adjusted
MY_GATEWAY_LOCATION = 'C:/IBC/StartGateway.bat'
MY_GATEWAY_PORT = 4002
CFD_FILE = 'cfd/cfd_batch1_usa_part1.csv' #sample batch


def open_gateway(): 

	'''Called if -nogateway unspecified'''

	subprocess.call([MY_GATEWAY_LOCATION])
	time.sleep(30)


def connect_ib():
	
	'''Connects to IB API'''

	ib = IB()
	ib.connect('127.0.0.1', MY_GATEWAY_PORT, clientId=125)
	print("Connected to Gateway.") 
	return ib


class MovingShareExtractor: 


	def __init__(self, m="NYSE"):
		self.end_dates, self.lower_limit = self.parse_arguments()
		self.ib = connect_ib()
		self.m = m
		self.contracts = self.get_contracts()
		self.high_path, self.low_path = self.get_output_paths()


	def parse_arguments(self): 
		
		''' Parses command line args '''
		
		parser = argparse.ArgumentParser(description='Mover Shares Extractor: +/-4%')
		today = dt.date.today().strftime("%Y%m%d") 
		parser.add_argument('dates', 
			type=str, nargs='+',
			help=('Datetime string list, format: "20180825" (incl. quotes), data of the '
				'5 trading days before incl. the date entered will be extracted.')) 
		parser.add_argument('-ll', 
			metavar='L', type=int, nargs='?', default=0,
			help=('Lower line boundary in <CFD_FILE> for CFDs to be extracted.')) 
		parser.add_argument('-nogateway', action='store_true',
			help=('If specified, IB Gateway will not be opened on startup.'))
		args = parser.parse_args()

		if not args.nogateway: 
			open_gateway()
		return args.dates, args.ll


	def get_contracts(self): 
		
		'''Returns pd.Series of share contracts to be iterated through'''
		
		df = pd.read_csv(CFD_FILE, header=None)
		return df[1][self.lower_limit:]


	def get_output_paths(self):

		'''Generates file path for output'''

		i = j = 1
		while os.path.exists("csv/master/master-h-{}.csv".format(i)):
			i += 1	
		while os.path.exists("csv/master/master-l-{}.csv".format(j)):
			j += 1	
		return ("csv/master/master-h-{}.csv".format(i),
				"csv/master/master-l-{}.csv".format(j))


	def request_contract(self, c, end_date): 

		''' Requests a single contract from IB API '''

		contract = Stock(c, 'SMART', 'USD')
		bars = self.ib.reqHistoricalData(
				contract,
				endDateTime = '{} 23:59:59'.format(end_date),
				durationStr = '6 D',
				barSizeSetting = '30 secs',
				whatToShow = 'TRADES',
				useRTH = True,
				formatDate = 1)
		df = util.df(bars)
		return df

	
	def store_date(self, df, c, loc, highlow):

		'''Writes mover date, market, contract in csv'''

		d = str(df.iloc[loc+1].date)[:10]
		print("Logged {} as {} on {}.".format(c,highlow,d))
 
		if highlow == "high":
			with open(self.high_path, 'a') as csv:
				csv.write(d+","+self.m+","+c+"\n")
		elif highlow == "low": 
			with open(self.low_path, 'a') as csv:
				csv.write(d+","+self.m+","+c+"\n")


	def handle_dataframe(self, df, c): 

		'''Calculates potential high/low days'''
		
		for loc in [779, 1559, 2339, 3119, 3899]: 
			
			#Calculate if +/- 4%
			try: 
				close = df.iloc[loc].close
				minimum = min(df.iloc[loc+1:loc+780].low)
				maximum = max(df.iloc[loc+1:loc+780].high)

				if maximum / close > 1.04: 
					self.store_date(df,c,loc,"high")
				elif minimum / close < 0.96: 
					self.store_date(df,c,loc,"low")

			#CFD now available, but not at the time requested
			except ValueError: 
				print("Raised Value Error on {}".format(c))
				break
			except IndexError: break

	@timeit
	def main(self): 

		'''Main Logic'''

		for c in self.contracts:

			#Load contract data in df
			for date in self.end_dates:

				df = self.request_contract(c,date)
				print("Contract {} running.".format(c))
				
				#Check if CFD generally available
				if df is not None: 
					self.handle_dataframe(df,c)
				else: 
					print("Contract {} not found. Pls delete from DB.".format(c))

		self.ib.disconnect()


#Main
if __name__ == "__main__":
	MovingShareExtractor().main()
	