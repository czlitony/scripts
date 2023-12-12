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
        success_cnt = 0
        failure_cnt = 0
        total_time_cost = 0
        for index in range(1, 1 + 100):
            print('Running ' + program + ': ' + str(index))
            start_time = time.time()
            succeeded = run_test(sys.argv[1])
            end_time = time.time()
            time_cost = end_time - start_time
            print('succeeded: ' + str(succeeded) + ', time cost: ' + str(time_cost))
            if succeeded:
                success_cnt += 1
                total_time_cost += time_cost
            else:
                failure_cnt += 1
        print('success_cnt: ' + str(success_cnt) + ', total time cost: ' + str(total_time_cost) + ', failure_cnt: ' + str(failure_cnt))
