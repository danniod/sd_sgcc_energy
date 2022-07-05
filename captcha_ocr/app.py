from ddddocr import DdddOcr
from flask import Flask, request

app = Flask(__name__)


@app.post('/ocr')
def hello():
    image = request.get_data()

    captcha = DdddOcr().classification(image)
    return captcha
