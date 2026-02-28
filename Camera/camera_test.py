import cv2
import time
from deepface import DeepFace

# 1. Initialize USB Camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Warming up camera...")
time.sleep(2)

if not cap.isOpened():
    print("Error: Could not open USB camera.")
    exit()

print("Camera ready. Starting DeepFace test...")
print("NOTE: Frame 1 will take much longer as it loads the AI models into memory.\n")

# 2. Test Loop - We will process 5 frames to test the speed
for i in range(1, 6):
    print(f"--- Frame {i}/5 ---")
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to grab frame.")
        break
        
    # Start timer for DeepFace analysis
    start_time = time.time()
    
    try:
        # Analyze emotion. enforce_detection=False prevents crashes if no face is found
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        
        # DeepFace can return a list (if multiple faces) or a dictionary
        if isinstance(results, list):
            result = results[0]
        else:
            result = results
            
        emotion = result['dominant_emotion']
        
        # Stop timer
        end_time = time.time()
        process_time = end_time - start_time
        
        print(f"Emotion detected: {emotion.upper()}")
        print(f"Processing time: {process_time:.2f} seconds")
        
        # Save an annotated image so you can see the result headlessly
        # Get face coordinates to draw a box
        x = result['region']['x']
        y = result['region']['y']
        w = result['region']['w']
        h = result['region']['h']
        
        # Draw a rectangle around the face and write the emotion
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"{emotion} ({process_time:.2f}s)", (x, y-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        filename = f"deepface_result_{i}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Saved annotated frame to '{filename}'\n")
            
    except Exception as e:
        print(f"DeepFace Error: {e}")
        
# 3. Cleanup
cap.release()
print("Test complete. Check your folder for the saved images!")
