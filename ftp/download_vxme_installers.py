# -*- coding: utf-8 -*-
import os
import ftplib
from ftplib import FTP

# test comment

local_installer_path = os.path.expanduser("~") + "\\Desktop\\VxmeInstallers\\"
ftp_installer_path = '/FTPServer/users/chengzhl/VxmeInstallers'

FTP_SERVER = 'cmbu-ftp.cisco.com'
FTP_USERNAME = 'cmbu'
FTP_PASSWORD = 'cisco123!@#'

def mkdir(path):
    path=path.strip()
    path=path.rstrip("\\")

    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        print path + ' created.'
        return True
    else:
        print path + ' already exist.'
        return False


if __name__ == "__main__":
    mkdir(local_installer_path)

    try:
        ftp = FTP(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD)
        ftp.cwd(ftp_installer_path)
        remote_files = ftp.nlst()

        local_files = os.listdir(local_installer_path)
        download_files = list(set(remote_files)-set(local_files))

        if len(download_files) > 0:
            for download_file in download_files:
                local_file = os.path.join(local_installer_path, download_file)
                file = open(local_file, 'wb')
                ftp.retrbinary('RETR '+ download_file, file.write)
                file.close()
                print "Downloading file: " + download_file

            print "File downloaded" 
        else:
            print "No files need to be downloaded."

        ftp.quit()
    except:
        print "An error occured"
