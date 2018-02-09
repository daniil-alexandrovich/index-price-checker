'''Script to download .csv data for the MPIBest20 Tracker data from an MPI
server, compare it against data from financial data APIs, and e-mail the
results in a report. This takes two command line arguments:
    
    - Username - personal username of MPI employee using the script. This
                 will also be the recipient of the generated report.
    - Server password - password for 'mpiindex' user on 52.35.34.210.

Created on 2/9/2018 by Daniil Feoktistov for Markov Processes International, Inc.
'''

import os
import sys

from  csv_data  import CSVData
from  snetwork  import SNetworkFeed
from  datetime  import timedelta, datetime

if __name__ == '__main__':
    files_to_analyze = ['SNA', 'CLS.SNC']
    recipient = sys.argv[1]+'@markovprocesses.com'
    download_path = "C:\\MPIBEST20T"
    # Data will be fetched for the previous business day.
    dt = datetime.today()
    offset = -3 if dt.weekday() == 0 else -1
    prev_date = dt + timedelta(days=offset)    
    prev_date = prev_date.strftime("%Y%m%d")
    # Files are downloaded for the previous business day, the ones that we
    # don't want to analyze are filtered out.
    try:
        full_path = lambda filename: os.path.join(download_path, filename)
        include = lambda filename: any(pattern in filename for pattern in files_to_analyze)
        sn = SNetworkFeed(password=sys.argv[2], local_path=download_path)
        downloaded_files = sn.get_files(prev_date)
        filenames = [file for file in downloaded_files if include(file)]
        # If there are files to parse, a CSVData object loads each one in turn and
        # runs a comparison on the price data. The aggregated data is then exported
        # to a .csv report and mailed to recipient.
        if filenames:
            cs = CSVData()
            for filename in filenames:
                cs.load_csv(download_path, filename)
                cs.check_contents()
            print('\nAll tickers loaded.')    
            cs.generate_report(mail_to=recipient)
        # Otherwise, an alert is printed to the console.
        else:
            print('No data available for %s.' % prev_date)
    except Exception as e:
        print(e)