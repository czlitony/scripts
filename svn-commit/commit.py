import subprocess
import time


if __name__ == '__main__':
    cnt = 0
    time_start=time.time()

    while True:
        cnt = cnt + 1
        print 'Committing...'
        cmd = 'svn cleanup && svn up && svn commit -m "Merge Spark Client Framework integraion codes from branch https://wwwin-svn-sjc-3.cisco.com/jabber-all/jabber/branches/users/chengzhl/spabber"'

        ret = subprocess.call(cmd, shell=True)
        if ret == 0 or cnt > 100:
            break

    time_end=time.time()
    print '----------------------------------------------------'
    print 'Number of attempts: ', cnt
    print 'Time cost: ', (time_end-time_start)/60, '(min), ', time_end-time_start, '(s)'
    print '----------------------------------------------------'
