
#Imports 
import subprocess
import time
from ib_insync import *
from notify_run import Notify
import sys
import argparse
from datetime import datetime as dt


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



class AlertConfig: 

    '''Contains one alert configuration defined by the user 
    as index/stock ticker & lower/upper limit for notification'''

    def __init__(self, ticker, ll, ul, kind):
        self.ticker = ticker
        self.lower_limit = ll
        self.upper_limit = ul
        self.kind = kind
        self.req = Stock(ticker, 'SMART', 'USD') \
                   if self.kind == 'Stock' \
                   else CFD(ticker, 'SMART', 'USD') 
        self.ticker_count = 0


    def adjust_limits_up(self): 
        self.lower_limit *= 1.005
        self.upper_limit *= 1.005


    def adjust_limits_down(self): 
        self.lower_limit *= 0.995
        self.upper_limit *= 0.995


    def evaluate_alert(self, price):
        
        ''' Handles alert logic & prints every 6th ticker'''

        self.ticker_count += 1 
        if self.ticker_count % 6 == 0: 
            print(self.ticker,  'at', price, '$')

        if price > self.upper_limit: 
            self.send_alert('High', price)
        
        elif price < self.lower_limit: 
            self.send_alert('Low', price)

        return

    
    def send_alert(self, flag, price): 

        '''Sends notification & adjusts limits by 0.5%'''

        notify = Notify()

        if flag == 'High': 
            notify.send('Instrument {} > {}$'.format(self.ticker,self.upper_limit))
            self.adjust_limits_up()
        elif flag == 'Low': 
            notify.send('Instrument {} < {}$'.format(self.ticker,self.lower_limit))
            self.adjust_limits_down()
        
        print('{} alert sent for {} at {}$ ({}).'.format(flag, self.ticker, price,
                                                         dt.now().strftime('%H:%m')))
        print("New low: {}, new high {}".format(round(self.lower_limit,3),
                                                round(self.upper_limit),3))
        


class AlertHandler:

    '''Main Class: handles program logic, 
    contains multiple AlertConfig objects'''

    def __init__(self):
  
        self.alerts = []
        self.closing = 0 
        self.parse_arguments()
        self.ib = connect_ib()
        self.count = 0

    def add_alert(self, obj): 
        self.alerts.append(obj)
    

    def parse_arguments(self): 

        '''Parses command line args'''

        parser = argparse.ArgumentParser(
            description='Alert Setter Stocks/Indices')
        parser.add_argument('-s', 
            metavar='Stocks', type=str, nargs='*', default='',
            help=('Enter stocks to be monitored (e.g. "WAB").'))
        parser.add_argument('-i', 
            metavar='Indices', type=str, nargs='*', default='',
            help=('Enter IB-Index-CFDs to be monitored (e.g. "IBUS30").'))
        parser.add_argument('-nogateway', action='store_true',
            help=('If specified, IB Gateway will not be opened on startup.'))
        args = parser.parse_args()
        
        if list(args.s) + list(args.i) == ['']: 
            print('No stocks or indices entered as cmd-line arguments. '
                'Refer to -h for help.')
            sys.exit()   

        for s in args.s:
            alert_obj = self.handle_user_input(s, 'Stock')
            self.alerts.append(alert_obj)

        for i in args.i:
            alert_obj = self.handle_user_input(i, 'Index-CFD')
            self.alerts.append(alert_obj)

        self.request_closing()

        if not args.nogateway: 
            open_gateway()
        
        return


    def handle_user_input(self, t, kind): 

        '''Handles upper & lower limits inputs by user'''

        ll = input("Pls. enter lower limit for {} {}: ".format(kind,t))
        ul = input("Pls. enter upper limit for {} {}: ".format(kind,t))

        try: 
            ll, ul = float(ll), float(ul)
        except ValueError:
            print('Please enter digits only (comma seperation with ".").')
            self.handle_user_input(t, kind)

        return AlertConfig(t, ll, ul, kind)


    def request_closing(self): 

        '''Gives user the possibility to turn off ticker after closing hour'''

        closing = input('When should the ticker stop? ' 
            'Pls. enter integers for full hours (e.g. "22" for 22:00): ') 

        try: 
            closing = int(closing)
        except ValueError:
            print('Please enter integers only (e.g. "22" for 22:00).')
            self.request_closing()
        
        self.closing = closing


    def ticker_logic(self):
        
        '''Requests Market Prices'''
        tickers = []

        for i,config in enumerate(self.alerts):
            self.ib.reqMktData(config.req, '', False, False)
            tickers.append(self.ib.ticker(config.req))
            
        self.ib.sleep(2)
        
        for ticker,config in zip(tickers, self.alerts): 
            price = ticker.marketPrice()
            config.evaluate_alert(price)

            
    def main(self): 
        
        #Main Loop
        while True: 

            try: 
            
                self.ticker_logic()
            
                #Exit at full hour
                if dt.now().hour >= self.closing: 
                    self.ib.disconnect()
                    sys.exit()

            except KeyboardInterrupt: 
                
                print('KeyboardInterrupt at {}.'.format(dt.now().strftime('%H:%m')))
                self.ib.disconnect()
                sys.exit()


#Main 
if __name__ == "__main__": 
    AlertHandler().main()