'''
SNetworkFeed is a simple class to fetch price and asset data for the MPI Best
20 Tracker Index from an MPI server. 

Created on 2/7/2018 by Aleksey Matiychenko and Daniil Feoktistov for Markov
Processes International, Inc.
'''

import ftplib

from datetime import timedelta,datetime
from    os    import path, listdir

class SNetworkFeed:
    def __init__(self, *, password, local_path="."):
        self.server = '52.35.34.210'
        self.username = 'mpiindex'
        self.password = password
        self.local_path = local_path
        self.inbox = "/MPI_INDEXES/MBEST20T/Inbox"
    
    def ftp(self,cn=None):
        if cn is None:
            return ftplib.FTP(self.server, self.username, self.password) 
        return cn
    
    def send_file(self, *,filename, connection=None):     
        fullname = path.join(self.local_path, filename)
        with open(fullname,'rb') as fh:           
            self.ftp(connection).storbinary('STOR %s' %filename, fh)

    def send_files(self):
        files = listdir(self.local_path)
        with self.ftp() as cn:
            files = [f for f in files if 'MBEST20T' in f]
            for f in files:
                self.send_file(filename=cn,connection=cn)
            
    def get_files(self,pattern=None):
        '''Retrieves files from the server.'''
        with self.ftp() as cn:
            # A list of items in self.inbox is appended to the list of file
            # to check and download.
            cn.cwd(self.inbox)
            filelist = []
            cn.dir(filelist.append)
            downloaded_files = []
            for fileinfo in filelist:
                filename = fileinfo.split(" ")[-1]
                # Each filename is checked for a substring pattern. Only those
                # that contain this pattern will be downloaded.
                do_get = pattern is None or pattern in filename
                if do_get:
                    local_name = path.join(self.local_path, filename)
                    downloaded_files.append(filename)
                    with open(local_name,'wb') as file:
                        print("Downloading %s" % local_name)
                        cn.retrbinary('RETR %s' % filename, file.write)
            # A list of downloaded files is returned after the transfer completes.
            return downloaded_files
        

