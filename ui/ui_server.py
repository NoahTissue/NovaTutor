import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
import socket
import logging
import os
import subprocess
import time


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nova_cise_lab_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    return render_template('index.html')

class NovaUI:

    def __init__(self):
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print("Nova UI server starting on http://0.0.0.0:5000") 

    def _run_server(self):
        socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, log_output=False)
    
    def wait_until_ready(self, timeout=10.0):
        deadline = time.time() +timeout
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", 5000), timeout=0.5):
                    print("[UI] Flask is ready.")
                    return
            except (ConnectionRefusedError, OSError):
                time.sleep(0.1)
        print("[UI] WARNING: Flask did not start within timeout. Launching browser anyway.")




    def set_state(self, state):

        print(f">> UI State: {state}")
        socketio.emit('status_change', {'status': state})

    def show_text(self, text, sender):

        socketio.emit('update_text', {'text': text, 'sender': sender})

class kioskFunctions():

    
    def launch_kiosk():
        print("<<Launching Kiosk Browser>>")
        cmd = [
                "chromium", 
                "--kiosk", 
                "--app=http://127.0.0.1:5000",
                "--window-size=1280,800",    
                "--start-fullscreen",
                "--noerrdialogs", 
                "--disable-infobars",
                "--overscroll-history-navigation=0",
                "--touch-events=enabled",
                "--enable-features=TouchpadOverscrollScrolling,OverlayScrollbar",
                "--ozone-platform-hint=auto"
        ]
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        try: 
            subprocess.Popen(cmd, env=env, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception as e:
                print(f"Error launching browser: {e}")


    def close_kiosk():
        # This finds any process named 'chromium' and kills it
        os.system("pkill -o chromium")

              
@socketio.on('connect')
def handle_connect():
    print(">> UI Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print(">> UI Client disconnected")
