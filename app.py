from flask import Flask, Blueprint, url_for, jsonify, current_app, abort
from flask_restplus import Api, Resource, reqparse
from datetime import datetime
import requests
import json

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

        curr_day = datetime.today()
        max_year = 0
        for i in range(0, len(_response)):
            if _response[i]['aaSesId'] > max_year:
                max_year = _response[i]['aaSesId']

        for i in range(0, len(_response)):
            if _response[i]['aaSesId'] == max_year:
                startDate = extractData(_response[i]['dataInizio'])
                endDate = extractData(_response[i]['dataFine'])

                if curr_day >= startDate and curr_day <= endDate:
                    curr_sem = _response[i]['des']
                    if (curr_sem == "Sessione Anticipata" or curr_sem == "Sessione Estiva"):
                        return jsonify({'curr_sem': _response[i]['des'],
                                        'semestre': "Secondo Semestre"})
                    else:
                        return jsonify({'curr_sem': _response[i]['des'],
                                        'semestre': "Primo Semestre"})


@api.route('/api/uniparthenope/pianoId/<token>/<stuId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, stuId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId, headers=headers)
        _response = response.json()
        pianoId = _response[0]['pianoId']

        return jsonify({'pianoId': pianoId})


@api.route('/api/uniparthenope/exams/<token>/<stuId>/<pianoId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, stuId, pianoId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId + "/" + pianoId, headers=headers)
        _response = response.json()
        my_exams = []

        for i in range(0, len(_response['attivita'])):
            if _response['attivita'][i]['sceltaFlg'] == 1:
                print("MyExam =" + str(_response['attivita'][i]['chiaveADContestualizzata']['adDes']))
                actual_exam = {}
                actual_exam.update({'nome':_response['attivita'][i]['adLibDes'],
                                    'codice': _response['attivita'][i]['adLibCod'],
                                    'adId': _response['attivita'][i]['chiaveADContestualizzata']['adId'],
                                    'CFU': _response['attivita'][i]['peso'],
                                    'annoId': _response['attivita'][i]['scePianoId'],
                                    'adsceId': _response['attivita'][i]['adsceAttId']
                                 })

                my_exams.append(actual_exam)

        return jsonify(my_exams)


@api.route('/api/uniparthenope/checkExam/<token>/<matId>/<examId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, matId, examId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/righe/" + examId, headers=headers)
        _response = response.json()

        return jsonify({'stato': _response['statoDes'],
                        'tipo': _response['tipoInsDes'],
                        'data': _response['esito']['dataEsa'],
                        'lode': _response['esito']['lodeFlg'],
                        'voto': _response['esito']['voto'],
                        })


def extractData(data):
    data_split = data.split()[0]
    export_data = datetime.strptime(data_split, '%d/%m/%Y')

    return export_data


if __name__ == '__main__':
        app.run(ssl_context='adhoc')

