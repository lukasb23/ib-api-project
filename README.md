
## ib-api-project

The *ib-api-project* got a little bit more than a fun side project for playing around with stock data... 
A big thanks goes to Ewald de Wit for creating the great Python framework [ib_inysnc](https://github.com/erdewit/ib_insync),
massively simplyfying the interaction with the - not always intuitive - Interactive Brokers API. In this repo, you'll find 
a little part of the things I did with [ib_inysnc](https://github.com/erdewit/ib_insync) and the IB API, which might help 
getting the workflow more easily when you're starting out. 

The first two programs (*01_share_extractor.py*, *02_file_generator.py*) extract historical stock data - in particular moving shares, 
i.e. shares that were at least 4% up or down at a certain trading day - as csv-files into the local directory. 

The third program (*03_alert_setter.py*) started as a workaround (I couldn't figure out how to use IB's SMS Alert Service with my
mobile phone provider). Depending on the instruments defined as command line-args, it sends price-alerts during trading hours as push-notifications to your smartphone. 
It uses the very simple [notify-run](https://notify.run/) as a third party push-service. 

Some remarks: 
- All three programs require command-line arguments (see -h for help). 
- They currently focus on US Stocks, but could of course be easily extended to other markets.
- When talking about CFDs, I herin solely refer to Stock CFDs. It might also happen that I use the terms "stocks" and "CFDs" in comments/descriptions interchangeably - 
both of course, always refer to the same underlying instrument (i.e. a stock ;-) ).
- My environment is Windows running [IBC](https://github.com/IbcAlpha/IBC) and IB Gateway on port 4002. The IB Gateway is opened over the corresponding .bat file at the beginning of every script. Depending on your system, you'll need to define your IB Gateway location & port as global variables 'MY_GATEWAY_LOCATION' and 'MY_GATEWAY_PORT' directly in the source code.


### 01_share_extractor.py: Share Extractor

The Share Extractor captures US Movers (+/- 4%) during one trading week by iterating through the stocks defined in the 'CFD_FILE'.
The path to the CFD file needs to be specified in the source code under 'CFD_FILE'.
 
It returns a simple master file as .csv, where stock, date and market are stored, either in:
- csv/master/master-l-{}.csv
- csv/master/master-h-{}.csv 

Those 'batches' are incremented and are further processed in *02_file_generator.py*.


### 02_file_generator.py: Stock File Generator 

The File Generator captures the collected US Movers from the batch extracted in *01-share-extractor* and given as command-line-arg. It
returns 14d stock prices (3d before the focus day, 1 focus day and 9 days after) in either:
- csv/files_high
- csv/files_low
(depending if high or low mover)
It skips files that are already present in output directory.


### 03_alert_setter.py: Alert Setter for US Markets 
  
The alert setter requires installation and configuration of [notify-run](https://notify.run/) 
to enable push notifications to your smartphone. 

During trading hours, you're supposed to define the instruments you'll want to monitor as command line args. Note that the command line args
are different for Index-CFDs and Stocks (-i and -s respetively). After launching the program, you'll be prompted to define upper and lower boundaries for notification 
for every instrument you entered as command line arg.
If the price of the stock or index is above/below the defined threshold, you're alerted once and the upper/lower boundaries are adjusted by 0.5%. 

Of course, the usage makes more sense for markets with a corresponsing market data subscription of Interactive Brokers. 


