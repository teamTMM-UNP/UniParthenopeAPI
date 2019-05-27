from flask import Flask, Blueprint, url_for, jsonify, current_app, abort
from flask_restplus import Api, Resource, reqparse
from flask_marshmallow import Marshmallow, base_fields
from marshmallow import post_dump
import werkzeug
import requests
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

@api.route('/api/uniparthenope/login/<token>',methods=['GET'])
class Login(Resource):
    def get(self,token):

        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }

        response = requests.request("GET", url+"login", headers=headers)
        
        return jsonify({'response' : response.json()})


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
