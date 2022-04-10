'''
Description: 
Author: Huang Wen
Date: 2022-04-09 13:37:59
LastEditTime: 2022-04-09 23:56:41
LastEditors: Huang Wen
'''
import cv2
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