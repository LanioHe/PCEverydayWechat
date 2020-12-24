# 腾讯机器人的key
app_id='2160467528'               # 修改成自己的腾讯机器人的APPid
app_key='5p949pxgOh7oklhW'        # 修改成自己的腾讯机器人的APPkey
# 腾讯机器人经常返回空且不够智能的时候尝试调用图灵机器人，
# 可不填或填多个，因为图灵基本版本一个每天只能调用100
apikey_arr = ['6866e20ce6724adc99105dc801c2f860', 'cccc89863cd548668e79e6becdf01ed9'] # 修改成自己的图灵key
apikey_arr_index = 0
stupid_reply = 'emmmm，我不是很懂你的意思' # 当无法获取AI回复时的默认回复
reply_suffix = '[自动回复]'

import time, logging, random, requests
from PyWeChatSpy import WeChatSpy
import hashlib
import time
import requests
import random
import string
from urllib.parse import quote
from qqai.vision.picture import ImgToText
import re
from qqai import ImgToText

robot = ImgToText(app_id, app_key)

def curlmd5(src):
    m = hashlib.md5(src.encode('UTF-8'))
    return m.hexdigest().upper()               # 将得到的MD5值所有字符转换成大写

def get_params(plus_item):                    #用于返回request需要的data内容
    global params
    global app_id
    global app_key
    t = time.time()                                             #请求时间戳（秒级）,（保证签名5分钟有效）
    time_stamp=str(int(t))
    nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 10))            # 请求随机字符串，用于保证签名不可预测
    params = {'app_id':app_id,
              'question':plus_item,
              'time_stamp':time_stamp,
              'nonce_str':nonce_str,
              'session':'10000'}
    sign_before = ''
    for key in sorted(params):                      #要对key排序再拼接
        sign_before += '{}={}&'.format(key,quote(params[key], safe=''))    # 拼接过程需要使用quote函数形成URL编码
    sign_before += 'app_key={}'.format(app_key)                                           # 将app_key拼接到sign_before后
    sign = curlmd5(sign_before)
    params['sign'] = sign                                 # 对sign_before进行MD5运算
    return params                                              #得到request需要的data内容

def get_content(plus_item):
    global payload,r
    url = "https://api.ai.qq.com/fcgi-bin/nlp/nlp_textchat"         # 聊天的API地址
    plus_item = plus_item.encode('utf-8')
    payload = get_params(plus_item)
    r = requests.post(url,data=payload)
    result=r.json()["data"]["answer"]
    return result

# 图灵机器人返回消息
def reply_msg(receive_msg):
    global apikey_arr
    global apikey_arr_index
    if bool(apikey_arr) == False or apikey_arr_index > (len(apikey_arr) - 1):
        return stupid_reply
    apikey = apikey_arr[apikey_arr_index]
    apiurl = 'http://www.tuling123.com/openapi/api?key=%s&info=%s' % (apikey, receive_msg)
    result = requests.get(apiurl)
    result.encoding = 'utf-8'
    data = result.json()
    returnTxt = data['text']
    if returnTxt == '亲爱的，当天请求次数已用完。' and apikey_arr_index < len(apikey_arr) - 1:
        apikey_arr_index += 1
        returnTxt = reply_msg(receive_msg)
    else:
        returnTxt = stupid_reply
    return returnTxt

def auto_reply(msg):
    answer=get_content(msg)
    if answer=='':                                 #防止返回内容为空
        for i in range(2):
            time.sleep(3)
            answer=get_content(msg)
            if answer != '' and answer != stupid_reply:
                break
            else:
                answer = stupid_reply
    if answer == stupid_reply:
        answer = reply_msg(msg)
    return answer + reply_suffix

def auto_replyEmoji(msg):
    data = robot.run(msg)
    answer = data.get('data').get('text')
    if answer=='':                                 #防止返回内容为空
        for i in range(2):
            time.sleep(2)
            data = robot.run(msg)
            answer = data.get('data').get('text')
            if answer!='' and answer != stupid_reply:
                break
            else:
                answer = stupid_reply
    return answer + reply_suffix

# 识别图片URL
def lets_fuck_it(content):
    img_url_pattern = r'.+?*cdnurl\s*=\s*"(\S+)"' #img_url的正则式
    need_replace_list = re.findall(img_url_pattern, content)#找到所有的img标签
    return need_replace_list

def parser(data):
    # 获取文本信息
    if data.get("type") == 1:
        # spy.query_personal_info()  # 获取登录账号的个人信息
        print(data)  # 打印收到的信息
        if data.get('chatroom_ID'):  # 微信群消息
            chatroom_ID = data.get('chatroom_ID')  
            # 获取微信群idspy.send_text(chatroom_ID, '微信群消息自动回复测试！')  在此，你可以根据需要来设置消息的内容
        elif not data.get('chatroom_ID') and data.get('self') == 0 and data.get('msg_type') == 1:
            wx_ID = data.get('wx_ID')  # 好友消息
            spy.send_text(wx_ID, auto_reply(data.get('content')))  # 在此，你可以根据需要来设置消息的内容
        elif not data.get('chatroom_ID') and data.get('self') == 0 and data.get('msg_type') == 3:
            wx_ID = data.get('wx_ID')  # 好友消息
            spy.send_text(wx_ID, '图片……' + stupid_reply + reply_suffix)  # 在此，你可以根据需要来设置消息的内容
        elif not data.get('chatroom_ID') and data.get('self') == 0 and data.get('msg_type') == 47:
            wx_ID = data.get('wx_ID')  # 好友消息
            url = lets_fuck_it(data.get('content'))
            spy.send_text(wx_ID, auto_replyEmoji(url[0]) + reply_suffix)
    # 获取个人信息
    elif data.get("type") == 2:
        print(data)

if __name__ == '__main__':
    spy = WeChatSpy(parser=parser)
    spy.run()