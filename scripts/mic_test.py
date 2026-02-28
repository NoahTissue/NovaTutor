import sounddevice as sd
import numpy as np

def callback(indata, frames, time, status):
    # Calculate volume
    volume_norm = np.linalg.norm(indata) * 10
    # Print it out so you can see the noise level
    print(f"Volume: {volume_norm:.4f}")

print("<<Listening Ctrl+C to stop>>")
with sd.InputStream(callback=callback):
    while True:
        pass