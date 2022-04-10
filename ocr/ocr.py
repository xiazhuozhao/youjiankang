'''
Description: 
Author: Huang Wen
Date: 2022-04-09 12:34:10
LastEditTime: 2022-04-10 09:57:22
LastEditors: Huang Wen
'''
import re
import cv2
import easyocr
from pyzbar import pyzbar as pyzbar
import numpy as np

# 颜色范围定义
color_dist = {
    'red': {'Lower': np.array([0, 60, 60]), 'Upper': np.array([6, 255, 255])},
    'blue': {'Lower': np.array([100, 80, 46]), 'Upper': np.array([124, 255, 255])},
    'green': {'Lower': np.array([35, 43, 35]), 'Upper': np.array([90, 255, 255])},
}

# 检测颜色
def detect_color(image, color):
    gs = cv2.GaussianBlur(image, (5, 5), 0)  # 高斯模糊
    hsv = cv2.cvtColor(gs, cv2.COLOR_BGR2HSV)  # HSV
    erode_hsv = cv2.erode(hsv, None, iterations=2) # 腐蚀
    inRange_hsv = cv2.inRange(erode_hsv, color_dist[color]['Lower'], color_dist[color]['Upper'])
    contours = cv2.findContours(inRange_hsv.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    if len(contours) > 0: # 检测到相关颜色
        return True
    else:
        return False

# 提取二维码
def detect(img):
    barcodes = pyzbar.decode(img)
    for barcode in barcodes:
        # 提取二维码的边界框的位置
        # 画出图像中条形码的边界框
        (x, y, w, h) = barcode.rect
        # 目标区域y1:y2,x1:x2
        img_dst = img[y-5:y+h+5,x-5:x+w+5]
    return img_dst
        
def HS_OCR(img_path):
    '''识别核酸报告
    :param img_path: 待检测图片的路径
    :return 核酸结果,采样时间,检测时间
    '''
    # 读取图片
    img_original = cv2.imread(img_path,1)
    h, w = img_original.shape[:2]
    # 裁剪图片
    crop_img = img_original[int(0.2*h):int(0.55*h), :]
    # # 识别颜色
    # color_img = detect_color(crop_img,'green')
    
    # 识别文字内容
    try:
        reader = easyocr.Reader(['ch_sim'])
        result_ocr = reader.readtext(crop_img, paragraph="True")
    

        if len(result_ocr[1][1])==2:
            res_check=result_ocr[1][1]
            time=result_ocr[2][1]
        else:
            res_check=result_ocr[2][1]
            time=result_ocr[1][1]
        # 采样时间
        time_sampling=re.findall(r'(\d{4}-\d{2}-\d{2})',time)[0]
        # 检测时间
        time_detect=re.findall(r'(\d{4}-\d{2}-\d{2})',time)[1]
        return res_check,time_sampling,time_detect
    except Exception as e:
            return (0,0,0)


def JKM_OCR(img_path):
    '''识别健康码
    :param img_path: 待检测图片的路径
    :return 健康码颜色(green、yellow、red、Error)
    '''
    # 读取图片
    original_img = cv2.imread(img_path,1)
    try:
        # 提取二维码
        img_dst=detect(original_img)
        # 识别二维码颜色（检测绿色）
        color_qr = detect_color(img_dst,'green')
        # 识别文字内容
        reader = easyocr.Reader(['ch_sim'])
        result_ocr = reader.readtext(original_img, paragraph="True")
    except Exception as e:
        return -1
    # 数据处理
    temp_str=''
    for data in result_ocr:
        temp_str+=data[1]
    if '绿码' in temp_str and color_qr:
        return 0
    elif '黄码' in temp_str:
        return 1
    elif '红码' in temp_str:
        return 2
    else:
        return -1
    
# 测试代码    
import os
files=[]
for root, dirs, files in os.walk('./img_file'):
    pass
for file in files:
    if file[:2]=='HS':
        print(HS_OCR('img_file/'+file))
    else:
        print(JKM_OCR('img_file/'+file))