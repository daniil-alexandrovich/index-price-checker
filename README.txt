------------------------------
- MPIBEST20 INDEX VALIDATION -
------------------------------

This package validates price data for the MPI Best 20 Tracker Index. It downloads price information from the server and compares it against various financial data APIs, producing a report of discrepancies and sending it to the user via e-mail.

-------------------
- Getting Started -
-------------------

This package is compatible with Python 2.6+. Each of the external libraries used can be downloaded with pip:

    pip install alpha_vantage
    pip install quandl
    pip install pandas

----------------------
- Running Validation -
----------------------

Run check_data.py with the following command line arguments:

    * Username - personal username of MPI employee using the script. This will also be the recipient of the generated report.
    * Server password - password for 'mpiindex' user on 52.35.34.210.

This will download the most recent available price data to C:\MPIBEST20T--ensure that this directory exists before running. The script then compares each fund's price in each downloaded file to information on AlphaVantage or Quandl and compiles a report. This report is then sent to the user.
