import dlib
from imutils import face_utils
import cv2
import numpy as np
# --------------------------------
# 1.顔ランドマーク検出の前準備
# --------------------------------
# 顔ランドマーク検出ツールの呼び出し
face_detector = dlib.get_frontal_face_detector()
predictor_path = 'shape_predictor_68_face_landmarks.dat'
face_predictor = dlib.shape_predictor(predictor_path)


# --------------------------------
# 2.画像から顔のランドマーク検出する関数
# --------------------------------
def face_landmark_find(img):
    # 顔検出
    
    faces = face_detector(img, 1)

    # 検出した全顔に対して処理
    for face in faces:
        # 顔のランドマーク検出
        landmark = face_predictor(img, face)
        # 処理高速化のためランドマーク群をNumPy配列に変換(必須)
        landmark = face_utils.shape_to_np(landmark)

        # ランドマーク描画
        for (x, y) in landmark:
            cv2.circle(img, (x, y), 1, (0, 0, 255), -1)

    return img


# --------------------------------
# 3.カメラ画像の取得
# --------------------------------
# カメラの指定(適切な引数を渡す)
cam = cv2.VideoCapture("udpsrc port=5005 ! application/x-rtp,media=video,encoding-name=H264 ! queue ! rtph264depay ! avdec_h264 ! videoconvert ! appsink")

# カメラ画像の表示 ('q'入力で終了)
while(True):
    _ret, prev = cam.read()
    gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    # 顔のランドマーク検出(2.の関数呼び出し)
    img = face_landmark_find(gray)

    # 結果の表示
    cv2.imshow('img', img)

    # 'q'が入力されるまでループ
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 後処理
cv2.destroyAllWindows()