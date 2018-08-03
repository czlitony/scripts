# -*- coding: UTF-8 -*-

import requests
from HTMLParser import HTMLParser
from threading import _Timer
import pygame

class LoopTimer(_Timer):
    """Call a function after a specified number of seconds: 
 
 
            t = LoopTi
            mer(30.0, f, args=[], kwargs={}) 
            t.start() 
            t.cancel()     # stop the timer's action if it's still waiting 
 
 
    """
 
    def __init__(self, interval, function, args=[], kwargs={}):
        _Timer.__init__(self, interval, function, args, kwargs)
 
    def run(self):
        '''self.finished.wait(self.interval) 
        if not self.finished.is_set(): 
            self.function(*self.args, **self.kwargs) 
        self.finished.set()'''
        while True:
            self.finished.wait(self.interval)
            if self.finished.is_set():
                self.finished.set()
                break
            self.function(*self.args, **self.kwargs)


taskstr = str()

class MyHTMLParser(HTMLParser):
    meet_task_name = False
    meet_claim_num = False
    meet_name = False
    meet_num = False

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if ('class', 'task-name') in attrs:
                self.meet_task_name = True
            if ('class', 'claim-num') in attrs:
                self.meet_claim_num = True
 
        if tag=='span':
            if self.meet_task_name:
                self.meet_name = True
            if self.meet_claim_num:
                self.meet_num = True

    def handle_endtag(self, tag):
        if tag=='div':
            self.meet_task_name = False
            self.meet_claim_num = False

        if tag=='span':
            self.meet_name = False
            self.meet_num = False

    def handle_data(self, data):
        global taskstr

        if self.meet_name:
            taskstr += str(data)
            taskstr += ': '

        if self.meet_num:
            taskstr += str(data)
            taskstr += '\n'

def get_youdao_task():
    url = 'https://f.youdao.com/ds/task.do?method=index'
    headers = {
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip, deflate',
        # 'Accept-Language': 'zh-Hans-CN,zh-Hans;q=0.8,en-US;q=0.5,en;q=0.3',
        'Cookie': 'OUTFOX_SEARCH_USER_ID=310822447@113.108.225.251; NTES_SESS=uFtYx58yRLaj9gXVCHaGEoMgrWPQH_90_PF21HdEQc0mpvFRpWZ9_iWVHdVhuKjFqRSaNGgnNS5zxq.GJWhVFTUAThMQ.t9JoR..XUAeAUW5SQ_M8Pb8sjdPzocjmvzRi0v1hSQVHPR3IjihVBEp.P3Pws5_8D0XU3qkvEULyHfvqMrorjHdcQF33c5KQPxinhAE8wqs8Vxoi; S_INFO=1533266440|0|3&80##|szhgloria#m15651635739_1#m18625085971; P_INFO=szhgloria@163.com|1533266440|0|dict_hts|00&99|jis&1533257113&dict_hts#US&null#10#0#0|&0|dict_hts&search&youdaodict_client|szhgloria@163.com; SESSION_FROM_COOKIE=unknown; JSESSIONID=aaaC_aDobhpl2hDNtZ9tw'
    }

    try:
        requests.packages.urllib3.disable_warnings()
        r = requests.get(url, headers=headers, verify=False)

        with open('response.html', 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

        text = str()
        with open('response.html', 'r') as fd:
            text = fd.read()

        par = MyHTMLParser()
        par.feed(text)
        # print taskstr

        return taskstr
    except:
        print "Failed to get youdao tasks! Please check your network."
        return None

def play_music(music):
    pygame.mixer.init()
    pygame.mixer.music.load(music)
    pygame.mixer.music.play(-1)

def stop_music():
    pygame.mixer.init()
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()

def print_task(task_nums):
    if task_nums[1] > 0:
        print 'File File File : ' + str(task_nums[1])
    if task_nums[0] > 0:
        print 'Quick : ' + str(task_nums[0])

def get_task_nums(tasks):
    # non_zero_number = filter(lambda ch: ch in '123456789', tasks)
    splited_tasks = tasks.split('\n')
    fast_task_num = int(splited_tasks[0].split(':')[-1])
    file_task_num = int(splited_tasks[1].split(':')[-1])

    return [fast_task_num, file_task_num]

if __name__ == "__main__":
    num = 0
    def fun_timer():
        global num
        num += 1
        if num > 2880: # 12 hours
            exit()

        print '------------------------------------------------------------'
        print str(num) + ' - Checking youdao translation tasks!'
        print ''

        tasks = get_youdao_task()

        if not tasks:
            return

        task_nums = get_task_nums(tasks)

        print_task(task_nums)

        if task_nums[1] > 0:
            play_music("Despacito.mp3")
        elif task_nums[0] > 0:
            play_music("Sunrise.wav")
        else:
            stop_music()

        global taskstr
        taskstr = str()
        print ''

    fun_timer()
    t = LoopTimer(15, fun_timer)
    t.start()
