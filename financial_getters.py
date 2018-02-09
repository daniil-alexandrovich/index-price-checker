'''
AVData and QuandlData, both child classes of DataGetter, retrieve and store
historical price data for a given fund from AlphaVantage and Quandl, respectively.

Each DataGetter object shares the following objects:
    - load_data(ticker) - Loads historic price data as a pandas DataFrame.
    - price() - Returns price for a specific date from the loaded data.
    - loaded_ticker - The ticker of the fund whose data is currently loaded.

Since DataGetter is implemented as abstractly, it will be relatively easy to
add a getter for an additional data source should the need arise. 

Created on 2/8/2018 by Daniil Feoktistov for Markov Processes International, Inc.
'''

import quandl

from alpha_vantage.timeseries import TimeSeries
from         datetime         import datetime
from          pandas          import DataFrame
from           abc            import ABC, abstractmethod

class DataGetter(ABC):
    '''Encompasses getter subclasses for different data sources.'''
    def __init__(self):
        # Dictionary of Quandl-specific tickers to their parent database.
        # Both are necessary in order to get data from Quandl.
        self.quandl_db = {'IGLT':'LSE'}
        # An API key is necessary to retrieve data from AlphaVantage.
        self.av_key = 'FLOPHMSIC2BPEJDX'
        self.ts = TimeSeries(key = self.av_key)
        self.data = None
        self.loaded_ticker = None

    @abstractmethod
    def load_data(self,ticker):
        '''Loads data for input ticker.'''
        pass
    
    @abstractmethod
    def price(self,date,adjusted=False):
        '''Returns the price of loaded data at an input date.'''
        pass    

class QuandlData(DataGetter):     
    def load_data(self,ticker):
        '''Retrieves price data for an input ticker from Quandl.'''
        # Quandl lookup keys are of the form '<database>/<ticker>'.
        key = self.quandl_db[ticker] + '/' + ticker
        self.data = quandl.get(key)
        self.loaded_ticker = ticker
    
    def price(self,date,adjusted=False):
        '''Returns the price of the currently loaded data at the input date.'''
        if self.data is None:
            return None
        return self.data['Price'][date]


class AVData(DataGetter):
    def load_data(self,ticker):
        '''Retrieves price information for an input ticker from AlphaVantage.'''
        # ALphaVantage likes to give up on connections, so a request may take
        # a few tries to go through.
        while True:        
            try:
                hist, meta = self.ts.get_daily_adjusted(ticker)
                break
            except:
                print('Connection interrupted -- service unavailable. Attempting to reconnect.')
        # For consistency, date strings are reformatted to datetime. The data
        # retrieved from AV is then loaded into a pandas DataFrame.
        format_date = lambda s: datetime.strptime(s,"%Y-%m-%d")
        hist = {format_date(date):self.__clean_keys(hist[date]) for date in hist}
        self.data = DataFrame.from_dict(hist)
        self.loaded_ticker = ticker

    def price(self, date, adjusted=False):
        '''Returns the price of the currently loaded data at the input date.'''
        if self.data is None:
            return None
        close = 'close' if not adjusted else 'adjusted close'
        return self.data[date][close]

    def __clean_keys(self, keys):
        '''Strips AlphaVantage formatting from keys returned.'''
        new_keys = {}
        # Initially, the returned field names are in the format '1. <fieldname>'
        for old_key in keys:
            new_key = old_key.split('. ')[1]
            new_keys[new_key] = keys[old_key]
        return new_keys