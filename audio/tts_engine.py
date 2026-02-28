import requests
import subprocess
import shutil

class TextToSpeech:
    def __init__(self, api_key):
        self.api_key = api_key
        self.is_speaking = False
        self.voice_id = "CwhRBWXzGAHq8TQ4Fs17"
        
        if not shutil.which("mpv"):

            raise RuntimeError("mpv not found. Please install it with: sudo apt-get install mpv")

    def speak(self, text):
        print("<<Generating Speech via ElevenLabs>>")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.7
            }
        }

        player = subprocess.Popen(
            ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        self.is_speaking = True
        try:
            with requests.post(url, json=data, headers=headers, stream=True) as response:
                if response.status_code == 200:
                    print("<<Streaming Speech>>")
                    for chunk in response.iter_content(chunk_size=4096):
                        if chunk:
                            player.stdin.write(chunk)
                            player.stdin.flush()
                else:
                    print(f"Error from ElevenLabs: {response.text}")
                    
        except Exception as e:
            print(f"Connection Error: {e}")
            
        finally:
            self.is_speaking = False
            if player.stdin:
                player.stdin.close()

            player.wait()