import sounddevice as sd
import numpy as np
import threading
import time

class AudioKeepAlive:
    def __init__(self):
        self.running = False
        self.thread = None

    def _play_noise(self):
        # Generates a 10Hz sine wave (Below human hearing range of 20Hz)
        samplerate = 44100
        duration = 1.0 # 1 second buffer
        t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
        
        # 10 Hz tone at very low volume
        tone = (0.01 * np.sin(2 * np.pi * 10 * t)).astype(np.float32)
        
        with sd.OutputStream(samplerate=samplerate, channels=1) as stream:
            while self.running:
                stream.write(tone)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._play_noise, daemon=True)
            self.thread.start()
            print("<<Audio Keep-Alive Started>>")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()