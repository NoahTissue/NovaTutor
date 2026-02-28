from core.gemini_api import AIAgent
from audio.tts_engine import TextToSpeech
from audio.fwhisp import SpeechListener
from audio.wakeword_engine import WakeWordListener
from audio.speaker_correction1 import AudioKeepAlive
from utils.text_utils import strip_formatting
from ui.ui_server import NovaUI, kioskFunctions
from core.emotion_engine import EmotionEngine
from core.prompts import build_prompt
import subprocess
import time
import os
import re
import queue
import threading
from dotenv import load_dotenv


load_dotenv()

ELEVEN_KEY = os.getenv('ELEVEN_KEY')
GOOGLE_KEY = os.getenv('GOOGLE_KEY')
PICOVOICE_KEY = os.getenv('PICOVOICE_KEY')
emotion_engine = None

tts_queue = queue.Queue()
def tts_worker(tts_engine):
    while True:
        try:
            text_to_speak = tts_queue.get()

            if text_to_speak is None:
                break
            
            tts_engine.speak(text_to_speak)

            tts_queue.task_done()
        except Exception as e:
            print(f'Worker Function Error: {e}')
            
def main():
    ui = NovaUI()
    ui.wait_until_ready()
    kioskFunctions.launch_kiosk()
    amp_guard = AudioKeepAlive()
    amp_guard.start()

    global emotion_engine
    emotion_engine = EmotionEngine(history_size=10, scan_interval=3)
    emotion_engine.start()


    try:
        wake_engine = WakeWordListener(PICOVOICE_KEY)
        listener = SpeechListener()
        bot = AIAgent(GOOGLE_KEY)
        tts = TextToSpeech(ELEVEN_KEY)

        worker_thread = threading.Thread(target=tts_worker, args=(tts,), daemon=True)
        worker_thread.start()  
    except Exception as e:
        print(f"Start Up Failed: {e}")
        return
    ui.set_state('idle')
    time.sleep(2)
    ui.show_text('**Hey Gator!**, I\'m Nova, your personal tutoring assistant. \n\nCall me by saying <\'Hey Nova\'> and asking whatever question you need. \n\n•ᴗ•', sender='nova')   
    while True:
        
        wake_engine.listen()
        ui.set_state('listening')
        
        os.system("aplay assets/beep.wav 2>/dev/null &")
        
        user_text = listener.listen()
        print("<<Wake Word Detected>>")

        if not user_text:
            print("No speech detected.")
            ui.show_text("I didn't catch that - try saying it again.", sender='nova')
            ui.set_state('idle')
            continue
            
        ui.set_state('processing')
        print(f'Words Heard: {user_text}')
        ui.show_text(user_text, sender='user')



        print("<< Streaming Gemini Response >>")

        emotion_context = emotion_engine.get_context()
        response_stream = bot.chat.send_message(build_prompt(user_text, emotion_context), stream=True)

        buffer = ""
        full_log = ""
        
        ui.set_state('speaking')

        for chunk in response_stream:
            try:
                text_chunk = chunk.text
            except ValueError:
                continue
            
            buffer += text_chunk
            full_log += text_chunk

         
            parts = re.split(r'([.!?])', buffer)

            if len(parts) > 1:
                sentences = []
                
            
                for i in range(0, len(parts) - 1, 2):
                    if i+1 < len(parts):
                        sent_text = parts[i]
                        punct = parts[i+1]
                        sentences.append(sent_text + punct)

                
                buffer = parts[-1]

                for sentence in sentences:
                    if len(sentence.strip()) > 2:

                       
                        ui.show_text(sentence, sender='nova')
                        
                        
                        clean_sent = strip_formatting(sentence)
                        tts_queue.put(clean_sent)

        
        if buffer.strip():
            ui.show_text(buffer, sender='nova')
            tts_queue.put(strip_formatting(buffer))
        
        print(f'\nFull Response: {full_log}')
        
        # REMOVE .JOIN when implelement interruptions.
        tts_queue.join()
        
        ui.set_state('idle')
                 

                        

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n<<Stopping>>")
        time.sleep(0.5)
        kioskFunctions.close_kiosk()
        emotion_engine.stop()
