import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import queue
import time
import sys

class SpeechListener:
    def __init__(self, model_size="tiny.en"):
        print(f"Loading Faster-Whisper model: {model_size}...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        self.q = queue.Queue()
        self.samplerate = 16000 
        self.channels = 1
        

        self.silence_threshold = 100  
        self.silence_duration = .8   
        print("<<Whisper Model Loaded.>>")

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(indata.copy())

    def listen(self):
    

        print("\n //Listening for speech... ")
        audio_buffer = []
        silence_start = None
        speaking_started = False
        
        
        with sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=self.callback):
            while True:
               
                indata = self.q.get()
                    
                volume_norm = np.linalg.norm(indata) * 10
                      
                if volume_norm > self.silence_threshold:
                    if not speaking_started:
                        print("--> Voice detected")
                        speaking_started = True
                    silence_start = None 
                else:
                    if speaking_started and silence_start is None:
                        silence_start = time.time() 
                
                
                if speaking_started:
                    audio_buffer.append(indata)
                
                
                if speaking_started and silence_start and (time.time() - silence_start > self.silence_duration):
                    print("--> Silence detected, processing...")
                    break

        
        if not audio_buffer:
            return ""
            
        
        audio_data = np.concatenate(audio_buffer, axis=0)
        
        audio_data = audio_data.flatten().astype(np.float32)
  
        segments, info = self.model.transcribe(audio_data, beam_size=1)
        
        full_text = ""
        for segment in segments:
            full_text += segment.text + " "
            
        return full_text.strip()

if __name__ == "__main__":

    listener = SpeechListener()
    result = listener.listen()
    print(f"Final Transcription: {result}")

