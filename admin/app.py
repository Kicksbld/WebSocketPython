from flask import Flask, render_template, jsonify
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Context import Context

app = Flask(__name__)

# Get WebSocket server configs
ctx_dev = Context.dev()
ctx_prod = Context.prod()

@app.route('/')
def index():
    return render_template('index.html',
                          ws_url_dev=ctx_dev.url(),
                          ws_url_prod=ctx_prod.url())

@app.route('/api/config')
def get_config():
    return jsonify({
        'dev': {'ws_url': ctx_dev.url(), 'host': ctx_dev.host, 'port': ctx_dev.port},
        'prod': {'ws_url': ctx_prod.url(), 'host': ctx_prod.host, 'port': ctx_prod.port}
    })

if __name__ == '__main__':
    print(f"Admin Dashboard running at http://127.0.0.1:5000")
    print(f"Dev server: {ctx_dev.url()} | Prod server: {ctx_prod.url()}")
    app.run(debug=True, port=5000)
