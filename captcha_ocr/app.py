from ddddocr import DdddOcr
from flask import Flask, request

app = Flask(__name__)


@app.post('/captcha')
def captcha():
    image = request.get_data()

    code = DdddOcr().classification(image)
    return code
