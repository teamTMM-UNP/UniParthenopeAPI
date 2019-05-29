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
        if curr_day.day <= 15 and curr_day.month >= 9:
            academic_year = str(curr_day.year) + " - " + str(curr_day.year+1)
        else:
            academic_year = str(curr_day.year - 1) + " - " + str(curr_day.year)

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
                                        'semestre': "Secondo Semestre",
                                        'aa_accad': academic_year
                                        })
                    else:
                        return jsonify({'curr_sem': _response[i]['des'],
                                        'semestre': "Primo Semestre",
                                        'aa_accad': academic_year})


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

        if response.status_code == 500:
            return jsonify({'stato': "Indefinito",
                            'tipo': "",
                            'data': "",
                            'lode': 0,
                            'voto': "OK",
                            })
        elif _response['statoDes'] == "Superata":
            return jsonify({'stato': _response['statoDes'],
                            'tipo': _response['tipoInsDes'],
                            'data': _response['esito']['dataEsa'].split()[0],
                            'lode': _response['esito']['lodeFlg'],
                            'voto': _response['esito']['voto'],
                            })
        else:
            return jsonify({'stato': _response['statoDes'],
                            'tipo': _response['tipoInsDes'],
                            'data': _response['esito']['dataEsa'],
                            'lode': _response['esito']['lodeFlg'],
                            'voto': _response['esito']['voto'],
                            })


@api.route('/api/uniparthenope/checkAppello/<token>/<cdsId>/<adId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, cdsId, adId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "calesa-service-v1/appelli/" + cdsId + "/" + adId, headers=headers)
        _response = response.json()

        my_exams = []
        for i in range(0, len(_response)):
            if _response[i]['stato'] == "I" or _response[i]['stato'] == "P":
                actual_exam = {}
                actual_exam.update({'esame': _response[i]['adDes'],
                                    'appId': _response[i]['appId'],
                                    'stato': _response[i]['stato'],
                                    'statoDes': _response[i]['statoDes'],
                                    'docente': _response[i]['presidenteCognome'].capitalize(),
                                    'docente_completo': _response[i]['presidenteCognome'].capitalize() + " " + _response[i]['presidenteNome'].capitalize(),
                                    'numIscritti': _response[i]['numIscritti'],
                                    'note': _response[i]['note'],
                                    'descrizione': _response[i]['desApp'],
                                    'dataFine': _response[i]['dataFineIscr'].split()[0],
                                    'dataInizio': _response[i]['dataInizioIscr'].split()[0],
                                    'dataEsame': _response[i]['dataInizioApp'].split()[0],
                                    })

                my_exams.append(actual_exam)

        return jsonify(my_exams)


@api.route('/api/uniparthenope/RecentAD/<adId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, adId):
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("GET", url + "logistica-service-v1/logistica?adId=" + adId, headers=headers)
        _response = response.json()

        max_year = 0
        for i in range(0, len(_response)):
            if _response[i]['chiaveADFisica']['aaOffId'] > max_year:
                max_year = _response[i]['chiaveADFisica']['aaOffId']

        for i in range(0, len(_response)):
            if _response[i]['chiaveADFisica']['aaOffId'] == max_year:
                return jsonify({'adLogId': _response[i]['chiavePartizione']['adLogId'],
                                'inizio': _response[i]['dataInizio'].split()[0],
                                'fine': _response[i]['dataFine'].split()[0],
                                'ultMod': _response[i]['dataModLog'].split()[0]
                                })


@api.route('/api/uniparthenope/infoCourse/<adLogId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, adLogId):
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("GET", url + "logistica-service-v1/logistica/" + adLogId + "/adLogConSyllabus", headers=headers)
        _response = response.json()

        return jsonify({'contenuti': _response[0]['SyllabusAD'][0]['contenuti'],
                        'metodi': _response[0]['SyllabusAD'][0]['metodiDidattici'],
                        'verifica': _response[0]['SyllabusAD'][0]['modalitaVerificaApprendimento'],
                        'obiettivi': _response[0]['SyllabusAD'][0]['obiettiviFormativi'],
                        'prerequisiti': _response[0]['SyllabusAD'][0]['prerequisiti'],
                        'testi': _response[0]['SyllabusAD'][0]['testiRiferimento'],
                        'altro': _response[0]['SyllabusAD'][0]['altreInfo']
                        })


def extractData(data):
    data_split = data.split()[0]
    export_data = datetime.strptime(data_split, '%d/%m/%Y')

    return export_data


if __name__ == '__main__':
        app.run(ssl_context='adhoc')

