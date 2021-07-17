import cv2
import numpy as np

cap = cv2.VideoCapture("udpsrc port=5005 ! application/x-rtp,media=video,encoding-name=H264 ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! appsink")
Width = int(cap.get(3))
Height = int(cap.get(4))
fourcc = cv2.VideoWriter_fourcc(*'MPEG')        
video = cv2.VideoWriter('video.avi', fourcc, 30, (Width,Height))  
while True:
    ret, img = cap.read()
    if not ret:
        break

    cv2.imshow("img",img)
    video.write(img)
    
    key = cv2.waitKey(1)
    if key==27: #[esc] key
        break

cap.release()
cv2.destroyAllWindows()