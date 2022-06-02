from flask import Flask
from flask_restful import Resource, Api
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app) ## To allow direct AJAX calls

@app.route('/btc/price', methods=['GET'])
def home():
    r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
    return r.json()

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=80, debug=True)
