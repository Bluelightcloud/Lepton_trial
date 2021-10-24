import cv2
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import socket

mouth_cascade = cv2.CascadeClassifier('haarcascade_mcs_mouth.xml')
nose_cascade = cv2.CascadeClassifier('haarcascade_mcs_nose.xml')
host = "192.168.3.11"
port = 11111

def sendData(mouth_r, nose_r):
    message = ""
    
    for i in range(0, 8):
        if i <= 3:
            message += str(mouth_r[0][i])
            message += ','
        else:
            message += str(nose_r[0][i-4])
            if i < 7:
                message += ','

    client.send(message.encode('utf-8'))
    response = client.recv(4096)
    print(response)

def main():
    capture = cv2.VideoCapture(0)

    while(True):
        ret, frame = capture.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mouth_rects = mouth_cascade.detectMultiScale(gray, 1.3, 5, minSize=(60, 60))
        nose_rects = nose_cascade.detectMultiScale(gray, 1.3, 5, minSize=(60, 60))
        sendData(mouth_rects, nose_rects)
        
        for (x,y,w,h) in mouth_rects:
            frame = cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),5) # 青色
        for (x,y,w,h) in nose_rects:
            frame = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),5) # 緑色

        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.release()

if __name__ == '__main__':
    print(__doc__)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    main()
    cv2.destroyAllWindows()