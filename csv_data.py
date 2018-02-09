'''
CSVData loads asset data for the MPIBEST20 tracker indes from .csv files
and compares it to prices provided by financial data APIs. In addition, the
class can generate a .csv report of differences between these two data souces
and e-mail it to an MPI employee.

Created on 2/8/2018 by Daniil Feoktistov for Markov Processes International, Inc.
'''

import smtplib
import csv
import os
import time

from email.mime.multipart import MIMEMultipart
from    email.mime.text   import MIMEText
from      email.utils     import formatdate
from   financial_getters  import AVData, QuandlData
from       datetime       import datetime

'''
TODO: Implement pymongo to write results to an internal database, maybe.
TODO also: Eventually, we'll have this calculate price data for a portfolio
      comprised of these funds.
'''

class CSVData:
    '''Gets price data for indices from internal MPI CSV file and compares it
    to data available from financial APIs.'''
    def __init__(self):
        # id is one of two values (SNA or SNC), each of which refers to a
        # different formatting for input data.
        self.id = None
        self.data = None
        self.date = None
        # AlphaVantage price data on international funds can vary in whether it
        # refers to index or price data, depending on the region.
        self.price_column = {'DE' : 'LOCAL PRICE',
                             'L'  : 'INDEX PRICE'}
        # Suffixes indicating local markets are stripped from the RIC to
        # produce a ticker. International markets keep their RIC suffix.
        self.local_markets = ('OQ', 'P')
        # Data is fetched from AlphaVantage unless it is strictly available on
        # Quandl.
        self.quandl_tickers = ('IGLT')
        self.prices = {}
    
    def load_csv(self, path, filename):
        '''Loads an input .csv file as a dictionary.'''
        format_date = lambda s: datetime.strptime(s,"%Y%m%d")
        # Downloaded filenames begin with a date formatted as YYYYMMDD.
        self.date = format_date(filename[:8])
        # Additionally, the end of each filename is <3-character ID>.csv.
        self.id = filename[-7:-4]
        self.data = {}
        with open(os.path.join(path,filename)) as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['RIC']:
                    self.data[row['RIC']] = row
        print("\nLoaded %s" % (filename))
        
        
    def compare(self, RIC):
        '''Compares price data for a particular RIC in the CSV to data obtained
        from a financial API.'''
        # RICs follow <ticker>.<suffix> formatting. Their lookup key in
        # AlphaVantage is <ticker> if the index is provided by an American
        # exchange and <ticker>.<suffix> if international.
        ticker, suffix = RIC.split('.')
        if ticker not in self.quandl_tickers and suffix not in self.local_markets:
            ticker = RIC
        api = QuandlData() if ticker in self.quandl_tickers else AVData()
        # Data for the indicated RIC is loaded into the API wrapper and timed.
        t0 = time.time()
        if api.loaded_ticker != ticker:
            api.load_data(ticker=ticker)
        t = time.time()
        # The name of the column containing price data is determined by id and RIC.
        # SNC.csv files store price under 'INDEX PRICE' unless otherwise indicated.
        if self.id == 'SNC':
            if suffix in self.price_column:
                column = self.price_column[suffix]
            else:
                column = 'INDEX PRICE'
        # SNA.csv files store price information under 'CURRENT PRICE'.
        elif self.id == 'SNA':
            column = 'CURRENT PRICE'
        # Finally, .csv data is compared to API data (if it exists) and returned.
        csv_price = float(self.data[RIC][column])
        if self.date not in api.data:
            print('Warning: %s data not provided for %s' % (self.date.date(), ticker))
            return ticker, csv_price, None
        else:
            api_price = float(api.price(date = self.date))
        print('Received %s in %.2f sec' % (ticker, t-t0))
        return ticker, csv_price, api_price
    
    def check_contents(self):
        '''Constructs an internal dictionary (self.prices) mapping each index
        in the loaded .csv file to its internal and public price data.'''
        for RIC in self.data:
            ticker, csv_price, api_price = self.compare(RIC)
            self.prices[RIC] = {'Ticker'    :ticker, 
                                'CSV Price' :csv_price,
                                'API Price' :api_price if api_price else 'NA',
                                'Difference':csv_price-api_price if api_price else 'NA'}
    
    def generate_report(self, mail_to=None):
        '''Generates a .csv report from price data as compiled by self.check_contents. 
        
        The output report is a .csv table with headers Ticker, CSV Price, API
        Price, and Difference. This is then sent via e-mail if a recipient
        address is indicated in mail_to.
        '''
        filename = 'MPIBEST20_%s%s%s.csv' % (self.date.year, self.date.month, self.date.day)
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Ticker', 'CSV Price', 'API Price', 'Difference']
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csv_writer.writeheader()
            for RIC in self.prices:
                csv_writer.writerow(self.prices[RIC])
        print('\nData written to %s' % filename)
        if mail_to:
            self.send_email(filename=filename, recipient=mail_to)
    
    def send_email(self, *, filename, recipient):
        '''Sends an indicated text file from MPIBEST20@gmail.com to recipient.'''
        mail_from = 'Index Price Check'
        username = 'MPIBEST20'
        password = 'mpiindex'     
        # The message document is generated and file attached using MIME.
        msg = MIMEMultipart()
        msg['From'] = mail_from
        msg['To'] = recipient
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = 'MPI BEST 20 Price Check %s' % self.date.date()
        with open(filename, 'r') as file:
            attachment = MIMEText(file.read())
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(attachment)
        # This message is then sent from gmail using SMTP.
        smtp = smtplib.SMTP('smtp.gmail.com:587')
        smtp.ehlo()
        smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(mail_from, recipient, msg.as_string())
        smtp.close()
        print('\n%s sent to %s' % (filename, recipient))
