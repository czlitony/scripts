"""
This file is used to do hello world service test
"""

import subprocess
import sys
import time

def run_test(program):
    """do test"""
    t0 = time.time()

    command = program + " > repeat_test.log 2>&1"

    sp = subprocess.Popen(command, shell=True)
    sp.communicate()
    if sp.returncode != 0:
        return False

    print("Finished: " + str(time.time() - t0) + " seconds\n")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("You need to run this script like this:\n   python run_test_repeatedly.py \"TestProgramName --gtest-filter=*\"")
    else:
        program = sys.argv[1]
        for index in range(1, 10000):
            print('Running ' + program + ': ' + str(index))
            if not run_test(sys.argv[1]):
                break
