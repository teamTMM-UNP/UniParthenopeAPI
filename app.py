from flask import Flask, Blueprint, url_for, jsonify, current_app, abort
from flask_restplus import Api, Resource, reqparse
from flask_marshmallow import Marshmallow, base_fields
from marshmallow import post_dump
import werkzeug
import os

app = Flask(__name__)
url = "https://uniparthenope.esse3.cineca.it/e3rest/api/"
class BaseConfig(object):
    DATA_FOLDER="data_folder"

config = {
    "default": BaseConfig
}


def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')
    app.config.from_object(config[config_name]) # object-based default configuration
    app.config.from_pyfile('config.cfg', silent=True) # instance-folders configuration


configure_app(app)

api = Api(app)

@api.route('/login/<token>',methods=['GET'])
class login(Resource):
    def login(token):
        return {'token': token}


'''@app.route('/boundle', methods=['GET'])
def return_file():
    return send_file('./file/boundle.zip', as_attachment=True, attachment_filename="boundle.zip")

@api.route('/version', methods=['GET'])
class version(Resource):
    def get(self):
        contents = ""
        f = open('version.txt', 'r')
        contents = f.read().splitlines()
        return {'version' : contents[0]}'''

if __name__ == '__main__':
    app.run()
