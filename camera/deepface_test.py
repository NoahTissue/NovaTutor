# debug_camera.py
import cv2
from deepface import DeepFace
import time

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
time.sleep(2)

# Flush the buffer first — read and discard 10 frames
for _ in range(10):
    cap.read()

print("Taking 3 debug photos...")

for i in range(3):
    # Flush again right before capture
    for _ in range(5):
        cap.read()
    
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        continue

    # Save the raw frame BEFORE DeepFace so you can see what the camera sees
    cv2.imwrite(f"raw_frame_{i}.jpg", frame)

    try:
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, silent=True)
        result = results[0] if isinstance(results, list) else results

        emotion = result['dominant_emotion']
        confidence = round(result['emotion'][emotion], 2)
        face_x = result['region']['x']
        face_y = result['region']['y']
        face_w = result['region']['w']
        face_h = result['region']['h']

        # Draw what DeepFace thinks it found
        cv2.rectangle(frame, (face_x, face_y), (face_x+face_w, face_y+face_h), (0, 255, 0), 2)
        cv2.putText(frame, f"{emotion} {confidence}%", (face_x, face_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imwrite(f"annotated_frame_{i}.jpg", frame)
        print(f"Frame {i}: {emotion} at {confidence}% | Face region: x={face_x} y={face_y} w={face_w} h={face_h}")

    except Exception as e:
        print(f"Frame {i} error: {e}")
    
    time.sleep(1)

cap.release()
print("Done. Check raw_frame_X.jpg and annotated_frame_X.jpg")
