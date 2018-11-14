#Imports
from pandas.tseries.offsets import CustomBusinessDay
from modules import nyse_module as nyse


def get_nyse_calender():

	''' Adjusts pandas calender to NYSE calender'''

	nyse_days = CustomBusinessDay(
		calendar=nyse.NYSEExchangeCalendar().regular_holidays)
	return nyse_days