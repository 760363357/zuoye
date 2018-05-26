from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# 创建微博登录类
class SinaLogin(object):
    # 通过用户名和密码来登录
    def __init__(self, user, pswd):
        self.user = user
        self.pswd = pswd
        self.option = webdriver.ChromeOptions()
        self.option.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(chrome_options=self.option)
        self.wait = WebDriverWait(self.driver, 10)

    # 登录函数，很容易看懂的
    def login(self):
        self.driver.get('https://weibo.com')
        try:
            user_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="loginname"]')))
            pswd_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="pl_login_form"]//input[@type="password"]')))
        except Exception as e:
            print('无法找到输入框', e)
            raise e
        else:
            time.sleep(1)
            user_input.clear()
            user_input.send_keys(self.user)
            time.sleep(1)
            pswd_input.clear()
            pswd_input.send_keys(self.pswd)
            time.sleep(1)
            login_button = self.driver.find_element_by_xpath('//*[@id="pl_login_form"]//a[@action-type="btn_submit"]')
            login_button.click()

    # 保存cookies到文件中
    def save_cookies(self, filename):
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//a[@bpfilter="page_frame"]')))
        except Exception as e:
            print('登录失败！请查看原因', e)
        else:
            cookies = self.driver.get_cookies()
            with open(filename, 'w') as f:
                json.dump(cookies, f)

    # 主要调用函数
    def __call__(self, *args, **kwargs):
        self.login()
        self.save_cookies(args[0])
        time.sleep(10)
        self.driver.quit()

if __name__ == '__main__':
    filename = 'weibo_cookies.json'
    login = SinaLogin('13025668791', 'qq11235')
    login(filename)