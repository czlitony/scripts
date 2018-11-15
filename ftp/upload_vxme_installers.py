# -*- coding: utf-8 -*-
import os
import time
import shutil
import ftplib
from ftplib import FTP

jabber_project_path = 'J:\\jabber\\vxme_mra\\'
ftp_installer_path = '/FTPServer/users/chengzhl/VxmeInstallers'

TEMP_INSTALLER_PATH = os.path.expanduser("~") + "\\Desktop\\VxmeInstallers\\"
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

def TimeStampToTime(timestamp):
    timeStruct = time.localtime(timestamp)
    return time.strftime('%m-%d_%H_%M_%S',timeStruct)

def get_FileModifyTime(filePath):
    filePath = unicode(filePath,'utf8')
    t = os.path.getmtime(filePath)
    return TimeStampToTime(t)

def copy_file(src, dst):
    copied_file = dst + get_FileModifyTime(src) + "_" + os.path.basename(src)
    shutil.copy(src, copied_file)

def prepare_installers():
    mkpath = TEMP_INSTALLER_PATH
    mkdir(mkpath)

    copy_file(jabber_project_path + 'products\\jabber-virtualization\\Installers\\vxme-agent\\Output\\CiscoJVDIAgentSetup.msi', mkpath)
    copy_file(jabber_project_path + 'products\\jabber-win\\installation\\Output\\CiscoJabberSetup.msi', mkpath)


if __name__ == "__main__":
    prepare_installers()

    try:
        ftp = FTP(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD)
        ftp.cwd(ftp_installer_path)

        remote_files = ftp.nlst()
        local_files = os.listdir(TEMP_INSTALLER_PATH)
        installers = list(set(local_files)-set(remote_files))

        if len(installers) > 0:
            for installer in installers:
                file = open(os.path.join(TEMP_INSTALLER_PATH, installer), 'rb')
                ftp.storbinary('STOR ' + installer, file)
                file.close()
                print "Uploading file: " + installer

            print "File transfered"
        else:
            print "No files need to be uploaded."

        ftp.quit()
    except:
        print "An error occured"
