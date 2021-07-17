import cv2
import csv

cap = cv2.VideoCapture("udpsrc port=5005 ! application/x-rtp,media=video,encoding-name=H264 ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! appsink")

while True:
    ret, img = cap.read()
    if not ret:
        break
    
    cv2.imshow("",img)
    key = cv2.waitKey(1)
    if key==27: #[esc] key
        break

filename = 'RGBdata' + '.csv'
with open(filename, 'a') as f:
    writer = csv.writer(f, lineterminator='\n')
    writer.writerows(img)

cv2.destroyAllWindows()