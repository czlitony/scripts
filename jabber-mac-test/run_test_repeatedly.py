"""
This file is used to do hello world service test
"""

import subprocess
import os
import sys
import time

def run_test(program):
    """do test"""
    start_time = time.time()

    command = program + " > repeat_test.log 2>&1"

    sp = subprocess.Popen(command, shell=True)
    sp.communicate()
    if sp.returncode != 0:
        return False, 0

    end_time = time.time()
    time_cost = end_time - start_time
    print("Time cost: " + str(time_cost) + " seconds")
    return True, time_cost

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("You need to run this script like this:\n   python run_test_repeatedly.py \"TestProgramName --gtest-filter=*\"")
    else:
        program = sys.argv[1]
        success_cnt = 0
        failure_cnt = 0
        total_time_cost = 0
        for index in range(1, 1 + 100):
            print('Running ' + program + ': ' + str(index))
            succeeded, time_cost = run_test(sys.argv[1])
            print('Succeeded: ' + str(succeeded))
            print('')
            if succeeded:
                success_cnt += 1
                total_time_cost += time_cost
            else:
                failure_cnt += 1
                if os.path.exists('current_log.txt'):
                    os.rename('current_log.txt', 'failure_' + str(time.time()) + '_current_log.txt')
        print('Success count: ' + str(success_cnt) + ', total time cost: ' + str(total_time_cost) + ', failure count: ' + str(failure_cnt))
