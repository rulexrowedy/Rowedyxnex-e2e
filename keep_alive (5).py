from flask import Flask, jsonify
from threading import Thread
import time
import os

app = Flask('')

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FB Multi-Session Manager</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0;
            }
            .container {
                background: rgba(255,255,255,0.95);
                padding: 40px 60px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                margin-bottom: 10px;
            }
            p {
                color: #666;
                font-size: 18px;
            }
            .status {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 20px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>FB Multi-Session Manager</h1>
            <p>Server is running and ready!</p>
            <div class="status">ONLINE</div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": "running"
    })

@app.route('/status')
def status():
    return jsonify({
        "status": "active",
        "service": "FB Multi-Session Manager",
        "server": "online",
        "timestamp": time.time()
    })

@app.route('/ping')
def ping():
    return "pong"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

def keep_alive():
    """Start the keep-alive server in a background thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    print("Keep-alive server started!")
    print(f"Server running on port {os.environ.get('PORT', 8080)}")
    return t

if __name__ == "__main__":
    print("Starting FB Multi-Session Manager Server...")
    keep_alive()
    
    while True:
        time.sleep(60)
        print(f"Server heartbeat - {time.strftime('%Y-%m-%d %H:%M:%S')}")
