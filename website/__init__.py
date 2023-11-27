# 一旦website被import了，这里面的代码会自动跑
import os
from flask import Flask
import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["mydatabase"]


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dfkdfdkl'  # mandatory. because we need to use 'session'

    from . import views, auth

    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)

    return app
