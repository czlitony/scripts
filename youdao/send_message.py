# -*- coding: UTF-8 -*-

from twilio.rest import Client

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


if __name__ == "__main__":
    send_sms('test')