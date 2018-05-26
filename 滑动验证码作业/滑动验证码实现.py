import time
import re
import numpy as np
import requests
import cv2 as cv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

"极验滑动验证码"
class Jeecap(object):
    # 初始化时传入虎啸的主页URL，设置浏览器参数以及等待对象
    def __init__(self, url_index):
        self.url_index = url_index
        self.option = webdriver.ChromeOptions()
        self.option.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(chrome_options=self.option)
        self.wait = WebDriverWait(self.driver, 10)

    # 获取注册页面，然后输入一个key并验证是否打开了注册窗口
    def get_reg(self, key):
        self.driver.get(self.url_index)
        try:
            reg_button = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="top"]/div/ul[2]/li[4]/a')))
        except Exception as e:
            print('获取注册按钮有误', e)
        else:
            reg_button.click()
            try:
                phone_number = self.wait.until(EC.visibility_of_all_elements_located((By.XPATH, '//*[@id="sms_username"]')))[0]
            except Exception as e:
                print('获取注册窗口有误', e)
            else:
                phone_number.send_keys(key)
                return True

    # 通过页面URL获取图片函数，并进行滑动操作
    def get_image(self):
        # 获取图片的URL
        try:
            de_image_divs = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="gt_cut_bg_slice"]')))
            no_image_divs = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="gt_cut_fullbg_slice"]')))
        except Exception as e:
            print('获取图片标签有误', e)
        else:
            de_image_url = re.findall('url\("(.*)"\)', de_image_divs[0].get_attribute('style'))[0]
            no_image_url = re.findall('url\("(.*)"\)', no_image_divs[0].get_attribute('style'))[0]
            de_position_list = [re.findall('position: -?(\d*)px -?(\d*)', div.get_attribute('style'))[0] for div in de_image_divs]
            no_position_list = [re.findall('position: -?(\d*)px -?(\d*)', div.get_attribute('style'))[0] for div in no_image_divs]

            # 通过图片url来获取灰度图片
            de_image = self.image_rgb(de_image_url, de_position_list)
            no_image = self.image_rgb(no_image_url, no_position_list)

            # 保存图片，以便验证和识别进行预操作,识别准确坐标预测可达95%以上
            cv.imwrite('de_image.png', de_image)
            cv.imwrite('no_image.png', no_image)

            # 两图片相减，得到差值矩阵
            img = no_image - de_image
            img_b = img > 200
            # 通过PS可得出一些干扰像素值，直接把大于200和小于200的像素值改为0
            row, col = np.nonzero(img_b)
            for i in range(len(row)):
                img[row[i], col[i]] = 0
            img_b = img < 80
            row, col = np.nonzero(img_b)
            for i in range(len(row)):
                img[row[i], col[i]] = 0
            # 将0除外的像素值改为255
            row, col = np.nonzero(img)
            for i in range(len(row)):
                img[row[i], col[i]] = 255
            # 遍历像素矩阵，从上到下获取最大的像素值的位置，max_loc[0]就是我们需要滑动的缺陷块在图片的x坐标
            min_val, min_loc, max_val, max_loc = cv.minMaxLoc(img)
            # 这个遍历max_loc区块坐标中y坐标值为max_loc[1]的所有x坐标上的非0像素值并统计，如果像素数量大于10，需要修改一下偏移量
            # 根据缺块的形状会识别出两种坐标，一种是区块的左上角坐标，一种是区块中间顶点的坐标。这里是一个修正操作，统一认为是左上角坐标
            if np.count_nonzero(img[max_loc[1]]) < 10:
                max_loc = (max_loc[0] - 22, max_loc[1])
            print('缺块坐标为：', max_loc)
            # 传入缺块的X坐标进行移动
            self.slide_button(max_loc[0])


    # 通过url和裁剪图片的坐标来获取完整的图片信息
    def image_rgb(self, url, position_list):
        # 通过url获取图片的二进制数据
        image_cen = requests.get(url)
        # 将二进制数据转成rgb图片格式的矩阵，此时其中图片的大小是116X312
        image_r = cv.imdecode(np.fromstring(image_cen.content, np.uint8), cv.IMREAD_COLOR)
        # 创建全部是0,116X260的矩阵，用于储存切割处理的图片
        image_pix = np.zeros((116, 260, 3), dtype=np.uint8)
        # 保存到新建图片左上角的位置
        row, col = (0, 0)
        # 对图片切割并储存到image_pix变量中
        for cur_col, cur_row in position_list[:26]:
            cur_row = int(cur_row)
            cur_col = int(cur_col)
            image_pix[row:row+58, col: col+10] = image_r[cur_row:cur_row+58, cur_col:cur_col+10]
            col += 10
        row = 58
        col = 0
        for cur_col, cur_row in position_list[26:]:
            cur_row = int(cur_row)
            cur_col = int(cur_col)
            image_pix[row:row+58, col: col+10] = image_r[cur_row:cur_row+58, cur_col:cur_col+10]
            col += 10
        # 返回灰度图片，方便处理
        return cv.cvtColor(image_pix, cv.COLOR_BGR2GRAY)

    # 滑动滑块，来完成验证操作
    def slide_button(self, position):
        try:
            # 找到滑动的滑块
            click_button = self.wait.until(EC.visibility_of_element_located((
                By.XPATH,
                '//*[@id="login-modal"]//div[@class="gt_slider"]/div[2]'
            )))
            # 点击并拿起滑块
            ActionChains(self.driver).click_and_hold(click_button).perform()
            # 根据生成的移动轨迹，逐步移动鼠标，其中-3是修正参数
            for i in self.slide_move(position - 3):
                ActionChains(self.driver).move_by_offset(
                    xoffset=i, yoffset=0).perform()
            # 松开鼠标
            ActionChains(self.driver).release().perform()
        except Exception as e:
            print('滑动滑块出错！')

    # 滑动轨迹计算，每一段都是一个小的位移，总位于是识别出来的位置，这个轨迹是参考老师你的，之前通过自己想过的用概率方式来
    # 确定速度的大小，不过还不是很完善，很容易被识别人机器操作，这个通过公式的方式来设置轨迹，还是有一点会被认为是机器，还有
    # 待完善。
    def slide_move(self, position):
        # 计算移动距离所需的时间间隔
        t = 0.2
        # 当前距离
        currtent = 0
        # 改变加速度的时间点
        mid = position * 3 / 5
        # 速度
        speed = 0
        # 移动距离的列表
        move_distance_list = []
        while currtent < position:
            if currtent < mid:
                a = 3
                # 距离的计算公式
                move_distance = speed * t + 0.5 * a * t * t
                # 将生成的移动距离添加到列表中
                move_distance_list.append(round(move_distance))
                speed += (a * t)
                currtent += move_distance
            else:
                # 当距离大于五分之三的position时，添加减速轨迹，并跳出循环
                move_distance_list.extend([3, 3, 2, 2, 1, 1])
                break
        # 识别当前总共移动距离是大于还是小于position
        # 大于则补连续的-1，小于则补连续的1
        offset = sum(move_distance_list) - position
        if offset > 0:
            move_distance_list.extend([-1 for i in range(offset)])
        elif offset < 0:
            move_distance_list.extend([1 for i in range(abs(offset))])

        # 模拟终点附近的左右移动
        move_distance_list.extend(
            [0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, 0, 0, 0, 0, 0, 1, 1])
        return move_distance_list

    # 通过对象调用来调用该函数执行
    def __call__(self, *args, **kwargs):
        key = '18888888888'
        stat = self.get_reg(key)
        if stat:
            self.get_image()
        time.sleep(2)
        self.driver.save_screenshot('screen1.png')
        self.driver.quit()


if __name__ == '__main__':
    url_index = 'https://www.huxiu.com'
    jee = Jeecap(url_index)
    jee()


