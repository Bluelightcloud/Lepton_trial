from __future__ import print_function

import dlib
from imutils import face_utils

import numpy as np
import cv2 as cv
import math
import time

import pprint
import datetime

import queue
import threading

global criticalpoint     #Feature point
global start             #start time

face_detector = dlib.get_frontal_face_detector()
predictor_path = 'shape_predictor_68_face_landmarks.dat'
face_predictor = dlib.shape_predictor(predictor_path)

def imageproc(img):
    img_after = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    
    return img_after

def face_landmark_find(qface, img):
    faces = face_detector(img, 1)

    for face in faces:
        landmark = face_predictor(img, face)
        landmark = face_utils.shape_to_np(landmark)

        for (x, y) in landmark:
            cv.circle(img, (x, y), 1, (0, 0, 255), -1)

    qface.put(img)

def draw_flow(q, post, prev, step=32): #step : The points will be detailed for lower param 
    flow = cv.calcOpticalFlowFarneback(prev, post, None, 0.5, 1, 15, 1, 5, 1.1, 0)
    h, w = post.shape[:2]         #height and width params of image (size)
    y, x = np.mgrid[step/2:h:step, step/2:w:step].reshape(2,-1).astype(int)     #if step = 32 16~h made 32 kizami de point wo utsu
    fx, fy = flow[y,x].T
    lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)
    vis = cv.cvtColor(post, cv.COLOR_GRAY2BGR)
    
    #cv.polylines(vis, lines, 0, (0, 255, 0))
    global criticalpoint
    global start
    oneline = np.empty(0)     #one of line
    dis = np.empty(0)     #distance
    count = 0            #my range counter
    for (x1, y1), (_x2, _y2) in lines:
        oneline = np.array(((x1, y1), (_x2, _y2)))
        dx = _x2 - x1
        dy = _y2 - y1
        dl = math.sqrt((dx ** 2)+(dy ** 2))
        theta = math.degrees(math.atan2(dy, dx))
        
        if dl > 8 and (-45 < theta < 45 or theta > 135 or theta < -135):
            cv.polylines(vis, [oneline], 0, (0, 0, 255))
            cv.circle(vis, (x1, y1), 1, (0, 0, 255), -1)
            count += 1
        else :
            cv.polylines(vis, [oneline], 0, (0, 255, 0))
            cv.circle(vis, (x1, y1), 1, (0, 255, 0), -1)
            
    if count >= 7 :
        criticalpoint += 1
        print("Detection")
        if time.time() - start > 11 or start == 0 : 
            start = time.time()
    
    q.put(vis)


def main():
    import sys
    try:
        fn = sys.argv[1]
    except IndexError:
        fn = 0
        
    global criticalpoint
    global start
    
    cam = cv.VideoCapture("udpsrc port=5005 ! application/x-rtp,media=video,encoding-name=H264 ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! appsink")
    _ret, prev = cam.read()
    prevgray = imageproc(prev)
    q = queue.Queue()
    qface = queue.Queue()
    #########average############
    count = 0
    sume = 0
    ############################
    while True:
        _ret, post = cam.read()
            
        postgray = imageproc(post)
        ##########################
        timer = time.time()
        
        t = threading.Thread(target=draw_flow, args=(q, postgray, prevgray))
        tface = threading.Thread(target=face_landmark_find, args=(qface, postgray))
        t.start()
        tface.start()
        t.join()
        tface.join()
        flowvis = q.get()
        facevis = qface.get()
        cv.imshow('flow', flowvis)
        cv.imshow('face', facevis)
        
        sume += time.time() - timer
        count += 1
        ##########################
        prevgray = postgray
        
        if 12 >= time.time() - start >= 10 :
            if criticalpoint >= 5 :
                print('Detection : {0}'.format(criticalpoint))
            criticalpoint = 0
            start = 0
            
        ch = cv.waitKey(1)
        if ch == 27:
            break

    print('Done')
    #################
    print(sume/count)
    #################
    
if __name__ == '__main__':
    print(__doc__)
    criticalpoint = 0
    start = 0
    main()
    cv.destroyAllWindows()