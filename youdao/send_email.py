# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.header import Header

def send_email(mail_msg):
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


if __name__ == "__main__":
    send_email('test')