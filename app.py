import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from api import api_blueprint

app = Flask(__name__)
app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)