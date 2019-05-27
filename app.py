from flask import Flask, Blueprint, url_for, jsonify, current_app, abort
from flask_restplus import Api, Resource, reqparse
from datetime import date
from flask_marshmallow import Marshmallow, base_fields
from marshmallow import post_dump
import werkzeug
import requests
import re
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
    def get(self, token):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url+"login", headers=headers)
        
        return jsonify({'response': response.json()})


@api.route('/api/uniparthenope/totalexams/<token>/<matId>', methods=['GET'])
class TotalExams(Resource):
    def get(self, token, matId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/stats", headers=headers)
        _response = response.json()
        totAdSuperate = _response['numAdSuperate'] + _response['numAdFrequentate']
        return jsonify({'totAdSuperate': totAdSuperate,
                        'numAdSuperate': _response['numAdSuperate'],
                        'cfuPar': _response['umPesoSuperato'],
                        'cfuTot': _response['umPesoPiano']})


@api.route('/api/uniparthenope/average/<token>/<matId>/<value>', methods=['GET'])
class TotalExams(Resource):
    def get(self, token, matId, value):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/medie", headers=headers)

        _response = response.json()
        for i in range(0,len(_response)):
            if _response[i]['tipoMediaCod']['value'] is value:
                if _response[i]['base'] is 30:
                    base_trenta = 30
                    media_trenta = _response[i]['media']
                if _response[i]['base'] is 110:
                    base_centodieci = 110
                    media_centodieci = _response[i]['media']

        return jsonify({'trenta': media_trenta,
                            'base_trenta': base_trenta,
                            'base_centodieci': base_centodieci,
                            'centodieci': media_centodieci})


@api.route('/api/uniparthenope/current_aa/<token>/<cdsId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, cdsId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "calesa-service-v1/sessioni?cdsId=" + cdsId, headers=headers)
        _response = response.json()

        today = date.today()
        max_year = 0
        for i in range(0, len(_response)):
            if _response[i]['aaSesId'] > max_year:
                max_year = _response[i]['aaSesId']

                dataInizio = re.search(r'\d{2}/\d{2}/\d{4}', _response[i]['dataInizio'])
                dataFine = re.search(r'\d{2}/\d{2}/\d{4}', _response[i]['dataFine'])

                print('D.INIZIO =' + dataInizio)
                print('D.FINE =' + dataFine)


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
