from __future__ import print_function

import numpy as np
import cv2 as cv
import math
import time

import queue
import threading

face_cascade = cv.CascadeClassifier("haarcascade_frontalface_default.xml")

def imageproc(img):
    img_after = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    
    return img_after

def deg_thread1(q1, img):
    ave = 0
    rgx = int(320/2)
    rgy = int(240/2)
    for i in range(0, rgy, 4):
        for j in range(0, rgx, 4):
            r,g,b = img[i][j]
            if r == g and r == b:
                if r > 30 and r < 180:
                    ave += 1
    q1.put(ave)
    
def deg_thread2(q2, img):
    ave = 0
    rgx = int(320/2)
    rgy = int(240/2)
    for i in range(rgy, 240, 4):
        for j in range(0, rgx, 4):
            r,g,b = img[i][j]
            if r == g and r == b:
                if r > 70 and r < 170:
                    ave += 1
    q2.put(ave)
    
def deg_thread3(q3, img):
    ave = 0
    rgx = int(320/2)
    rgy = int(240/2)
    for i in range(0, rgy, 4):
        for j in range(rgx, 320, 4):
            r,g,b = img[i][j]
            if r == g and r == b:
                if r > 30 and r < 180:
                    ave += 1
    q3.put(ave)

def deg_thread4(q4, img):
    ave = 0
    rgx = int(320/2)
    rgy = int(240/2)
    for i in range(rgy, 240, 4):
        for j in range(rgx, 320, 4):
            r,g,b = img[i][j]
            if r == g and r == b:
                if r > 30 and r < 180:
                    ave += 1
    q4.put(ave)
    
def main():
    import sys
    try:
        fn = sys.argv[1]
    except IndexError:
        fn = 0
    
    cam = cv.VideoCapture("udpsrc port=5005 ! application/x-rtp,media=video,encoding-name=H264 ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! appsink")
    
    q1 = queue.Queue()
    q2 = queue.Queue()
    q3 = queue.Queue()
    q4 = queue.Queue()

    while True:
        _ret, post = cam.read()
            
        t1 = threading.Thread(target=deg_thread1, args=(q1, post))
        t2 = threading.Thread(target=deg_thread2, args=(q2, post))
        t3 = threading.Thread(target=deg_thread3, args=(q3, post))
        t4 = threading.Thread(target=deg_thread4, args=(q4, post))
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        
        cv.imshow('face', post)
        
        t1.join()
        t2.join()
        t3.join()
        t4.join()
        postave = q1.get() + q2.get() + q3.get() + q4.get()

        if postave >= 2400:
            print("減少 : " , postave)

        ch = cv.waitKey(1)
        if ch == 27:
            break

    print('Done')
    
if __name__ == '__main__':
    print(__doc__)
    main()
    cv.destroyAllWindows()