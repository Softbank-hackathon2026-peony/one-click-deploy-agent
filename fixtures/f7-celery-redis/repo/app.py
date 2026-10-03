import time

from flask import Flask
from tasks import send_report

app = Flask(__name__)


@app.get('/health')
def health():
    return 'ok'


@app.get('/slow')
def slow():
    time.sleep(40)
    return 'ok'
