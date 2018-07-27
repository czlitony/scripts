# -*- coding: UTF-8 -*-

import requests
from HTMLParser import HTMLParser
import smtplib
from email.mime.text import MIMEText
from email.header import Header

taskstr = str()

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print "Start tag:", tag
        for attr in attrs:
            print "     attr:", attr

    def handle_endtag(self, tag):
        print "End tag  :", tag

    def handle_data(self, data):
        print "Data     :", data

# class MyHTMLParser(HTMLParser):
#     tempstr=str()

#     def handle_starttag(self, tag, attrs):
#         if tag=='<div class="task-name">':
#             self.tempstr=''
 
#     def handle_endtag(self, tag):
#         if tag=='</div>':
#             matchObj = re.match( r'task-name', self.tempstr)
#             if matchObj:
#                 taskstr += (':' +self.tempstr)
 
#             matchObj = re.match( r'claim-num', self.tempstr)
#             if matchObj:
#                 taskstr += (':' +self.tempstr)

#     def handle_data(self, data):
#         if(data.isspace()==False):
#             self.tempstr+=data+'\t'

def get_youdao_task():
    url = 'https://f.youdao.com/ds/task.do?method=index'
    headers = {
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip, deflate',
        # 'Accept-Language': 'zh-Hans-CN,zh-Hans;q=0.8,en-US;q=0.5,en;q=0.3',
        'Cookie': 'OUTFOX_SEARCH_USER_ID=310822447@113.108.225.251; DICT_LOGIN=8||1532605338270; DICT_FORCE=true; NTES_SESS=CQcM27ByGiblaZ4UR_lWChviPC7bTIf7X7hYgmEK2GSArOhUrIJ5LfIZmEZBCkzhRU.FQxV6Q.Nl8RXx9IBZhanDaBi2X359pZSAla82vI9H.2LiW7_WMzE7lpGzAOlUfSOgB.2Zm7UoezfBZyKrX7o7tMNLW4SqnoRwOKn0PmvORispszmEG2hooGNk278f6BDKWtRMWZ8pf; S_INFO=1532605445|0|3&80##|szhgloria#m15651635739_1#m18625085971; P_INFO=szhgloria@163.com|1532605445|0|dict_hts|00&99|US&1532604628&dict_hts#US&null#10#0#0|&0|dict_hts|szhgloria@163.com; SESSION_FROM_COOKIE=unknown; JSESSIONID=aaaAzIxR2Awro45JBnwtw'
    }

    r = requests.get(url, headers=headers, verify=False)

    with open('response.txt', 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

    text = str()
    with open('response.txt', 'r') as fd:
        text = fd.read()

    par = MyHTMLParser()
    print text
    par.feed(text)
    print taskstr

    return text

def send_mail(mail_msg):
    # sender = 'czlitony@163.com'
    # receivers = ['1271673214@qq.com']
    # mail_host = 'smtp.163.com'
    # mail_user = 'czlitony'
    # mail_pass = 'szhlcz1016'

    sender = '1271673214@qq.com'
    receivers = ["czlitony@163.com"]
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


if __name__ == "__main__":
    # message = get_youdao_task()
    # send_mail(message)