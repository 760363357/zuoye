import json
import requests
import re

if __name__ == '__main__':
    # 定义一些需要用到的数据
    filename = 'weibo_cookies.json'
    url_verification = 'https://weibo.com/u/3042680022/home'
    cookies_dict = {}
    # 读取文件的cookies并转化成cookie_jar格式
    with open(filename, 'r') as f:
        cookies = json.load(f)
    for cookie in cookies:
        cookies_dict[cookie['name']] = cookie['value']
    cookies_jar = requests.utils.cookiejar_from_dict(cookies_dict)
    # 创建session会话并传入cookie
    sess = requests.Session()
    sess.cookies = cookies_jar
    # 访问我的微博首页，根据状态码和标题即可知道该cookie是否可用。
    result = sess.get('https://weibo.com/u/3042680022/home')
    if result.status_code == 200:
        title = re.findall('<title>(.*?)</title>', result.text)[0]
        print(title)

