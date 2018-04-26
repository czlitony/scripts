import os
import platform
import sys

def build(mode):
    if platform.system() == 'Windows':
        os.system('python patchbuild.py -p jabberwin --isolate jcf client -j 8 --cachedir=J:\SCONSCache -m ' + mode)
    elif platform.system() == 'Darwin':
        os.system('python patchbuild.py -p jabbermac --isolate jcf client -j 4 --cachedir=$HOME/SCONSCache -m ' + mode)

if __name__ == '__main__':
    mode = 'Release'
    if len(sys.argv) > 1:
        mode = 'Debug'

    build(mode)