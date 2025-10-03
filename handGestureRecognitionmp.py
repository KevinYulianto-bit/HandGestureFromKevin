from googletrans import Translator
import cv2
import mediapipe as mp
from gtts import gTTS
import pygame
import os
import re
import time

pygame.mixer.init()

translator = Translator()
cache = {}

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# fungsi TTS
def get_tts(text, lang="id"):
    safe_text = re.sub(r'[^a-zA-Z0-9]', '_', text)
    filename = f"voice_{safe_text}.mp3"
    if text not in cache:
        if not os.path.exists(filename):
            tts = gTTS(text=text, lang=lang)
            tts.save(filename)
        sound = pygame.mixer.Sound(filename)
        cache[text] = sound
    return cache[text]

def recognize_hand_gesture(hand_landmarks):
    ujung_jempol = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    ujung_telunjuk = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    ujung_jariTengah = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ujung_jarimanis = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
    ujung_kelingking = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

    if (ujung_jempol.y < ujung_telunjuk.y and
        ujung_jempol.y < ujung_jariTengah.y and
        ujung_jempol.y < ujung_jarimanis.y and
        ujung_jempol.y < ujung_kelingking.y):
        return "TEKNIK WANI"

    if (ujung_telunjuk.y < ujung_jempol.y and
        ujung_jariTengah.y < ujung_jempol.y and
        ujung_jarimanis.y > ujung_jempol.y and
        ujung_kelingking.y > ujung_jempol.y):
        return "SALAM KENAL"

    if (ujung_jempol.y > ujung_telunjuk.y and
        ujung_jempol.y > ujung_jariTengah.y and
        ujung_jempol.y > ujung_jarimanis.y and
        ujung_jempol.y > ujung_kelingking.y):
        return "IZIN PERKENALAN"

    if (ujung_telunjuk.y < ujung_jempol.y and
        ujung_kelingking.y < ujung_jempol.y and
        ujung_jariTengah.y > ujung_jempol.y and
        ujung_jarimanis.y > ujung_jempol.y):
        return "UNIVERSITAS"


# main loop
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

last_gesture = None
current_sound = None
text, translated = "", ""

last_time = 0        # timer untuk jeda antar suara
cooldown = 5         # jeda minimal 3 detik

cv2.namedWindow("Hand gesture Recognition", cv2.WINDOW_NORMAL)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret or frame is None:
        break

    gesture = None
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            gesture = recognize_hand_gesture(hand_landmarks)
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.putText(frame, gesture, (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # mainkan audio hanya jika ada gesture baru + jeda cukup + tidak ada audio aktif
    if gesture and gesture != last_gesture:
        if not pygame.mixer.get_busy() and (time.time() - last_time > cooldown):
            last_gesture = gesture
            last_time = time.time()  # update waktu terakhir

            if current_sound:
                current_sound.stop()  # stop audio sebelumnya

            if gesture == "TEKNIK WANI":
                text = "TEKNIK WANI, TEKNIK WANI, TEKNIK WANI, FAKULTAS TEKNIK, WANI WANI WANI"
            elif gesture == "SALAM KENAL":
                text = "Saya Adalah Mahasiswa Sistem Informasi"
            elif gesture == "IZIN PERKENALAN":
                text = "Hallo teman-teman, perkenalkan nama saya adalah Febrio Kevin Yulianto"
            elif gesture == "UNIVERSITAS":
                text = "Dari Fakultas Teknik Informatika Universitas Negeri Surabaya"
            
            
            current_sound = get_tts(text)
            current_sound.play()
            translated = translator.translate(text, dest="en").text

    # tampilkan subtitle
    if text:
        lines = [text[i:i+40] for i in range(0, len(text), 40)]
        lines_trans = [translated[i:i+40] for i in range(0, len(translated), 40)]
        for idx, line in enumerate(lines):
            cv2.putText(frame, line, (50, frame.shape[0]-80 - (len(lines)-1-idx)*30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
        for idx, line in enumerate(lines_trans):
            cv2.putText(frame, line, (50, frame.shape[0]-40 + idx*30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("Hand gesture Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
