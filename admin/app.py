from flask import Flask, render_template, jsonify
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Context import Context

app = Flask(__name__)

# Get WebSocket server config
ctx = Context.prod()

@app.route('/')
def index():
    return render_template('index.html', ws_url=ctx.url())

@app.route('/api/config')
def get_config():
    return jsonify({
        'ws_url': ctx.url(),
        'host': ctx.host,
        'port': ctx.port
    })

if __name__ == '__main__':
    print(f"Admin Dashboard running at http://127.0.0.1:5000")
    print(f"WebSocket server expected at {ctx.url()}")
    app.run(debug=True, port=5000)
