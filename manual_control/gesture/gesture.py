import cv2
import mediapipe as mp
import websocket
import json
import math

ESP32_IP = "192.168.222.17"
ws = websocket.WebSocket()
ws.connect(f"ws://{ESP32_IP}:81/")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret: break
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        wrist = hand.landmark[0]
        palm_x = wrist.x
        thumb_tip = hand.landmark[4]
        index_tip = hand.landmark[8]
        dist = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)


        if palm_x > 0.55:        # compress arm (right)
            angles = [90,90,90,90,0]
        elif palm_x < 0.45:      # extend arm (left)
            angles = [0,0,0,0,0]


        # Gripper: default open (0), close on fist
        if dist < 0.05:
            angles[4] = 180
        else:
            angles[4] = 0

        ws.send(json.dumps({"angles": angles}))

    cv2.imshow("Pose Arm Control", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
ws.close()

