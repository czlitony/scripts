# -*- coding: UTF-8 -*-

import requests
from HTMLParser import HTMLParser
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from twilio.rest import Client
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
        'Cookie': 'OUTFOX_SEARCH_USER_ID=310822447@113.108.225.251; DICT_LOGIN=8||1532605338270; DICT_FORCE=true; NTES_SESS=CQcM27ByGiblaZ4UR_lWChviPC7bTIf7X7hYgmEK2GSArOhUrIJ5LfIZmEZBCkzhRU.FQxV6Q.Nl8RXx9IBZhanDaBi2X359pZSAla82vI9H.2LiW7_WMzE7lpGzAOlUfSOgB.2Zm7UoezfBZyKrX7o7tMNLW4SqnoRwOKn0PmvORispszmEG2hooGNk278f6BDKWtRMWZ8pf; S_INFO=1532605445|0|3&80##|szhgloria#m15651635739_1#m18625085971; P_INFO=szhgloria@163.com|1532605445|0|dict_hts|00&99|US&1532604628&dict_hts#US&null#10#0#0|&0|dict_hts|szhgloria@163.com; SESSION_FROM_COOKIE=unknown; JSESSIONID=aaaAzIxR2Awro45JBnwtw'
    }

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

def send_mail(mail_msg):
    # sender = 'czlitony@163.com'
    # receivers = ['1271673214@qq.com']
    # mail_host = 'smtp.163.com'
    # mail_user = 'czlitony'
    # mail_pass = 'szhlcz1016'

    sender = '1271673214@qq.com'
    receivers = ["czlitony@163.com", "393592935@qq.com"]
    mail_host = 'smtp.qq.com'
    mail_user = '1271673214'
    mail_pass = 'avllcfcaihkogjii'

    # message = MIMEText(mail_msg, 'html', 'utf-8')
    message = MIMEText(mail_msg, 'plain', 'utf-8')
    message['From'] = sender
    message['To'] = ";".join(receivers)
    message['Subject'] = Header('有道翻译来任务了！', 'utf-8')

    try:
        server = smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_user, mail_pass)
        server.sendmail(sender, receivers, message.as_string())
        server.close()
        print "Send mail successfully"
    except smtplib.SMTPException as e:
        print e
        print "Error: Can't send mail"


# 使用Twilio的免费手机号发送短信
# 你需要在官网上申请一个账号，这里是官网：https://www.twilio.com/
def send_sms(msg='你好，这是来自自动发送的消息！'):
    # 从官网获得以下信息
    account_sid = 'AC02e7184da0252e678a6f4e68b47a6e6f'
    auth_token = '891894f90e30b33226a100050716650f'
    twilio_number = '+18142125134'
    my_number = '+8613262709358'

    account_sid = 'ACb4f3e0045754e807f9188909cb468084'
    auth_token = 'b583ecdaf05e175f5a48d838a4fa7eeb'
    twilio_number = '+18704744096'
    my_number = '+8618625085971'

    client = Client(account_sid, auth_token)
    try:
        client.messages.create(to=my_number, from_=twilio_number, body=msg)
        print('短信已经发送！')
    except:
        print('发送失败，请检查你的账号是否有效或网络是否良好！')


def play_music(isFileTask):
    pygame.mixer.init()
    music = "Despacito.mp3"
    if isFileTask:
        music = "Sunrise.wav"
    pygame.mixer.music.load(music)
    pygame.mixer.music.play()

def stop_music():
    pygame.mixer.init()
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()

def print_task(tasks):
    import sys
    reload(sys)
    sys.setdefaultencoding( "utf-8" )
    print tasks.decode('utf-8')

if __name__ == "__main__":
    num = 0
    def fun_timer():
        global num
        num += 1
        if num > 10000:
            exit()

        print '------------------------------------------------------------'
        print str(num) + ' - Checking youdao translation tasks!'

        tasks = get_youdao_task()

        print_task(tasks)

        non_zero_number = filter(lambda ch: ch in '123456789', tasks)
        if non_zero_number:
            if len(non_zero_number) > 1:
                play_music(True)
            else:
                play_music(False)
            # send_sms(tasks)
        else:
            stop_music()

        global taskstr
        taskstr = str()
        print ''

    t = LoopTimer(15, fun_timer)
    t.start()
