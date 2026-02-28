# emotion_engine.py
import cv2
import time
import os
import threading
from collections import deque, Counter
from deepface import DeepFace


class EmotionEngine:
    def __init__(self, history_size=10, scan_interval=3):
        self.history = deque(maxlen=history_size)
        self.scan_interval = scan_interval
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self.cap = None
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self._frame_thread = None

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def start(self):
        """Auto-detect USB camera and start background threads."""
        camera_index = self._find_camera()

        if camera_index is None:
            print("[EmotionEngine] WARNING: Could not find any working USB camera. Emotion detection disabled.")
            return

        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Full res for better detection
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._running = True

        self._frame_thread = threading.Thread(target=self._frame_grabber, daemon=True)
        self._frame_thread.start()

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        print("[EmotionEngine] Emotion detection started.")

    def stop(self):
        """Gracefully shut down the camera and threads."""
        self._running = False
        if self._frame_thread and self._frame_thread.is_alive():
            self._frame_thread.join(timeout=2.0)
        time.sleep(0.3)
        if self.cap:
            self.cap.release()
        print("[EmotionEngine] Stopped.")

    def get_context(self):
        """
        Called by main.py right before sending to Gemini.
        Returns a plain English summary, or None if no valid face data exists.
        """
        with self._lock:
            if not self.history:
                return None  # No data — main.py will skip emotion context

            # Discard stale data if student stepped away for 30+ seconds
            most_recent_time = self.history[-1]['timestamp']
            if time.time() - most_recent_time > 30:
                return None

            emotions = [item["emotion"] for item in self.history]

        context_map = {
            "angry":    "frustrated or struggling to understand the material, please try to make the most nice and kindest approach to explaining a concept. Be forgiving, slow, annd egnaging, and try to make it aws kind as possible.",
            "sad":      "discouraged or losing confidence",
            "fear":     "overwhelmed or anxious about the topic",
            "happy":    "engaged, confident, and following along well",
            "surprise": "just had a realization or is surprised by something",
            "neutral":  "focused and listening attentively",
            "disgust":  "dissatisfied with the current explanation"
        }

        latest   = emotions[-1]
        majority = Counter(emotions).most_common(1)[0][0]

        majority_count = Counter(emotions).most_common(1)[0][1]
        min_count = max(1, len(emotions) // 3)

        if majority_count < min_count:
            return "The student's emotional state is unclear — insufficient data."

        if latest == majority:
            description = context_map.get(latest, "attentive")
            return f"The student appears to be {description}."
        else:
            old_desc = context_map.get(majority, "neutral")
            new_desc = context_map.get(latest, "neutral")
            return (
                f"The student was mostly {old_desc}, "
                f"but their expression has just shifted to {new_desc}."
            )

    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------

    def _frame_grabber(self):
        """Runs at full camera speed, always keeps the latest frame."""
        consecutive_failures = 0
        MAX_FAILURES = 30

        while self._running:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                with self._frame_lock:
                    self._latest_frame = frame
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= MAX_FAILURES:
                    print("[EmotionEngine] Camera lost! Attempting to reconnect...")
                    self._reconnect()
                    consecutive_failures = 0

    def _reconnect(self):
        """Release and re-open the camera if it disconnects."""
        try:
            if self.cap:
                self.cap.release()
            time.sleep(2)
            camera_index = self._find_camera()
            if camera_index is not None:
                self.cap = cv2.VideoCapture(camera_index)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print("[EmotionEngine] Camera reconnected successfully.")
            else:
                print("[EmotionEngine] Reconnect failed. Will retry next cycle.")
        except Exception as e:
            print(f"[EmotionEngine] Reconnect error: {e}")

    def _get_fresh_frame(self):
        """Returns a copy of the most recently captured frame, or None."""
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def _find_camera(self):
        """Scans indices 1-5, suppressing noisy OpenCV warnings during scan."""
        print("[EmotionEngine] Searching for USB camera...")

        # Suppress OpenCV's stderr spam during scanning
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(2)
        os.dup2(devnull, 2)

        found_index = None
        for i in range(1, 6):
            test_cap = cv2.VideoCapture(i)
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                if ret and frame is not None:
                    test_cap.release()
                    found_index = i
                    break
            test_cap.release()

        # Always restore stderr before returning
        os.dup2(old_stderr, 2)
        os.close(devnull)
        os.close(old_stderr)

        if found_index is not None:
            print(f"[EmotionEngine] Found working camera at index {found_index}.")
        else:
            print("[EmotionEngine] No working camera found.")

        return found_index

    def _loop(self):
        """Analyzes the latest frame every scan_interval seconds."""
        MIN_CONFIDENCE = 80.0

        print("[EmotionEngine] Waiting for first live frame...")
        while self._running and self._get_fresh_frame() is None:
            time.sleep(0.1)

        print("[EmotionEngine] Loading DeepFace model (first-time only)...")
        try:
            warmup_frame = self._get_fresh_frame()
            if warmup_frame is not None:
                DeepFace.analyze(
                    warmup_frame,
                    actions=['emotion'],
                    enforce_detection=False,
                    silent=True
                )
        except Exception:
            pass
        print("[EmotionEngine] Model loaded. Now scanning in real time.")

        while self._running:
            try:
                frame = self._get_fresh_frame()

                if frame is None:
                    time.sleep(0.5)
                    continue

                # Resize 640x480 → 320x240 for faster DeepFace processing
                small_frame = cv2.resize(frame, (320, 240))

                results = DeepFace.analyze(
                    small_frame,
                    actions=['emotion'],
                    enforce_detection=False,
                    detector_backend='yunet',  # More sensitive than default opencv
                    silent=True
                )

                result = results[0] if isinstance(results, list) else results

                face_w = result['region']['w']
                face_h = result['region']['h']
                frame_area = small_frame.shape[0] * small_frame.shape[1]  # 76800
                face_area  = face_w * face_h

                # Reject readings with no real face detected
                if face_area == 0 or face_area > (frame_area * 0.90) or face_area < 100:
                    print(f"[EmotionEngine] No real face detected (region {face_w}x{face_h}). Skipping.")
                    time.sleep(self.scan_interval)
                    continue

                emotion    = result['dominant_emotion']
                confidence = round(result['emotion'][emotion], 2)

                if confidence >= MIN_CONFIDENCE:
                    reading = {
                        "timestamp": time.time(),
                        "emotion": emotion,
                        "confidence": confidence
                    }
                    with self._lock:
                        self.history.append(reading)
                    print(f"[EmotionEngine] Detected: {emotion} ({confidence}%)")
                else:
                    print(f"[EmotionEngine] Skipped low-confidence reading: {emotion} ({confidence}%)")

            except Exception as e:
                print(f"[EmotionEngine] Analysis error: {e}")

            time.sleep(self.scan_interval)
