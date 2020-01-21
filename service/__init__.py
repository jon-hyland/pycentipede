import os
from flask import Flask

# create an instance of the flask class
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY') or "16dcbbd3-f781-4ec0-8a53-6151ac412e61"
