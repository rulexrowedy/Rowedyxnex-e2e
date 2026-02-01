from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return "FB Multi-Session Manager is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.route('/status')
def status():
    return {
        "status": "active",
        "service": "FB Multi-Session Manager",
        "uptime": "running"
    }

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Start the keep-alive server in a background thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    print("Keep-alive server started on port 8080")
    return t

if __name__ == "__main__":
    keep_alive()
    while True:
        time.sleep(60)
