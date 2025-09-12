import cv2 as cv

cap = cv.VideoCapture(0) #PCカメラを起動,0はデバイス番号

face_cascade = cv.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv.CascadeClassifier('haarcascade_eye.xml')

while True: #無限ループ
    ret, frame = cap.read() #カメラから1フレーム取得

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5) #顔認識,1.3はスケールファクター,5は近傍矩形数,サンプルの通り

    print(len(faces)) #認識した顔の位置情報を表示
    #x,yは顔の左上の座標、xは下へ,yは右にいくにつれて増えていく,hは顔の幅と高さ
    #(x,y) = (左上のx座標, 左上のy座標)、顔が認識された部分
    #(x+w, y+h) = (右下のx座標, 右下のy座標)、xから右にw、yから下にh移動した部分
    for (x,y,w,h) in faces:
        cv.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2) #顔の部分に青い四角を描画,2は線の太さ

        eye_gray = gray[y:y+h, x:x+w] #目認識用に顔の部分を切り出し
        eye_color = frame[y:y+h, x:x+w] #目認識用に顔の部分を切り出し
        eyes = eye_cascade.detectMultiScale(eye_gray) #目認識
        for (ex,ey,ew,eh) in eyes: #
            cv.rectangle(eye_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2) #目の部分に緑の四角を描画

    cv.imshow('frame',frame)#画像を表示
    if cv.waitKey(1) & 0xFF == ord('q'): #1ms待機してから次のループ処理へ,'q'キーが押されたらループを抜ける
        break #OxFFは16進数で255、ordは文字をASCIIコードに変換する関数,qに対応するASCIIコードは113,つまり113と比較している,113と255はビットANDをとっている
    
cv.destroyAllWindows()#ウィンドウを閉じる