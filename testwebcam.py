import cv2

# 把这里的地址换成你手机屏幕上显示的地址
# 注意：后面通常要加 '/video' 才能直接取流，具体看 App 说明
# IP Webcam 通常是这个格式：
url = "http://192.168.6.250:3925/video"

cap = cv2.VideoCapture(url)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("无法连接手机摄像头")
        break

    cv2.imshow("Phone Camera", frame)
    if cv2.waitKey(1) == 27:
        break