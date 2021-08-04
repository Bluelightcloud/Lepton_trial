"""
Difference
frame : 200
criticalpoint : 5
vc_dl > 9
"""


from __future__ import print_function

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage

import numpy as np
import cv2 as cv
import math
import time

import csv
import pprint
import datetime
from playsound import playsound

import queue
import threading

global criticalpoint     #Feature point
global optoff            #face's detection stopped
global filename
global flame
global flswitch
global starttime

face_cascade = cv.CascadeClassifier("haarcascade_frontalface_default.xml")

cred = credentials.Certificate('lepton-detection-firebase-adminsdk-yafvr-74c2998d96.json')
firebase_admin.initialize_app(cred, {'storageBucket': 'lepton-detection.appspot.com'})
bucket = storage.bucket()

class vector_calc:
    def __init__(self, x1, y1, _x2, _y2):
        self.x1 = x1
        self.y1 = y1
        self._x2 = _x2
        self._y2 = _y2
        self.dl = 0
        self.theta = 0
    
    def vector(self):
        dx = self._x2 - self.x1
        dy = self._y2 - self.y1
        self.dl = ((dx * dx)+(dy * dy))**0.5
        self.theta = (math.atan2(dy, dx)) * (180 / math.pi)

def sound():
    playsound("detect.wav")
    
def output_csv():
    global criticalpoint
    global filename
    global starttime
    now = datetime.datetime.now()
    rectime = time.time() - starttime
    filename = 'log_' + now.strftime('%Y%m%d') + '.csv'
    with open(filename, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([rectime, criticalpoint])

def imageproc(img):
    img_after = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    
    return img_after

def face_haarlike_find(qface, img):
    global optoff
    face_img = img.copy()
    face_rects = face_cascade.detectMultiScale(face_img,scaleFactor=1.02,minNeighbors=2,minSize=(100, 100))
    if len(face_rects) == 0:
        optoff = True
    else :
        optoff = False
        x = face_rects[0][0]
        y = face_rects[0][1]
        w = face_rects[0][2]
        h = face_rects[0][3]
        cv.rectangle(face_img,(x,y),(x+w,y+h),(255,255,255),10)
            
    #for (x,y,w,h) in face_rects:

    qface.put(face_img)

def draw_flow(q, post, prev, step=32): #step : The points will be detailed for lower param 
    flow = cv.calcOpticalFlowFarneback(prev, post, None, 0.5, 1, 15, 1, 5, 1.1, 0)
    h, w = post.shape[:2]         #height and width params of image (size)
    y, x = np.mgrid[step/2:h:step, step/2:w:step].reshape(2,-1).astype(int)     #if step = 32 16~h made 32 kizami de point wo utsu
    fx, fy = flow[y,x].T
    lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)
    vis = cv.cvtColor(post, cv.COLOR_GRAY2BGR)
    
    global criticalpoint
    global flame
    global optoff
    global filename
    global flswitch
    
    oneline = np.empty(0)     #one of line
    dis = np.empty(0)     #distance
    count = 0            #my range counter
    for (x1, y1), (_x2, _y2) in lines:
        oneline = np.array(((x1, y1), (_x2, _y2)))
        vc = vector_calc(x1, y1, _x2, _y2)    #インスタンス生成
        vc.vector()
        
        if optoff == False and vc.dl > 9 and (-35 < vc.theta < 35 or vc.theta > 145 or vc.theta < -145):
            cv.polylines(vis, [oneline], 0, (0, 0, 255))
            cv.circle(vis, (x1, y1), 1, (0, 0, 255), -1)
            count += 1
        else :
            cv.polylines(vis, [oneline], 0, (0, 255, 0))
            cv.circle(vis, (x1, y1), 1, (0, 255, 0), -1)
            
    if count >= 7 :
        criticalpoint += 1
        print("Detection")
        if flswitch == False:
            flswitch = True
    
    if flswitch == True:
        flame += 1
    
    q.put(vis)


def main():
    import sys
    try:
        fn = sys.argv[1]
    except IndexError:
        fn = 0
        
    global criticalpoint
    global start
    global flame
    global flswitch
    
    cam = cv.VideoCapture("Movie.mp4")
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
        if not _ret:
            break
        postgray = imageproc(post)
        ##########################
        timer = time.time()
        
        t = threading.Thread(target=draw_flow, args=(q, postgray, prevgray))
        tface = threading.Thread(target=face_haarlike_find, args=(qface, postgray))
        t.start()
        tface.start()
        t.join()
        tface.join()
        flowvis = q.get()
        facevis = qface.get()
        cv.imshow('flow', flowvis)
        cv.imshow('face', facevis)
        
        time.sleep(0.004)
        sume += time.time() - timer
        count += 1
        ##########################
        prevgray = postgray
        
        if flame >= 250 :
            if criticalpoint >= 5 :
                #tsound = threading.Thread(target=sound)
                #tsound.start()
                print('Detection : {0}'.format(criticalpoint))
                output_csv()
            print(flame)
            criticalpoint = 0
            flame = 0
            flswitch = False
            
        
        ch = cv.waitKey(1)
        if ch == 27:
            break

    print('Done')
    #################
    print(sume/count)
    #################
    
if __name__ == '__main__':
    print(__doc__)
    optoff = False
    criticalpoint = 0
    flame = 0
    flswitch = False
    starttime = time.time()
    main()
    output_csv()
    
    try:
        global filename
        content_type = 'csv'
        blob = bucket.blob(filename)
        with open(filename, 'rb') as f:
            blob.upload_from_file(f, content_type=content_type)
        print("Upload was done")
        
    except:
        print("ファイルがありません")
    
    cv.destroyAllWindows()
