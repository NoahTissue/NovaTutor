import pvporcupine
import sounddevice as sd
import struct
import os

class WakeWordListener:
    def __init__(self, access_key):
        keyword_file = 'assets/Hey_Nova.ppn' 
        

        if not os.path.exists(keyword_file):
            raise FileNotFoundError(f"Could not find {keyword_file}. Did you drag it into the folder?")

        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[keyword_file] 
            )
        except Exception as e:
            print(f"Error loading Porcupine: {e}")
            raise

    def listen(self):
        print(f"<Listening for 'Hey Nova'...>")
        
        with sd.InputStream(
            samplerate=self.porcupine.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=self.porcupine.frame_length
        ) as stream:
            while True:

                pcm, overflow = stream.read(self.porcupine.frame_length)
                
                pcm = pcm.flatten().tolist()

                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print("<'Hey Nova' Detected>")
                    return True