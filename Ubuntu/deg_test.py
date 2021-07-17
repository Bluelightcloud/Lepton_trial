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

def deg_thread1(q1, img, x, y, w, h):
    ave = 0
    rgx = int((x+w)/2)
    rgy = int((y+h)/2)
    for i in range(y, rgy, 2):
        for j in range(x, rgx, 2):
            r,g,b = img[i][j]
            if r == g and r == b:
                ave -= r
            else :
                ave += r
    q1.put(ave)
    
def deg_thread2(q2, img, x, y, w, h):
    ave = 0
    rgx = int((x+w)/2)
    rgy = int((y+h)/2)
    for i in range(rgy, y+h, 2):
        for j in range(x, rgx, 2):
            r,g,b = img[i][j]
            if r == g and r == b:
                ave -= r
            else :
                ave += r
    q2.put(ave)
    
def deg_thread3(q3, img, x, y, w, h):
    ave = 0
    rgx = int((x+w)/2)
    rgy = int((y+h)/2)
    for i in range(y, rgy, 2):
        for j in range(rgx, x+w, 2):
            r,g,b = img[i][j]
            if r == g and r == b:
                ave -= r
            else :
                ave += r
    q3.put(ave)

def deg_thread4(q4, img, x, y, w, h):
    ave = 0
    rgx = int((x+w)/2)
    rgy = int((y+h)/2)
    for i in range(rgy, y+h, 2):
        for j in range(rgx, x+w, 2):
            r,g,b = img[i][j]
            if r == g and r == b:
                ave -= r
            else :
                ave += r
    q4.put(ave)
    
def main():
    import sys
    try:
        fn = sys.argv[1]
    except IndexError:
        fn = 0
    
    cam = cv.VideoCapture("udpsrc port=5005 ! application/x-rtp,media=video,encoding-name=H264 ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! appsink")
    _ret, prev = cam.read()
    prevgray = imageproc(prev)
    postave = 0
    prevave = 0
    firstswitch = True
    q1 = queue.Queue()
    q2 = queue.Queue()
    q3 = queue.Queue()
    q4 = queue.Queue()

    while True:
        _ret, post = cam.read()
            
        postgray = imageproc(post)
        face_img = postgray.copy()
        face_rects = face_cascade.detectMultiScale(face_img,scaleFactor=1.02,minNeighbors=2,minSize=(100, 100))
        if len(face_rects) != 0:
            x, y, w, h = face_rects[0]
            t1 = threading.Thread(target=deg_thread1, args=(q1, post, x, y, w, h))
            t2 = threading.Thread(target=deg_thread2, args=(q2, post, x, y, w, h))
            t3 = threading.Thread(target=deg_thread3, args=(q3, post, x, y, w, h))
            t4 = threading.Thread(target=deg_thread4, args=(q4, post, x, y, w, h))
            t1.start()
            t2.start()
            t3.start()
            t4.start()
            
            cv.rectangle(post,(x,y),(x+w,y+h),(255,255,255),10)
            
            t1.join()
            t2.join()
            t3.join()
            t4.join()
            postave = q1.get() + q2.get() + q3.get() + q4.get()
            postave /= w*h/4
            
            if firstswitch == True:
                firstswitch = False
            else :
                difference = postave - prevave
                if difference >= 8:
                    print("上昇 : " , difference)
                    
                elif difference <= -8:
                    print("減少 : " , difference)
                    
            prevave = postave
        else:
            prevave = 0
            firstswitch = True
        
        cv.imshow('face', post)
        prevgray = postgray

        ch = cv.waitKey(1)
        if ch == 27:
            break

    print('Done')
    
if __name__ == '__main__':
    print(__doc__)
    main()
    cv.destroyAllWindows()